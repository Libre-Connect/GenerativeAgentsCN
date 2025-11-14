"""
无限扩展地图系统
支持100+agents的分块动态加载地图
"""

import random
import math
from collections import defaultdict
from typing import Dict, Tuple, Set, List, Optional
from dataclasses import dataclass
import heapq

from modules.memory.event import Event


# 复用原来的Tile类，但优化为支持动态创建
class InfiniteTile:
    """无限地图的瓦片"""
    
    def __init__(
        self,
        coord,
        world,
        address_keys,
        address=None,
        collision=False,
        tile_type="grass"  # 默认地形类型
    ):
        self.coord = coord
        self.address = [world]
        if address:
            self.address += address
        self.address_keys = address_keys
        self.address_map = dict(zip(address_keys[:len(self.address)], self.address))
        self.collision = collision
        self.tile_type = tile_type
        self.event_cnt = 0
        self._events = {}
        
        if len(self.address) == 4:
            self.add_event(Event(self.address[-1], address=self.address))
    
    def abstract(self):
        address = ":".join(self.address)
        if self.collision:
            address += "(collision)"
        return {
            "coord[{},{}]".format(self.coord[0], self.coord[1]): address,
            "events": {k: str(v) for k, v in self.events.items()},
            "type": self.tile_type
        }
    
    def get_events(self):
        return self._events.values()
    
    def add_event(self, event):
        if isinstance(event, (tuple, list)):
            event = Event.from_list(event)
        if all(e != event for e in self._events.values()):
            self._events["e_" + str(self.event_cnt)] = event
            self.event_cnt += 1
        return event
    
    def remove_events(self, subject=None, event=None):
        r_events = {}
        for tag, eve in self._events.items():
            if subject and eve.subject == subject:
                r_events[tag] = eve
            if event and eve == event:
                r_events[tag] = eve
        for r_eve in r_events:
            self._events.pop(r_eve)
        return r_events
    
    def update_events(self, event, match="subject"):
        u_events = {}
        for tag, eve in self._events.items():
            if match == "subject" and eve.subject == event.subject:
                self._events[tag] = event
                u_events[tag] = event
        return u_events
    
    def has_address(self, key):
        return key in self.address_map
    
    def get_address(self, level=None, as_list=True):
        level = level or self.address_keys[-1]
        pos = self.address_keys.index(level) + 1
        if as_list:
            return self.address[:pos]
        return ":".join(self.address[:pos])
    
    def get_addresses(self):
        addresses = []
        if len(self.address) > 1:
            addresses = [
                ":".join(self.address[:i]) for i in range(2, len(self.address) + 1)
            ]
        return addresses
    
    @property
    def events(self):
        return self._events
    
    @property
    def is_empty(self):
        return len(self.address) == 1 and not self._events


@dataclass
class Chunk:
    """地图块"""
    chunk_x: int  # chunk坐标（不是瓦片坐标）
    chunk_y: int
    chunk_size: int = 32  # 每个chunk包含32x32个瓦片
    
    def __post_init__(self):
        self.tiles: Dict[Tuple[int, int], InfiniteTile] = {}
        self.is_generated = False
        self.last_access_time = 0
        self.agent_count = 0  # 当前chunk中的agent数量
    
    def get_tile(self, local_x: int, local_y: int) -> Optional[InfiniteTile]:
        """获取chunk内的瓦片（local坐标）"""
        return self.tiles.get((local_x, local_y))
    
    def set_tile(self, local_x: int, local_y: int, tile: InfiniteTile):
        """设置chunk内的瓦片"""
        self.tiles[(local_x, local_y)] = tile
    
    def get_world_coord(self) -> Tuple[int, int]:
        """获取chunk左上角的世界坐标"""
        return (self.chunk_x * self.chunk_size, self.chunk_y * self.chunk_size)


