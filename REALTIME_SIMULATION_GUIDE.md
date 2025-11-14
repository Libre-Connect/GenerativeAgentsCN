# 实时模拟使用指南

## 功能说明

现在可以在Web界面实时查看AI模拟过程，不需要先模拟完再回放！

## 主要改进

✅ **真实AI思考** - 使用真实的AI agent思考逻辑，而不是简单的随机移动  
✅ **实时显示** - 通过WebSocket实时更新画面  
✅ **保持界面** - 使用现有的回放界面，无需修改前端  
✅ **可见对话** - 显示角色之间的对话和活动  

## 如何使用

### 方法1：直接启动Web服务器（推荐）

```bash
cd /Users/sunyuefeng/GenerativeAgentsCN-1/generative_agents

# 启动服务器
python web_server.py
```

然后在浏览器打开：
```
http://127.0.0.1:5000
```

**说明**：
- 启动后会自动创建实时模拟实例
- 自动加载 `frontend/static/assets/village/agents/` 目录中的所有角色
- 自动开始模拟，角色会开始思考和移动
- 在浏览器中实时看到角色活动

### 方法2：通过API控制

```bash
# 1. 启动服务器
python web_server.py

# 2. 在另一个终端，使用API控制

# 开始模拟
curl -X POST http://localhost:5000/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"name": "my-simulation", "stride": 10}'

# 暂停模拟
curl -X POST http://localhost:5000/api/simulation/pause

# 停止模拟
curl -X POST http://localhost:5000/api/simulation/stop

# 查看状态
curl http://localhost:5000/api/simulation/status
```

## 界面说明

### 主画面
- **地图视图** - 显示整个小镇地图
- **角色精灵** - 显示所有角色的位置
- **对话气泡** - 显示角色当前活动和对话
- **时间显示** - 显示当前模拟时间

### 右侧边栏
- **角色列表** - 显示所有角色及其当前状态
- **控制按钮** - 启动/暂停/停止模拟

### 控制
- **方向键** - 移动视角
- **鼠标滚轮** - 缩放画面
- **点击角色** - 查看详细信息

## 工作原理

### 1. 初始化
```python
RealTimeSimulation(name, stride=10)
```
- 创建游戏实例
- 加载所有角色配置
- 初始化AI系统

### 2. 每步执行
```python
simulate_step()
```
对每个角色：
1. 调用 `game_instance.agent_think(name, status)`
2. 获取AI决策的行动计划
3. 更新角色位置和状态
4. 收集对话内容
5. 通过WebSocket发送到前端

### 3. 前端更新
```javascript
socket.on('simulation_update', function(data) {
    // 更新角色位置
    // 更新对话气泡
    // 更新时间显示
})
```

## 配置选项

### 修改模拟速度

编辑 `web_server.py`，找到 `run_simulation()` 函数：

```python
# 控制模拟速度
time.sleep(2)  # 默认2秒一步
```

调整这个值：
- `time.sleep(0.5)` - 快速模拟（每0.5秒一步）
- `time.sleep(1)` - 正常速度（每秒一步）
- `time.sleep(2)` - 推荐速度（每2秒一步，给AI足够时间）
- `time.sleep(5)` - 慢速模拟（每5秒一步）

### 修改时间步进

```python
# 创建模拟时设置stride
current_simulation = RealTimeSimulation(simulation_name, stride=10)
```

`stride` 参数：
- `stride=5` - 每步代表5分钟
- `stride=10` - 每步代表10分钟（默认）
- `stride=30` - 每步代表30分钟

## 查看日志

### 终端输出

运行时会在终端看到详细日志：

```
=== 实时模拟已启动 ===
模拟名称: web_auto_1699876543
步进间隔: 10 分钟
使用真实AI: 是

--- 执行步骤 1 ---
[步骤 1] 阿伊莎: 阿伊莎正在图书馆学习 at [25, 32]
[步骤 1] 克劳斯: 克劳斯正在咖啡馆喝咖啡 at [45, 28]
✓ 已发送更新到前端，包含 25 个角色

--- 执行步骤 2 ---
[步骤 2] 阿伊莎: 阿伊莎在和克劳斯聊天 at [26, 32]
...
```

### 浏览器控制台

打开浏览器的开发者工具（F12），查看控制台：

```javascript
Connected to server
Received simulation update: {step: 1, agents: {...}}
Updated 阿伊莎 position to (800, 1024)
Updated 克劳斯 position to (1440, 896)
```

## 角色准备

### 使用现有角色

如果 `generative_agents/frontend/static/assets/village/agents/` 目录中有角色：
- 系统会自动加载
- 自动开始模拟

### 创建新角色

```bash
# 使用角色生成器
python test_character_generator.py
```

或在Web界面中：
1. 访问 `http://127.0.0.1:5000/add_agent`
2. 填写角色信息
3. 选择角色图片（从63个预设中选择）
4. 保存角色

