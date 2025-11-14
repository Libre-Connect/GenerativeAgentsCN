"""
无限地图使用示例
演示如何在现有Game类中集成无限地图系统
"""

import os
import sys
from modules import utils
from modules.infinite_map import create_infinite_maze


class InfiniteMapGame:
    """使用无限地图的Game类示例"""
    
    def __init__(self, name, config, conversation, logger=None):
        self.name = name
        self.logger = logger or utils.IOLogger()
        self.conversation = conversation
        
        # ========== 关键变化 1: 使用无限地图 ==========
        # 原来: self.maze = Maze(config["maze"], self.logger)
        # 现在:
        self.maze = create_infinite_maze(
            config={
                "world": config.get("world", "The Infinite World"),
                "tile_size": 32,
                "chunk_size": 32,  # 每个区块32x32瓦片
                "max_loaded_chunks": 100,  # 最多同时加载100个区块
                "tile_address_keys": ["world", "sector", "arena", "game_object"]
            },
            logger=self.logger,
            use_infinite=True  # 设为False可回退到原始固定地图
        )
        
        self.logger.info("✓ 使用无限地图系统")
        
        # ========== 关键变化 2: 智能分配Agent位置 ==========
        # 假设有100个agents
        agent_count = 100
        
        # 自动生成合适的出生位置
        spawn_locations = self.maze.generate_spawn_locations(agent_count)
        self.logger.info(f"✓ 为{agent_count}个Agent生成了{len(spawn_locations)}个出生位置")
        
        # 创建agents并分配位置
        self.agents = {}
        for i, agent_name in enumerate([f"Agent{j}" for j in range(agent_count)]):
            # 这里简化，实际应该调用Agent类
            if i < len(spawn_locations):
                agent_pos = spawn_locations[i]
                self.agents[agent_name] = {
                    "coord": agent_pos,
                    "name": agent_name
                }
                
                # ========== 关键变化 3: 预加载周围区域 ==========
                # 为每个Agent预加载周围2个区块
                self.maze.preload_area_around(agent_pos, radius=2)
        
        self.logger.info(f"✓ 创建了{len(self.agents)}个Agent")
    
    def agent_think(self, agent_name):
        """Agent思考逻辑"""
        agent = self.agents.get(agent_name)
        if not agent:
            return
        
        # 获取当前位置
        coord = agent["coord"]
        
        # ========== 关键变化 4: 动态预加载 ==========
        # Agent移动时，预加载新区域
        self.maze.preload_area_around(coord, radius=1)
        
        # 其他逻辑保持不变
        # 获取视野范围
        scope = self.maze.get_scope(coord, {"vision_r": 5, "mode": "box"})
        
        # 寻路等
        # path = self.maze.find_path(current_pos, target_pos)
        
        return {"agent": agent_name, "scope_size": len(scope)}
    
    def get_map_stats(self):
        """获取地图统计"""
        return self.maze.get_stats()
    
    def export_visible_map(self, output_file="exported_map.json"):
        """导出当前可见地图区域"""
        # 找到所有Agent的中心位置
        if not self.agents:
            center = (0, 0)
        else:
            coords = [agent["coord"] for agent in self.agents.values()]
            avg_x = sum(x for x, y in coords) // len(coords)
            avg_y = sum(y for x, y in coords) // len(coords)
            center = (avg_x, avg_y)
        
        # 导出中心周围的区域
        self.maze.export_current_view(
            center_coord=center,
            radius=10,  # 10个区块半径
            output_file=output_file
        )
        
        self.logger.info(f"✓ 导出地图到 {output_file}")


