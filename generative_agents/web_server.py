import os
import json
import copy
import threading
import time
import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from modules.agent_generator import AgentGenerator
from modules.game import create_game, get_game
from modules import utils
from start import personas, get_config

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
    static_url_path="/static",
)

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化角色生成器
agent_generator = AgentGenerator()

# 角色保存路径
AGENTS_BASE_PATH = "frontend/static/assets/village/agents"

# 实时模拟相关变量
simulation_thread = None
simulation_running = False
simulation_paused = False
current_simulation = None
simulation_lock = threading.Lock()


class RealTimeSimulation:
    """实时模拟类"""
    
    def __init__(self, name, stride=10):
        self.name = name
        self.stride = stride
        self.step_count = 0
        self.start_time = datetime.datetime.now()
        self.agent_status = {}
        self.game_instance = None
        self.load_agents_from_config()
    
    def load_agents_from_config(self):
        """从配置文件加载角色信息并初始化游戏实例"""
        # 初始化游戏实例
        try:
            from start import get_config
            import datetime
            
            # 创建游戏配置
            start_time = datetime.datetime.now().strftime("%Y%m%d-%H:%M")
            config = get_config(start_time, 10, personas)
            
            # 创建游戏实例
            static_root = "frontend/static"
            conversation = {}
            logger = utils.create_io_logger("info")
            
            self.game_instance = create_game(self.name, static_root, config, conversation, logger=logger)
            print(f"Game instance created successfully with {len(self.game_instance.agents)} agents")
            
        except Exception as e:
            print(f"Error creating game instance: {e}")
            self.game_instance = None
        
        # 加载agent状态
        if os.path.exists(AGENTS_BASE_PATH):
            for agent_folder in os.listdir(AGENTS_BASE_PATH):
                agent_path = os.path.join(AGENTS_BASE_PATH, agent_folder)
                config_path = os.path.join(agent_path, 'agent.json')
                
                if os.path.isdir(agent_path) and os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        agent_name = config.get('name', agent_folder)
                        coord = config.get('coord', [50, 50])
                        currently = config.get('currently', f'{agent_name}正在活动')
                        
                        self.agent_status[agent_name] = {
                            "coord": coord,
                            "currently": currently,
                            "original_coord": coord.copy(),
                            "move_direction": [1, 0]  # 移动方向
                        }
                        
                    except Exception as e:
                        print(f"读取角色配置失败 {agent_folder}: {e}")
    
    def simulate_step(self):
        """执行一步模拟 - 真正调用AI思考"""
        global simulation_running, simulation_paused
        
        if not simulation_running or simulation_paused:
            return None
            
        self.step_count += 1
        
        # 收集所有角色的移动和状态信息
        movement_data = {}
        
        # 如果有游戏实例，使用真实的AI思考逻辑
        if self.game_instance:
            for name in list(self.agent_status.keys()):
                try:
                    # 调用agent的真实思考逻辑
                    agent = self.game_instance.get_agent(name)
                    if not agent:
                        print(f"Agent {name} not found in game instance")
                        continue
                    
                    # 执行AI思考
                    status = self.agent_status[name]
                    plan = self.game_instance.agent_think(name, status)
                    
                    # 获取agent的当前状态
                    if plan and "plan" in plan:
                        plan_data = plan["plan"]
                        
                        # 更新位置（如果有路径）
                        if plan_data.get("path"):
                            new_coord = plan_data["path"][-1]
                            status["coord"] = new_coord
                        
                        # 获取当前活动描述
                        currently = agent.scratch.currently if hasattr(agent, 'scratch') else f"{name}在活动"
                        status["currently"] = currently
                        
                        # 收集移动数据
                        movement_data[name] = {
                            "movement": status["coord"],
                            "currently": currently,
                            "action": currently
                        }
                        
                        # 获取最近的对话
                        if hasattr(agent, 'chats') and agent.chats:
                            recent_chats = agent.chats[-1:] if len(agent.chats) > 0 else []
                            for chat_partner, chat_content in recent_chats:
                                if chat_content:
                                    movement_data[name]["recent_chat"] = f"{name}对{chat_partner}: {chat_content}"
                        
                        print(f"[步骤 {self.step_count}] {name}: {currently} at {status['coord']}")
                    
                except Exception as e:
                    print(f"Error simulating agent {name}: {e}")
                    import traceback
                    traceback.print_exc()
                    # 出错时使用简单的随机移动
                    import random
                    status = self.agent_status[name]
                    original_coord = status.get("original_coord", status["coord"])
                    new_x = original_coord[0] + random.randint(-5, 5)
                    new_y = original_coord[1] + random.randint(-5, 5)
                    new_x = max(10, min(90, new_x))
                    new_y = max(10, min(90, new_y))
                    status["coord"] = [new_x, new_y]
                    movement_data[name] = {
                        "movement": status["coord"],
                        "currently": status.get("currently", f"{name}在活动"),
                        "action": f"{name}正在移动"
                    }
        else:
            # 没有游戏实例时，使用简单的随机移动
            print("警告：游戏实例不存在，使用简单模拟")
            for name, status in self.agent_status.items():
                try:
                    import random
                    original_coord = status.get("original_coord", status["coord"])
                    new_x = original_coord[0] + random.randint(-5, 5)
                    new_y = original_coord[1] + random.randint(-5, 5)
                    new_x = max(10, min(90, new_x))
                    new_y = max(10, min(90, new_y))
                    status["coord"] = [new_x, new_y]
                    movement_data[name] = {
                        "movement": status["coord"],
                        "currently": status.get("currently", f"{name}在活动"),
                        "action": f"{name}正在移动到({new_x}, {new_y})"
                    }
                except Exception as e:
                    print(f"Error in simple simulation for {name}: {e}")
                    continue
        
        # 计算当前时间
        current_time = self.start_time + datetime.timedelta(seconds=self.step_count * self.stride)
        
        # 获取对话数据
        conversation_data = {}
        try:
            # 如果有游戏实例，尝试获取真实对话数据
            if self.game_instance and hasattr(self.game_instance, 'conversation'):
                time_key = current_time.strftime("%Y%m%d-%H:%M")
                if time_key in self.game_instance.conversation:
                    conversation_data[time_key] = self.game_instance.conversation[time_key]
                
                # 获取agent的chats数据
                for name in self.agent_status.keys():
                    try:
                        agent = self.game_instance.get_agent(name)
                        if agent and hasattr(agent, 'chats') and agent.chats:
                            recent_chats = agent.chats[-3:] if len(agent.chats) > 3 else agent.chats
                            for chat_name, chat_content in recent_chats:
                                if name in movement_data:
                                    movement_data[name]["recent_chat"] = f"{chat_name}: {chat_content}"
                    except Exception as e:
                        print(f"Error getting chats for agent {name}: {e}")
                        continue
            else:
                # 如果没有游戏实例，生成一些模拟对话数据
                import random
                
                # 每10步生成一次模拟对话
                if self.step_count % 10 == 0:
                    agent_names = list(self.agent_status.keys())
                    if len(agent_names) >= 2:
                        # 随机选择两个agent进行对话
                        speaker = random.choice(agent_names)
                        listener = random.choice([name for name in agent_names if name != speaker])
                        
                        # 生成简单的对话内容
                        conversations = [
                            f"{speaker}: 今天天气真不错！",
                            f"{speaker}: 你好，最近怎么样？",
                            f"{speaker}: 我正在忙着工作。",
                            f"{speaker}: 有什么新鲜事吗？",
                            f"{speaker}: 这个地方真美丽。"
                        ]
                        
                        chat_content = random.choice(conversations)
                        
                        # 添加到movement_data中
                        if speaker in movement_data:
                            movement_data[speaker]["recent_chat"] = chat_content
                        if listener in movement_data:
                            movement_data[listener]["recent_chat"] = f"听到了{speaker}的话"
                            
        except Exception as e:
            print(f"Error getting conversation data: {e}")
        
        # 构造返回数据 - 使用前端期望的格式
        sim_data = {
            "step": self.step_count,
            "current_time": current_time.isoformat(),
            "agents": movement_data,  # 前端期望 "agents" 字段
            "movement": movement_data,  # 保持兼容性
            "conversation": conversation_data,
            "running": True
        }
        
        return sim_data