### 角色配置

每个角色需要：
- `agent.json` - 配置文件
- `texture.png` - 角色图片（96x128像素）

示例配置：
```json
{
  "name": "张三",
  "age": 30,
  "occupation": "工程师",
  "personality": "友善",
  "coord": [50, 50],
  "currently": "张三正在工作"
}
```

## 性能考虑

### 角色数量
- 1-5个角色：流畅运行
- 5-10个角色：正常运行
- 10-25个角色：较慢但可运行
- 25+个角色：需要强大的LLM和硬件

### LLM配置

编辑 `generative_agents/data/config.json`：

```json
{
  "provider": "ollama",
  "model": "qwen2.5:14b",
  "base_url": "http://localhost:11434"
}
```

推荐模型：
- **快速**: qwen2.5:7b, llama3.1:8b
- **平衡**: qwen2.5:14b, llama3.1:70b (4bit量化)
- **高质量**: qwen2.5:32b, gpt-4

### 优化建议

1. **减少角色数量** - 从3-5个角色开始测试
2. **使用本地模型** - Ollama + 量化模型更快
3. **增加时间间隔** - `stride=30` 减少AI调用频率
4. **调整速度** - `time.sleep(3)` 给AI更多时间

## 常见问题

### Q: 为什么角色不动？

A: 检查：
1. 模拟是否正在运行？查看终端日志
2. 游戏实例是否创建成功？查看"使用真实AI: 是/否"
3. LLM是否正常？检查 `config.json` 配置
4. 是否暂停了？点击恢复按钮

### Q: 为什么没有对话？

A: 
- AI需要时间才能产生对话
- 角色需要接近才会对话
- 增加运行时间，等待几分钟
- 检查终端是否有对话日志

### Q: 如何加快速度？

A:
1. 修改 `time.sleep(2)` 为更小的值
2. 使用更快的LLM模型
3. 减少角色数量
4. 使用GPU加速

### Q: 如何保存模拟结果？

A:
当前实时模拟不自动保存。如需保存：
1. 使用命令行模式 `python start.py` 
2. 或修改 `simulate_step()` 添加保存逻辑

### Q: 能同时运行多个模拟吗？

A:
不能。当前只支持单个实时模拟。如需多个模拟，使用命令行模式多次启动。

## 与命令行模式的对比

| 特性 | 实时模拟（Web） | 命令行模式 |
|-----|---------------|----------|
| 实时查看 | ✅ 是 | ❌ 否 |
| 保存数据 | ❌ 否 | ✅ 是 |
| 断点恢复 | ❌ 否 | ✅ 是 |
| 交互性 | ✅ 高 | ❌ 低 |
| 适用场景 | 观察、调试、演示 | 长期运行、数据收集 |

## 最佳实践

1. **先测试小规模** - 从2-3个角色开始
2. **观察日志** - 确保AI正常工作
3. **调整速度** - 根据硬件性能调整
4. **定期检查** - 观察角色是否合理行动
5. **创建有趣角色** - 不同性格的角色互动更有趣

## 示例：快速开始

```bash
# 1. 进入目录
cd /Users/sunyuefeng/GenerativeAgentsCN-1/generative_agents

# 2. 创建2-3个测试角色（如果还没有）
python test_character_generator.py

# 3. 启动Web服务器
python web_server.py

# 4. 打开浏览器
# http://127.0.0.1:5000

# 5. 观察角色移动和对话！
```

就是这么简单！现在你可以实时看到AI角色的活动了！🎉

## 技术细节

### 系统架构

```
Web浏览器 <--WebSocket--> Flask服务器
                              |
                         RealTimeSimulation
                              |
                         Game实例
                              |
                    +---------+---------+
                    |         |         |
                 Agent1    Agent2    Agent3
                    |         |         |
                    +----AI思考逻辑----+
                              |
                            LLM API
```

### 关键文件

- `web_server.py` - 主服务器和实时模拟逻辑
- `modules/game.py` - 游戏核心逻辑
- `modules/agent.py` - Agent思考逻辑
- `frontend/templates/index.html` - 前端页面
- `frontend/templates/main_script.html` - WebSocket处理

### 数据流

```
1. simulate_step() 调用
   ↓
2. 对每个agent调用 agent_think()
   ↓
3. AI返回决策（位置、活动、对话）
   ↓
4. 收集所有agent数据
   ↓
5. socketio.emit('simulation_update', data)
   ↓
6. 前端接收并更新画面
```

## 未来改进

可能的增强功能：
- [ ] 模拟数据自动保存
- [ ] 可调节的实时速度控制（通过UI）
- [ ] 更详细的角色信息面板
- [ ] 对话历史记录
- [ ] 暂停时编辑角色
- [ ] 动态添加/删除角色
- [ ] 多模拟实例支持

---

**享受实时模拟的乐趣吧！** 🚀












