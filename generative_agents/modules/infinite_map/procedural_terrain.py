"""
程序化地形生成器
使用柏林噪声和规则生成自然、连续的地形
"""

import random
import math
from typing import Dict, List, Tuple
from .chunk_manager import ChunkData, BiomeType


class SimplexNoise:
    """简化的柏林噪声实现"""
    
    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 1000000)
        random.seed(self.seed)
        
        # 创建置换表
        self.perm = list(range(256))
        random.shuffle(self.perm)
        self.perm *= 2
    
    def _fade(self, t: float) -> float:
        """缓动函数"""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """线性插值"""
        return a + t * (b - a)
    
    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """梯度函数"""
        h = hash_val & 3
        u = x if h < 2 else y
        v = y if h < 2 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise(self, x: float, y: float) -> float:
        """
        生成2D噪声值
        
        Returns:
            范围 [-1, 1] 的噪声值
        """
        # 计算单位立方体坐标
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        
        # 相对坐标
        x -= math.floor(x)
        y -= math.floor(y)
        
        # 计算淡化曲线
        u = self._fade(x)
        v = self._fade(y)
        
        # 哈希坐标
        A = self.perm[X] + Y
        B = self.perm[X + 1] + Y
        
        # 插值
        return self._lerp(
            self._lerp(
                self._grad(self.perm[A], x, y),
                self._grad(self.perm[B], x - 1, y),
                u
            ),
            self._lerp(
                self._grad(self.perm[A + 1], x, y - 1),
                self._grad(self.perm[B + 1], x - 1, y - 1),
                u
            ),
            v
        )
    
    def octave_noise(self, x: float, y: float, octaves: int = 4, persistence: float = 0.5) -> float:
        """
        多层噪声
        
        Returns:
            范围约 [-1, 1] 的噪声值
        """
        total = 0
        frequency = 1
        amplitude = 1
        max_value = 0
        
        for _ in range(octaves):
            total += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2
        
        return total / max_value


