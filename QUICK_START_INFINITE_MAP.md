# 无限地图快速开始指南

## 🎯 3分钟快速上手

### 1. 运行测试（验证功能）

```bash
cd /Users/sunyuefeng/GenerativeAgentsCN-1
python test_infinite_map.py
```

✅ 如果所有测试通过，系统就可以使用了！

### 2. 在Game类中集成（3行代码）

打开 `generative_agents/modules/game.py`，找到Maze初始化的地方：

**原来的代码：**
```python
from .maze import Maze

class Game:
    def __init__(self, ...):
        self.maze = Maze(self.load_static(config["maze"]["path"]), self.logger)
```

**改为：**
```python
from modules.infinite_map import create_infinite_maze

class Game:
    def __init__(self, ...):
        # 使用无限地图
        self.maze = create_infinite_maze(
            config={
                "world": "The Infinite World",
                "tile_size": 32,
                "chunk_size": 32,
                "max_loaded_chunks": 100
            },
            logger=self.logger,
            use_infinite=True  # 改为False可回退
        )
```

### 3. 为100+个Agent分配位置

在创建agents后添加：

```python
# 在Game.__init__中，创建agents后

# 自动生成100个出生位置
spawn_locations = self.maze.generate_spawn_locations(100)

# 为每个Agent分配位置
for i, (agent_name, agent) in enumerate(self.agents.items()):
    if i < len(spawn_locations):
        agent.coord = spawn_locations[i]
        
        # 预加载周围区域（可选，提高性能）
        self.maze.preload_area_around(agent.coord, radius=2)

self.logger.info(f"✓ 为 {len(spawn_locations)} 个Agent分配了位置")
```

### 4. 启动游戏

```bash
python generative_agents/web_server.py
```

**就这么简单！** 🎉

## 🔍 验证是否成功

启动后查看日志，应该看到：

```
[INFO] ✓ 使用无限地图系统
[INFO] Initialized infinite map spawn area (25 chunks)
[INFO] ✓ 为 100 个Agent分配了位置
```

## 📊 查看地图统计

在Python console或代码中：

```python
stats = game.maze.get_stats()
print(f"地图类型: {stats['type']}")           # infinite
print(f"已加载区块: {stats['loaded_chunks_count']}")
print(f"缓存命中率: {stats['cache_hit_rate']:.1f}%")
```

## 🎮 导出地图（用于前端）

如果前端需要静态地图：

```python
# 导出一个大区域
game.maze.export_current_view(
    center_coord=(0, 0),
    radius=20,  # 40x40个区块
    output_file="frontend/static/assets/village/generated_map.json"
)
```

## ⚙️ 配置选项

### 根据Agent数量调整

| Agent数量 | chunk_size | max_loaded_chunks |
|----------|-----------|------------------|
| < 50 | 32 | 50 |
| 50-100 | 32 | 100 |
| 100-200 | 32-64 | 150 |
| > 200 | 64 | 200 |

### 示例配置

```python
# 50个Agent（轻量级）
config = {
    "chunk_size": 32,
    "max_loaded_chunks": 50
}

# 150个Agent（中等）
config = {
    "chunk_size": 32,
    "max_loaded_chunks": 150
}

# 300个Agent（重度）
config = {
    "chunk_size": 64,
    "max_loaded_chunks": 200
}
```

## 🔙 回退到原始地图

如果遇到问题，一行代码就能回退：

```python
self.maze = create_infinite_maze(
    config=config,
    logger=logger,
    use_infinite=False  # 改为False
)
```

或者直接用原来的Maze：

```python
from .maze import Maze
self.maze = Maze(config, logger)
```

## 🐛 故障排查

### 问题1: Agent不移动？

**原因**: 可能出生在水域或障碍物上

**解决**: 系统会自动避开，但如果还有问题：

```python
# 检查位置是否可通行
tile = game.maze.tile_at(agent.coord)
if tile.collision:
    print("Agent位置有障碍")
```

### 问题2: 内存占用太高？

**解决**: 减少max_loaded_chunks：

```python
config = {
    "max_loaded_chunks": 50  # 从100降到50
}
```

### 问题3: 地图生成很慢？

**解决**: 增大chunk_size：

```python
config = {
    "chunk_size": 64  # 从32增到64
}
```

### 问题4: 想要固定种子（相同地形）？

**解决**: 在ProceduralTerrainGenerator中设置：

```python
# 修改 chunk_manager.py
self.terrain_generator = ProceduralTerrainGenerator(
    chunk_size=chunk_size,
    tile_size=tile_size,
    seed=12345  # 固定种子
)
```

## 📚 更多信息

- **完整文档**: `INFINITE_MAP_GUIDE.md`
- **实现细节**: `INFINITE_MAP_SUMMARY.md`
- **测试脚本**: `test_infinite_map.py`
- **使用示例**: `generative_agents/example_infinite_map_usage.py`

## 💡 实用技巧

### 1. 预加载优化

```python
# 只在Agent移动到新区域时预加载
def on_agent_move(agent, new_coord):
    # 检查是否进入新区块
    old_chunk = (agent.coord[0] // 32, agent.coord[1] // 32)
    new_chunk = (new_coord[0] // 32, new_coord[1] // 32)
    
    if old_chunk != new_chunk:
        game.maze.preload_area_around(new_coord, radius=2)
```

### 2. 批量操作

```python
# 一次性为所有Agent预加载
for agent in game.agents.values():
    game.maze.preload_area_around(agent.coord, radius=1)
```

### 3. 定期清理

```python
# 在游戏循环中，定期卸载远离所有Agent的区块
def cleanup_distant_chunks():
    # chunk_manager会自动处理，无需手动
    pass
```

## ✅ 检查清单

集成前确认：

- [ ] 运行 `python test_infinite_map.py` 通过
- [ ] 修改 `game.py` 使用 `create_infinite_maze`
- [ ] 添加 `generate_spawn_locations` 代码
- [ ] （可选）调整配置参数
- [ ] 启动游戏测试

## 🎉 完成！

**恭喜！你的游戏现在支持无限大的地图和100+个Agent了！**

如有问题，查看：
1. 完整文档：`INFINITE_MAP_GUIDE.md`
2. 测试日志：运行测试查看详细输出
3. 示例代码：`example_infinite_map_usage.py`

---

**快速开始只需要：**
1. ✅ 3行代码修改Game类
2. ✅ 5行代码分配Agent位置
3. ✅ 启动游戏

**就这么简单！** 🚀

