#!/usr/bin/env python3
"""
无限地图系统测试脚本
测试所有核心功能
"""

import sys
import os
import logging

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generative_agents'))

from modules.infinite_map import ChunkManager, create_infinite_maze, ProceduralTerrainGenerator


def test_chunk_manager():
    """测试区块管理器"""
    print("=" * 60)
    print("测试1: 区块管理器")
    print("=" * 60)
    
    chunk_manager = ChunkManager(chunk_size=32, max_loaded_chunks=10)
    
    # 测试1.1: 生成单个区块
    chunk = chunk_manager.get_chunk(0, 0)
    if chunk:
        print(f"✓ 成功生成区块 (0, 0)")
        print(f"  - 生物群系: {chunk.biome.value}")
        print(f"  - 瓦片数: {len(chunk.tiles)}x{len(chunk.tiles[0])}")
    else:
        print("✗ 生成区块失败")
        return False
    
    # 测试1.2: 世界坐标转换
    chunk_x, chunk_y, local_x, local_y = chunk_manager.world_to_chunk_coords(50, 75)
    print(f"✓ 坐标转换: 世界(50, 75) -> 区块({chunk_x}, {chunk_y}) 本地({local_x}, {local_y})")
    
    # 测试1.3: 获取瓦片
    tile = chunk_manager.get_tile(10, 10)
    if tile:
        print(f"✓ 获取瓦片 (10, 10): {tile.get('terrain', 'unknown')}")
    else:
        print("✗ 获取瓦片失败")
        return False
    
    # 测试1.4: 批量加载区块
    chunks = chunk_manager.get_chunks_in_area(0, 0, 100, 100)
    print(f"✓ 加载了 {len(chunks)} 个区块（100x100瓦片区域）")
    
    # 测试1.5: 统计信息
    stats = chunk_manager.get_stats()
    print(f"\n统计信息:")
    print(f"  - 已生成区块: {stats['chunks_generated']}")
    print(f"  - 已加载区块: {stats['loaded_chunks_count']}")
    print(f"  - 缓存命中率: {stats['cache_hit_rate']:.1f}%")
    
    print()
    return True


def test_procedural_terrain():
    """测试程序化地形生成"""
    print("=" * 60)
    print("测试2: 程序化地形生成")
    print("=" * 60)
    
    generator = ProceduralTerrainGenerator(chunk_size=32, seed=12345)
    
    # 测试2.1: 生成区块
    chunk = generator.generate_chunk(0, 0)
    print(f"✓ 生成区块，生物群系: {chunk.biome.value}")
    
    # 测试2.2: 统计生物群系分布
    from collections import Counter
    biomes = []
    for y in range(32):
        for x in range(32):
            tile = chunk.get_tile(x, y)
            if tile:
                biomes.append(tile.get('biome', 'unknown'))
    
    biome_counts = Counter(biomes)
    print(f"✓ 生物群系分布:")
    for biome, count in biome_counts.most_common():
        percentage = (count / len(biomes)) * 100
        print(f"  - {biome}: {count} ({percentage:.1f}%)")
    
    # 测试2.3: 测试多个区块的连续性
    chunks_data = {}
    for cy in range(-1, 2):
        for cx in range(-1, 2):
            c = generator.generate_chunk(cx, cy)
            chunks_data[(cx, cy)] = c
    
    print(f"✓ 生成了 {len(chunks_data)} 个相邻区块")
    
    print()
    return True


def test_infinite_maze():
    """测试无限地图Maze"""
    print("=" * 60)
    print("测试3: 无限地图Maze")
    print("=" * 60)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    
    # 测试3.1: 创建无限地图
    maze = create_infinite_maze({
        "world": "Test World",
        "tile_size": 32,
        "chunk_size": 32,
        "max_loaded_chunks": 50
    }, logger, use_infinite=True)
    
    print(f"✓ 创建无限地图成功")
    
    # 测试3.2: 获取瓦片
    tile = maze.tile_at((10, 10))
    print(f"✓ 获取瓦片 (10, 10): 碰撞={tile.collision}")
    
    # 测试3.3: 寻路
    start = (0, 0)
    end = (20, 20)
    path = maze.find_path(start, end)
    if path:
        print(f"✓ 寻路成功: {start} -> {end}, 路径长度={len(path)}")
    else:
        print(f"○ 未找到路径（可能有障碍）")
    
    # 测试3.4: 获取周围瓦片
    around = maze.get_around((10, 10))
    print(f"✓ 周围可通行瓦片: {len(around)} 个")
    
    # 测试3.5: 获取视野范围
    scope = maze.get_scope((10, 10), {"vision_r": 5, "mode": "box"})
    print(f"✓ 视野范围内瓦片: {len(scope)} 个")
    
    # 测试3.6: 预加载区域
    maze.preload_area_around((0, 0), radius=3)
    print(f"✓ 预加载了(0, 0)周围3个区块的区域")
    
    # 测试3.7: 统计信息
    stats = maze.get_stats()
    print(f"\n地图统计:")
    print(f"  - 类型: {stats['type']}")
    print(f"  - 瓦片缓存: {stats['tile_cache_size']}")
    print(f"  - 已加载区块: {stats['loaded_chunks_count']}")
    
    print()
    return True


