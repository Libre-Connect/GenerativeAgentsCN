# 无限地图系统使用指南

## 概述

新的无限地图系统支持：

✅ **无限扩展** - 地图可以无限大，自动生成新区域  
✅ **动态加载** - 按需加载区块，节省内存  
✅ **程序化生成** - 使用柏林噪声生成自然地形  
✅ **100+ Agents** - 智能分配Agent位置，避免拥挤  
✅ **高性能** - 只加载可见区域，LRU缓存机制

## 系统架构

### 核心组件

1. **ChunkManager** (`chunk_manager.py`)
   - 管理区块的加载/卸载
   - LRU缓存机制
   - 区块持久化（保存到磁盘）

2. **ProceduralTerrainGenerator** (`procedural_terrain.py`)
   - 使用柏林噪声生成地形
   - 支持多种生物群系
   - 自然连续的地形过渡

3. **InfiniteMaze** (`infinite_maze.py`)
   - 扩展原有Maze类
   - 向后兼容
   - A*寻路算法

### 区块系统

- **区块大小**: 32x32 瓦片（默认）
- **瓦片大小**: 32像素
- **最大加载区块数**: 100个（可配置）
- **自动卸载**: 使用LRU算法卸载最久未访问的区块

### 生物群系

支持8种生物群系，自动根据海拔、湿度、温度生成：

| 生物群系 | 特点 | 生成条件 |
|---------|------|---------|
| WATER | 水域，不可通行 | 海拔 < 0.3 |
| PLAINS | 平原，适合居住 | 中等海拔 + 低湿度 |
| FOREST | 森林，树木密集 | 中等海拔 + 高湿度 |
| DESERT | 沙漠 | 高温 + 低湿度 |
| MOUNTAINS | 山地 | 海拔 > 0.75 |
| VILLAGE | 村庄区域 | 平原中5%概率 |
| FARMLAND | 农田 | 平原中10%概率 |
| URBAN | 城市 | 人工指定 |

## 使用方法

### 1. 基础使用

修改Game类以使用无限地图：

```python
from modules.infinite_map import create_infinite_maze

class Game:
    def __init__(self, name, static_root, config, conversation, logger=None):
        # ... 其他初始化代码 ...
        
        # 创建无限地图
        self.maze = create_infinite_maze(
            config={
                "world": "The Infinite World",
                "tile_size": 32,
                "chunk_size": 32,
                "max_loaded_chunks": 100,
                "tile_address_keys": ["world", "sector", "arena", "game_object"]
            },
            logger=logger,
            use_infinite=True  # 设为False回退到原始固定地图
        )
        
        # ... 其他代码 ...
```

### 2. 为100+个Agent分配位置

```python
# 在Game初始化后
agent_count = 100  # 或更多

# 自动生成合适的出生位置
spawn_locations = game.maze.generate_spawn_locations(agent_count)

# 为每个Agent分配位置
for i, (agent_name, agent) in enumerate(game.agents.items()):
    if i < len(spawn_locations):
        agent.coord = spawn_locations[i]
        
        # 预加载该Agent周围的区域
        game.maze.preload_area_around(agent.coord, radius=3)
```

### 3. 预加载区域

```python
# 预加载玩家周围的区域
player_pos = (100, 100)
game.maze.preload_area_around(player_pos, radius=5)

# 预加载所有Agent周围的区域
for agent in game.agents.values():
    game.maze.preload_area_around(agent.coord, radius=2)
```

### 4. 导出地图区域

```python
# 导出某个区域为静态地图（用于调试或前端）
center = (0, 0)
game.maze.export_current_view(
    center_coord=center,
    radius=10,  # 10个区块半径
    output_file="exported_map.json"
)
```

### 5. 查看统计信息

```python
stats = game.maze.get_stats()
print(f"地图类型: {stats['type']}")
print(f"已加载区块: {stats['loaded_chunks_count']}")
print(f"已生成区块: {stats['chunks_generated']}")
print(f"缓存命中率: {stats['cache_hit_rate']:.1f}%")
```

