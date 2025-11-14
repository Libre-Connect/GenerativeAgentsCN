"""
动态分块地图系统 - Chunk Manager
支持无限拓展的地图，按需加载和卸载区块
"""

import json
import os
import random
import math
from typing import Dict, Tuple, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum


class BiomeType(Enum):
    """生物群系类型"""
    PLAINS = "plains"           # 平原
    FOREST = "forest"           # 森林
    DESERT = "desert"           # 沙漠
    MOUNTAINS = "mountains"     # 山地
    WATER = "water"            # 水域
    VILLAGE = "village"         # 村庄
    FARMLAND = "farmland"       # 农田
    URBAN = "urban"            # 城市


@dataclass
class ChunkData:
    """区块数据"""
    chunk_x: int                # 区块X坐标
    chunk_y: int                # 区块Y坐标
    biome: BiomeType           # 生物群系
    tiles: List[List[Dict]]    # 瓦片数据 [y][x]
    generated: bool = True     # 是否已生成
    loaded: bool = False       # 是否已加载到内存
    last_access_time: float = 0.0  # 最后访问时间
    
    def get_tile(self, x: int, y: int) -> Optional[Dict]:
        """获取瓦片数据"""
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]
        return None
    
    def set_tile(self, x: int, y: int, tile_data: Dict):
        """设置瓦片数据"""
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            self.tiles[y][x] = tile_data