@app.route("/", methods=['GET'])
def index():
    """主页 - 显示现有的游戏界面"""
    # 获取现有角色列表和位置信息
    persona_names = []
    persona_init_pos = {}
    
    if os.path.exists(AGENTS_BASE_PATH):
        for agent_folder in os.listdir(AGENTS_BASE_PATH):
            agent_path = os.path.join(AGENTS_BASE_PATH, agent_folder)
            config_path = os.path.join(agent_path, 'agent.json')
            
            if os.path.isdir(agent_path) and os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    agent_name = config.get('name', agent_folder)
                    persona_names.append(agent_name)
                    
                    # 获取角色坐标，如果没有则分配随机位置
                    coord = config.get('coord', [])
                    if len(coord) >= 2:
                        persona_init_pos[agent_name] = coord[:2]
                    else:
                        # 分配随机位置
                        import random
                        persona_init_pos[agent_name] = [
                            random.randint(10, 90),
                            random.randint(10, 90)
                        ]
                        # 保存更新的坐标到配置文件
                        config['coord'] = persona_init_pos[agent_name]
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(config, f, indent=2, ensure_ascii=False)
                        
                except Exception as e:
                    print(f"读取角色配置失败 {agent_folder}: {e}")

    # 检查是否有现有的模拟正在运行
    global current_simulation, simulation_running
    if not current_simulation and not simulation_running:
        # 自动启动一个实时模拟
        try:
            simulation_name = f'web_auto_{int(time.time())}'
            current_simulation = RealTimeSimulation(simulation_name, 10)
            simulation_running = True
            
            # 启动模拟线程
            global simulation_thread
            simulation_thread = threading.Thread(target=run_simulation)
            simulation_thread.daemon = True
            simulation_thread.start()
            
            print(f"自动启动实时模拟: {simulation_name}")
        except Exception as e:
            print(f"自动启动模拟失败: {e}")

    # 渲染模板
    return render_template(
        "index.html",
        persona_init_pos=persona_init_pos,
        step=0,
        sec_per_step=10,
        zoom=1.0,
        play_speed=2,
        start_datetime="2023-02-13 00:00:00",
        all_movement={"conversation": {}}
    )