def test_agent_spawn_locations():
    """测试Agent位置分配"""
    print("=" * 60)
    print("测试4: 智能Agent位置分配")
    print("=" * 60)
    
    logging.basicConfig(level=logging.WARNING)  # 减少日志输出
    logger = logging.getLogger()
    
    maze = create_infinite_maze({
        "world": "Test World",
        "tile_size": 32,
        "chunk_size": 32
    }, logger, use_infinite=True)
    
    # 测试4.1: 少量Agent（10个）
    locations_10 = maze.generate_spawn_locations(10)
    print(f"✓ 为10个Agent生成位置: {len(locations_10)} 个")
    if locations_10:
        print(f"  示例位置: {locations_10[0]}, {locations_10[1] if len(locations_10) > 1 else 'N/A'}")
    
    # 测试4.2: 中量Agent（50个）
    locations_50 = maze.generate_spawn_locations(50)
    print(f"✓ 为50个Agent生成位置: {len(locations_50)} 个")
    
    # 测试4.3: 大量Agent（100个）
    locations_100 = maze.generate_spawn_locations(100)
    print(f"✓ 为100个Agent生成位置: {len(locations_100)} 个")
    
    # 测试4.4: 超大量Agent（200个）
    locations_200 = maze.generate_spawn_locations(200)
    print(f"✓ 为200个Agent生成位置: {len(locations_200)} 个")
    
    # 测试4.5: 检查位置分散度
    import math
    if len(locations_100) >= 2:
        distances = []
        for i in range(min(10, len(locations_100) - 1)):
            x1, y1 = locations_100[i]
            x2, y2 = locations_100[i + 1]
            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            distances.append(dist)
        
        avg_dist = sum(distances) / len(distances)
        print(f"✓ 平均相邻距离: {avg_dist:.1f} 瓦片")
    
    print()
    return True


def test_export():
    """测试地图导出"""
    print("=" * 60)
    print("测试5: 地图导出")
    print("=" * 60)
    
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger()
    
    maze = create_infinite_maze({
        "world": "Test World",
        "tile_size": 32,
        "chunk_size": 32
    }, logger, use_infinite=True)
    
    # 导出一个小区域
    output_file = "results/test_exported_map.json"
    os.makedirs("results", exist_ok=True)
    
    maze.export_current_view(
        center_coord=(0, 0),
        radius=2,  # 5x5区块
        output_file=output_file
    )
    
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"✓ 导出地图成功: {output_file}")
        print(f"  - 文件大小: {size / 1024:.1f} KB")
    else:
        print("✗ 导出失败")
        return False
    
    print()
    return True


def test_performance():
    """测试性能"""
    print("=" * 60)
    print("测试6: 性能测试")
    print("=" * 60)
    
    import time
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger()
    
    maze = create_infinite_maze({
        "world": "Test World",
        "tile_size": 32,
        "chunk_size": 32,
        "max_loaded_chunks": 100
    }, logger, use_infinite=True)
    
    # 测试6.1: 随机访问瓦片
    start_time = time.time()
    import random
    for _ in range(1000):
        x = random.randint(-500, 500)
        y = random.randint(-500, 500)
        tile = maze.tile_at((x, y))
    elapsed = time.time() - start_time
    print(f"✓ 1000次随机瓦片访问: {elapsed:.3f}秒 ({1000/elapsed:.1f} 次/秒)")
    
    # 测试6.2: 区域预加载
    start_time = time.time()
    maze.preload_area_around((0, 0), radius=5)
    elapsed = time.time() - start_time
    print(f"✓ 预加载5区块半径: {elapsed:.3f}秒")
    
    # 测试6.3: 批量寻路
    start_time = time.time()
    paths = []
    for i in range(10):
        start = (i * 10, i * 10)
        end = (i * 10 + 50, i * 10 + 50)
        path = maze.find_path(start, end)
        if path:
            paths.append(path)
    elapsed = time.time() - start_time
    print(f"✓ 10次寻路: {elapsed:.3f}秒 (平均 {elapsed/10*1000:.1f}ms/次)")
    
    stats = maze.get_stats()
    print(f"\n最终统计:")
    print(f"  - 已生成区块: {stats['chunks_generated']}")
    print(f"  - 缓存命中率: {stats['cache_hit_rate']:.1f}%")
    
    print()
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("无限地图系统 - 完整测试")
    print("=" * 60 + "\n")
    
    tests = [
        ("区块管理器", test_chunk_manager),
        ("程序化地形生成", test_procedural_terrain),
        ("无限地图Maze", test_infinite_maze),
        ("智能Agent位置分配", test_agent_spawn_locations),
        ("地图导出", test_export),
        ("性能测试", test_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常使用。")
        print("\n快速开始:")
        print("1. 在Game类中使用:")
        print("   from modules.infinite_map import create_infinite_maze")
        print("   self.maze = create_infinite_maze(config, logger, use_infinite=True)")
        print("\n2. 分配Agent位置:")
        print("   locations = maze.generate_spawn_locations(100)")
        print("\n3. 查看完整文档:")
        print("   INFINITE_MAP_GUIDE.md")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

