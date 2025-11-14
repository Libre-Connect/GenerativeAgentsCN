"""
无限地图Maze实现
扩展原有Maze类以支持无限动态地图
"""

import random
from typing import List, Tuple, Optional, Set
from itertools import product

from modules.maze import Tile
from modules.memory.event import Event
from .chunk_manager import ChunkManager


class InfiniteMazeTile(Tile):
    """无限地图的瓦片（扩展原有Tile类）"""
    
    def __init__(self, coord, world, address_keys, chunk_data=None, **kwargs):
        super().__init__(coord, world, address_keys, **kwargs)
        self.chunk_data = chunk_data or {}
    
    @classmethod
    def from_chunk_tile(cls, coord, world, address_keys, tile_data):
        """从chunk瓦片数据创建"""
        collision = tile_data.get("collision", False)
        
        # 如果有建筑，创建address
        address = None
        if "building" in tile_data:
            address = [world, "sector", "arena", tile_data["building"]]
        
        return cls(
            coord=coord,
            world=world,
            address_keys=address_keys,
            address=address,
            collision=collision,
            chunk_data=tile_data
        )


class InfiniteMaze:
    """
    无限地图Maze
    与原有Maze接口兼容，但支持无限扩展
    """
    
    def __init__(self, config, logger, use_infinite=True):
        """
        初始化无限地图
        
        Args:
            config: 配置字典
            logger: 日志记录器
            use_infinite: 是否使用无限地图（False则回退到原始Maze）
        """
        self.logger = logger
        self.use_infinite = use_infinite
        
        # 基础配置
        self.world = config.get("world", "the Infinite World")
        self.tile_size = config.get("tile_size", 32)
        self.address_keys = config.get("tile_address_keys", ["world", "sector", "arena", "game_object"])
        
        if use_infinite:
            # 使用区块管理器
            self.chunk_manager = ChunkManager(
                chunk_size=config.get("chunk_size", 32),
                tile_size=self.tile_size,
                max_loaded_chunks=config.get("max_loaded_chunks", 100)
            )
            
            # 无限地图没有固定大小
            self.maze_width = None
            self.maze_height = None
            
            # 瓦片缓存（只缓存最近访问的）
            self._tile_cache: Dict[Tuple[int, int], InfiniteMazeTile] = {}
            self._cache_size = 1000
            
            # 地址到瓦片的映射
            self.address_tiles = {}
            
            # 初始化中心区域
            self._initialize_spawn_area()
            
        else:
            # 回退到原始固定地图
            from modules.maze import Maze
            self._fallback_maze = Maze(config, logger)
            # 复制属性以保持兼容
            self.maze_width = self._fallback_maze.maze_width
            self.maze_height = self._fallback_maze.maze_height
            self.tiles = self._fallback_maze.tiles
            self.address_tiles = self._fallback_maze.address_tiles
    
    def _initialize_spawn_area(self):
        """初始化出生区域（中心安全区）"""
        # 在(0,0)周围生成一些区块
        for cy in range(-2, 3):
            for cx in range(-2, 3):
                self.chunk_manager.get_chunk(cx, cy)
        
        self.logger.info(f"Initialized infinite map spawn area (25 chunks)")
    
    def tile_at(self, coord: Tuple[int, int]) -> InfiniteMazeTile:
        """
        获取指定坐标的瓦片
        
        Args:
            coord: (x, y) 坐标
        
        Returns:
            瓦片对象
        """
        if not self.use_infinite:
            return self._fallback_maze.tile_at(coord)
        
        x, y = coord
        
        # 检查缓存
        if coord in self._tile_cache:
            return self._tile_cache[coord]
        
        # 从chunk manager获取
        tile_data = self.chunk_manager.get_tile(x, y)
        
        if tile_data:
            tile = InfiniteMazeTile.from_chunk_tile(
                coord=coord,
                world=self.world,
                address_keys=self.address_keys,
                tile_data=tile_data
            )
        else:
            # 默认瓦片
            tile = InfiniteMazeTile(
                coord=coord,
                world=self.world,
                address_keys=self.address_keys
            )
        
        # 添加到缓存
        self._add_to_cache(coord, tile)
        
        # 更新地址映射
        for addr in tile.get_addresses():
            self.address_tiles.setdefault(addr, set()).add(coord)
        
        return tile
    
    def _add_to_cache(self, coord: Tuple[int, int], tile: InfiniteMazeTile):
        """添加瓦片到缓存"""
        if len(self._tile_cache) >= self._cache_size:
            # 移除最旧的条目（简单FIFO）
            oldest_key = next(iter(self._tile_cache))
            del self._tile_cache[oldest_key]
        
        self._tile_cache[coord] = tile
    
    def find_path(self, src_coord: Tuple[int, int], dst_coord: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        寻找从src到dst的路径（A*算法）
        
        Args:
            src_coord: 起点坐标
            dst_coord: 终点坐标
        
        Returns:
            路径坐标列表
        """
        if not self.use_infinite:
            return self._fallback_maze.find_path(src_coord, dst_coord)
        
        # 使用A*算法（对无限地图更合适）
        import heapq
        
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        open_set = []
        heapq.heappush(open_set, (0, src_coord))
        
        came_from = {}
        g_score = {src_coord: 0}
        f_score = {src_coord: heuristic(src_coord, dst_coord)}
        
        max_iterations = 10000  # 防止无限循环
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            current = heapq.heappop(open_set)[1]
            
            if current == dst_coord:
                # 重建路径
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return path[::-1]
            
            for neighbor in self.get_around(current):
                tentative_g = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, dst_coord)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # 找不到路径，返回空
        return []
    
    def get_around(self, coord: Tuple[int, int], no_collision: bool = True) -> List[Tuple[int, int]]:
        """
        获取周围的瓦片坐标
        
        Args:
            coord: 中心坐标
            no_collision: 是否排除碰撞瓦片
        
        Returns:
            周围瓦片坐标列表
        """
        if not self.use_infinite:
            return self._fallback_maze.get_around(coord, no_collision)
        
        x, y = coord
        coords = [
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        ]
        
        if no_collision:
            coords = [c for c in coords if not self.tile_at(c).collision]
        
        return coords
    
    def get_scope(self, coord: Tuple[int, int], config: dict) -> List[InfiniteMazeTile]:
        """
        获取视野范围内的瓦片
        
        Args:
            coord: 中心坐标
            config: 配置（vision_r, mode等）
        
        Returns:
            瓦片列表
        """
        if not self.use_infinite:
            return self._fallback_maze.get_scope(coord, config)
        
        coords = []
        vision_r = config.get("vision_r", 5)
        mode = config.get("mode", "box")
        
        if mode == "box":
            x_range = range(coord[0] - vision_r, coord[0] + vision_r + 1)
            y_range = range(coord[1] - vision_r, coord[1] + vision_r + 1)
            coords = list(product(x_range, y_range))
        
        return [self.tile_at(c) for c in coords]
    
    def update_obj(self, coord: Tuple[int, int], obj_event: Event):
        """更新对象事件"""
        if not self.use_infinite:
            return self._fallback_maze.update_obj(coord, obj_event)
        
        tile = self.tile_at(coord)
        if not tile.has_address("game_object"):
            return
        if obj_event.address != tile.get_address("game_object"):
            return
        
        addr = ":".join(obj_event.address)
        if addr not in self.address_tiles:
            return
        
        for c in self.address_tiles[addr]:
            self.tile_at(c).update_events(obj_event)
    
    def get_address_tiles(self, address: List[str]) -> Set[Tuple[int, int]]:
        """获取指定地址的所有瓦片坐标"""
        if not self.use_infinite:
            return self._fallback_maze.get_address_tiles(address)
        
        addr = ":".join(address)
        if addr in self.address_tiles:
            return self.address_tiles[addr]
        
        # 如果没有，返回出生点附近的一个随机位置
        return {(random.randint(-10, 10), random.randint(-10, 10))}
    
    def preload_area_around(self, coord: Tuple[int, int], radius: int = 5):
        """
        预加载某个坐标周围的区域
        
        Args:
            coord: 中心坐标
            radius: 预加载半径（区块数）
        """
        if not self.use_infinite:
            return
        
        chunk_x, chunk_y, _, _ = self.chunk_manager.world_to_chunk_coords(coord[0], coord[1])
        self.chunk_manager.preload_area(chunk_x, chunk_y, radius)
        
        self.logger.debug(f"Preloaded area around {coord}, radius {radius} chunks")
    
    def generate_spawn_locations(self, count: int) -> List[Tuple[int, int]]:
        """
        生成Agent出生位置
        
        Args:
            count: 需要的位置数量
        
        Returns:
            坐标列表
        """
        if not self.use_infinite:
            # 对于固定地图，在中心区域随机选择
            locations = []
            attempts = 0
            while len(locations) < count and attempts < count * 10:
                attempts += 1
                x = random.randint(10, self.maze_width - 10)
                y = random.randint(10, self.maze_height - 10)
                
                tile = self.tile_at((x, y))
                if not tile.collision:
                    locations.append((x, y))
            
            return locations
        
        # 使用chunk manager的智能分配
        locations = self.chunk_manager.find_suitable_spawn_locations(count)
        
        self.logger.info(f"Generated {len(locations)} spawn locations for agents")
        
        return locations
    
    def get_stats(self) -> dict:
        """获取地图统计信息"""
        if not self.use_infinite:
            return {
                "type": "fixed",
                "width": self.maze_width,
                "height": self.maze_height,
                "total_tiles": self.maze_width * self.maze_height
            }
        
        chunk_stats = self.chunk_manager.get_stats()
        
        return {
            "type": "infinite",
            "tile_cache_size": len(self._tile_cache),
            "address_mappings": len(self.address_tiles),
            **chunk_stats
        }
    
    def export_current_view(self, center_coord: Tuple[int, int], radius: int, output_file: str):
        """
        导出当前视图为静态地图文件（用于调试）
        
        Args:
            center_coord: 中心坐标
            radius: 导出半径（区块数）
            output_file: 输出文件路径
        """
        if not self.use_infinite:
            self.logger.warning("Export only available for infinite maps")
            return
        
        chunk_x, chunk_y, _, _ = self.chunk_manager.world_to_chunk_coords(
            center_coord[0], center_coord[1]
        )
        
        self.chunk_manager.export_area_to_json(chunk_x, chunk_y, radius, output_file)
        
        self.logger.info(f"Exported map view to {output_file}")


def create_infinite_maze(config, logger, use_infinite=True):
    """
    创建地图实例的工厂函数
    
    Args:
        config: 配置字典
        logger: 日志记录器
        use_infinite: 是否使用无限地图
    
    Returns:
        InfiniteMaze 或 Maze实例
    """
    if use_infinite:
        return InfiniteMaze(config, logger, use_infinite=True)
    else:
        from modules.maze import Maze
        return Maze(config, logger)