@app.route("/add_agent", methods=['GET'])
def add_agent_page():
    """角色添加页面"""
    return render_template("add_agent.html")


@app.route("/api/get_character_images", methods=['GET'])
def get_character_images():
    """获取可用的角色形象列表"""
    try:
        characters_path = "frontend/static/assets/characters"
        character_images = []
        
        if os.path.exists(characters_path):
            for filename in os.listdir(characters_path):
                if filename.lower().endswith('.png'):
                    character_images.append(filename)
        
        # 按文件名排序
        character_images.sort()
        
        return jsonify(character_images)
        
    except Exception as e:
        print(f"获取角色形象列表时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@app.route("/api/generate_agent", methods=['POST'])
def generate_agent():
    """生成角色API"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        # 验证必填字段
        required_fields = ['name', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 生成角色配置
        try:
            config = agent_generator.generate_agent_config(data)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'生成角色配置失败: {str(e)}'
            }), 500
        
        # 生成角色图片
        try:
            images = agent_generator.generate_agent_images(config, data)
        except Exception as e:
            # 图片生成失败不影响整体流程，使用默认图片
            print(f"图片生成失败: {e}")
            images = {
                'texture': '/static/assets/default_image.png'
            }
        
        return jsonify({
            'success': True,
            'data': {
                'config': config,
                'images': images
            }
        })
        
    except Exception as e:
        print(f"生成角色时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@app.route("/api/save_agent", methods=['POST'])
def save_agent():
    """保存角色API"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data or 'config' not in data or 'images' not in data:
            return jsonify({
                'success': False,
                'message': '请求数据格式错误'
            }), 400
        
        config = data['config']
        images = data['images']
        
        # 验证配置数据
        if not config.get('name'):
            return jsonify({
                'success': False,
                'message': '角色名称不能为空'
            }), 400
        
        # 确保保存目录存在
        os.makedirs(AGENTS_BASE_PATH, exist_ok=True)
        
        # 保存角色到文件夹
        try:
            folder_path = agent_generator.save_agent_to_folder(
                config, images, AGENTS_BASE_PATH
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'保存角色失败: {str(e)}'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'folder_path': folder_path,
                'agent_name': config['name']
            }
        })
        
    except Exception as e:
        print(f"保存角色时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@app.route("/api/agents", methods=['GET'])
def list_agents():
    """获取所有角色列表"""
    try:
        agents = []
        
        if os.path.exists(AGENTS_BASE_PATH):
            for agent_folder in os.listdir(AGENTS_BASE_PATH):
                agent_path = os.path.join(AGENTS_BASE_PATH, agent_folder)
                config_path = os.path.join(agent_path, 'agent.json')
                
                if os.path.isdir(agent_path) and os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        # 检查图片文件
                        portrait_path = os.path.join(agent_path, 'portrait.png')
                        image_path = os.path.join(agent_path, 'image.png')
                        
                        agent_info = {
                            'name': config.get('name', agent_folder),
                            'folder': agent_folder,
                            'config': config,
                            'has_portrait': os.path.exists(portrait_path),
                            'has_image': os.path.exists(image_path),
                            'created_at': config.get('created_at', '')
                        }
                        
                        agents.append(agent_info)
                        
                    except Exception as e:
                        print(f"读取角色配置失败 {agent_folder}: {e}")
                        continue
        
        return jsonify({
            'success': True,
            'data': {
                'agents': agents,
                'total': len(agents)
            }
        })
        
    except Exception as e:
        print(f"获取角色列表时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@app.route("/api/agent/<agent_name>", methods=['GET'])
def get_agent(agent_name):
    """获取特定角色信息"""
    try:
        agent_path = os.path.join(AGENTS_BASE_PATH, agent_name)
        config_path = os.path.join(agent_path, 'agent.json')
        
        if not os.path.exists(config_path):
            return jsonify({
                'success': False,
                'message': '角色不存在'
            }), 404
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查图片文件
        portrait_path = os.path.join(agent_path, 'portrait.png')
        image_path = os.path.join(agent_path, 'image.png')
        
        agent_info = {
            'name': config.get('name', agent_name),
            'folder': agent_name,
            'config': config,
            'has_portrait': os.path.exists(portrait_path),
            'has_image': os.path.exists(image_path),
            'portrait_url': f'/static/assets/village/agents/{agent_name}/portrait.png' if os.path.exists(portrait_path) else None,
            'image_url': f'/static/assets/village/agents/{agent_name}/image.png' if os.path.exists(image_path) else None
        }
        
        return jsonify({
            'success': True,
            'data': agent_info
        })
        
    except Exception as e:
        print(f"获取角色信息时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@app.route("/api/agent/<agent_name>", methods=['DELETE'])
def delete_agent(agent_name):
    """删除角色"""
    try:
        import shutil
        
        agent_path = os.path.join(AGENTS_BASE_PATH, agent_name)
        
        if not os.path.exists(agent_path):
            return jsonify({
                'success': False,
                'message': '角色不存在'
            }), 404
        
        # 删除整个角色文件夹
        shutil.rmtree(agent_path)
        
        return jsonify({
            'success': True,
            'message': f'角色 {agent_name} 已删除'
        })
        
    except Exception as e:
        print(f"删除角色时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@app.route("/api/add_agent_to_game", methods=['POST'])
def add_agent_to_game():
    """动态添加角色到游戏中"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        agent_name = data.get('agent_name')
        if not agent_name:
            return jsonify({
                'success': False,
                'message': '角色名称不能为空'
            }), 400
        
        # 检查角色是否存在
        agent_path = os.path.join(AGENTS_BASE_PATH, agent_name)
        config_path = os.path.join(agent_path, 'agent.json')
        
        if not os.path.exists(config_path):
            return jsonify({
                'success': False,
                'message': '角色不存在'
            }), 404
        
        # 读取角色配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取或分配角色位置
        coord = config.get('coord', [])
        if len(coord) < 2:
            import random
            coord = [
                random.randint(10, 90),
                random.randint(10, 90)
            ]
            # 更新配置文件中的坐标
            config['coord'] = coord
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 检查图片文件
        portrait_path = os.path.join(agent_path, 'portrait.png')
        image_path = os.path.join(agent_path, 'image.png')
        
        agent_info = {
            'name': config.get('name', agent_name),
            'folder': agent_name,
            'coord': coord[:2],
            'config': config,
            'portrait_url': f'/static/assets/village/agents/{agent_name}/portrait.png' if os.path.exists(portrait_path) else None,
            'image_url': f'/static/assets/village/agents/{agent_name}/image.png' if os.path.exists(image_path) else None
        }
        
        return jsonify({
            'success': True,
            'message': f'角色 {agent_name} 已添加到游戏中',
            'data': agent_info
        })
        
    except Exception as e:
        print(f"添加角色到游戏时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@app.route("/api/game_agents", methods=['GET'])
def get_game_agents():
    """获取当前游戏中的所有角色"""
    try:
        persona_names = []
        persona_init_pos = {}
        
        if os.path.exists(AGENTS_BASE_PATH):
            for agent_folder in os.listdir(AGENTS_BASE_PATH):
                agent_path = os.path.join(AGENTS_BASE_PATH, agent_folder)
                config_path = os.path.join(agent_path, 'agent.json')
                
                if os.path.isdir(agent_path) and os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        agent_name = config.get('name', agent_folder)
                        persona_names.append(agent_name)
                        
                        # 获取角色坐标
                        coord = config.get('coord', [])
                        if len(coord) >= 2:
                            persona_init_pos[agent_name] = coord[:2]
                        else:
                            # 分配随机位置
                            import random
                            coord = [
                                random.randint(10, 90),
                                random.randint(10, 90)
                            ]
                            persona_init_pos[agent_name] = coord
                            
                    except Exception as e:
                        print(f"读取角色配置失败 {agent_folder}: {e}")
                        continue
        
        return jsonify({
            'success': True,
            'data': {
                'persona_names': persona_names,
                'persona_init_pos': persona_init_pos,
                'total': len(persona_names)
            }
        })
        
    except Exception as e:
        print(f"获取游戏角色列表时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


# 实时模拟控制API
@app.route("/api/simulation/start", methods=['POST'])
def start_simulation():
    """开始实时模拟"""
    global simulation_thread, simulation_running, simulation_paused, current_simulation
    
    with simulation_lock:
        if simulation_running:
            return jsonify({
                'success': False,
                'message': '模拟已在运行中'
            }), 400
        
        try:
            data = request.get_json() or {}
            simulation_name = data.get('name', f'realtime_{int(time.time())}')
            stride = data.get('stride', 10)
            
            # 创建新的模拟实例
            current_simulation = RealTimeSimulation(simulation_name, stride)
            simulation_running = True
            simulation_paused = False
            
            # 启动模拟线程
            simulation_thread = threading.Thread(target=run_simulation)
            simulation_thread.daemon = True
            simulation_thread.start()
            
            return jsonify({
                'success': True,
                'message': '实时模拟已启动',
                'simulation_name': simulation_name
            })
            
        except Exception as e:
            simulation_running = False
            return jsonify({
                'success': False,
                'message': f'启动模拟失败: {str(e)}'
            }), 500


@app.route("/api/simulation/pause", methods=['POST'])
def pause_simulation():
    """暂停/恢复实时模拟"""
    global simulation_paused
    
    with simulation_lock:
        if not simulation_running:
            return jsonify({
                'success': False,
                'message': '没有正在运行的模拟'
            }), 400
        
        simulation_paused = not simulation_paused
        status = "已暂停" if simulation_paused else "已恢复"
        
        return jsonify({
            'success': True,
            'message': f'模拟{status}',
            'paused': simulation_paused
        })


@app.route("/api/simulation/stop", methods=['POST'])
def stop_simulation():
    """停止实时模拟"""
    global simulation_running, simulation_paused, current_simulation
    
    with simulation_lock:
        if not simulation_running:
            return jsonify({
                'success': False,
                'message': '没有正在运行的模拟'
            }), 400
        
        simulation_running = False
        simulation_paused = False
        current_simulation = None
        
        return jsonify({
            'success': True,
            'message': '模拟已停止'
        })


@app.route("/api/simulation/status", methods=['GET'])
def get_simulation_status():
    """获取模拟状态"""
    return jsonify({
        'success': True,
        'running': simulation_running,
        'paused': simulation_paused,
        'step': current_simulation.step_count if current_simulation else 0,
        'name': current_simulation.name if current_simulation else None
    })


def run_simulation():
    """模拟运行线程"""
    global simulation_running, current_simulation
    
    print(f"=== 实时模拟已启动 ===")
    print(f"模拟名称: {current_simulation.name if current_simulation else 'Unknown'}")
    print(f"步进间隔: {current_simulation.stride if current_simulation else 10} 分钟")
    print(f"使用真实AI: {'是' if current_simulation and current_simulation.game_instance else '否'}")
    
    while simulation_running and current_simulation:
        try:
            if not simulation_paused:
                print(f"\n--- 执行步骤 {current_simulation.step_count + 1} ---")
                
                # 执行一步模拟
                sim_data = current_simulation.simulate_step()
                
                if sim_data:
                    # 通过WebSocket发送数据到前端
                    socketio.emit('simulation_update', sim_data)
                    print(f"✓ 已发送更新到前端，包含 {len(sim_data.get('agents', {}))} 个角色")
                else:
                    print("⚠ 模拟步骤返回空数据")
            
            # 控制模拟速度（默认每秒一步，可以调整）
            # 如果你想加快模拟，减小这个值；如果想减慢，增大这个值
            time.sleep(2)  # 2秒一步，给AI足够时间思考
            
        except Exception as e:
            print(f"❌ 模拟错误: {e}")
            import traceback
            traceback.print_exc()
            simulation_running = False
            socketio.emit('simulation_error', {'message': str(e)})
            break
    
    print(f"\n=== 实时模拟已停止 ===")


# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('Client connected')
    emit('connected', {'message': '已连接到实时模拟服务器'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('Client disconnected')


@socketio.on('request_current_state')
def handle_request_current_state():
    """请求当前状态"""
    if current_simulation and simulation_running:
        # 发送当前所有角色的位置信息
        movement_data = {}
        for name, status in current_simulation.agent_status.items():
            try:
                movement_data[name] = {
                    "movement": status["coord"],
                    "currently": status["currently"],
                    "action": f"{name}正在移动到({status['coord'][0]}, {status['coord'][1]})"
                }
            except Exception as e:
                print(f"获取agent {name} 状态失败: {e}")
                movement_data[name] = {
                    "movement": status["coord"],
                    "currently": f"{name} 正在小镇中活动",
                    "action": ""
                }
        
        emit('current_state', {
            'step': current_simulation.step_count,
            'movement': movement_data,
            'running': simulation_running,
            'paused': simulation_paused
        })
    else:
        # 如果没有运行的模拟，发送静态agent位置
        persona_init_pos = {}
        if os.path.exists(AGENTS_BASE_PATH):
            for agent_folder in os.listdir(AGENTS_BASE_PATH):
                agent_path = os.path.join(AGENTS_BASE_PATH, agent_folder)
                config_path = os.path.join(agent_path, 'agent.json')
                
                if os.path.isdir(agent_path) and os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        agent_name = config.get('name', agent_folder)
                        coord = config.get('coord', [50, 50])
                        persona_init_pos[agent_name] = {
                            "movement": coord[:2] if len(coord) >= 2 else [50, 50],
                            "currently": config.get('currently', f"{agent_name} 正在小镇中活动"),
                            "action": ""
                        }
                    except Exception as e:
                        print(f"读取agent配置失败 {agent_folder}: {e}")
        
        emit('current_state', {
            'step': 0,
            'movement': persona_init_pos,
            'running': False,
            'paused': False
        })


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'message': '页面不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500


if __name__ == "__main__":
    # 确保角色保存目录存在
    os.makedirs(AGENTS_BASE_PATH, exist_ok=True)
    
    # 使用SocketIO运行应用
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)