class ProceduralTerrainGenerator:
    """程序化地形生成器"""
    
    def __init__(self, chunk_size: int = 32, tile_size: int = 32, seed: int = None):
        self.chunk_size = chunk_size
        self.tile_size = tile_size
        self.seed = seed or random.randint(0, 1000000)
        
        # 为不同特征创建不同的噪声生成器
        self.elevation_noise = SimplexNoise(self.seed)
        self.moisture_noise = SimplexNoise(self.seed + 1)
        self.temperature_noise = SimplexNoise(self.seed + 2)
        self.detail_noise = SimplexNoise(self.seed + 3)
        
        # 噪声参数
        self.elevation_scale = 0.02  # 海拔变化的频率
        self.moisture_scale = 0.03   # 湿度变化的频率
        self.temperature_scale = 0.01  # 温度变化的频率
    
    def generate_chunk(self, chunk_x: int, chunk_y: int) -> ChunkData:
        """
        生成一个区块
        
        Args:
            chunk_x: 区块X坐标
            chunk_y: 区块Y坐标
        
        Returns:
            生成的区块数据
        """
        # 计算世界坐标偏移
        world_offset_x = chunk_x * self.chunk_size
        world_offset_y = chunk_y * self.chunk_size
        
        # 生成瓦片数据
        tiles = []
        
        for y in range(self.chunk_size):
            row = []
            for x in range(self.chunk_size):
                # 世界坐标
                world_x = world_offset_x + x
                world_y = world_offset_y + y
                
                # 生成地形特征
                elevation = self._get_elevation(world_x, world_y)
                moisture = self._get_moisture(world_x, world_y)
                temperature = self._get_temperature(world_x, world_y)
                
                # 确定生物群系
                biome = self._determine_biome(elevation, moisture, temperature)
                
                # 生成瓦片
                tile = self._generate_tile(biome, elevation, moisture, x, y)
                row.append(tile)
            
            tiles.append(row)
        
        # 确定区块主要生物群系（使用中心点）
        center_elevation = self._get_elevation(
            world_offset_x + self.chunk_size // 2,
            world_offset_y + self.chunk_size // 2
        )
        center_moisture = self._get_moisture(
            world_offset_x + self.chunk_size // 2,
            world_offset_y + self.chunk_size // 2
        )
        center_temperature = self._get_temperature(
            world_offset_x + self.chunk_size // 2,
            world_offset_y + self.chunk_size // 2
        )
        
        chunk_biome = self._determine_biome(center_elevation, center_moisture, center_temperature)
        
        # 创建区块
        chunk = ChunkData(
            chunk_x=chunk_x,
            chunk_y=chunk_y,
            biome=chunk_biome,
            tiles=tiles,
            generated=True,
            loaded=False
        )
        
        return chunk
    
    def _get_elevation(self, world_x: int, world_y: int) -> float:
        """获取海拔值 (0-1)"""
        value = self.elevation_noise.octave_noise(
            world_x * self.elevation_scale,
            world_y * self.elevation_scale,
            octaves=4,
            persistence=0.5
        )
        # 归一化到 [0, 1]
        return (value + 1) / 2
    
    def _get_moisture(self, world_x: int, world_y: int) -> float:
        """获取湿度值 (0-1)"""
        value = self.moisture_noise.octave_noise(
            world_x * self.moisture_scale,
            world_y * self.moisture_scale,
            octaves=3,
            persistence=0.6
        )
        return (value + 1) / 2
    
    def _get_temperature(self, world_x: int, world_y: int) -> float:
        """获取温度值 (0-1)"""
        value = self.temperature_noise.octave_noise(
            world_x * self.temperature_scale,
            world_y * self.temperature_scale,
            octaves=2,
            persistence=0.4
        )
        return (value + 1) / 2
    
    def _determine_biome(self, elevation: float, moisture: float, temperature: float) -> BiomeType:
        """
        根据地形特征确定生物群系
        
        Args:
            elevation: 海拔 (0-1)
            moisture: 湿度 (0-1)
            temperature: 温度 (0-1)
        
        Returns:
            生物群系类型
        """
        # 水域（低海拔）
        if elevation < 0.3:
            return BiomeType.WATER
        
        # 山地（高海拔）
        if elevation > 0.75:
            return BiomeType.MOUNTAINS
        
        # 中等海拔区域 - 根据湿度和温度决定
        if temperature > 0.7:
            # 炎热地区
            if moisture < 0.3:
                return BiomeType.DESERT
            elif moisture < 0.6:
                return BiomeType.PLAINS
            else:
                return BiomeType.FOREST
        elif temperature > 0.4:
            # 温和地区
            if moisture < 0.4:
                return BiomeType.PLAINS
            elif moisture < 0.7:
                # 有一定概率生成村庄或农田
                if random.random() < 0.05:  # 5%概率
                    return BiomeType.VILLAGE
                elif random.random() < 0.1:  # 10%概率
                    return BiomeType.FARMLAND
                else:
                    return BiomeType.PLAINS
            else:
                return BiomeType.FOREST
        else:
            # 寒冷地区
            if moisture < 0.5:
                return BiomeType.PLAINS
            else:
                return BiomeType.FOREST
    
    def _generate_tile(self, biome: BiomeType, elevation: float, moisture: float, x: int, y: int) -> Dict:
        """
        生成单个瓦片的数据
        
        Returns:
            瓦片数据字典，包含各图层的瓦片ID
        """
        tile = {
            "collision": False,
            "biome": biome.value,
            "elevation": elevation,
            "moisture": moisture
        }
        
        # 根据生物群系设置瓦片类型
        if biome == BiomeType.WATER:
            tile["terrain"] = "water"
            tile["collision"] = True
            tile["tile_id"] = 100  # 水瓦片ID示例
        
        elif biome == BiomeType.PLAINS:
            tile["terrain"] = "grass"
            tile["tile_id"] = 1 + random.randint(0, 3)  # 草地变体
            # 偶尔添加装饰
            if random.random() < 0.1:
                tile["decoration"] = random.choice(["flower", "rock", "bush"])
        
        elif biome == BiomeType.FOREST:
            tile["terrain"] = "grass"
            tile["tile_id"] = 5
            # 树木密度
            if random.random() < 0.4:
                tile["tree"] = True
                tile["collision"] = True
                tile["decoration"] = "tree"
        
        elif biome == BiomeType.DESERT:
            tile["terrain"] = "sand"
            tile["tile_id"] = 20 + random.randint(0, 2)
            # 偶尔有仙人掌
            if random.random() < 0.05:
                tile["decoration"] = "cactus"
                tile["collision"] = True
        
        elif biome == BiomeType.MOUNTAINS:
            tile["terrain"] = "rock"
            tile["tile_id"] = 30 + random.randint(0, 3)
            # 山地大多不可通行
            if elevation > 0.8:
                tile["collision"] = True
        
        elif biome == BiomeType.VILLAGE:
            tile["terrain"] = "stone_path"
            tile["tile_id"] = 50
            # 村庄区域偶尔有建筑
            if random.random() < 0.2:
                tile["building"] = random.choice(["house", "shop", "well"])
                tile["collision"] = True
        
        elif biome == BiomeType.FARMLAND:
            tile["terrain"] = "farmland"
            tile["tile_id"] = 60 + random.randint(0, 2)
            # 农田中的作物
            if random.random() < 0.7:
                tile["crop"] = random.choice(["wheat", "corn", "vegetables"])
        
        elif biome == BiomeType.URBAN:
            tile["terrain"] = "pavement"
            tile["tile_id"] = 70
            tile["collision"] = random.random() < 0.3  # 30%的城市瓦片有建筑
        
        return tile
    
    def get_tile_texture_name(self, tile: Dict) -> str:
        """
        根据瓦片数据获取纹理名称（用于渲染）
        
        Returns:
            纹理名称字符串
        """
        terrain = tile.get("terrain", "grass")
        decoration = tile.get("decoration")
        
        if decoration:
            return f"{terrain}_{decoration}"
        
        return terrain
    
    def generate_spawn_safe_area(self, chunk_x: int, chunk_y: int) -> ChunkData:
        """
        生成一个安全的出生区域（平坦、无障碍）
        
        Returns:
            安全的出生区块
        """
        tiles = []
        
        for y in range(self.chunk_size):
            row = []
            for x in range(self.chunk_size):
                # 全部生成为平原/草地
                tile = {
                    "terrain": "grass",
                    "tile_id": 1 + ((x + y) % 4),
                    "collision": False,
                    "biome": BiomeType.PLAINS.value,
                    "elevation": 0.5,
                    "moisture": 0.5
                }
                
                # 边缘添加一些装饰
                if x == 0 or y == 0 or x == self.chunk_size - 1 or y == self.chunk_size - 1:
                    if random.random() < 0.3:
                        tile["decoration"] = random.choice(["flower", "bush"])
                
                row.append(tile)
            
            tiles.append(row)
        
        chunk = ChunkData(
            chunk_x=chunk_x,
            chunk_y=chunk_y,
            biome=BiomeType.PLAINS,
            tiles=tiles,
            generated=True,
            loaded=False
        )
        
        return chunk