class InfiniteMaze:
    """无限扩展的地图系统"""
    
    def __init__(self, config, logger, chunk_size=32):
        """
        Args:
            config: 基础配置（world名称等）
            logger: 日志器
            chunk_size: 每个chunk的大小（默认32x32瓦片）
        """
        self.logger = logger
        self.chunk_size = chunk_size
        self.tile_size = config.get("tile_size", 32)
        self.world = config.get("world", "InfiniteWorld")
        self.address_keys = config.get("tile_address_keys", ["world", "sector", "arena", "game_object"])
        
        # Chunk存储
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        
        # 活跃区域跟踪
        self.active_chunks: Set[Tuple[int, int]] = set()
        self.agent_positions: Dict[str, Tuple[int, int]] = {}  # agent_id -> (x, y)
        
        # 缓存和优化
        self.tile_cache: Dict[Tuple[int, int], InfiniteTile] = {}  # 最近访问的瓦片
        self.max_cache_size = 10000
        
        # 地形生成器
        self.terrain_generators = self._initialize_terrain_generators()
        
        # 建筑和特殊区域
        self.buildings: Dict[Tuple[int, int], dict] = {}  # 坐标 -> 建筑信息
        self.special_zones: Dict[str, dict] = {}  # 特殊区域（城镇、村庄等）
        
        # 初始化起始区域
        self._initialize_spawn_area()
        
        self.logger.info(f"无限地图系统已初始化 (chunk_size={chunk_size})")
    
    def _initialize_terrain_generators(self) -> Dict[str, callable]:
        """初始化地形生成器"""
        return {
            "grass": lambda x, y: self._generate_grass_tile(x, y),
            "forest": lambda x, y: self._generate_forest_tile(x, y),
            "mountain": lambda x, y: self._generate_mountain_tile(x, y),
            "water": lambda x, y: self._generate_water_tile(x, y),
            "desert": lambda x, y: self._generate_desert_tile(x, y),
            "town": lambda x, y: self._generate_town_tile(x, y),
        }
    
    def _initialize_spawn_area(self):
        """初始化出生区域（中心3x3 chunks）"""
        for cx in range(-1, 2):
            for cy in range(-1, 2):
                self._generate_chunk(cx, cy, terrain_type="grass")
        
        # 创建一个中心城镇
        self.special_zones["spawn_town"] = {
            "center": (0, 0),
            "radius": 50,
            "type": "town",
            "name": "新手村"
        }
        
        self.logger.info("出生区域已初始化（中心3x3 chunks）")
    
    def _world_to_chunk_coord(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """世界坐标转chunk坐标"""
        chunk_x = world_x // self.chunk_size
        chunk_y = world_y // self.chunk_size
        return (chunk_x, chunk_y)
    
    def _world_to_local_coord(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """世界坐标转chunk内局部坐标"""
        local_x = world_x % self.chunk_size
        local_y = world_y % self.chunk_size
        return (local_x, local_y)
    
    def _generate_chunk(self, chunk_x: int, chunk_y: int, terrain_type: str = "auto") -> Chunk:
        """生成一个新的chunk"""
        chunk_coord = (chunk_x, chunk_y)
        
        if chunk_coord in self.chunks:
            return self.chunks[chunk_coord]
        
        chunk = Chunk(chunk_x, chunk_y, self.chunk_size)
        
        # 根据位置决定地形类型
        if terrain_type == "auto":
            terrain_type = self._determine_terrain_type(chunk_x, chunk_y)
        
        # 生成chunk内的所有瓦片
        for local_y in range(self.chunk_size):
            for local_x in range(self.chunk_size):
                world_x = chunk_x * self.chunk_size + local_x
                world_y = chunk_y * self.chunk_size + local_y
                
                # 使用地形生成器
                generator = self.terrain_generators.get(terrain_type, self.terrain_generators["grass"])
                tile = generator(world_x, world_y)
                
                chunk.set_tile(local_x, local_y, tile)
        
        chunk.is_generated = True
        self.chunks[chunk_coord] = chunk
        
        return chunk
    
    def _determine_terrain_type(self, chunk_x: int, chunk_y: int) -> str:
        """根据chunk位置确定地形类型"""
        distance_from_center = math.sqrt(chunk_x**2 + chunk_y**2)
        
        # 使用柏林噪声的简化版本
        noise_val = (math.sin(chunk_x * 0.3) + math.cos(chunk_y * 0.3)) / 2
        
        # 中心区域是草地和城镇
        if distance_from_center < 3:
            return "grass"
        elif distance_from_center < 8:
            # 中等距离：混合地形
            if noise_val > 0.3:
                return "forest"
            elif noise_val < -0.3:
                return "water"
            else:
                return "grass"
        else:
            # 远距离：更多山地和沙漠
            if noise_val > 0.5:
                return "mountain"
            elif noise_val < -0.5:
                return "desert"
            elif noise_val > 0:
                return "forest"
            else:
                return "grass"
    
    def _generate_grass_tile(self, x: int, y: int) -> InfiniteTile:
        """生成草地瓦片"""
        collision = random.random() < 0.05  # 5%概率有障碍物
        return InfiniteTile(
            coord=(x, y),
            world=self.world,
            address_keys=self.address_keys,
            collision=collision,
            tile_type="grass"
        )
    
    def _generate_forest_tile(self, x: int, y: int) -> InfiniteTile:
        """生成森林瓦片"""
        collision = random.random() < 0.3  # 30%概率是树木（不可通行）
        return InfiniteTile(
            coord=(x, y),
            world=self.world,
            address_keys=self.address_keys,
            collision=collision,
            tile_type="forest"
        )
    
    def _generate_mountain_tile(self, x: int, y: int) -> InfiniteTile:
        """生成山地瓦片"""
        collision = random.random() < 0.6  # 60%概率不可通行
        return InfiniteTile(
            coord=(x, y),
            world=self.world,
            address_keys=self.address_keys,
            collision=collision,
            tile_type="mountain"
        )
    
    def _generate_water_tile(self, x: int, y: int) -> InfiniteTile:
        """生成水域瓦片"""
        return InfiniteTile(
            coord=(x, y),
            world=self.world,
            address_keys=self.address_keys,
            collision=True,  # 水域不可通行
            tile_type="water"
        )
    
    def _generate_desert_tile(self, x: int, y: int) -> InfiniteTile:
        """生成沙漠瓦片"""
        collision = random.random() < 0.1  # 10%概率有障碍物
        return InfiniteTile(
            coord=(x, y),
            world=self.world,
            address_keys=self.address_keys,
            collision=collision,
            tile_type="desert"
        )
    
    def _generate_town_tile(self, x: int, y: int) -> InfiniteTile:
        """生成城镇瓦片"""
        return InfiniteTile(
            coord=(x, y),
            world=self.world,
            address_keys=self.address_keys,
            address=["town_sector", "town_plaza"],  # 城镇地址
            collision=False,
            tile_type="town"
        )
    
    def tile_at(self, coord) -> Optional[InfiniteTile]:
        """获取指定坐标的瓦片"""
        x, y = coord if isinstance(coord, tuple) else (coord[0], coord[1])
        
        # 先检查缓存
        if (x, y) in self.tile_cache:
            return self.tile_cache[(x, y)]
        
        # 确定所属chunk
        chunk_coord = self._world_to_chunk_coord(x, y)
        local_coord = self._world_to_local_coord(x, y)
        
        # 如果chunk不存在，生成它
        if chunk_coord not in self.chunks:
            self._generate_chunk(chunk_coord[0], chunk_coord[1])
        
        chunk = self.chunks[chunk_coord]
        tile = chunk.get_tile(local_coord[0], local_coord[1])
        
        # 更新缓存
        if tile:
            self.tile_cache[(x, y)] = tile
            if len(self.tile_cache) > self.max_cache_size:
                # 移除最旧的一半缓存
                to_remove = list(self.tile_cache.keys())[:self.max_cache_size // 2]
                for key in to_remove:
                    del self.tile_cache[key]
        
        return tile
    
    def update_agent_position(self, agent_id: str, x: int, y: int):
        """更新agent位置并管理活跃区域"""
        self.agent_positions[agent_id] = (x, y)
        
        # 更新活跃chunks
        self._update_active_chunks()
        
        # 检查是否需要扩展地图
        self._check_map_expansion(x, y)
    
    def _update_active_chunks(self):
        """更新活跃的chunks（agent周围的chunks）"""
        new_active = set()
        
        for agent_id, (x, y) in self.agent_positions.items():
            chunk_coord = self._world_to_chunk_coord(x, y)
            
            # 加载agent周围3x3的chunks
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    cx = chunk_coord[0] + dx
                    cy = chunk_coord[1] + dy
                    new_active.add((cx, cy))
                    
                    # 确保chunk已生成
                    if (cx, cy) not in self.chunks:
                        self._generate_chunk(cx, cy)
        
        self.active_chunks = new_active
    
    def _check_map_expansion(self, x: int, y: int):
        """检查是否需要扩展地图边界"""
        chunk_coord = self._world_to_chunk_coord(x, y)
        
        # 预加载相邻chunks
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                cx = chunk_coord[0] + dx
                cy = chunk_coord[1] + dy
                if (cx, cy) not in self.chunks:
                    self._generate_chunk(cx, cy)
    
    def get_active_tiles(self) -> List[InfiniteTile]:
        """获取所有活跃区域的瓦片"""
        tiles = []
        for chunk_coord in self.active_chunks:
            chunk = self.chunks.get(chunk_coord)
            if chunk:
                tiles.extend(chunk.tiles.values())
        return tiles
    
    def find_path(self, src_coord, dst_coord, max_distance=100):
        """
        优化的A*寻路算法（限制搜索范围）
        
        Args:
            src_coord: 起点
            dst_coord: 终点
            max_distance: 最大搜索距离
        
        Returns:
            路径列表，如果找不到返回空列表
        """
        src = tuple(src_coord) if not isinstance(src_coord, tuple) else src_coord
        dst = tuple(dst_coord) if not isinstance(dst_coord, tuple) else dst_coord
        
        # 曼哈顿距离启发函数
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        # A* 算法
        frontier = []
        heapq.heappush(frontier, (0, src))
        came_from = {src: None}
        cost_so_far = {src: 0}
        
        while frontier:
            current_priority, current = heapq.heappop(frontier)
            
            if current == dst:
                break
            
            # 限制搜索范围
            if heuristic(current, src) > max_distance:
                continue
            
            # 检查四个方向
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_pos = (current[0] + dx, current[1] + dy)
                
                # 检查瓦片是否可通行
                tile = self.tile_at(next_pos)
                if not tile or tile.collision:
                    continue
                
                new_cost = cost_so_far[current] + 1
                
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(next_pos, dst)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current
        
        # 重建路径
        if dst not in came_from:
            return []  # 找不到路径
        
        path = []
        current = dst
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        
        return path
    
    def get_around(self, coord, radius=1):
        """获取周围的坐标"""
        x, y = coord if isinstance(coord, tuple) else (coord[0], coord[1])
        around = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                around.append((x + dx, y + dy))
        return around
    
    def get_address_tiles(self, address):
        """获取指定地址的所有瓦片坐标"""
        # 简化实现：搜索活跃区域
        if isinstance(address, str):
            address = address.split(":")
        
        tiles = set()
        for chunk_coord in self.active_chunks:
            chunk = self.chunks.get(chunk_coord)
            if chunk:
                for tile in chunk.tiles.values():
                    if address[-1] in tile.get_address(as_list=False):
                        tiles.add(tile.coord)
        
        return tiles if tiles else {(0, 0)}  # 默认返回中心
    
    def update_obj(self, coord, event):
        """更新物体事件"""
        tile = self.tile_at(coord)
        if tile:
            tile.update_events(event)
    
    def get_statistics(self) -> dict:
        """获取地图统计信息"""
        return {
            "total_chunks": len(self.chunks),
            "active_chunks": len(self.active_chunks),
            "active_agents": len(self.agent_positions),
            "tile_cache_size": len(self.tile_cache),
            "generated_tiles": sum(len(c.tiles) for c in self.chunks.values()),
            "memory_usage_mb": (
                len(self.chunks) * self.chunk_size * self.chunk_size * 0.001  # 粗略估计
            )
        }
    
    def cleanup_inactive_chunks(self, keep_distance=5):
        """清理不活跃的chunks以释放内存"""
        # 找出所有agent位置的chunks
        agent_chunks = set()
        for x, y in self.agent_positions.values():
            chunk_coord = self._world_to_chunk_coord(x, y)
            # 保留周围keep_distance范围的chunks
            for dx in range(-keep_distance, keep_distance + 1):
                for dy in range(-keep_distance, keep_distance + 1):
                    agent_chunks.add((chunk_coord[0] + dx, chunk_coord[1] + dy))
        
        # 删除远离所有agent的chunks
        chunks_to_remove = []
        for chunk_coord in list(self.chunks.keys()):
            if chunk_coord not in agent_chunks:
                # 但保留中心区域
                if abs(chunk_coord[0]) <= 2 and abs(chunk_coord[1]) <= 2:
                    continue
                chunks_to_remove.append(chunk_coord)
        
        for chunk_coord in chunks_to_remove:
            del self.chunks[chunk_coord]
        
        if chunks_to_remove:
            self.logger.info(f"清理了 {len(chunks_to_remove)} 个不活跃的chunks")
        
        return len(chunks_to_remove)