class ChunkManager:
    """区块管理器 - 支持无限拓展的地图"""
    
    def __init__(self, 
                 chunk_size: int = 32,
                 tile_size: int = 32,
                 max_loaded_chunks: int = 100,
                 save_dir: str = "results/map_chunks"):
        """
        初始化区块管理器
        
        Args:
            chunk_size: 每个区块的瓦片数（默认32x32）
            tile_size: 每个瓦片的像素大小（默认32px）
            max_loaded_chunks: 最大同时加载的区块数
            save_dir: 区块保存目录
        """
        self.chunk_size = chunk_size
        self.tile_size = tile_size
        self.max_loaded_chunks = max_loaded_chunks
        self.save_dir = save_dir
        
        # 区块缓存
        self.loaded_chunks: Dict[Tuple[int, int], ChunkData] = {}
        self.chunk_load_order: List[Tuple[int, int]] = []  # LRU队列
        
        # 地形生成器
        from .procedural_terrain import ProceduralTerrainGenerator
        self.terrain_generator = ProceduralTerrainGenerator(
            chunk_size=chunk_size,
            tile_size=tile_size
        )
        
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        
        # 统计信息
        self.stats = {
            "chunks_generated": 0,
            "chunks_loaded": 0,
            "chunks_unloaded": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def world_to_chunk_coords(self, world_x: int, world_y: int) -> Tuple[int, int, int, int]:
        """
        世界坐标转换为区块坐标和区块内坐标
        
        Returns:
            (chunk_x, chunk_y, local_x, local_y)
        """
        chunk_x = world_x // self.chunk_size
        chunk_y = world_y // self.chunk_size
        local_x = world_x % self.chunk_size
        local_y = world_y % self.chunk_size
        
        return chunk_x, chunk_y, local_x, local_y
    
    def chunk_to_world_coords(self, chunk_x: int, chunk_y: int) -> Tuple[int, int]:
        """
        区块坐标转换为世界坐标（区块左上角）
        
        Returns:
            (world_x, world_y)
        """
        return chunk_x * self.chunk_size, chunk_y * self.chunk_size
    
    def get_chunk(self, chunk_x: int, chunk_y: int, auto_generate: bool = True) -> Optional[ChunkData]:
        """
        获取区块数据（如果不存在则生成）
        
        Args:
            chunk_x: 区块X坐标
            chunk_y: 区块Y坐标
            auto_generate: 是否自动生成不存在的区块
        
        Returns:
            区块数据，如果不存在且不自动生成则返回None
        """
        chunk_key = (chunk_x, chunk_y)
        
        # 检查是否已加载
        if chunk_key in self.loaded_chunks:
            self.stats["cache_hits"] += 1
            self._update_chunk_access(chunk_key)
            return self.loaded_chunks[chunk_key]
        
        self.stats["cache_misses"] += 1
        
        # 尝试从磁盘加载
        chunk = self._load_chunk_from_disk(chunk_x, chunk_y)
        
        if chunk is None and auto_generate:
            # 生成新区块
            chunk = self._generate_chunk(chunk_x, chunk_y)
        
        if chunk:
            self._add_chunk_to_cache(chunk_key, chunk)
        
        return chunk
    
    def get_tile(self, world_x: int, world_y: int, auto_generate: bool = True) -> Optional[Dict]:
        """
        获取世界坐标的瓦片数据
        
        Args:
            world_x: 世界X坐标
            world_y: 世界Y坐标
            auto_generate: 是否自动生成不存在的区块
        
        Returns:
            瓦片数据字典
        """
        chunk_x, chunk_y, local_x, local_y = self.world_to_chunk_coords(world_x, world_y)
        
        chunk = self.get_chunk(chunk_x, chunk_y, auto_generate)
        if chunk:
            return chunk.get_tile(local_x, local_y)
        
        return None
    
    def set_tile(self, world_x: int, world_y: int, tile_data: Dict):
        """设置世界坐标的瓦片数据"""
        chunk_x, chunk_y, local_x, local_y = self.world_to_chunk_coords(world_x, world_y)
        
        chunk = self.get_chunk(chunk_x, chunk_y, auto_generate=True)
        if chunk:
            chunk.set_tile(local_x, local_y, tile_data)
    
    def get_chunks_in_area(self, 
                           world_x: int, 
                           world_y: int, 
                           width: int, 
                           height: int) -> List[ChunkData]:
        """
        获取指定世界区域内的所有区块
        
        Args:
            world_x: 区域左上角世界X坐标
            world_y: 区域左上角世界Y坐标
            width: 区域宽度（瓦片数）
            height: 区域高度（瓦片数）
        
        Returns:
            区块列表
        """
        # 计算区块范围
        start_chunk_x = world_x // self.chunk_size
        start_chunk_y = world_y // self.chunk_size
        end_chunk_x = (world_x + width - 1) // self.chunk_size
        end_chunk_y = (world_y + height - 1) // self.chunk_size
        
        chunks = []
        for cy in range(start_chunk_y, end_chunk_y + 1):
            for cx in range(start_chunk_x, end_chunk_x + 1):
                chunk = self.get_chunk(cx, cy)
                if chunk:
                    chunks.append(chunk)
        
        return chunks
    
    def preload_area(self, center_x: int, center_y: int, radius: int = 3):
        """
        预加载某个区域周围的区块
        
        Args:
            center_x: 中心区块X坐标
            center_y: 中心区块Y坐标
            radius: 加载半径（区块数）
        """
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                self.get_chunk(center_x + dx, center_y + dy)
    
    def _generate_chunk(self, chunk_x: int, chunk_y: int) -> ChunkData:
        """生成新区块"""
        chunk = self.terrain_generator.generate_chunk(chunk_x, chunk_y)
        self.stats["chunks_generated"] += 1
        
        # 保存到磁盘
        self._save_chunk_to_disk(chunk)
        
        return chunk
    
    def _add_chunk_to_cache(self, chunk_key: Tuple[int, int], chunk: ChunkData):
        """将区块添加到缓存"""
        # 检查缓存大小
        if len(self.loaded_chunks) >= self.max_loaded_chunks:
            self._unload_oldest_chunk()
        
        self.loaded_chunks[chunk_key] = chunk
        chunk.loaded = True
        self.chunk_load_order.append(chunk_key)
        self.stats["chunks_loaded"] += 1
    
    def _update_chunk_access(self, chunk_key: Tuple[int, int]):
        """更新区块访问时间（LRU）"""
        if chunk_key in self.chunk_load_order:
            self.chunk_load_order.remove(chunk_key)
        self.chunk_load_order.append(chunk_key)
        
        import time
        if chunk_key in self.loaded_chunks:
            self.loaded_chunks[chunk_key].last_access_time = time.time()
    
    def _unload_oldest_chunk(self):
        """卸载最久未使用的区块"""
        if not self.chunk_load_order:
            return
        
        # 获取最旧的区块
        oldest_key = self.chunk_load_order.pop(0)
        
        if oldest_key in self.loaded_chunks:
            chunk = self.loaded_chunks[oldest_key]
            
            # 保存到磁盘
            self._save_chunk_to_disk(chunk)
            
            # 从内存移除
            chunk.loaded = False
            del self.loaded_chunks[oldest_key]
            self.stats["chunks_unloaded"] += 1
    
    def _get_chunk_filename(self, chunk_x: int, chunk_y: int) -> str:
        """获取区块文件名"""
        return os.path.join(self.save_dir, f"chunk_{chunk_x}_{chunk_y}.json")
    
    def _save_chunk_to_disk(self, chunk: ChunkData):
        """保存区块到磁盘"""
        filename = self._get_chunk_filename(chunk.chunk_x, chunk.chunk_y)
        
        data = {
            "chunk_x": chunk.chunk_x,
            "chunk_y": chunk.chunk_y,
            "biome": chunk.biome.value,
            "tiles": chunk.tiles,
            "generated": chunk.generated
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_chunk_from_disk(self, chunk_x: int, chunk_y: int) -> Optional[ChunkData]:
        """从磁盘加载区块"""
        filename = self._get_chunk_filename(chunk_x, chunk_y)
        
        if not os.path.exists(filename):
            return None
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunk = ChunkData(
                chunk_x=data["chunk_x"],
                chunk_y=data["chunk_y"],
                biome=BiomeType(data["biome"]),
                tiles=data["tiles"],
                generated=data.get("generated", True),
                loaded=False
            )
            
            return chunk
        
        except Exception as e:
            print(f"Error loading chunk ({chunk_x}, {chunk_y}): {e}")
            return None
    
    def unload_all_chunks(self):
        """卸载所有区块（保存到磁盘）"""
        for chunk_key, chunk in list(self.loaded_chunks.items()):
            self._save_chunk_to_disk(chunk)
        
        self.loaded_chunks.clear()
        self.chunk_load_order.clear()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "loaded_chunks_count": len(self.loaded_chunks),
            "cache_hit_rate": (
                self.stats["cache_hits"] / 
                max(1, self.stats["cache_hits"] + self.stats["cache_misses"])
            ) * 100
        }
    
    def find_suitable_spawn_locations(self, 
                                     count: int, 
                                     search_radius: int = 10) -> List[Tuple[int, int]]:
        """
        寻找合适的Agent生成位置
        
        Args:
            count: 需要的位置数量
            search_radius: 搜索半径（区块数）
        
        Returns:
            世界坐标列表 [(world_x, world_y), ...]
        """
        locations = []
        attempts = 0
        max_attempts = count * 10
        
        # 优先选择村庄和平原区域
        preferred_biomes = [BiomeType.VILLAGE, BiomeType.PLAINS, BiomeType.FARMLAND]
        
        while len(locations) < count and attempts < max_attempts:
            attempts += 1
            
            # 在搜索范围内随机选择一个区块
            chunk_x = random.randint(-search_radius, search_radius)
            chunk_y = random.randint(-search_radius, search_radius)
            
            chunk = self.get_chunk(chunk_x, chunk_y)
            if not chunk:
                continue
            
            # 如果不是首选生物群系，降低概率
            if chunk.biome not in preferred_biomes and random.random() > 0.3:
                continue
            
            # 在区块内随机选择一个位置
            local_x = random.randint(0, self.chunk_size - 1)
            local_y = random.randint(0, self.chunk_size - 1)
            
            world_x, world_y = self.chunk_to_world_coords(chunk_x, chunk_y)
            world_x += local_x
            world_y += local_y
            
            # 检查该位置是否可用（不是水域、不太靠近其他位置）
            tile = chunk.get_tile(local_x, local_y)
            if tile and not tile.get("collision", False):
                # 检查与已有位置的距离
                too_close = False
                min_distance = self.chunk_size // 4  # 最小距离
                
                for ex_x, ex_y in locations:
                    dist = math.sqrt((world_x - ex_x)**2 + (world_y - ex_y)**2)
                    if dist < min_distance:
                        too_close = True
                        break
                
                if not too_close:
                    locations.append((world_x, world_y))
        
        return locations
    
    def export_area_to_json(self, 
                           center_x: int, 
                           center_y: int, 
                           radius: int, 
                           output_file: str):
        """
        导出指定区域为Phaser兼容的JSON格式
        
        Args:
            center_x: 中心区块X
            center_y: 中心区块Y
            radius: 导出半径（区块数）
            output_file: 输出文件路径
        """
        # 计算导出范围
        start_cx = center_x - radius
        start_cy = center_y - radius
        end_cx = center_x + radius
        end_cy = center_y + radius
        
        total_width = (end_cx - start_cx + 1) * self.chunk_size
        total_height = (end_cy - start_cy + 1) * self.chunk_size
        
        # 收集所有瓦片数据
        layers_data = {}
        
        for cy in range(start_cy, end_cy + 1):
            for cx in range(start_cx, end_cx + 1):
                chunk = self.get_chunk(cx, cy)
                if not chunk:
                    continue
                
                # 计算在导出地图中的偏移
                offset_x = (cx - start_cx) * self.chunk_size
                offset_y = (cy - start_cy) * self.chunk_size
                
                # 遍历区块的每个瓦片
                for y in range(self.chunk_size):
                    for x in range(self.chunk_size):
                        tile = chunk.get_tile(x, y)
                        if not tile:
                            continue
                        
                        world_x = offset_x + x
                        world_y = offset_y + y
                        
                        # 组织图层数据
                        for layer_name, tile_id in tile.items():
                            if layer_name not in layers_data:
                                layers_data[layer_name] = {}
                            
                            layers_data[layer_name][(world_x, world_y)] = tile_id
        
        # 创建Phaser格式的地图数据
        map_data = {
            "width": total_width,
            "height": total_height,
            "tilewidth": self.tile_size,
            "tileheight": self.tile_size,
            "infinite": False,  # 导出的是固定大小
            "layers": []
        }
        
        # 添加图层
        for layer_name, tiles in layers_data.items():
            layer = {
                "name": layer_name,
                "type": "tilelayer",
                "width": total_width,
                "height": total_height,
                "data": [0] * (total_width * total_height)
            }
            
            # 填充瓦片数据
            for (x, y), tile_id in tiles.items():
                if 0 <= y < total_height and 0 <= x < total_width:
                    index = y * total_width + x
                    layer["data"][index] = tile_id
            
            map_data["layers"].append(layer)
        
        # 保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
        
        print(f"Exported area to {output_file}: {total_width}x{total_height} tiles")