def example_basic_usage():
    """示例1: 基础使用"""
    print("=" * 60)
    print("示例1: 基础使用无限地图")
    print("=" * 60)
    
    from modules import utils
    
    # 设置时间系统
    utils.set_timer()
    
    # 创建logger
    logger = utils.IOLogger()
    
    # 创建无限地图
    maze = create_infinite_maze(
        config={
            "world": "Example World",
            "tile_size": 32,
            "chunk_size": 32
        },
        logger=logger,
        use_infinite=True
    )
    
    print("✓ 创建无限地图")
    
    # 获取一些瓦片
    tile = maze.tile_at((10, 20))
    print(f"✓ 瓦片(10, 20): 碰撞={tile.collision}")
    
    # 寻路
    path = maze.find_path((0, 0), (30, 40))
    print(f"✓ 寻路: 找到长度为{len(path)}的路径")
    
    # 统计
    stats = maze.get_stats()
    print(f"✓ 统计: 已加载{stats['loaded_chunks_count']}个区块")
    
    print()


def example_100_agents():
    """示例2: 100个Agents"""
    print("=" * 60)
    print("示例2: 为100个Agent分配位置")
    print("=" * 60)
    
    from modules import utils
    
    logger = utils.IOLogger()
    
    # 创建无限地图
    maze = create_infinite_maze(
        config={
            "world": "100 Agents World",
            "tile_size": 32,
            "chunk_size": 32,
            "max_loaded_chunks": 150  # 更多Agent需要更多区块
        },
        logger=logger,
        use_infinite=True
    )
    
    # 生成位置
    locations = maze.generate_spawn_locations(100)
    print(f"✓ 生成了{len(locations)}个位置")
    
    # 预加载所有位置周围的区域
    for loc in locations[:10]:  # 只预加载前10个作为示例
        maze.preload_area_around(loc, radius=2)
    
    stats = maze.get_stats()
    print(f"✓ 预加载后: {stats['loaded_chunks_count']}个区块在内存中")
    print(f"✓ 缓存命中率: {stats['cache_hit_rate']:.1f}%")
    
    print()


def example_export_map():
    """示例3: 导出地图"""
    print("=" * 60)
    print("示例3: 导出地图区域")
    print("=" * 60)
    
    from modules import utils
    
    logger = utils.IOLogger()
    
    maze = create_infinite_maze(
        config={
            "world": "Export World",
            "tile_size": 32,
            "chunk_size": 32
        },
        logger=logger,
        use_infinite=True
    )
    
    # 导出一个大区域（用于前端）
    output_file = "results/exported_large_map.json"
    os.makedirs("results", exist_ok=True)
    
    maze.export_current_view(
        center_coord=(0, 0),
        radius=20,  # 40x40个区块 = 1280x1280瓦片
        output_file=output_file
    )
    
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"✓ 导出成功: {output_file}")
        print(f"  大小: {size / 1024 / 1024:.1f} MB")
    
    print()


def example_integration():
    """示例4: 完整集成"""
    print("=" * 60)
    print("示例4: 完整Game类集成")
    print("=" * 60)
    
    from modules import utils
    
    # 模拟Game初始化
    game = InfiniteMapGame(
        name="infinite_test",
        config={
            "world": "Integration Test World"
        },
        conversation=None,
        logger=utils.IOLogger()
    )
    
    print(f"✓ Game初始化完成")
    print(f"  Agent数量: {len(game.agents)}")
    
    # 模拟一些Agent思考
    for agent_name in list(game.agents.keys())[:5]:  # 只测试前5个
        result = game.agent_think(agent_name)
        # print(f"  {agent_name} 思考完成")
    
    # 获取统计
    stats = game.get_map_stats()
    print(f"✓ 地图统计:")
    print(f"  类型: {stats['type']}")
    print(f"  已加载区块: {stats['loaded_chunks_count']}")
    
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("无限地图系统 - 使用示例")
    print("=" * 60 + "\n")
    
    examples = [
        example_basic_usage,
        example_100_agents,
        example_export_map,
        example_integration
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ 示例失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print("完成！")
    print("=" * 60)
    print("\n如需在实际项目中使用，请修改:")
    print("1. modules/game.py 中的 Maze 初始化")
    print("2. 使用 maze.generate_spawn_locations() 分配Agent位置")
    print("3. 在 agent_think() 中调用 maze.preload_area_around()")
    print("\n详细文档: INFINITE_MAP_GUIDE.md")


if __name__ == "__main__":
    main()

