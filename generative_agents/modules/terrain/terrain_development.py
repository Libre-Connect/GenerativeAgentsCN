"""
地形开拓建造系统
实现AI自主规划并执行地形改造、资源分配和基础设施建设
"""

import json
import math
import random
import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import numpy as np


class TerrainType(Enum):
    """地形类型"""
    PLAIN = "plain"                 # 平原
    HILL = "hill"                   # 丘陵
    MOUNTAIN = "mountain"           # 山地
    WATER = "water"                 # 水域
    FOREST = "forest"               # 森林
    DESERT = "desert"               # 沙漠
    SWAMP = "swamp"                 # 沼泽
    DEVELOPED = "developed"         # 已开发
    URBAN = "urban"                 # 城市区域


class ResourceType(Enum):
    """资源类型"""
    WOOD = "wood"                   # 木材
    STONE = "stone"                 # 石材
    METAL = "metal"                 # 金属
    WATER = "water"                 # 水资源
    FOOD = "food"                   # 食物
    ENERGY = "energy"               # 能源
    LABOR = "labor"                 # 劳动力


class BuildingType(Enum):
    """建筑类型 - 扩展为城市级别"""
    # 住宅类型
    HOUSE = "house"                 # 独栋住宅
    APARTMENT = "apartment"         # 公寓
    CONDO = "condo"                 # 公寓楼
    
    # 商业类型
    SHOP = "shop"                   # 商店
    MALL = "mall"                   # 购物中心
    OFFICE = "office"               # 办公楼
    RESTAURANT = "restaurant"       # 餐厅
    HOTEL = "hotel"                 # 酒店
    
    # 工业类型
    FACTORY = "factory"             # 工厂
    WAREHOUSE = "warehouse"         # 仓库
    WORKSHOP = "workshop"           # 工坊
    
    # 基础设施
    FARM = "farm"                   # 农场
    MINE = "mine"                   # 矿场
    ROAD = "road"                   # 道路
    HIGHWAY = "highway"             # 高速公路
    BRIDGE = "bridge"               # 桥梁
    PARK = "park"                   # 公园
    SCHOOL = "school"               # 学校
    UNIVERSITY = "university"       # 大学
    HOSPITAL = "hospital"           # 医院
    CLINIC = "clinic"               # 诊所
    POWER_PLANT = "power_plant"     # 发电厂
    WATER_TREATMENT = "water_treatment"  # 水处理厂
    POLICE_STATION = "police_station"    # 警察局
    FIRE_STATION = "fire_station"        # 消防站
    GOVERNMENT = "government"            # 政府大楼
    LIBRARY = "library"                  # 图书馆
    MUSEUM = "museum"                    # 博物馆
    STADIUM = "stadium"                  # 体育场
    CINEMA = "cinema"                    # 电影院
    BANK = "bank"                        # 银行
    CHURCH = "church"                    # 教堂
    
    # 交通设施
    BUS_STATION = "bus_station"          # 公交站
    TRAIN_STATION = "train_station"      # 火车站
    AIRPORT = "airport"                  # 机场
    PARKING_LOT = "parking_lot"          # 停车场


