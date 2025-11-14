import os
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

from compress import frames_per_step, file_movement
from start import personas
from modules.terrain.terrain_development import TerrainDevelopmentEngine
from modules.social.relationship import SocialNetwork
from modules.environment.environment_manager import EnvironmentManager
from modules.civilization.evolution import CivilizationEvolution
from modules.economy.economy import EconomyEngine

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
    static_url_path="/static",
)
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量存储地形、社会关系和环境数据
terrain_engine = None
social_network = None
environment_manager = None
civilization_manager = None
economy_engine = None
terrain_events_store = []
terrain_events_file = "results/checkpoints/live_simulation/terrain_events.json"

def load_terrain_events_store():
    global terrain_events_store
    try:
        if os.path.exists(terrain_events_file):
            with open(terrain_events_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    terrain_events_store = data
    except Exception as e:
        print(f"Error loading terrain events store: {e}")

def save_terrain_events_store():
    global terrain_events_store
    try:
        os.makedirs(os.path.dirname(terrain_events_file), exist_ok=True)
        with open(terrain_events_file, 'w', encoding='utf-8') as f:
            json.dump(terrain_events_store, f, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving terrain events store: {e}")

# 初始化地形和社会网络系统
if terrain_engine is None:
    terrain_engine = TerrainDevelopmentEngine(width=60, height=60)
    terrain_engine._generate_initial_terrain()

if social_network is None:
    social_network = SocialNetwork()
    # 为现有的角色添加到社会网络中
    for persona in personas:
        social_network.add_agent(persona, {"name": persona})

if environment_manager is None:
    environment_manager = EnvironmentManager(time_scale=10.0, auto_time_flow=True)  # 启用自动时间流逝
if civilization_manager is None:
    civilization_manager = CivilizationEvolution()
if economy_engine is None:
    economy_engine = EconomyEngine()
    # 注册现有角色到经济系统
    for persona in personas:
        economy_engine.register_agent(persona)
        # 基础物资注入，便于交易/合成演示
        try:
            inv = economy_engine.agent_inventories.get(persona)
            if inv:
                inv.add_material(ResourceType.WOOD, 50.0)
                inv.add_material(ResourceType.STONE, 30.0)
                inv.add_material(ResourceType.METAL, 12.0)
                inv.add_material(ResourceType.FOOD, 40.0)
        except Exception:
            pass
    # 初始价格同步一次
    if terrain_engine is not None:
        economy_engine.update_prices(terrain_engine)

# 后台环境更新任务
def update_environment_loop():
    """后台线程，定期更新环境系统"""
    while True:
        try:
            if environment_manager:
                environment_manager.update()
                # 同步文明演化
                if civilization_manager:
                    env_data = environment_manager.get_environment_data()
                    civilization_manager.update(env_data["time"]["current_time"], env_data)
            time.sleep(1)  # 每秒更新一次
        except Exception as e:
            print(f"Environment update error: {e}")
            time.sleep(5)  # 出错时等待5秒

# 启动后台更新线程
update_thread = threading.Thread(target=update_environment_loop, daemon=True)
update_thread.start()

# 后台经济更新任务（价格更新与简易自动交易/合成）
def update_economy_loop():
    """后台线程，定期更新经济价格并产生自动事件"""
    while True:
        try:
            if economy_engine and terrain_engine:
                # 更新价格
                economy_engine.update_prices(terrain_engine)
                # 简易自动事件
                evt = economy_engine.auto_step(agent_ids=list(personas), terrain_engine=terrain_engine)
                if evt:
                    # 通过SocketIO广播经济事件（可选）
                    try:
                        socketio.emit('economy_event', evt)
                    except Exception:
                        pass
            time.sleep(3)
        except Exception as e:
            print(f"Economy update error: {e}")
            time.sleep(5)

economy_thread = threading.Thread(target=update_economy_loop, daemon=True)
economy_thread.start()

# 初始化载入已保存的地形事件
load_terrain_events_store()


@app.route("/", methods=['GET'])
def index():
    global terrain_engine, social_network
    
    name = request.args.get("name", "")          # 记录名称
    step = int(request.args.get("step", 0))      # 回放起始步数
    speed = int(request.args.get("speed", 2))    # 回放速度（0~5）
    zoom = float(request.args.get("zoom", 0.3))  # 画面缩放比例（直播更适配默认 0.3）

    if len(name) > 0:
        compressed_folder = f"results/compressed/{name}"
    else:
        return f"Invalid name of the simulation: '{name}'"
    
    # 初始化地形和社会关系系统
    if terrain_engine is None:
        terrain_engine = TerrainDevelopmentEngine(width=60, height=60)
        terrain_engine._generate_initial_terrain()
    
    if social_network is None:
        social_network = SocialNetwork()
        # 为现有的角色添加到社会网络中
        for persona in personas:
            social_network.add_agent(persona, {"name": persona})

    replay_file = f"{compressed_folder}/{file_movement}"
    if not os.path.exists(replay_file):
        return f"The data file doesn‘t exist: '{replay_file}'<br />Run compress.py to generate the data first."

    with open(replay_file, "r", encoding="utf-8") as f:
        params = json.load(f)

    if step < 1:
        step = 1
    if step > 1:
        # 重新设置回放的起始时间
        t = datetime.fromisoformat(params["start_datetime"])
        dt = t + timedelta(minutes=params["stride"]*(step-1))
        params["start_datetime"] = dt.isoformat()
        step = (step-1) * frames_per_step + 1
        if step >= len(params["all_movement"]):
            step = len(params["all_movement"])-1

        # 重新设置Agent的初始位置
        for agent in params["persona_init_pos"].keys():
            persona_init_pos = params["persona_init_pos"]
            persona_step_pos = params["all_movement"][f"{step}"]
            persona_init_pos[agent] = persona_step_pos[agent]["movement"]

    if speed < 0:
        speed = 0
    elif speed > 5:
        speed = 5
    speed = 2 ** speed

    return render_template(
        "index.html",
        persona_names=personas,
        step=step,
        play_speed=speed,
        zoom=zoom,
        **params
    )


@app.route("/api/terrain", methods=['GET'])
def get_terrain_data():
    """获取地形数据"""
    global terrain_engine
    if terrain_engine is None:
        return jsonify({"error": "Terrain engine not initialized"}), 500
    
    terrain_data = []
    for x in range(terrain_engine.width):
        for y in range(terrain_engine.height):
            tile = terrain_engine.get_tile(x, y)
            if tile:
                terrain_data.append({
                    "x": x,
                    "y": y,
                    "type": tile.terrain_type.value,
                    "elevation": tile.elevation,
                    "development_level": tile.development_level,
                    "buildings": tile.buildings,
                    "population": tile.current_population
                })
    
    return jsonify({"terrain": terrain_data})


@app.route("/api/social", methods=['GET'])
def get_social_data():
    """获取社会关系数据"""
    import sys
    print("=== get_social_data function called ===", flush=True)
    sys.stdout.flush()
    global social_network
    
    print(f"social_network is None: {social_network is None}", flush=True)
    sys.stdout.flush()
    
    if social_network is None:
        print("social_network is None, returning empty relationships", flush=True)
        sys.stdout.flush()
        return jsonify({"relationships": []})
    
    relationships = []
    
    # 尝试从对话记录中分析关系变化
    try:
        conversation_file = "conversation.json"
        if os.path.exists(conversation_file):
            with open(conversation_file, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
            
            print(f"Loaded conversations with {len(conversations)} timestamps", flush=True)
            sys.stdout.flush()
            
            # 分析对话中的情感倾向和互动模式
            agent_interactions = {}
            
            for timestamp, conv_list in conversations.items():
                print(f"Processing timestamp: {timestamp} with {len(conv_list)} conversations", flush=True)
                for conv_data in conv_list:
                    for location_info, dialogues in conv_data.items():
                        print(f"Location info: {location_info}", flush=True)
                        print(f"Number of dialogues: {len(dialogues)}", flush=True)
                        
                        # 从location_info中提取参与者信息 (格式: "agent1 -> agent2 @ location")
                        if ' -> ' in location_info and ' @ ' in location_info:
                            agents_part = location_info.split(' @ ')[0]
                            if ' -> ' in agents_part:
                                agent1, agent2 = agents_part.split(' -> ')
                                agents_in_conversation = [agent1.strip(), agent2.strip()]
                            else:
                                agents_in_conversation = [agents_part.strip()]
                        else:
                            # 从对话内容中提取参与者
                            agents_in_conversation = list(set([dialogue[0] for dialogue in dialogues]))
                        
                        print(f"Agents in conversation: {agents_in_conversation}", flush=True)
                        
                        for dialogue in dialogues:
                            agent_name = dialogue[0]
                            content = dialogue[1]
                            
                            # 分析对话情感倾向
                            positive_keywords = ['喜欢', '很好', '棒', '赞', '支持', '同意', '开心', '高兴', '感谢', '帮助', '好啊', '不错', '有趣', '挺准', '合适']
                            negative_keywords = ['不喜欢', '讨厌', '反对', '不同意', '生气', '失望', '批评', '争论', '问题', '错误']
                            
                            # 检查与其他角色的互动
                            for other_agent in agents_in_conversation:
                                if other_agent != agent_name:
                                    key = tuple(sorted([agent_name, other_agent]))
                                    print(f"Recording interaction between {agent_name} and {other_agent}", flush=True)
                                    
                                    if key not in agent_interactions:
                                        agent_interactions[key] = {
                                            'positive_count': 0,
                                            'negative_count': 0,
                                            'total_interactions': 0,
                                            'last_interaction': timestamp
                                        }
                                    
                                    agent_interactions[key]['total_interactions'] += 1
                                    agent_interactions[key]['last_interaction'] = timestamp
                                    
                                    # 检查情感倾向
                                    if any(keyword in content for keyword in positive_keywords):
                                        agent_interactions[key]['positive_count'] += 1
                                        print(f"Positive interaction detected: {content[:30]}...", flush=True)
                                    elif any(keyword in content for keyword in negative_keywords):
                                        agent_interactions[key]['negative_count'] += 1
                                        print(f"Negative interaction detected: {content[:30]}...", flush=True)
            
            print(f"Total agent interactions found: {len(agent_interactions)}", flush=True)
            sys.stdout.flush()
            
            # 基于分析结果生成关系数据
            for (agent1, agent2), interaction_data in agent_interactions.items():
                total = interaction_data['total_interactions']
                positive = interaction_data['positive_count']
                negative = interaction_data['negative_count']
                
                # 计算关系强度 (0-100)
                if total > 0:
                    positive_ratio = positive / total
                    negative_ratio = negative / total
                    base_strength = min(total * 10, 80)  # 基础强度基于互动次数
                    
                    if positive_ratio > negative_ratio:
                        strength = base_strength + (positive_ratio * 20)
                        rel_type = "FRIEND" if strength > 60 else "ACQUAINTANCE"
                        status = "ACTIVE"
                    elif negative_ratio > positive_ratio:
                        strength = max(base_strength - (negative_ratio * 30), 10)
                        rel_type = "RIVAL" if negative_ratio > 0.3 else "ACQUAINTANCE"
                        status = "TENSE" if negative_ratio > 0.5 else "NEUTRAL"
                    else:
                        strength = base_strength
                        rel_type = "ACQUAINTANCE"
                        status = "NEUTRAL"
                    
                    relationships.append({
                        "agent1": agent1,
                        "agent2": agent2,
                        "type": rel_type,
                        "strength": min(int(strength), 100),
                        "status": status,
                        "last_interaction": f"2024-02-13T{interaction_data['last_interaction'].split('-')[1]}:00",
                        "interaction_count": total,
                        "positive_interactions": positive,
                        "negative_interactions": negative
                    })
            
            print(f"Generated {len(relationships)} relationships", flush=True)
            sys.stdout.flush()
    
    except Exception as e:
        print(f"Error analyzing social relationships: {e}", flush=True)
        sys.stdout.flush()
    
    # 如果没有从对话中分析出关系，使用默认关系
    if not relationships:
        print("No relationships found from conversations, using default data", flush=True)
        sys.stdout.flush()
        for rel in social_network.relationships.values():
            relationships.append({
                "agent1": rel.agent1_id,
                "agent2": rel.agent2_id,
                "type": rel.relationship_type.value,
                "intimacy": rel.intimacy_level,
                "trust": rel.trust_level,
                "status": rel.status.value
            })
    
    return jsonify({"relationships": relationships})


@app.route("/api/terrain/events", methods=['GET'])
def get_terrain_events():
    """获取地形变化事件"""
    # 先使用前端上报的实时事件
    events = list(terrain_events_store)
    
    # 尝试从对话记录中提取地形相关事件
    try:
        conversation_file = "results/checkpoints/live_simulation/conversation.json"
        if os.path.exists(conversation_file):
            with open(conversation_file, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
            
            # 分析对话内容，提取地形相关事件
            for timestamp, conv_list in conversations.items():
                for conv_data in conv_list:
                    for location_info, dialogues in conv_data.items():
                        # 从location_info中提取位置信息
                        location_name = location_info.split(' @ ')[-1] if ' @ ' in location_info else location_info
                        
                        # 分析对话内容是否包含地形相关关键词
                        for dialogue in dialogues:
                            agent_name = dialogue[0]
                            content = dialogue[1]
                            
                            # 检查是否包含建设、装修、改造等关键词
                            if any(keyword in content for keyword in ['建造', '装修', '改造', '建设', '盖房', '修建', '施工', '房子', '建筑']):
                                events.append({
                                    "timestamp": f"2024-02-13T{timestamp.split('-')[1]}:00",
                                    "type": "building_construction",
                                    "location": {"x": 25, "y": 30},
                                    "description": f"{agent_name}在{location_name}提到了建设相关的话题：{content[:50]}...",
                                    "agent": agent_name
                                })
                            
                            # 检查是否包含花园、种植、绿化等关键词
                            elif any(keyword in content for keyword in ['花园', '种植', '绿化', '植物', '树木', '草地', '冬天', '雪花', '风景']):
                                events.append({
                                    "timestamp": f"2024-02-13T{timestamp.split('-')[1]}:00",
                                    "type": "terrain_development",
                                    "location": {"x": 20, "y": 25},
                                    "description": f"{agent_name}在{location_name}谈论了环境美化：{content[:50]}...",
                                    "agent": agent_name
                                })
                            
                            # 检查是否包含聚会、见面、交流等关键词
                            elif any(keyword in content for keyword in ['聚会', '见面', '一起', '交流', '聊天', '讨论', '帮助', '合作', '准备']):
                                events.append({
                                    "timestamp": f"2024-02-13T{timestamp.split('-')[1]}:00",
                                    "type": "social_gathering",
                                    "location": {"x": 30, "y": 35},
                                    "description": f"社交活动：{agent_name}在{location_name}说：{content[:50]}...",
                                    "agent": agent_name,
                                    "social_impact": "社交关系得到加强"
                                })
    
    except Exception as e:
        print(f"Error reading conversation file: {e}")
    
    # 如果没有任何事件，使用默认事件
    if not events:
        events = [
            {
                "timestamp": "2024-02-13T09:30:00",
                "type": "building_construction",
                "location": {"x": 25, "y": 30},
                "description": "约翰开始建造新房屋",
                "agent": "约翰"
            },
            {
                "timestamp": "2024-02-13T10:15:00",
                "type": "terrain_development",
                "location": {"x": 20, "y": 25},
                "description": "梅在附近开辟了一个小花园",
                "agent": "梅"
            },
            {
                "timestamp": "2024-02-13T11:00:00",
                "type": "social_gathering",
                "location": {"x": 30, "y": 35},
                "description": "汤姆和简在新建的公园里聊天，增进了友谊",
                "agents": ["汤姆", "简"],
                "social_impact": "友谊度 +15"
            }
        ]
    
    # 限制事件数量并按时间排序
    events = sorted(events, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    return jsonify({"events": events})


@app.route("/api/terrain/events", methods=['POST'])
def post_terrain_event():
    """前端上报地形/建筑事件，持久化并在列表中显示"""
    global terrain_events_store
    try:
        payload = request.get_json(force=True) or {}
        # 最小必填字段校验与默认值
        evt_type = payload.get('type') or 'building_construction'
        timestamp = payload.get('timestamp') or datetime.utcnow().isoformat()
        description = payload.get('description') or ''
        agent = payload.get('agent') or payload.get('agents') or '系统'
        location = payload.get('location') or {"x": 0, "y": 0}
        building = payload.get('building')

        event = {
            "type": evt_type,
            "timestamp": timestamp,
            "description": description,
            "agent": agent if isinstance(agent, str) else None,
            "agents": agent if isinstance(agent, list) else None,
            "location": location,
        }
        if building:
            event["building"] = building

        terrain_events_store.append(event)
        # 限制内存中的事件数量，避免无限增长
        if len(terrain_events_store) > 200:
            terrain_events_store = terrain_events_store[-200:]
        save_terrain_events_store()

        # 返回标准响应
        return jsonify({
            "status": "success",
            "event": event
        })
    except Exception as e:
        print(f"Error posting terrain event: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route("/api/environment", methods=['GET'])
def get_environment_data():
    """获取完整的环境数据"""
    global environment_manager
    
    try:
        # 更新环境系统
        environment_manager.update()
        
        # 获取环境数据
        env_data = environment_manager.get_environment_data()
        
        return jsonify({
            "status": "success",
            "data": env_data
        })
    
    except Exception as e:
        print(f"Error getting environment data: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/weather", methods=['GET'])
def get_weather_data():
    """获取天气数据"""
    global environment_manager
    
    try:
        environment_manager.update()
        env_data = environment_manager.get_environment_data()
        
        return jsonify({
            "status": "success",
            "weather": env_data["weather"],
            "visibility": env_data["visibility"],
            "comfort_level": env_data["comfort_level"]
        })
    
    except Exception as e:
        print(f"Error getting weather data: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/weather", methods=['POST'])
def set_weather():
    """设置天气"""
    global environment_manager
    
    try:
        data = request.get_json()
        weather_type = data.get('weather_type', data.get('type', 'sunny'))
        intensity = data.get('intensity', 1.0)
        
        environment_manager.set_weather(weather_type, intensity)
        
        return jsonify({
            "status": "success",
            "message": f"Weather set to {weather_type} with intensity {intensity}"
        })
    
    except Exception as e:
        print(f"Error setting weather: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/time", methods=['GET'])
def get_time_data():
    """获取时间数据"""
    global environment_manager
    
    try:
        environment_manager.update()
        env_data = environment_manager.get_environment_data()
        
        return jsonify({
            "status": "success",
            "time": env_data["time"],
            "combined_effects": env_data["combined_effects"]
        })
    
    except Exception as e:
        print(f"Error getting time data: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/time/scale", methods=['POST'])
def set_time_scale():
    """设置时间缩放"""
    global environment_manager
    
    try:
        data = request.get_json()
        scale = data.get('scale', 1.0)
        
        environment_manager.set_time_scale(scale)
        
        return jsonify({
            "status": "success",
            "message": f"Time scale set to {scale}x"
        })
    
    except Exception as e:
        print(f"Error setting time scale: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/time/advance", methods=['POST'])
def advance_time():
    """快进时间"""
    global environment_manager
    
    try:
        data = request.get_json()
        hours = data.get('hours', 1.0)
        
        environment_manager.advance_time(hours)
        
        return jsonify({
            "status": "success",
            "message": f"Time advanced by {hours} hours"
        })
    
    except Exception as e:
        print(f"Error advancing time: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/environment/events", methods=['GET'])
def get_environment_events():
    """获取环境事件"""
    global environment_manager
    
    try:
        limit = request.args.get('limit', 10, type=int)
        events = environment_manager.get_recent_events(limit)
        
        return jsonify({
            "status": "success",
            "events": events
        })
    
    except Exception as e:
        print(f"Error getting environment events: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/environment/history", methods=['GET'])
def get_environment_history():
    """获取环境历史"""
    global environment_manager
    
    try:
        hours = request.args.get('hours', 24, type=int)
        history = environment_manager.get_environment_history(hours)
        
        return jsonify({
            "status": "success",
            "history": history
        })
    
    except Exception as e:
        print(f"Error getting environment history: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/environment/status", methods=['GET'])
def get_environment_status():
    """获取环境状态摘要"""
    global environment_manager
    
    try:
        environment_manager.update()
        status_summary = environment_manager.get_status_summary()
        
        return jsonify({
            "status": "success",
            "summary": status_summary
        })
    
    except Exception as e:
        print(f"Error getting environment status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/economy/state", methods=['GET'])
def get_economy_state():
    """获取经济系统状态（价格、各Agent钱包与库存）"""
    global economy_engine, terrain_engine
    try:
        if economy_engine is None:
            return jsonify({"status": "error", "message": "Economy engine not initialized"}), 500
        # 同步一次价格
        if terrain_engine is not None:
            economy_engine.update_prices(terrain_engine)
        return jsonify({
            "status": "success",
            "state": economy_engine.get_state()
        })
    except Exception as e:
        print(f"Error getting economy state: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/economy/events", methods=['GET'])
def get_economy_events():
    """获取最近的经济事件（交易、合成等）"""
    global economy_engine
    try:
        limit = request.args.get('limit', 20, type=int)
        events = economy_engine.get_events(limit)
        return jsonify({
            "status": "success",
            "events": events
        })
    except Exception as e:
        print(f"Error getting economy events: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/economy/trade", methods=['POST'])
def post_economy_trade():
    """提交交易提议（资源/物品/货币），返回执行结果"""
    global economy_engine, terrain_engine
    try:
        payload = request.get_json(force=True) or {}
        sender = payload.get('sender')
        receiver = payload.get('receiver')
        offer_resources = payload.get('offer_resources')  # {"wood": 5.0} 等，使用 ResourceType.value
        request_resources = payload.get('request_resources')
        offer_items = payload.get('offer_items')          # {"food_pack": 1} 等，使用 ItemType.value
        request_items = payload.get('request_items')
        offer_money = float(payload.get('offer_money', 0.0))
        request_money = float(payload.get('request_money', 0.0))

        if not sender or not receiver:
            return jsonify({"status": "error", "message": "sender/receiver required"}), 400

        result = economy_engine.propose_trade(
            sender=sender,
            receiver=receiver,
            offer_resources=offer_resources,
            request_resources=request_resources,
            offer_items=offer_items,
            request_items=request_items,
            offer_money=offer_money,
            request_money=request_money,
        )

        # 每次交易后根据资源变化更新一次价格
        if terrain_engine is not None:
            economy_engine.update_prices(terrain_engine)

        return jsonify(result)
    except Exception as e:
        print(f"Error posting economy trade: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/economy/craft", methods=['POST'])
def post_economy_craft():
    """提交合成请求（例如制作食物包或砖）"""
    global economy_engine
    try:
        payload = request.get_json(force=True) or {}
        agent_id = payload.get('agent_id')
        recipe_id = payload.get('recipe_id')
        if not agent_id or not recipe_id:
            return jsonify({"status": "error", "message": "agent_id/recipe_id required"}), 400
        result = economy_engine.craft(agent_id, recipe_id)
        return jsonify(result)
    except Exception as e:
        print(f"Error posting economy craft: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == "__main__":
    socketio.run(app, debug=True, port=8000)

@app.route("/api/civilization/state", methods=['GET'])
def get_civilization_state():
    """获取文明演化状态"""
    global civilization_manager, environment_manager
    try:
        environment_manager.update()
        env_data = environment_manager.get_environment_data()
        civilization_manager.update(env_data["time"]["current_time"], env_data)
        state = civilization_manager.get_state()
        return jsonify({
            "status": "success",
            "state": state
        })
    except Exception as e:
        print(f"Error getting civilization state: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/civilization/events", methods=['GET'])
def get_civilization_events():
    """获取文明演化事件"""
    global civilization_manager
    try:
        limit = request.args.get('limit', 10, type=int)
        events = civilization_manager.get_recent_events(limit)
        return jsonify({
            "status": "success",
            "events": events
        })
    except Exception as e:
        print(f"Error getting civilization events: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/civilization/command", methods=['POST'])
def post_civilization_command():
    """发布AI文明指令，影响文明状态并记录事件"""
    global civilization_manager, environment_manager
    try:
        payload = request.get_json(force=True) or {}
        action = payload.get('action') or payload.get('type') or ''
        intensity = payload.get('intensity') or payload.get('value') or 1.0
        metadata = payload.get('metadata') or {}

        # 同步一次环境与时间，确保演化更新
        environment_manager.update()
        env_data = environment_manager.get_environment_data()
        civilization_manager.update(env_data["time"]["current_time"], env_data)

        applied_event = civilization_manager.apply_directive(action, intensity, metadata)
        state = civilization_manager.get_state()
        return jsonify({
            "status": "success",
            "applied_event": applied_event,
            "state": state
        })
    except Exception as e:
        print(f"Error applying civilization directive: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
