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
        self.static_root = "frontend/static"
        self.checkpoints_folder = f"results/checkpoints/{name}"
        
        # 创建检查点文件夹
        os.makedirs(self.checkpoints_folder, exist_ok=True)
        
        # 创建配置
        start_time = datetime.datetime.now().strftime("%Y%m%d-%H:%M")
        self.config = get_config(start_time, stride, personas)
        
        # 创建游戏
        self.logger = utils.create_io_logger("info")
        self.game = create_game(name, self.static_root, self.config, {}, logger=self.logger)
        self.game.reset_game()
        
        # 初始化角色状态
        self.agent_status = {}
        if "agent_base" in self.config:
            agent_base = self.config["agent_base"]
        else:
            agent_base = {}
            
        for agent_name, agent in self.config["agents"].items():
            agent_config = copy.deepcopy(agent_base)
            agent_config.update(self.load_static(agent["config_path"]))
            self.agent_status[agent_name] = {
                "coord": agent_config["coord"],
                "path": [],
            }
    
    def load_static(self, path):
        return utils.load_dict(os.path.join(self.static_root, path))
    
    def simulate_step(self):
        """执行一步模拟"""
        global simulation_running, simulation_paused
        
        if not simulation_running or simulation_paused:
            return None
            
        timer = utils.get_timer()
        self.step_count += 1
        
        # 收集所有角色的移动和状态信息
        movement_data = {}
        
        for name, status in self.agent_status.items():
            try:
                plan = self.game.agent_think(name, status)["plan"]
                agent = self.game.get_agent(name)
                
                if name not in self.config["agents"]:
                    self.config["agents"][name] = {}
                    
                self.config["agents"][name].update(agent.to_dict())
                
                if plan.get("path"):
                    status["coord"], status["path"] = plan["path"][-1], []
                    
                self.config["agents"][name].update({"coord": status["coord"]})
                
                # 收集移动数据
                movement_data[name] = {
                    "movement": status["coord"],
                    "currently": agent.scratch.currently,
                    "action": agent.action.abstract() if hasattr(agent, 'action') else "",
                    "address": agent.get_tile().get_address(as_list=False) if hasattr(agent, 'get_tile') else ""
                }
                
            except Exception as e:
                print(f"Error simulating agent {name}: {e}")
                continue
        
        # 更新时间
        timer.forward(self.stride)
        
        # 构造返回数据
        sim_data = {
            "step": self.step_count,
            "time": timer.get_date("%Y%m%d-%H:%M:%S"),
            "movement": movement_data,
            "conversation": getattr(self.game, 'conversation', {}),
            "description": {name: {"currently": data["currently"]} for name, data in movement_data.items()}
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
                        
                except Exception as e:
                    print(f"读取角色配置失败 {agent_folder}: {e}")
                    continue
    
    # 构造all_movement数据结构
    all_movement = {
        "conversation": {},
        "description": {}
    }
    
    # 为每个角色添加描述信息
    for agent_name in persona_init_pos.keys():
        all_movement["description"][agent_name] = {
            "currently": f"{agent_name} 正在小镇中活动"
        }
    
    return render_template(
        "index.html",
        persona_names=persona_names,
        persona_init_pos=persona_init_pos,
        step=0,
        sec_per_step=1,
        play_speed=4,
        zoom=1,
        all_movement=all_movement,
        start_datetime="2023-01-01T00:00:00"
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
    
    while simulation_running and current_simulation:
        try:
            if not simulation_paused:
                # 执行一步模拟
                sim_data = current_simulation.simulate_step()
                
                if sim_data:
                    # 通过WebSocket发送数据到前端
                    socketio.emit('simulation_update', sim_data)
            
            # 控制模拟速度（每秒一步）
            time.sleep(1)
            
        except Exception as e:
            print(f"Simulation error: {e}")
            simulation_running = False
            socketio.emit('simulation_error', {'message': str(e)})
            break


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
            agent = current_simulation.game.get_agent(name)
            movement_data[name] = {
                "movement": status["coord"],
                "currently": agent.scratch.currently if hasattr(agent, 'scratch') else "",
            }
        
        emit('current_state', {
            'step': current_simulation.step_count,
            'movement': movement_data,
            'running': simulation_running,
            'paused': simulation_paused
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