class DevelopmentPriority(Enum):
    """开发优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class CityDistrict(Enum):
    """城市区域类型"""
    DOWNTOWN = "downtown"           # 市中心 - 商业区
    RESIDENTIAL = "residential"     # 住宅区
    INDUSTRIAL = "industrial"       # 工业区
    COMMERCIAL = "commercial"       # 商业区
    GOVERNMENT = "government"       # 政府区
    EDUCATION = "education"         # 教育区
    MEDICAL = "medical"             # 医疗区
    ENTERTAINMENT = "entertainment" # 娱乐区
    TRANSPORT = "transport"         # 交通区
    PARK = "park"                   # 公园区
    SUBURBAN = "suburban"           # 郊区
    RURAL = "rural"                 # 农村区


@dataclass
class TerrainTile:
    """地形瓦片 - 城市级别扩展"""
    x: int
    y: int
    terrain_type: TerrainType
    elevation: float                # 海拔高度
    fertility: float               # 肥沃度 (0-1)
    accessibility: float           # 可达性 (0-1)
    resources: Dict[ResourceType, float]  # 资源储量
    buildings: List[str]           # 建筑ID列表
    development_level: float       # 开发程度 (0-1)
    population_capacity: int       # 人口容量
    current_population: int        # 当前人口
    
    # 城市相关属性
    city_district: Optional[CityDistrict] = None  # 城市区域类型
    land_value: float = 0.0         # 土地价值 (0-1)
    traffic_density: float = 0.0    # 交通密度 (0-1)
    pollution_level: float = 0.0    # 污染水平 (0-1)
    crime_rate: float = 0.0         # 犯罪率 (0-1)
    happiness_index: float = 0.5   # 幸福指数 (0-1)
    infrastructure_quality: float = 0.0  # 基础设施质量 (0-1)
    
    def __post_init__(self):
        if not self.resources:
            self.resources = self._generate_default_resources()
    
    def _generate_default_resources(self) -> Dict[ResourceType, float]:
        """根据地形类型生成默认资源"""
        base_resources = {resource: 0.0 for resource in ResourceType}
        
        if self.terrain_type == TerrainType.FOREST:
            base_resources[ResourceType.WOOD] = random.uniform(50, 100)
            base_resources[ResourceType.WATER] = random.uniform(20, 40)
        elif self.terrain_type == TerrainType.MOUNTAIN:
            base_resources[ResourceType.STONE] = random.uniform(70, 100)
            base_resources[ResourceType.METAL] = random.uniform(30, 80)
        elif self.terrain_type == TerrainType.PLAIN:
            base_resources[ResourceType.FOOD] = random.uniform(40, 80)
            base_resources[ResourceType.WATER] = random.uniform(30, 60)
        elif self.terrain_type == TerrainType.WATER:
            base_resources[ResourceType.WATER] = 100.0
            base_resources[ResourceType.FOOD] = random.uniform(20, 50)
        
        return base_resources
    
    def can_build(self, building_type: BuildingType) -> bool:
        """检查是否可以建造特定建筑"""
        if self.terrain_type == TerrainType.WATER and building_type != BuildingType.BRIDGE:
            return False
        if self.terrain_type == TerrainType.MOUNTAIN and building_type in [BuildingType.FARM, BuildingType.FACTORY]:
            return False
        if len(self.buildings) >= self.get_max_buildings():
            return False
        return True
    
    def get_max_buildings(self) -> int:
        """获取最大建筑数量"""
        if self.terrain_type == TerrainType.URBAN:
            return 5
        elif self.terrain_type == TerrainType.DEVELOPED:
            return 3
        elif self.terrain_type in [TerrainType.PLAIN, TerrainType.HILL]:
            return 2
        else:
            return 1


@dataclass
class Building:
    """建筑物"""
    id: str
    building_type: BuildingType
    x: int
    y: int
    construction_cost: Dict[ResourceType, float]
    maintenance_cost: Dict[ResourceType, float]
    production: Dict[ResourceType, float]
    construction_time: int          # 建造时间（天）
    construction_progress: float    # 建造进度 (0-1)
    is_completed: bool
    efficiency: float              # 效率 (0-1)
    condition: float               # 建筑状况 (0-1)
    workers_needed: int            # 所需工人数
    current_workers: int           # 当前工人数
    created_at: datetime.datetime
    
    def get_actual_production(self) -> Dict[ResourceType, float]:
        """获取实际产出（考虑效率和工人数）"""
        if not self.is_completed:
            return {resource: 0.0 for resource in ResourceType}
        
        worker_efficiency = min(1.0, self.current_workers / max(1, self.workers_needed))
        total_efficiency = self.efficiency * self.condition * worker_efficiency
        
        return {
            resource: amount * total_efficiency 
            for resource, amount in self.production.items()
        }


class DevelopmentProject:
    """开发项目"""
    
    def __init__(self, project_id: str, name: str, description: str):
        self.project_id = project_id
        self.name = name
        self.description = description
        self.priority = DevelopmentPriority.MEDIUM
        self.status = "planned"  # planned, in_progress, completed, cancelled
        self.progress = 0.0
        self.estimated_duration = 0  # 天数
        self.actual_duration = 0
        self.resource_requirements: Dict[ResourceType, float] = {}
        self.resource_allocated: Dict[ResourceType, float] = {}
        self.buildings_to_construct: List[str] = []
        self.terrain_modifications: List[dict] = []
        self.assigned_agents: List[str] = []
        self.created_at = datetime.datetime.now()
        self.started_at: Optional[datetime.datetime] = None
        self.completed_at: Optional[datetime.datetime] = None
    
    def start_project(self):
        """开始项目"""
        self.status = "in_progress"
        self.started_at = datetime.datetime.now()
    
    def complete_project(self):
        """完成项目"""
        self.status = "completed"
        self.progress = 1.0
        self.completed_at = datetime.datetime.now()
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).days
    
    def update_progress(self, progress_delta: float):
        """更新项目进度"""
        self.progress = min(1.0, self.progress + progress_delta)
        if self.progress >= 1.0:
            self.complete_project()


class TerrainDevelopmentEngine:
    """地形开发引擎 - 城市级别"""
    
    def __init__(self, width: int = 100, height: int = 100, city_type: str = "metropolis"):
        self.width = width
        self.height = height
        self.city_type = city_type  # metropolis, large_city, medium_city, small_city
        self.terrain_map: Dict[Tuple[int, int], TerrainTile] = {}
        self.buildings: Dict[str, Building] = {}
        self.projects: Dict[str, DevelopmentProject] = {}
        self.global_resources: Dict[ResourceType, float] = {}
        self.building_templates = self._initialize_building_templates()
        self.city_districts: Dict[CityDistrict, List[Tuple[int, int]]] = {}
        
        # 初始化地形
        self._generate_city_terrain()
        self._initialize_global_resources()
        self._generate_city_districts()
    
    def _generate_city_terrain(self):
        """生成城市地形 - 基于真实城市规划"""
        # 确定城市规模和特征
        city_config = self._get_city_config()
        
        # 生成基础地形
        for x in range(self.width):
            for y in range(self.height):
                # 使用更复杂的噪声生成地形
                noise_value = self._city_noise(x, y, city_config)
                elevation = noise_value * 100
                
                # 城市地形生成逻辑 - 更适合建设
                if elevation < 15:
                    terrain_type = TerrainType.WATER  # 河流/湖泊
                elif elevation < 25:
                    terrain_type = TerrainType.SWAMP  # 湿地
                elif elevation < 70:
                    terrain_type = TerrainType.PLAIN  # 平原 - 主要建设区域
                elif elevation < 85:
                    terrain_type = TerrainType.HILL   # 丘陵 - 可建设
                elif elevation < 95:
                    terrain_type = TerrainType.FOREST # 森林 - 保护区
                else:
                    terrain_type = TerrainType.MOUNTAIN # 山地 - 限制建设
                
                # 计算城市相关属性
                fertility = max(0, min(1, 1 - elevation / 100 + random.uniform(-0.2, 0.2)))
                accessibility = self._calculate_city_accessibility(x, y, city_config)
                land_value = self._calculate_land_value(x, y, elevation, accessibility)
                
                tile = TerrainTile(
                    x=x, y=y,
                    terrain_type=terrain_type,
                    elevation=elevation,
                    fertility=fertility,
                    accessibility=accessibility,
                    resources={},
                    buildings=[],
                    development_level=0.0,
                    population_capacity=self._calculate_population_capacity(terrain_type),
                    current_population=0,
                    land_value=land_value,
                    infrastructure_quality=accessibility * 0.8  # 基础设施质量与可达性相关
                )
                
                self.terrain_map[(x, y)] = tile
    
    def _get_city_config(self) -> dict:
        """获取城市配置"""
        configs = {
            "metropolis": {
                "population_target": 1000000,
                "center_size": 15,
                "district_count": 12,
                "road_density": 0.8,
                "commercial_ratio": 0.3,
                "residential_ratio": 0.5,
                "industrial_ratio": 0.2
            },
            "large_city": {
                "population_target": 500000,
                "center_size": 10,
                "district_count": 8,
                "road_density": 0.7,
                "commercial_ratio": 0.25,
                "residential_ratio": 0.55,
                "industrial_ratio": 0.2
            },
            "medium_city": {
                "population_target": 100000,
                "center_size": 7,
                "district_count": 6,
                "road_density": 0.6,
                "commercial_ratio": 0.2,
                "residential_ratio": 0.6,
                "industrial_ratio": 0.2
            },
            "small_city": {
                "population_target": 50000,
                "center_size": 5,
                "district_count": 4,
                "road_density": 0.5,
                "commercial_ratio": 0.15,
                "residential_ratio": 0.65,
                "industrial_ratio": 0.2
            }
        }
        return configs.get(self.city_type, configs["medium_city"])
    
    def _city_noise(self, x: int, y: int, city_config: dict) -> float:
        """城市噪声生成 - 更适合城市规划"""
        # 基础地形噪声
        base_noise = (math.sin(x * 0.05) + math.cos(y * 0.05) + 
                     math.sin(x * 0.02 + y * 0.02)) / 3
        
        # 城市中心梯度 - 创建更平坦的中心区域
        center_x, center_y = self.width // 2, self.height // 2
        distance_from_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_distance = math.sqrt(center_x**2 + center_y**2)
        
        # 中心区域更平坦
        if distance_from_center < city_config["center_size"]:
            center_flattening = 0.8
        else:
            center_flattening = 1.0 - (distance_from_center - city_config["center_size"]) / max_distance * 0.3
        
        return (base_noise * center_flattening + 0.5) / 2
    
    def _calculate_city_accessibility(self, x: int, y: int, city_config: dict) -> float:
        """计算城市可达性"""
        center_x, center_y = self.width // 2, self.height // 2
        distance_from_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_distance = math.sqrt(center_x**2 + center_y**2)
        
        # 中心区域可达性最高
        center_accessibility = max(0, 1.0 - distance_from_center / max_distance)
        
        # 添加一些随机变化模拟道路规划
        road_influence = math.sin(x * 0.1) * math.cos(y * 0.1) * 0.2
        
        return max(0, min(1, center_accessibility + road_influence + random.uniform(-0.1, 0.1)))
    
    def _calculate_land_value(self, x: int, y: int, elevation: float, accessibility: float) -> float:
        """计算土地价值"""
        # 土地价值基于可达性和地形
        base_value = accessibility * 0.7
        elevation_factor = max(0, 1.0 - elevation / 100)  # 低海拔更有价值
        
        return max(0, min(1, base_value + elevation_factor * 0.3 + random.uniform(-0.1, 0.1)))
    
    def _generate_city_districts(self):
        """生成城市区域"""
        city_config = self._get_city_config()
        center_x, center_y = self.width // 2, self.height // 2
        
        # 定义各区域的优先位置
        districts_config = {
            CityDistrict.DOWNTOWN: {
                "center_offset": (0, 0),
                "radius": city_config["center_size"],
                "priority_buildings": [BuildingType.OFFICE, BuildingType.MALL, BuildingType.BANK, BuildingType.HOTEL]
            },
            CityDistrict.RESIDENTIAL: {
                "center_offset": (0, city_config["center_size"] + 5),
                "radius": city_config["center_size"] * 1.5,
                "priority_buildings": [BuildingType.APARTMENT, BuildingType.CONDO, BuildingType.HOUSE, BuildingType.PARK]
            },
            CityDistrict.INDUSTRIAL: {
                "center_offset": (city_config["center_size"] + 5, 0),
                "radius": city_config["center_size"],
                "priority_buildings": [BuildingType.FACTORY, BuildingType.WAREHOUSE, BuildingType.WORKSHOP]
            },
            CityDistrict.COMMERCIAL: {
                "center_offset": (-city_config["center_size"] - 5, 0),
                "radius": city_config["center_size"],
                "priority_buildings": [BuildingType.SHOP, BuildingType.RESTAURANT, BuildingType.MALL]
            },
            CityDistrict.EDUCATION: {
                "center_offset": (0, -city_config["center_size"] - 5),
                "radius": city_config["center_size"],
                "priority_buildings": [BuildingType.UNIVERSITY, BuildingType.SCHOOL, BuildingType.LIBRARY]
            },
            CityDistrict.MEDICAL: {
                "center_offset": (city_config["center_size"] + 5, city_config["center_size"] + 5),
                "radius": city_config["center_size"] * 0.8,
                "priority_buildings": [BuildingType.HOSPITAL, BuildingType.CLINIC]
            },
            CityDistrict.ENTERTAINMENT: {
                "center_offset": (-city_config["center_size"] - 5, -city_config["center_size"] - 5),
                "radius": city_config["center_size"] * 0.8,
                "priority_buildings": [BuildingType.CINEMA, BuildingType.STADIUM, BuildingType.MUSEUM]
            },
            CityDistrict.GOVERNMENT: {
                "center_offset": (city_config["center_size"] + 5, -city_config["center_size"] - 5),
                "radius": city_config["center_size"] * 0.6,
                "priority_buildings": [BuildingType.GOVERNMENT, BuildingType.POLICE_STATION, BuildingType.FIRE_STATION]
            },
            CityDistrict.TRANSPORT: {
                "center_offset": (-city_config["center_size"] - 5, city_config["center_size"] + 5),
                "radius": city_config["center_size"] * 0.7,
                "priority_buildings": [BuildingType.BUS_STATION, BuildingType.TRAIN_STATION, BuildingType.PARKING_LOT]
            },
            CityDistrict.PARK: {
                "center_offset": (0, city_config["center_size"] * 2),
                "radius": city_config["center_size"] * 0.5,
                "priority_buildings": [BuildingType.PARK]
            },
            CityDistrict.SUBURBAN: {
                "center_offset": (city_config["center_size"] * 2, city_config["center_size"] * 2),
                "radius": city_config["center_size"] * 1.2,
                "priority_buildings": [BuildingType.HOUSE, BuildingType.APARTMENT, BuildingType.SHOP, BuildingType.PARK]
            },
            CityDistrict.RURAL: {
                "center_offset": (-city_config["center_size"] * 2, city_config["center_size"] * 2),
                "radius": city_config["center_size"] * 1.5,
                "priority_buildings": [BuildingType.FARM, BuildingType.HOUSE, BuildingType.WORKSHOP]
            }
        }
        
        # 为每个区域分配瓦片
        for district, config in districts_config.items():
            district_tiles = []
            offset_x, offset_y = config["center_offset"]
            center_x, center_y = self.width // 2 + offset_x, self.height // 2 + offset_y
            radius = config["radius"]
            
            # 找到区域内的所有瓦片
            for x in range(max(0, center_x - radius), min(self.width, center_x + radius)):
                for y in range(max(0, center_y - radius), min(self.height, center_y + radius)):
                    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if distance <= radius and (x, y) in self.terrain_map:
                        tile = self.terrain_map[(x, y)]
                        tile.city_district = district
                        district_tiles.append((x, y))
            
            self.city_districts[district] = district_tiles
    
    def _simple_noise(self, x: int, y: int) -> float:
        """简单的噪声函数"""
        return (math.sin(x * 0.1) + math.cos(y * 0.1) + 
                math.sin(x * 0.05 + y * 0.05) + 
                random.uniform(-0.2, 0.2)) / 4 + 0.5
    
    def _calculate_population_capacity(self, terrain_type: TerrainType) -> int:
        """计算人口容量"""
        capacity_map = {
            TerrainType.PLAIN: 100,
            TerrainType.HILL: 60,
            TerrainType.MOUNTAIN: 30,
            TerrainType.WATER: 0,
            TerrainType.FOREST: 40,
            TerrainType.DESERT: 20,
            TerrainType.SWAMP: 25,
            TerrainType.DEVELOPED: 200,
            TerrainType.URBAN: 500
        }
        return capacity_map.get(terrain_type, 50)
    
    def _initialize_global_resources(self):
        """初始化全局资源"""
        self.global_resources = {
            ResourceType.WOOD: 1000.0,
            ResourceType.STONE: 800.0,
            ResourceType.METAL: 500.0,
            ResourceType.WATER: 2000.0,
            ResourceType.FOOD: 1500.0,
            ResourceType.ENERGY: 1000.0,
            ResourceType.LABOR: 100.0
        }
    
    def _initialize_building_templates(self) -> Dict[BuildingType, dict]:
        """初始化建筑模板 - 城市级别"""
        return {
            # 住宅类型
            BuildingType.HOUSE: {
                "construction_cost": {ResourceType.WOOD: 50, ResourceType.STONE: 30},
                "maintenance_cost": {ResourceType.ENERGY: 2},
                "production": {},
                "construction_time": 7,
                "workers_needed": 0,
                "population_increase": 4
            },
            BuildingType.APARTMENT: {
                "construction_cost": {ResourceType.STONE: 200, ResourceType.METAL: 150, ResourceType.WOOD: 100},
                "maintenance_cost": {ResourceType.ENERGY: 15, ResourceType.WATER: 10},
                "production": {},
                "construction_time": 30,
                "workers_needed": 0,
                "population_increase": 20
            },
            BuildingType.CONDO: {
                "construction_cost": {ResourceType.STONE: 300, ResourceType.METAL: 200, ResourceType.WOOD: 80},
                "maintenance_cost": {ResourceType.ENERGY: 20, ResourceType.WATER: 15},
                "production": {},
                "construction_time": 45,
                "workers_needed": 0,
                "population_increase": 15
            },
            
            # 商业类型
            BuildingType.SHOP: {
                "construction_cost": {ResourceType.WOOD: 40, ResourceType.STONE: 20},
                "maintenance_cost": {ResourceType.ENERGY: 3},
                "production": {},
                "construction_time": 8,
                "workers_needed": 2,
                "population_increase": 0
            },
            BuildingType.MALL: {
                "construction_cost": {ResourceType.STONE: 500, ResourceType.METAL: 300, ResourceType.WOOD: 200},
                "maintenance_cost": {ResourceType.ENERGY: 50, ResourceType.WATER: 30},
                "production": {},
                "construction_time": 60,
                "workers_needed": 50,
                "population_increase": 0
            },
            BuildingType.OFFICE: {
                "construction_cost": {ResourceType.STONE: 400, ResourceType.METAL: 250, ResourceType.WOOD: 150},
                "maintenance_cost": {ResourceType.ENERGY: 40, ResourceType.WATER: 25},
                "production": {},
                "construction_time": 50,
                "workers_needed": 30,
                "population_increase": 0
            },
            BuildingType.RESTAURANT: {
                "construction_cost": {ResourceType.STONE: 80, ResourceType.WOOD: 60, ResourceType.METAL: 40},
                "maintenance_cost": {ResourceType.ENERGY: 12, ResourceType.WATER: 8, ResourceType.FOOD: 5},
                "production": {},
                "construction_time": 20,
                "workers_needed": 8,
                "population_increase": 0
            },
            BuildingType.HOTEL: {
                "construction_cost": {ResourceType.STONE: 350, ResourceType.METAL: 200, ResourceType.WOOD: 180},
                "maintenance_cost": {ResourceType.ENERGY: 35, ResourceType.WATER: 25},
                "production": {},
                "construction_time": 40,
                "workers_needed": 25,
                "population_increase": 0
            },
            
            # 工业类型
            BuildingType.FACTORY: {
                "construction_cost": {ResourceType.STONE: 80, ResourceType.METAL: 50},
                "maintenance_cost": {ResourceType.ENERGY: 15, ResourceType.WATER: 8},
                "production": {ResourceType.ENERGY: 25},
                "construction_time": 15,
                "workers_needed": 8,
                "population_increase": 0
            },
            BuildingType.WAREHOUSE: {
                "construction_cost": {ResourceType.STONE: 100, ResourceType.METAL: 80, ResourceType.WOOD: 60},
                "maintenance_cost": {ResourceType.ENERGY: 5},
                "production": {},
                "construction_time": 25,
                "workers_needed": 3,
                "population_increase": 0
            },
            BuildingType.WORKSHOP: {
                "construction_cost": {ResourceType.WOOD: 50, ResourceType.METAL: 30, ResourceType.STONE: 40},
                "maintenance_cost": {ResourceType.ENERGY: 8},
                "production": {ResourceType.METAL: 5},
                "construction_time": 12,
                "workers_needed": 4,
                "population_increase": 0
            },
            
            # 农业类型
            BuildingType.FARM: {
                "construction_cost": {ResourceType.WOOD: 30, ResourceType.STONE: 10},
                "maintenance_cost": {ResourceType.WATER: 5},
                "production": {ResourceType.FOOD: 20},
                "construction_time": 5,
                "workers_needed": 2,
                "population_increase": 0
            },
            
            # 基础设施类型
            BuildingType.ROAD: {
                "construction_cost": {ResourceType.STONE: 20},
                "maintenance_cost": {},
                "production": {},
                "construction_time": 3,
                "workers_needed": 0,
                "population_increase": 0
            },
            BuildingType.BRIDGE: {
                "construction_cost": {ResourceType.STONE: 150, ResourceType.METAL: 100},
                "maintenance_cost": {ResourceType.ENERGY: 2},
                "production": {},
                "construction_time": 35,
                "workers_needed": 0,
                "population_increase": 0
            },
            BuildingType.WALL: {
                "construction_cost": {ResourceType.STONE: 60, ResourceType.METAL: 20},
                "maintenance_cost": {},
                "production": {},
                "construction_time": 15,
                "workers_needed": 0,
                "population_increase": 0
            },
            
            # 教育类型
            BuildingType.SCHOOL: {
                "construction_cost": {ResourceType.STONE: 120, ResourceType.WOOD: 80, ResourceType.METAL: 40},
                "maintenance_cost": {ResourceType.ENERGY: 15, ResourceType.WATER: 10},
                "production": {},
                "construction_time": 25,
                "workers_needed": 15,
                "population_increase": 0
            },
            BuildingType.UNIVERSITY: {
                "construction_cost": {ResourceType.STONE: 400, ResourceType.WOOD: 200, ResourceType.METAL: 150},
                "maintenance_cost": {ResourceType.ENERGY: 45, ResourceType.WATER: 30},
                "production": {},
                "construction_time": 80,
                "workers_needed": 80,
                "population_increase": 0
            },
            BuildingType.LIBRARY: {
                "construction_cost": {ResourceType.STONE: 200, ResourceType.WOOD: 150, ResourceType.METAL: 80},
                "maintenance_cost": {ResourceType.ENERGY: 20, ResourceType.WATER: 12},
                "production": {},
                "construction_time": 35,
                "workers_needed": 12,
                "population_increase": 0
            },
            
            # 医疗类型
            BuildingType.HOSPITAL: {
                "construction_cost": {ResourceType.STONE: 300, ResourceType.METAL: 200, ResourceType.WOOD: 150},
                "maintenance_cost": {ResourceType.ENERGY: 35, ResourceType.WATER: 25, ResourceType.FOOD: 5},
                "production": {},
                "construction_time": 55,
                "workers_needed": 60,
                "population_increase": 0
            },
            BuildingType.CLINIC: {
                "construction_cost": {ResourceType.STONE: 100, ResourceType.WOOD: 80, ResourceType.METAL: 60},
                "maintenance_cost": {ResourceType.ENERGY: 18, ResourceType.WATER: 12},
                "production": {},
                "construction_time": 20,
                "workers_needed": 8,
                "population_increase": 0
            },
            
            # 娱乐类型
            BuildingType.CINEMA: {
                "construction_cost": {ResourceType.STONE: 150, ResourceType.WOOD: 100, ResourceType.METAL: 80},
                "maintenance_cost": {ResourceType.ENERGY: 25, ResourceType.WATER: 15},
                "production": {},
                "construction_time": 30,
                "workers_needed": 15,
                "population_increase": 0
            },
            BuildingType.STADIUM: {
                "construction_cost": {ResourceType.STONE: 800, ResourceType.METAL: 500, ResourceType.WOOD: 300},
                "maintenance_cost": {ResourceType.ENERGY: 80, ResourceType.WATER: 50},
                "production": {},
                "construction_time": 120,
                "workers_needed": 200,
                "population_increase": 0
            },
            BuildingType.MUSEUM: {
                "construction_cost": {ResourceType.STONE: 250, ResourceType.WOOD: 180, ResourceType.METAL: 120},
                "maintenance_cost": {ResourceType.ENERGY: 22, ResourceType.WATER: 15},
                "production": {},
                "construction_time": 40,
                "workers_needed": 20,
                "population_increase": 0
            },
            
            # 政府类型
            BuildingType.GOVERNMENT: {
                "construction_cost": {ResourceType.STONE: 500, ResourceType.METAL: 300, ResourceType.WOOD: 200},
                "maintenance_cost": {ResourceType.ENERGY: 40, ResourceType.WATER: 25},
                "production": {},
                "construction_time": 70,
                "workers_needed": 100,
                "population_increase": 0
            },
            BuildingType.POLICE_STATION: {
                "construction_cost": {ResourceType.STONE: 200, ResourceType.METAL: 150, ResourceType.WOOD: 100},
                "maintenance_cost": {ResourceType.ENERGY: 25, ResourceType.WATER: 15},
                "production": {},
                "construction_time": 30,
                "workers_needed": 25,
                "population_increase": 0
            },
            BuildingType.FIRE_STATION: {
                "construction_cost": {ResourceType.STONE: 180, ResourceType.METAL: 140, ResourceType.WOOD: 90},
                "maintenance_cost": {ResourceType.ENERGY: 20, ResourceType.WATER: 25},
                "production": {},
                "construction_time": 28,
                "workers_needed": 20,
                "population_increase": 0
            },
            
            # 交通类型
            BuildingType.BUS_STATION: {
                "construction_cost": {ResourceType.STONE: 120, ResourceType.METAL: 80, ResourceType.WOOD: 60},
                "maintenance_cost": {ResourceType.ENERGY: 15, ResourceType.WATER: 8},
                "production": {},
                "construction_time": 25,
                "workers_needed": 8,
                "population_increase": 0
            },
            BuildingType.TRAIN_STATION: {
                "construction_cost": {ResourceType.STONE: 400, ResourceType.METAL: 300, ResourceType.WOOD: 200},
                "maintenance_cost": {ResourceType.ENERGY: 45, ResourceType.WATER: 25},
                "production": {},
                "construction_time": 60,
                "workers_needed": 40,
                "population_increase": 0
            },
            BuildingType.PARKING_LOT: {
                "construction_cost": {ResourceType.STONE: 80, ResourceType.METAL: 40},
                "maintenance_cost": {ResourceType.ENERGY: 5},
                "production": {},
                "construction_time": 15,
                "workers_needed": 1,
                "population_increase": 0
            },
            BuildingType.AIRPORT: {
                "construction_cost": {ResourceType.STONE: 2000, ResourceType.METAL: 1500, ResourceType.WOOD: 800},
                "maintenance_cost": {ResourceType.ENERGY: 200, ResourceType.WATER: 100},
                "production": {},
                "construction_time": 180,
                "workers_needed": 500,
                "population_increase": 0
            },
            
            # 绿地类型
            BuildingType.PARK: {
                "construction_cost": {ResourceType.WOOD: 30, ResourceType.STONE: 20},
                "maintenance_cost": {ResourceType.WATER: 3},
                "production": {},
                "construction_time": 10,
                "workers_needed": 2,
                "population_increase": 0
            }
        }
    
    def get_tile(self, x: int, y: int) -> Optional[TerrainTile]:
        """获取地形瓦片"""
        return self.terrain_map.get((x, y))
    
    def get_neighbors(self, x: int, y: int, radius: int = 1) -> List[TerrainTile]:
        """获取邻近瓦片"""
        neighbors = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    tile = self.get_tile(nx, ny)
                    if tile:
                        neighbors.append(tile)
        return neighbors
    
    def analyze_development_potential(self, x: int, y: int) -> dict:
        """分析开发潜力"""
        tile = self.get_tile(x, y)
        if not tile:
            return {"potential": 0, "reasons": ["位置无效"]}
        
        potential_score = 0
        reasons = []
        
        # 地形适宜性
        terrain_scores = {
            TerrainType.PLAIN: 0.9,
            TerrainType.HILL: 0.7,
            TerrainType.FOREST: 0.6,
            TerrainType.MOUNTAIN: 0.3,
            TerrainType.WATER: 0.1,
            TerrainType.DESERT: 0.4,
            TerrainType.SWAMP: 0.2,
            TerrainType.DEVELOPED: 0.5,
            TerrainType.URBAN: 0.3
        }
        
        terrain_score = terrain_scores.get(tile.terrain_type, 0.5)
        potential_score += terrain_score * 30
        
        # 资源丰富度
        total_resources = sum(tile.resources.values())
        resource_score = min(1.0, total_resources / 200)
        potential_score += resource_score * 25
        
        # 可达性
        potential_score += tile.accessibility * 20
        
        # 邻近发展情况
        neighbors = self.get_neighbors(x, y, 2)
        developed_neighbors = sum(1 for n in neighbors if n.development_level > 0.3)
        neighbor_score = min(1.0, developed_neighbors / len(neighbors)) if neighbors else 0
        potential_score += neighbor_score * 15
        
        # 当前开发程度（越低越有潜力）
        potential_score += (1 - tile.development_level) * 10
        
        # 生成原因说明
        if terrain_score > 0.7:
            reasons.append("地形适宜开发")
        elif terrain_score < 0.3:
            reasons.append("地形不适宜开发")
        
        if resource_score > 0.6:
            reasons.append("资源丰富")
        elif resource_score < 0.3:
            reasons.append("资源匮乏")
        
        if tile.accessibility > 0.7:
            reasons.append("交通便利")
        elif tile.accessibility < 0.3:
            reasons.append("交通不便")
        
        return {
            "potential": potential_score,
            "reasons": reasons,
            "terrain_score": terrain_score,
            "resource_score": resource_score,
            "accessibility_score": tile.accessibility,
            "neighbor_score": neighbor_score
        }
    
    def find_optimal_development_sites(self, building_type: BuildingType, count: int = 5) -> List[Tuple[int, int, float]]:
        """寻找最佳开发地点"""
        candidates = []
        
        for (x, y), tile in self.terrain_map.items():
            if not tile.can_build(building_type):
                continue
            
            analysis = self.analyze_development_potential(x, y)
            
            # 根据建筑类型调整评分
            score = analysis["potential"]
            
            if building_type == BuildingType.FARM:
                score += tile.fertility * 20
            elif building_type == BuildingType.MINE:
                score += (tile.resources.get(ResourceType.STONE, 0) + 
                         tile.resources.get(ResourceType.METAL, 0)) * 0.3
            elif building_type in [BuildingType.HOUSE, BuildingType.SHOP]:
                score += analysis["neighbor_score"] * 15
            
            candidates.append((x, y, score))
        
        # 排序并返回最佳地点
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[:count]
    
    def create_building(self, building_type: BuildingType, x: int, y: int, building_id: str = None) -> Optional[Building]:
        """创建建筑"""
        tile = self.get_tile(x, y)
        if not tile or not tile.can_build(building_type):
            return None
        
        if building_id is None:
            building_id = f"{building_type.value}_{x}_{y}_{len(self.buildings)}"
        
        template = self.building_templates.get(building_type, {})
        
        building = Building(
            id=building_id,
            building_type=building_type,
            x=x, y=y,
            construction_cost=template.get("construction_cost", {}),
            maintenance_cost=template.get("maintenance_cost", {}),
            production=template.get("production", {}),
            construction_time=template.get("construction_time", 7),
            construction_progress=0.0,
            is_completed=False,
            efficiency=1.0,
            condition=1.0,
            workers_needed=template.get("workers_needed", 0),
            current_workers=0,
            created_at=datetime.datetime.now()
        )
        
        # 检查资源是否足够
        if not self._check_resource_availability(building.construction_cost):
            return None
        
        # 扣除建造资源
        self._consume_resources(building.construction_cost)
        
        self.buildings[building_id] = building
        tile.buildings.append(building_id)
        
        return building
    
    def _check_resource_availability(self, required_resources: Dict[ResourceType, float]) -> bool:
        """检查资源是否足够"""
        for resource_type, amount in required_resources.items():
            if self.global_resources.get(resource_type, 0) < amount:
                return False
        return True
    
    def _consume_resources(self, resources: Dict[ResourceType, float]):
        """消耗资源"""
        for resource_type, amount in resources.items():
            self.global_resources[resource_type] = max(0, 
                self.global_resources.get(resource_type, 0) - amount)
    
    def _add_resources(self, resources: Dict[ResourceType, float]):
        """添加资源"""
        for resource_type, amount in resources.items():
            self.global_resources[resource_type] = (
                self.global_resources.get(resource_type, 0) + amount)
    
    def advance_construction(self, building_id: str, progress_delta: float = 0.1) -> bool:
        """推进建造进度"""
        building = self.buildings.get(building_id)
        if not building or building.is_completed:
            return False
        
        building.construction_progress = min(1.0, building.construction_progress + progress_delta)
        
        if building.construction_progress >= 1.0:
            building.is_completed = True
            tile = self.get_tile(building.x, building.y)
            if tile:
                tile.development_level = min(1.0, tile.development_level + 0.1)
                
                # 增加人口容量
                template = self.building_templates.get(building.building_type, {})
                population_increase = template.get("population_increase", 0)
                tile.population_capacity += population_increase
            
            return True
        
        return False
    
    def create_development_project(self, name: str, description: str, 
                                 buildings_plan: List[dict], 
                                 terrain_modifications: List[dict] = None) -> DevelopmentProject:
        """创建开发项目"""
        project_id = f"project_{len(self.projects)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        project = DevelopmentProject(project_id, name, description)
        
        # 计算资源需求
        total_resources = {resource: 0.0 for resource in ResourceType}
        estimated_time = 0
        
        for building_plan in buildings_plan:
            building_type = BuildingType(building_plan["type"])
            count = building_plan.get("count", 1)
            
            template = self.building_templates.get(building_type, {})
            construction_cost = template.get("construction_cost", {})
            construction_time = template.get("construction_time", 7)
            
            for resource, amount in construction_cost.items():
                total_resources[resource] += amount * count
            
            estimated_time += construction_time * count
        
        project.resource_requirements = total_resources
        project.estimated_duration = estimated_time
        project.terrain_modifications = terrain_modifications or []
        
        self.projects[project_id] = project
        return project
    
    def execute_project(self, project_id: str, assigned_agents: List[str] = None) -> bool:
        """执行开发项目"""
        project = self.projects.get(project_id)
        if not project or project.status != "planned":
            return False
        
        # 检查资源是否足够
        if not self._check_resource_availability(project.resource_requirements):
            return False
        
        project.assigned_agents = assigned_agents or []
        project.start_project()
        
        return True
    
    def update_project_progress(self, project_id: str, work_done: float = 0.1):
        """更新项目进度"""
        project = self.projects.get(project_id)
        if not project or project.status != "in_progress":
            return
        
        # 根据分配的agent数量调整工作效率
        efficiency_multiplier = 1.0 + len(project.assigned_agents) * 0.2
        actual_progress = work_done * efficiency_multiplier
        
        project.update_progress(actual_progress)
        
        # 如果项目完成，执行建造
        if project.status == "completed":
            self._execute_project_construction(project)
    
    def _execute_project_construction(self, project: DevelopmentProject):
        """执行项目建造"""
        # 消耗资源
        self._consume_resources(project.resource_requirements)
        
        # 执行地形修改
        for modification in project.terrain_modifications:
            x, y = modification["x"], modification["y"]
            new_terrain_type = TerrainType(modification["new_terrain_type"])
            tile = self.get_tile(x, y)
            if tile:
                tile.terrain_type = new_terrain_type
                tile.development_level = min(1.0, tile.development_level + 0.2)
        
        # 建造建筑（这里简化处理，实际应该根据项目计划建造）
        for building_id in project.buildings_to_construct:
            building = self.buildings.get(building_id)
            if building:
                building.is_completed = True
                building.construction_progress = 1.0
    
    def simulate_daily_operations(self):
        """模拟日常运营"""
        # 建筑生产资源
        for building in self.buildings.values():
            if building.is_completed:
                production = building.get_actual_production()
                self._add_resources(production)
                
                # 消耗维护资源
                self._consume_resources(building.maintenance_cost)
                
                # 建筑老化
                building.condition = max(0.1, building.condition - random.uniform(0.001, 0.005))
        
        # 推进在建项目
        for project in self.projects.values():
            if project.status == "in_progress":
                self.update_project_progress(project.project_id, random.uniform(0.05, 0.15))
        
        # 推进建筑建造
        for building in self.buildings.values():
            if not building.is_completed:
                self.advance_construction(building.id, random.uniform(0.1, 0.3))
        
        # 更新城市指标
        self.update_urban_metrics()
    
    def update_urban_metrics(self):
        """更新城市指标"""
        for (x, y), tile in self.terrain_map.items():
            # 计算交通密度
            self._calculate_traffic_density(tile, x, y)
            
            # 计算污染水平
            self._calculate_pollution_level(tile, x, y)
            
            # 计算犯罪率
            self._calculate_crime_rate(tile, x, y)
            
            # 计算幸福度
            self._calculate_happiness_index(tile, x, y)
    
    def _calculate_traffic_density(self, tile: TerrainTile, x: int, y: int):
        """计算交通密度"""
        # 基于可达性和邻近建筑数量
        neighbors = self.get_neighbors(x, y, radius=2)
        building_count = sum(1 for n in neighbors if n.buildings)
        
        # 交通设施增加交通密度
        transport_buildings = [b for b in tile.buildings 
                               if b in self.buildings and 
                               self.buildings[b].building_type in [
                                   BuildingType.BUS_STATION, BuildingType.TRAIN_STATION, 
                                   BuildingType.PARKING_LOT, BuildingType.AIRPORT
                               ]]
        
        base_traffic = tile.accessibility * 0.6
        building_traffic = min(1.0, building_count / 8) * 0.3
        transport_traffic = len(transport_buildings) * 0.1
        
        tile.traffic_density = min(1.0, base_traffic + building_traffic + transport_traffic)
    
    def _calculate_pollution_level(self, tile: TerrainTile, x: int, y: int):
        """计算污染水平"""
        # 工业建筑产生污染
        industrial_buildings = [b for b in tile.buildings 
                               if b in self.buildings and 
                               self.buildings[b].building_type in [
                                   BuildingType.FACTORY, BuildingType.WAREHOUSE, BuildingType.WORKSHOP
                               ]]
        
        # 交通密度影响污染
        traffic_pollution = tile.traffic_density * 0.4
        
        # 工业污染
        industrial_pollution = len(industrial_buildings) * 0.2
        
        # 绿地减少污染
        green_spaces = [b for b in tile.buildings 
                       if b in self.buildings and 
                       self.buildings[b].building_type == BuildingType.PARK]
        green_reduction = len(green_spaces) * 0.1
        
        tile.pollution = max(0.0, min(1.0, traffic_pollution + industrial_pollution - green_reduction))
    
    def _calculate_crime_rate(self, tile: TerrainTile, x: int, y: int):
        """计算犯罪率"""
        # 警察局和可达性降低犯罪率
        police_stations = [b for b in tile.buildings 
                          if b in self.buildings and 
                          self.buildings[b].building_type == BuildingType.POLICE_STATION]
        
        # 贫困和失业增加犯罪率（简化模型）
        base_crime = 0.3  # 基础犯罪率
        
        # 可达性好的区域犯罪率低
        accessibility_factor = (1 - tile.accessibility) * 0.3
        
        # 高密度区域犯罪率高
        density_factor = tile.traffic_density * 0.2
        
        # 污染高的区域犯罪率高
        pollution_factor = tile.pollution * 0.2
        
        # 警察局降低犯罪率
        police_reduction = len(police_stations) * 0.15
        
        # 政府建筑附近犯罪率低
        government_buildings = [b for b in self.get_neighbors(x, y, radius=3)
                               if any(bid in self.buildings and 
                                     self.buildings[bid].building_type == BuildingType.GOVERNMENT
                                     for bid in b.buildings)]
        government_reduction = len(government_buildings) * 0.05
        
        tile.crime_rate = max(0.0, min(1.0, base_crime + accessibility_factor + 
                                      density_factor + pollution_factor - 
                                      police_reduction - government_reduction))
    
    def _calculate_happiness_index(self, tile: TerrainTile, x: int, y: int):
        """计算幸福度指数"""
        happiness = 0.5  # 基础幸福度
        
        # 可达性增加幸福度
        happiness += tile.accessibility * 0.2
        
        # 绿地增加幸福度
        parks = [b for b in tile.buildings 
                if b in self.buildings and 
                self.buildings[b].building_type == BuildingType.PARK]
        happiness += len(parks) * 0.05
        
        # 娱乐设施增加幸福度
        entertainment = [b for b in tile.buildings 
                        if b in self.buildings and 
                        self.buildings[b].building_type in [
                            BuildingType.CINEMA, BuildingType.STADIUM, BuildingType.MUSEUM
                        ]]
        happiness += len(entertainment) * 0.08
        
        # 医疗设施增加幸福度
        medical = [b for b in tile.buildings 
                  if b in self.buildings and 
                  self.buildings[b].building_type in [BuildingType.HOSPITAL, BuildingType.CLINIC]]
        happiness += len(medical) * 0.06
        
        # 教育设施增加幸福度
        education = [b for b in tile.buildings 
                    if b in self.buildings and 
                    self.buildings[b].building_type in [BuildingType.SCHOOL, BuildingType.UNIVERSITY, BuildingType.LIBRARY]]
        happiness += len(education) * 0.06
        
        # 污染降低幸福度
        happiness -= tile.pollution * 0.3
        
        # 犯罪率降低幸福度
        happiness -= tile.crime_rate * 0.4
        
        # 高交通密度降低幸福度（噪音）
        happiness -= tile.traffic_density * 0.15
        
        tile.happiness_index = max(0.0, min(1.0, happiness))
    
    def get_city_statistics(self) -> dict:
        """获取城市统计信息"""
        total_tiles = len(self.terrain_map)
        developed_tiles = sum(1 for tile in self.terrain_map.values() if tile.development_level > 0.1)
        building_count = len(self.buildings)
        
        # 计算平均指标
        avg_traffic = sum(tile.traffic_density for tile in self.terrain_map.values()) / total_tiles
        avg_pollution = sum(tile.pollution for tile in self.terrain_map.values()) / total_tiles
        avg_crime = sum(tile.crime_rate for tile in self.terrain_map.values()) / total_tiles
        avg_happiness = sum(tile.happiness_index for tile in self.terrain_map.values()) / total_tiles
        avg_land_value = sum(tile.land_value for tile in self.terrain_map.values()) / total_tiles
        
        # 按区域统计
        district_stats = {}
        for district, tiles in self.city_districts.items():
            if tiles:
                district_tiles = [self.terrain_map[tile_pos] for tile_pos in tiles if tile_pos in self.terrain_map]
                district_stats[district.value] = {
                    "tile_count": len(tiles),
                    "avg_development": sum(t.development_level for t in district_tiles) / len(district_tiles),
                    "building_count": sum(len(t.buildings) for t in district_tiles),
                    "avg_traffic": sum(t.traffic_density for t in district_tiles) / len(district_tiles),
                    "avg_pollution": sum(t.pollution for t in district_tiles) / len(district_tiles),
                    "avg_crime": sum(t.crime_rate for t in district_tiles) / len(district_tiles),
                    "avg_happiness": sum(t.happiness_index for t in district_tiles) / len(district_tiles)
                }
        
        return {
            "total_tiles": total_tiles,
            "developed_tiles": developed_tiles,
            "development_rate": developed_tiles / total_tiles if total_tiles > 0 else 0,
            "building_count": building_count,
            "avg_traffic_density": avg_traffic,
            "avg_pollution_level": avg_pollution,
            "avg_crime_rate": avg_crime,
            "avg_happiness_index": avg_happiness,
            "avg_land_value": avg_land_value,
            "districts": district_stats,
            "global_resources": {resource.value: amount for resource, amount in self.global_resources.items()}
        }
    
    def get_development_statistics(self) -> dict:
        """获取开发统计信息"""
        total_tiles = len(self.terrain_map)
        developed_tiles = sum(1 for tile in self.terrain_map.values() if tile.development_level > 0.1)
        total_buildings = len(self.buildings)
        completed_buildings = sum(1 for b in self.buildings.values() if b.is_completed)
        total_population = sum(tile.current_population for tile in self.terrain_map.values())
        total_capacity = sum(tile.population_capacity for tile in self.terrain_map.values())
        
        building_types = {}
        for building in self.buildings.values():
            building_type = building.building_type.value
            building_types[building_type] = building_types.get(building_type, 0) + 1
        
        return {
            "total_tiles": total_tiles,
            "developed_tiles": developed_tiles,
            "development_percentage": (developed_tiles / total_tiles) * 100,
            "total_buildings": total_buildings,
            "completed_buildings": completed_buildings,
            "building_types": building_types,
            "total_population": total_population,
            "population_capacity": total_capacity,
            "population_utilization": (total_population / max(1, total_capacity)) * 100,
            "global_resources": dict(self.global_resources),
            "active_projects": len([p for p in self.projects.values() if p.status == "in_progress"])
        }
    
    def save_to_file(self, filepath: str):
        """保存地形数据到文件"""
        data = {
            "terrain_map": {
                f"{x}_{y}": {
                    "x": tile.x, "y": tile.y,
                    "terrain_type": tile.terrain_type.value,
                    "elevation": tile.elevation,
                    "fertility": tile.fertility,
                    "accessibility": tile.accessibility,
                    "resources": {rt.value: amount for rt, amount in tile.resources.items()},
                    "buildings": tile.buildings,
                    "development_level": tile.development_level,
                    "population_capacity": tile.population_capacity,
                    "current_population": tile.current_population
                }
                for (x, y), tile in self.terrain_map.items()
            },
            "buildings": {
                building_id: {
                    "id": building.id,
                    "building_type": building.building_type.value,
                    "x": building.x, "y": building.y,
                    "construction_cost": {rt.value: amount for rt, amount in building.construction_cost.items()},
                    "maintenance_cost": {rt.value: amount for rt, amount in building.maintenance_cost.items()},
                    "production": {rt.value: amount for rt, amount in building.production.items()},
                    "construction_time": building.construction_time,
                    "construction_progress": building.construction_progress,
                    "is_completed": building.is_completed,
                    "efficiency": building.efficiency,
                    "condition": building.condition,
                    "workers_needed": building.workers_needed,
                    "current_workers": building.current_workers,
                    "created_at": building.created_at.isoformat()
                }
                for building_id, building in self.buildings.items()
            },
            "global_resources": {rt.value: amount for rt, amount in self.global_resources.items()},
            "width": self.width,
            "height": self.height
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载地形数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.width = data.get("width", 50)
            self.height = data.get("height", 50)
            
            # 加载地形
            self.terrain_map = {}
            for key, tile_data in data.get("terrain_map", {}).items():
                x, y = map(int, key.split('_'))
                tile = TerrainTile(
                    x=tile_data["x"], y=tile_data["y"],
                    terrain_type=TerrainType(tile_data["terrain_type"]),
                    elevation=tile_data["elevation"],
                    fertility=tile_data["fertility"],
                    accessibility=tile_data["accessibility"],
                    resources={ResourceType(rt): amount for rt, amount in tile_data["resources"].items()},
                    buildings=tile_data["buildings"],
                    development_level=tile_data["development_level"],
                    population_capacity=tile_data["population_capacity"],
                    current_population=tile_data["current_population"]
                )
                self.terrain_map[(x, y)] = tile
            
            # 加载建筑
            self.buildings = {}
            for building_id, building_data in data.get("buildings", {}).items():
                building = Building(
                    id=building_data["id"],
                    building_type=BuildingType(building_data["building_type"]),
                    x=building_data["x"], y=building_data["y"],
                    construction_cost={ResourceType(rt): amount for rt, amount in building_data["construction_cost"].items()},
                    maintenance_cost={ResourceType(rt): amount for rt, amount in building_data["maintenance_cost"].items()},
                    production={ResourceType(rt): amount for rt, amount in building_data["production"].items()},
                    construction_time=building_data["construction_time"],
                    construction_progress=building_data["construction_progress"],
                    is_completed=building_data["is_completed"],
                    efficiency=building_data["efficiency"],
                    condition=building_data["condition"],
                    workers_needed=building_data["workers_needed"],
                    current_workers=building_data["current_workers"],
                    created_at=datetime.datetime.fromisoformat(building_data["created_at"])
                )
                self.buildings[building_id] = building
            
            # 加载全局资源
            self.global_resources = {
                ResourceType(rt): amount 
                for rt, amount in data.get("global_resources", {}).items()
            }
            
        except FileNotFoundError:
            pass  # 文件不存在时忽略