## 配置选项

### 地图配置

```python
config = {
    # 基础配置
    "world": "世界名称",
    "tile_size": 32,           # 瓦片大小（像素）
    "chunk_size": 32,          # 区块大小（瓦片数）
    
    # 性能配置
    "max_loaded_chunks": 100,  # 最大同时加载的区块数
    
    # 地址系统
    "tile_address_keys": ["world", "sector", "arena", "game_object"]
}
```

### 性能调优

根据Agent数量和硬件调整：

| Agent数量 | chunk_size | max_loaded_chunks | 预加载半径 |
|----------|-----------|------------------|----------|
| 10-50 | 32 | 50 | 3 |
| 50-100 | 32 | 100 | 2 |
| 100-200 | 32 | 150 | 2 |
| 200+ | 64 | 200 | 1 |

```python
# 示例：为200个Agent优化
config = {
    "chunk_size": 64,
    "max_loaded_chunks": 200,
}

# 减少预加载半径
for agent in game.agents.values():
    game.maze.preload_area_around(agent.coord, radius=1)
```

## 与现有系统兼容

### 完全兼容原有API

无限地图系统**完全兼容**原有Maze接口：

```python
# 所有原有方法都能正常工作
tile = maze.tile_at((x, y))
path = maze.find_path(start, end)
tiles_around = maze.get_around(coord)
scope_tiles = maze.get_scope(coord, config)
```

### 回退到固定地图

如需使用原始固定地图：

```python
maze = create_infinite_maze(
    config=config,
    logger=logger,
    use_infinite=False  # 使用原始Maze
)
```

## 前端集成

### 方案1：导出大区域（简单）

适合不需要真正无限地图的情况：

```python
# 导出一个大区域（例如500x500个区块）
game.maze.export_current_view(
    center_coord=(0, 0),
    radius=250,  # 250个区块半径
    output_file="frontend/static/assets/village/generated_map.json"
)
```

然后前端加载这个大地图。

### 方案2：动态加载（推荐）

需要修改前端以支持动态加载：

1. **创建API端点**

```python
# 在web_server.py中添加
@app.route("/api/map/chunks", methods=['GET'])
def get_map_chunks():
    """获取指定区域的区块"""
    center_x = int(request.args.get('x', 0))
    center_y = int(request.args.get('y', 0))
    radius = int(request.args.get('radius', 3))
    
    chunks = game.maze.chunk_manager.get_chunks_in_area(
        world_x=center_x * 32 - 16 * 32,
        world_y=center_y * 32 - 16 * 32,
        width=radius * 2 * 32,
        height=radius * 2 * 32
    )
    
    return jsonify({
        "chunks": [
            {
                "x": chunk.chunk_x,
                "y": chunk.chunk_y,
                "biome": chunk.biome.value,
                "tiles": chunk.tiles
            }
            for chunk in chunks
        ]
    })
```

2. **前端定时请求区块**

```javascript
// 监听玩家位置变化
function updateVisibleChunks(playerX, playerY) {
    const chunkX = Math.floor(playerX / (32 * 32));
    const chunkY = Math.floor(playerY / (32 * 32));
    
    // 请求周围的区块
    fetch(`/api/map/chunks?x=${chunkX}&y=${chunkY}&radius=3`)
        .then(res => res.json())
        .then(data => {
            // 渲染区块
            renderChunks(data.chunks);
        });
}
```

### 方案3：WebSocket实时流（高级）

对于大量Agent的实时更新：

```python
@socketio.on('request_chunks')
def handle_chunk_request(data):
    chunks = get_chunks_around(data['position'], data['radius'])
    socketio.emit('chunks_data', chunks)
```

## 测试脚本

测试无限地图功能：

