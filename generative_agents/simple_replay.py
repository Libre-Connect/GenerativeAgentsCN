import os
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
    static_url_path="/static",
)

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 硬编码的常量，避免导入compress.py
frames_per_step = 10
file_movement = "movement.json"

# 硬编码的角色名称，避免导入start.py
personas = [
    "阿伊莎", "克劳斯", "玛丽亚", "沃尔夫冈", "梅", "约翰", 
    "埃迪", "简", "汤姆", "卡门", "塔玛拉", "亚瑟"
]

# 实时播放相关变量
replay_thread = None
replay_running = False
replay_paused = False
current_replay = None
replay_lock = threading.Lock()

class ReplaySimulation:
    """回放模拟类"""
    
    def __init__(self, name, start_step=1, speed=2):
        self.name = name
        self.current_step = start_step
        self.speed = speed
        self.start_time = datetime.now()
        self.movement_data = None
        self.conversation_data = None
        self.start_datetime = None
        self.stride = 10
        self.load_replay_data()
    
    def load_replay_data(self):
        """加载回放数据"""
        compressed_folder = f"results/compressed/{self.name}"
        replay_file = f"{compressed_folder}/{file_movement}"
        
        if os.path.exists(replay_file):
            with open(replay_file, "r", encoding="utf-8") as f:
                params = json.load(f)
                self.movement_data = params.get("all_movement", {})
                self.conversation_data = params.get("conversation", {})
                self.start_datetime = datetime.fromisoformat(params.get("start_datetime", datetime.now().isoformat()))
                self.stride = params.get("stride", 10)
    
    def get_current_state(self):
        """获取当前步骤的状态"""
        if not self.movement_data or str(self.current_step) not in self.movement_data:
            return None
            
        step_data = self.movement_data[str(self.current_step)]
        
        # 计算当前时间
        current_time = self.start_datetime + timedelta(minutes=self.stride * (self.current_step - 1) / frames_per_step)
        
        # 获取对话数据
        conversation_key = current_time.strftime("%Y%m%d-%H:%M")
        conversation_text = self.conversation_data.get(conversation_key, "")
        
        # 构建前端期望的数据格式
        agents_data = {}
        for agent_name, agent_data in step_data.items():
            agents_data[agent_name] = {
                'movement': agent_data.get('movement', [0, 0]),
                'recent_chat': conversation_text if conversation_text else '',
                'action': agent_data.get('action', '活动中'),
                'currently': agent_data.get('currently', '活动中')
            }
        
        return {
            'step': self.current_step,
            'agents': agents_data,
            'current_time': current_time.isoformat(),
            'running': True
        }
    
    def advance_step(self):
        """前进一步"""
        if self.movement_data and str(self.current_step + 1) in self.movement_data:
            self.current_step += 1
            return True
        return False

@app.route("/", methods=['GET'])
def index():
    name = request.args.get("name", "example")    # 默认使用example数据
    step = int(request.args.get("step", 0))       # 回放起始步数
    speed = int(request.args.get("speed", 2))     # 回放速度（0~5）
    zoom = float(request.args.get("zoom", 0.5))   # 画面缩放比例

    compressed_folder = f"results/compressed/{name}"
    replay_file = f"{compressed_folder}/{file_movement}"
    
    if not os.path.exists(replay_file):
        return f"The data file doesn't exist: '{replay_file}'<br />Available data: example, web1"

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

def run_replay():
    """运行实时回放"""
    global replay_running, replay_paused, current_replay
    
    while replay_running and current_replay:
        if not replay_paused:
            with replay_lock:
                # 获取当前状态
                state = current_replay.get_current_state()
                if state:
                    # 发送更新到所有连接的客户端
                    socketio.emit('simulation_update', state)
                    
                    # 前进到下一步
                    if not current_replay.advance_step():
                        # 回放结束
                        replay_running = False
                        socketio.emit('simulation_status', {
                            'running': False,
                            'message': '回放已结束'
                        })
                        break
                else:
                    # 没有更多数据
                    replay_running = False
                    socketio.emit('simulation_status', {
                        'running': False,
                        'message': '回放数据已结束'
                    })
                    break
        
        # 根据速度控制播放间隔
        time.sleep(1.0 / current_replay.speed)

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('Client connected to replay')
    emit('connected', {'message': '已连接到回放服务器'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('Client disconnected from replay')

@socketio.on('request_current_state')
def handle_request_current_state():
    """请求当前状态"""
    global current_replay
    
    if current_replay and replay_running:
        state = current_replay.get_current_state()
        if state:
            emit('current_state', state)
    else:
        # 发送静态状态
        emit('current_state', {
            'step': 0,
            'movement': {},
            'running': False,
            'message': '回放未运行'
        })

@socketio.on('start_replay')
def handle_start_replay(data):
    """开始回放"""
    global replay_thread, replay_running, current_replay
    
    name = data.get('name', 'example')
    start_step = data.get('step', 1)
    speed = data.get('speed', 2)
    
    if not replay_running:
        current_replay = ReplaySimulation(name, start_step, speed)
        if current_replay.movement_data:
            replay_running = True
            replay_thread = threading.Thread(target=run_replay)
            replay_thread.start()
            
            emit('simulation_status', {
                'running': True,
                'message': f'开始回放 {name}'
            })
        else:
            emit('simulation_status', {
                'running': False,
                'message': f'无法加载回放数据: {name}'
            })

@socketio.on('pause_replay')
def handle_pause_replay():
    """暂停/恢复回放"""
    global replay_paused
    
    replay_paused = not replay_paused
    emit('simulation_status', {
        'running': replay_running,
        'paused': replay_paused,
        'message': '回放已暂停' if replay_paused else '回放已恢复'
    })

@socketio.on('stop_replay')
def handle_stop_replay():
    """停止回放"""
    global replay_running, replay_paused, current_replay
    
    replay_running = False
    replay_paused = False
    current_replay = None
    
    emit('simulation_status', {
        'running': False,
        'message': '回放已停止'
    })

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)