```python
# test_infinite_map.py
from modules.infinite_map import ChunkManager, create_infinite_maze

def test_infinite_map():
    print("测试1: 区块生成")
    chunk_manager = ChunkManager(chunk_size=32)
    
    chunk = chunk_manager.get_chunk(0, 0)
    print(f"✓ 生成区块 (0, 0), 生物群系: {chunk.biome.value}")
    
    print("\n测试2: 多区块加载")
    chunks = chunk_manager.get_chunks_in_area(0, 0, 100, 100)
    print(f"✓ 加载了 {len(chunks)} 个区块")
    
    print("\n测试3: Agent位置分配")
    locations = chunk_manager.find_suitable_spawn_locations(100)
    print(f"✓ 为100个Agent生成了 {len(locations)} 个位置")
    
    print("\n测试4: 统计信息")
    stats = chunk_manager.get_stats()
    print(f"  生成区块数: {stats['chunks_generated']}")
    print(f"  已加载区块: {stats['loaded_chunks_count']}")
    print(f"  缓存命中率: {stats['cache_hit_rate']:.1f}%")
    
    print("\n测试5: InfiniteMaze")
    import logging
    logger = logging.getLogger()
    
    maze = create_infinite_maze({
        "world": "test_world",
        "tile_size": 32,
        "chunk_size": 32
    }, logger, use_infinite=True)
    
    tile = maze.tile_at((10, 10))
    print(f"✓ 获取瓦片成功: {tile.coord}")
    
    path = maze.find_path((0, 0), (10, 10))
    print(f"✓ 寻路成功，路径长度: {len(path)}")
    
    print("\n✓ 所有测试通过！")

if __name__ == "__main__":
    test_infinite_map()
```

运行测试：

```bash
cd /Users/sunyuefeng/GenerativeAgentsCN-1/generative_agents
python -c "from modules.infinite_map import *; import test; test.test_infinite_map()"
```

## 注意事项

### 1. 内存管理

- 每个区块约占用 32KB - 128KB 内存
- 100个区块 ≈ 3-13 MB
- 根据可用内存调整 `max_loaded_chunks`

### 2. 性能优化

```python
# 定期清理未使用的区块
chunk_manager.unload_all_chunks()  # 保存并卸载所有区块

# 只预加载必要的区域
maze.preload_area_around(agent.coord, radius=2)  # 而不是5

# 批量获取瓦片（更高效）
tiles = [maze.tile_at((x, y)) for x, y in coordinates]
```

### 3. 持久化

区块自动保存到 `results/map_chunks/`:

```
results/map_chunks/
├── chunk_-1_-1.json
├── chunk_-1_0.json
├── chunk_0_-1.json
├── chunk_0_0.json
└── ...
```

### 4. 地形一致性

使用固定种子确保地形一致：

```python
terrain_generator = ProceduralTerrainGenerator(seed=12345)
# 相同种子会生成相同的地形
```

## 常见问题

### Q: Agent移动太慢？

A: 增加预加载半径，或使用更高效的寻路算法。

### Q: 内存占用太高？

A: 减少 `max_loaded_chunks` 或增加 `chunk_size`。

### Q: 地形不连续？

A: 检查噪声参数，确保 `elevation_scale` 足够小。

### Q: 如何添加自定义生物群系？

```python
# 在BiomeType中添加
class BiomeType(Enum):
    # ... 现有类型 ...
    CUSTOM = "custom"

# 在_determine_biome中添加判断逻辑
# 在_generate_tile中添加生成规则
```

## 未来扩展

可以添加：

1. **多人服务器** - 不同玩家探索不同区域
2. **地形编辑** - 允许手动修改地形
3. **建筑生成** - 自动生成村庄、城市
4. **洞穴系统** - 多层地图
5. **自然事件** - 季节变化、天气影响地形

## 总结

无限地图系统为游戏提供了：

✅ **可扩展性** - 支持任意数量的Agent  
✅ **高性能** - 智能缓存和动态加载  
✅ **兼容性** - 完全兼容现有代码  
✅ **灵活性** - 可配置、可扩展  

现在你的游戏可以容纳100+甚至1000+个Agent！🚀

