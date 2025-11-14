"""
AI自主建造决策模块
让Agent能够智能地分析地图、决定建造位置和类型、执行建造项目
"""

import random
import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from modules.terrain.terrain_development import (
    TerrainDevelopmentEngine,
    BuildingType,
    ResourceType,
    TerrainType,
    DevelopmentPriority,
    CityDistrict
)


class BuildingNeed(Enum):
    """建造需求类型 - 城市级别扩展"""
    HOUSING = "housing"           # 住房需求
    FOOD_PRODUCTION = "food"      # 食物生产
    RESOURCE_EXTRACTION = "resource"  # 资源开采
    INFRASTRUCTURE = "infrastructure"  # 基础设施
    COMMERCE = "commerce"          # 商业
    PUBLIC_SERVICE = "public"      # 公共服务
    ENTERTAINMENT = "entertainment"  # 娱乐
    EDUCATION = "education"       # 教育
    MEDICAL = "medical"           # 医疗
    TRANSPORTATION = "transportation"  # 交通
    GOVERNMENT = "government"      # 政府
    INDUSTRIAL = "industrial"      # 工业


class AIBuildingDecisionEngine:
    """AI建造决策引擎"""
    
    def __init__(self, terrain_engine: TerrainDevelopmentEngine):
        self.terrain_engine = terrain_engine
        self.agent_building_preferences: Dict[str, Dict[str, float]] = {}
        self.community_needs: Dict[BuildingNeed, float] = {}
        self.update_community_needs()
    
    def register_agent(self, agent_id: str, preferences: Optional[Dict[str, float]] = None):
        """注册Agent的建造偏好"""
        if preferences is None:
            # 默认偏好
            preferences = {
                BuildingType.HOUSE.value: 0.3,
                BuildingType.FARM.value: 0.3,
                BuildingType.MINE.value: 0.2,
                BuildingType.SHOP.value: 0.1,
                BuildingType.FACTORY.value: 0.1,
            }
        self.agent_building_preferences[agent_id] = preferences
    
    def update_community_needs(self):
        """更新社区需求 - 城市级别"""
        stats = self.terrain_engine.get_development_statistics()
        city_stats = self.terrain_engine.get_city_statistics()
        
        total_population = stats["total_population"]
        population_capacity = stats["population_capacity"]
        building_types = stats["building_types"]
        
        # 计算各种需求
        self.community_needs = {}
        
        # 住房需求：人口接近容量时需求增加
        housing_ratio = total_population / max(1, population_capacity)
        self.community_needs[BuildingNeed.HOUSING] = min(1.0, housing_ratio * 1.5)
        
        # 食物需求：基于人口和食物资源
        food_resource = self.terrain_engine.global_resources.get(ResourceType.FOOD, 0)
        food_per_capita = food_resource / max(1, total_population)
        self.community_needs[BuildingNeed.FOOD_PRODUCTION] = max(0, 1.0 - food_per_capita / 50)
        
        # 资源开采需求：基于资源稀缺度
        stone_level = self.terrain_engine.global_resources.get(ResourceType.STONE, 0)
        metal_level = self.terrain_engine.global_resources.get(ResourceType.METAL, 0)
        resource_scarcity = 1.0 - min(1.0, (stone_level + metal_level) / 2000)
        self.community_needs[BuildingNeed.RESOURCE_EXTRACTION] = resource_scarcity
        
        # 基础设施需求：基于道路密度
        road_count = building_types.get(BuildingType.ROAD.value, 0)
        total_buildings = stats["total_buildings"]
        road_ratio = road_count / max(1, total_buildings)
        self.community_needs[BuildingNeed.INFRASTRUCTURE] = max(0, 0.3 - road_ratio)
        
        # 商业需求：基于商店数量
        shop_count = (building_types.get(BuildingType.SHOP.value, 0) + 
                     building_types.get(BuildingType.MALL.value, 0))
        commerce_need = max(0, 1.0 - shop_count / max(1, total_population / 15))
        self.community_needs[BuildingNeed.COMMERCE] = commerce_need
        
        # 工业需求：基于平均幸福度和污染
        avg_happiness = city_stats.get("avg_happiness_index", 0.5)
        avg_pollution = city_stats.get("avg_pollution_level", 0.3)
        industrial_need = max(0, 1.0 - avg_happiness) * 0.5 + avg_pollution * 0.3
        self.community_needs[BuildingNeed.INDUSTRIAL] = min(1.0, industrial_need)
        
        # 娱乐需求：基于幸福度和娱乐设施
        entertainment_buildings = (
            building_types.get(BuildingType.CINEMA.value, 0) +
            building_types.get(BuildingType.STADIUM.value, 0) +
            building_types.get(BuildingType.MUSEUM.value, 0)
        )
        entertainment_need = max(0, 1.0 - entertainment_buildings / max(1, total_population / 100))
        entertainment_need += (1.0 - avg_happiness) * 0.3
        self.community_needs[BuildingNeed.ENTERTAINMENT] = min(1.0, entertainment_need)
        
        # 教育需求：基于人口和教育设施
        education_buildings = (
            building_types.get(BuildingType.SCHOOL.value, 0) +
            building_types.get(BuildingType.UNIVERSITY.value, 0) +
            building_types.get(BuildingType.LIBRARY.value, 0)
        )
        education_need = max(0, 1.0 - education_buildings / max(1, total_population / 80))
        self.community_needs[BuildingNeed.EDUCATION] = education_need
        
        # 医疗需求：基于人口和医疗设施
        medical_buildings = (
            building_types.get(BuildingType.HOSPITAL.value, 0) +
            building_types.get(BuildingType.CLINIC.value, 0)
        )
        medical_need = max(0, 1.0 - medical_buildings / max(1, total_population / 60))
        # 污染高的区域需要更多医疗设施
        medical_need += avg_pollution * 0.2
        self.community_needs[BuildingNeed.MEDICAL] = min(1.0, medical_need)
        
        # 交通需求：基于平均交通密度
        avg_traffic = city_stats.get("avg_traffic_density", 0.4)
        transport_buildings = (
            building_types.get(BuildingType.BUS_STATION.value, 0) +
            building_types.get(BuildingType.TRAIN_STATION.value, 0) +
            building_types.get(BuildingType.PARKING_LOT.value, 0)
        )
        transport_need = max(0, avg_traffic * 1.5 - transport_buildings / max(1, total_population / 200))
        self.community_needs[BuildingNeed.TRANSPORTATION] = min(1.0, transport_need)
        
        # 政府需求：基于犯罪率
        avg_crime = city_stats.get("avg_crime_rate", 0.2)
        government_buildings = building_types.get(BuildingType.GOVERNMENT.value, 0)
        government_need = max(0, avg_crime * 2.0 - government_buildings / max(1, total_population / 500))
        self.community_needs[BuildingNeed.GOVERNMENT] = min(1.0, government_need)
        
        # 公共服务需求：基于学校、医院等（兼容旧版本）
        public_buildings = (
            building_types.get(BuildingType.SCHOOL.value, 0) +
            building_types.get(BuildingType.HOSPITAL.value, 0) +
            building_types.get(BuildingType.POLICE_STATION.value, 0) +
            building_types.get(BuildingType.FIRE_STATION.value, 0)
        )
        public_need = max(0, 1.0 - public_buildings / max(1, total_population / 40))
        self.community_needs[BuildingNeed.PUBLIC_SERVICE] = public_need
    
    def analyze_agent_building_intention(
        self, 
        agent_id: str,
        agent_resources: Optional[Dict[ResourceType, float]] = None,
        agent_money: float = 0.0,
        agent_coord: Optional[Tuple[int, int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        分析Agent的建造意图 - 城市级别增强
        返回：建议的建造行动，如果不建议建造则返回None
        """
        # 更新社区需求
        self.update_community_needs()
        
        # 获取Agent偏好
        preferences = self.agent_building_preferences.get(agent_id, {})
        if not preferences:
            self.register_agent(agent_id)
            preferences = self.agent_building_preferences[agent_id]
        
        # 决定是否应该建造（基于概率和需求）
        total_need = sum(self.community_needs.values())
        if total_need < 0.5 and random.random() > 0.15:  # 提高建造概率
            return None  # 需求不高时，只有15%概率建造
        
        # 选择建造类型
        building_type = self._select_building_type(preferences, agent_resources, agent_money)
        if not building_type:
            return None
        
        # 选择建造位置 - 考虑就近原则和城市分区
        best_sites = self.terrain_engine.find_optimal_development_sites(building_type, count=15)  # 增加候选地点
        if not best_sites:
            return None
        
        # 应用城市分区优化
        best_sites = self._prioritize_district_appropriate_locations(best_sites, building_type)
        
        # 如果有Agent位置信息，优先选择附近的地点
        if agent_coord:
            best_sites = self._prioritize_nearby_locations(best_sites, agent_coord)
        
        # 选择得分最高的地点
        x, y, score = best_sites[0]
        
        # 检查资源是否足够
        template = self.terrain_engine.building_templates.get(building_type, {})
        construction_cost = template.get("construction_cost", {})
        
        can_afford = True
        if agent_resources:
            for resource_type, amount in construction_cost.items():
                if agent_resources.get(resource_type, 0) < amount:
                    can_afford = False
                    break
        
        if not can_afford:
            # 检查全局资源
            if not self.terrain_engine._check_resource_availability(construction_cost):
                return None
        
        # 获取城市指标信息
        city_stats = self.terrain_engine.get_city_statistics()
        tile = self.terrain_engine.get_tile(x, y)
        district_info = tile.city_district.value if tile and tile.city_district else "未分区"
        
        return {
            "action": "build",
            "building_type": building_type,
            "location": (x, y),
            "score": score,
            "cost": construction_cost,
            "reason": self._get_building_reason(building_type),
            "priority": self._calculate_priority(building_type),
            "district": district_info,
            "urban_metrics": {
                "traffic_density": tile.traffic_density if tile else 0,
                "pollution_level": tile.pollution if tile else 0,
                "crime_rate": tile.crime_rate if tile else 0,
                "happiness_index": tile.happiness_index if tile else 0,
                "land_value": tile.land_value if tile else 0
            }
        }
    
    def _select_building_type(
        self,
        preferences: Dict[str, float],
        agent_resources: Optional[Dict[ResourceType, float]],
        agent_money: float
    ) -> Optional[BuildingType]:
        """根据偏好和需求选择建造类型 - 城市级别"""
        
        # 建造类型与需求的映射 - 城市级别扩展
        type_to_need = {
            # 基础类型
            BuildingType.HOUSE: BuildingNeed.HOUSING,
            BuildingType.APARTMENT: BuildingNeed.HOUSING,
            BuildingType.CONDO: BuildingNeed.HOUSING,
            BuildingType.FARM: BuildingNeed.FOOD_PRODUCTION,
            BuildingType.MINE: BuildingNeed.RESOURCE_EXTRACTION,
            BuildingType.ROAD: BuildingNeed.INFRASTRUCTURE,
            BuildingType.SHOP: BuildingNeed.COMMERCE,
            BuildingType.MALL: BuildingNeed.COMMERCE,
            BuildingType.OFFICE: BuildingNeed.COMMERCE,
            BuildingType.RESTAURANT: BuildingNeed.COMMERCE,
            BuildingType.HOTEL: BuildingNeed.COMMERCE,
            BuildingType.FACTORY: BuildingNeed.INDUSTRIAL,
            BuildingType.WAREHOUSE: BuildingNeed.INDUSTRIAL,
            BuildingType.WORKSHOP: BuildingNeed.INDUSTRIAL,
            BuildingType.SCHOOL: BuildingNeed.EDUCATION,
            BuildingType.UNIVERSITY: BuildingNeed.EDUCATION,
            BuildingType.LIBRARY: BuildingNeed.EDUCATION,
            BuildingType.HOSPITAL: BuildingNeed.MEDICAL,
            BuildingType.CLINIC: BuildingNeed.MEDICAL,
            BuildingType.CINEMA: BuildingNeed.ENTERTAINMENT,
            BuildingType.STADIUM: BuildingNeed.ENTERTAINMENT,
            BuildingType.MUSEUM: BuildingNeed.ENTERTAINMENT,
            BuildingType.GOVERNMENT: BuildingNeed.GOVERNMENT,
            BuildingType.POLICE_STATION: BuildingNeed.PUBLIC_SERVICE,
            BuildingType.FIRE_STATION: BuildingNeed.PUBLIC_SERVICE,
            BuildingType.BUS_STATION: BuildingNeed.TRANSPORTATION,
            BuildingType.TRAIN_STATION: BuildingNeed.TRANSPORTATION,
            BuildingType.PARKING_LOT: BuildingNeed.TRANSPORTATION,
            BuildingType.AIRPORT: BuildingNeed.TRANSPORTATION,
            BuildingType.PARK: BuildingNeed.ENTERTAINMENT,
        }
        
        # 计算每种建筑类型的权重
        weights = {}
        for building_type, need_type in type_to_need.items():
            # 基础权重：偏好 * 社区需求
            pref_weight = preferences.get(building_type.value, 0.05)  # 降低默认值
            need_weight = self.community_needs.get(need_type, 0.3)
            
            # 综合权重
            combined_weight = pref_weight * 0.4 + need_weight * 0.6
            
            # 考虑资源可用性
            template = self.terrain_engine.building_templates.get(building_type, {})
            cost = template.get("construction_cost", {})
            
            # 如果全局资源不足，降低权重
            if not self.terrain_engine._check_resource_availability(cost):
                combined_weight *= 0.3
            
            weights[building_type] = combined_weight
        
        # 加权随机选择
        if not weights:
            return None
        
        total_weight = sum(weights.values())
        if total_weight <= 0:
            return None
        
        rand_val = random.random() * total_weight
        cumulative = 0
        
        for building_type, weight in weights.items():
            cumulative += weight
            if rand_val <= cumulative:
                return building_type
        
        # 默认返回第一个
        return list(weights.keys())[0] if weights else None
    
    def _get_building_reason(self, building_type: BuildingType) -> str:
        """获取建造原因说明 - 城市级别"""
        reasons = {
            # 住宅类型
            BuildingType.HOUSE: "增加人口容量，满足住房需求",
            BuildingType.APARTMENT: "提供高密度住宅，容纳更多居民",
            BuildingType.CONDO: "提供中高端住宅，提升居住品质",
            
            # 商业类型
            BuildingType.SHOP: "提供商业服务，促进经济发展",
            BuildingType.MALL: "建设大型购物中心，提升商业活力",
            BuildingType.OFFICE: "建设办公楼，促进商务活动",
            BuildingType.RESTAURANT: "提供餐饮服务，丰富生活配套",
            BuildingType.HOTEL: "建设酒店，促进旅游业发展",
            
            # 工业类型
            BuildingType.FACTORY: "生产能源和工业品",
            BuildingType.WAREHOUSE: "建设仓储设施，支持物流发展",
            BuildingType.WORKSHOP: "建设工坊，促进手工业发展",
            
            # 农业类型
            BuildingType.FARM: "生产食物，保障社区粮食供应",
            
            # 基础设施
            BuildingType.ROAD: "改善交通，提高地区可达性",
            BuildingType.BRIDGE: "跨越水域，拓展可用区域",
            BuildingType.WALL: "建设防护设施，保障安全",
            
            # 教育类型
            BuildingType.SCHOOL: "提供教育服务，提升社区文化水平",
            BuildingType.UNIVERSITY: "建设大学，提供高等教育",
            BuildingType.LIBRARY: "建设图书馆，促进知识传播",
            
            # 医疗类型
            BuildingType.HOSPITAL: "提供医疗服务，保障居民健康",
            BuildingType.CLINIC: "建设诊所，提供基础医疗服务",
            
            # 娱乐类型
            BuildingType.CINEMA: "建设电影院，丰富娱乐生活",
            BuildingType.STADIUM: "建设体育场，促进体育发展",
            BuildingType.MUSEUM: "建设博物馆，传承文化艺术",
            BuildingType.PARK: "提供休闲场所，改善生活质量",
            
            # 政府类型
            BuildingType.GOVERNMENT: "建设政府设施，提供行政服务",
            BuildingType.POLICE_STATION: "建设警察局，维护社会治安",
            BuildingType.FIRE_STATION: "建设消防站，保障消防安全",
            
            # 交通类型
            BuildingType.BUS_STATION: "建设公交站，改善公共交通",
            BuildingType.TRAIN_STATION: "建设火车站，提升交通能力",
            BuildingType.PARKING_LOT: "建设停车场，解决停车问题",
            BuildingType.AIRPORT: "建设机场，促进对外交通",
        }
        return reasons.get(building_type, "发展城市基础设施")
    
    def _prioritize_district_appropriate_locations(self, sites: List[Tuple[int, int, float]], building_type: BuildingType) -> List[Tuple[int, int, float]]:
        """优先选择适合建筑类型的城市分区
        
        Args:
            sites: 候选地点列表 [(x, y, score), ...]
            building_type: 建筑类型
            
        Returns:
            重新排序后的地点列表，优先考虑分区适宜性
        """
        if not sites:
            return sites
        
        # 建筑类型到适宜分区的映射
        building_district_map = {
            # 住宅类型 - 适合住宅区和郊区
            BuildingType.HOUSE: [CityDistrict.RESIDENTIAL, CityDistrict.SUBURBAN, CityDistrict.RURAL],
            BuildingType.APARTMENT: [CityDistrict.RESIDENTIAL, CityDistrict.SUBURBAN, CityDistrict.DOWNTOWN],
            BuildingType.CONDO: [CityDistrict.RESIDENTIAL, CityDistrict.SUBURBAN, CityDistrict.DOWNTOWN],
            
            # 商业类型 - 适合商业区、市中心
            BuildingType.SHOP: [CityDistrict.COMMERCIAL, CityDistrict.DOWNTOWN, CityDistrict.RESIDENTIAL],
            BuildingType.MALL: [CityDistrict.COMMERCIAL, CityDistrict.DOWNTOWN],
            BuildingType.OFFICE: [CityDistrict.COMMERCIAL, CityDistrict.DOWNTOWN],
            BuildingType.RESTAURANT: [CityDistrict.COMMERCIAL, CityDistrict.DOWNTOWN, CityDistrict.ENTERTAINMENT],
            BuildingType.HOTEL: [CityDistrict.COMMERCIAL, CityDistrict.DOWNTOWN, CityDistrict.ENTERTAINMENT],
            
            # 工业类型 - 适合工业区
            BuildingType.FACTORY: [CityDistrict.INDUSTRIAL],
            BuildingType.WAREHOUSE: [CityDistrict.INDUSTRIAL, CityDistrict.COMMERCIAL],
            BuildingType.WORKSHOP: [CityDistrict.INDUSTRIAL, CityDistrict.SUBURBAN],
            
            # 教育类型 - 适合教育区、住宅区
            BuildingType.SCHOOL: [CityDistrict.EDUCATION, CityDistrict.RESIDENTIAL, CityDistrict.SUBURBAN],
            BuildingType.UNIVERSITY: [CityDistrict.EDUCATION],
            BuildingType.LIBRARY: [CityDistrict.EDUCATION, CityDistrict.RESIDENTIAL],
            
            # 医疗类型 - 适合医疗区、住宅区
            BuildingType.HOSPITAL: [CityDistrict.MEDICAL, CityDistrict.RESIDENTIAL],
            BuildingType.CLINIC: [CityDistrict.MEDICAL, CityDistrict.RESIDENTIAL, CityDistrict.COMMERCIAL],
            
            # 娱乐类型 - 适合娱乐区、商业区
            BuildingType.CINEMA: [CityDistrict.ENTERTAINMENT, CityDistrict.COMMERCIAL],
            BuildingType.STADIUM: [CityDistrict.ENTERTAINMENT, CityDistrict.PARK],
            BuildingType.MUSEUM: [CityDistrict.ENTERTAINMENT, CityDistrict.EDUCATION],
            BuildingType.PARK: [CityDistrict.PARK, CityDistrict.RESIDENTIAL, CityDistrict.ENTERTAINMENT],
            
            # 政府类型 - 适合政府区、市中心
            BuildingType.GOVERNMENT: [CityDistrict.GOVERNMENT, CityDistrict.DOWNTOWN],
            BuildingType.POLICE_STATION: [CityDistrict.GOVERNMENT, CityDistrict.DOWNTOWN, CityDistrict.COMMERCIAL],
            BuildingType.FIRE_STATION: [CityDistrict.GOVERNMENT, CityDistrict.DOWNTOWN, CityDistrict.INDUSTRIAL],
            
            # 交通类型 - 适合交通区、商业区
            BuildingType.BUS_STATION: [CityDistrict.TRANSPORT, CityDistrict.COMMERCIAL, CityDistrict.DOWNTOWN],
            BuildingType.TRAIN_STATION: [CityDistrict.TRANSPORT, CityDistrict.COMMERCIAL],
            BuildingType.PARKING_LOT: [CityDistrict.TRANSPORT, CityDistrict.COMMERCIAL, CityDistrict.DOWNTOWN],
            BuildingType.AIRPORT: [CityDistrict.TRANSPORT],
            
            # 农业类型 - 适合农村区
            BuildingType.FARM: [CityDistrict.RURAL],
            
            # 基础设施 - 通用
            BuildingType.ROAD: [CityDistrict.DOWNTOWN, CityDistrict.COMMERCIAL, CityDistrict.RESIDENTIAL, CityDistrict.INDUSTRIAL],
            BuildingType.BRIDGE: [CityDistrict.TRANSPORT, CityDistrict.COMMERCIAL],
            BuildingType.WALL: [CityDistrict.GOVERNMENT, CityDistrict.DOWNTOWN],
        }
        
        appropriate_districts = building_district_map.get(building_type, [])
        prioritized_sites = []
        
        for x, y, original_score in sites:
            tile = self.terrain_engine.get_tile(x, y)
            if not tile:
                continue
                
            district_bonus = 0
            district_penalty = 0
            
            if tile.city_district:
                # 如果在适宜分区，给予奖励
                if tile.city_district in appropriate_districts:
                    district_bonus = 30  # 分区匹配奖励
                    
                    # 额外考虑城市指标
                    if tile.happiness_index > 0.7:
                        district_bonus += 10  # 高幸福度区域奖励
                    if tile.crime_rate < 0.2:
                        district_bonus += 10  # 低犯罪率区域奖励
                    if tile.pollution < 0.3:
                        district_bonus += 10  # 低污染区域奖励
                else:
                    # 如果在不适宜分区，给予惩罚
                    district_penalty = 20  # 分区不匹配惩罚
                    
                    # 特别不适宜的分区给予更大惩罚
                    if building_type in [BuildingType.FACTORY, BuildingType.WAREHOUSE] and tile.city_district in [CityDistrict.RESIDENTIAL, CityDistrict.EDUCATION]:
                        district_penalty += 30  # 工业建筑在住宅区或教育区严重惩罚
                    elif building_type in [BuildingType.HOUSE, BuildingType.APARTMENT] and tile.city_district in [CityDistrict.INDUSTRIAL]:
                        district_penalty += 25  # 住宅建筑在工业区严重惩罚
            else:
                # 未分区区域给予轻微惩罚
                district_penalty = 5
            
            new_score = original_score + district_bonus - district_penalty
            prioritized_sites.append((x, y, new_score))
        
        # 按新分数重新排序
        prioritized_sites.sort(key=lambda x: x[2], reverse=True)
        return prioritized_sites
    
    def _prioritize_nearby_locations(self, sites: List[Tuple[int, int, float]], agent_coord: Tuple[int, int], max_distance: int = 20) -> List[Tuple[int, int, float]]:
        """优先选择Agent附近的地点
        
        Args:
            sites: 候选地点列表 [(x, y, score), ...]
            agent_coord: Agent当前坐标 (x, y)
            max_distance: 最大考虑距离
            
        Returns:
            重新排序后的地点列表，优先考虑距离
        """
        if not sites or not agent_coord:
            return sites
        
        agent_x, agent_y = agent_coord
        prioritized_sites = []
        
        for x, y, original_score in sites:
            # 计算距离
            distance = abs(x - agent_x) + abs(y - agent_y)  # 曼哈顿距离
            
            # 如果距离在可接受范围内，增加分数
            if distance <= max_distance:
                # 距离越近，奖励越大
                distance_bonus = (max_distance - distance) / max_distance * 50
                new_score = original_score + distance_bonus
                prioritized_sites.append((x, y, new_score))
            else:
                # 超出范围的地点，稍微降低分数
                distance_penalty = (distance - max_distance) * 2
                new_score = original_score - distance_penalty
                prioritized_sites.append((x, y, new_score))
        
        # 按新分数重新排序
        prioritized_sites.sort(key=lambda x: x[2], reverse=True)
        return prioritized_sites
    
    def _calculate_priority(self, building_type: BuildingType) -> DevelopmentPriority:
        """计算建造优先级 - 城市级别"""
        # 根据社区需求确定优先级 - 城市级别扩展
        type_to_need = {
            # 基础类型
            BuildingType.HOUSE: BuildingNeed.HOUSING,
            BuildingType.FARM: BuildingNeed.FOOD_PRODUCTION,
            BuildingType.MINE: BuildingNeed.RESOURCE_EXTRACTION,
            BuildingType.ROAD: BuildingNeed.INFRASTRUCTURE,
            BuildingType.SHOP: BuildingNeed.COMMERCE,
            
            # 城市类型
            BuildingType.APARTMENT: BuildingNeed.HOUSING,
            BuildingType.CONDO: BuildingNeed.HOUSING,
            BuildingType.MALL: BuildingNeed.COMMERCE,
            BuildingType.OFFICE: BuildingNeed.COMMERCE,
            BuildingType.RESTAURANT: BuildingNeed.COMMERCE,
            BuildingType.HOTEL: BuildingNeed.COMMERCE,
            BuildingType.FACTORY: BuildingNeed.INDUSTRIAL,
            BuildingType.WAREHOUSE: BuildingNeed.INDUSTRIAL,
            BuildingType.WORKSHOP: BuildingNeed.INDUSTRIAL,
            BuildingType.SCHOOL: BuildingNeed.EDUCATION,
            BuildingType.UNIVERSITY: BuildingNeed.EDUCATION,
            BuildingType.LIBRARY: BuildingNeed.EDUCATION,
            BuildingType.HOSPITAL: BuildingNeed.MEDICAL,
            BuildingType.CLINIC: BuildingNeed.MEDICAL,
            BuildingType.CINEMA: BuildingNeed.ENTERTAINMENT,
            BuildingType.STADIUM: BuildingNeed.ENTERTAINMENT,
            BuildingType.MUSEUM: BuildingNeed.ENTERTAINMENT,
            BuildingType.PARK: BuildingNeed.ENTERTAINMENT,
            BuildingType.GOVERNMENT: BuildingNeed.GOVERNMENT,
            BuildingType.POLICE_STATION: BuildingNeed.PUBLIC_SERVICE,
            BuildingType.FIRE_STATION: BuildingNeed.PUBLIC_SERVICE,
            BuildingType.BUS_STATION: BuildingNeed.TRANSPORTATION,
            BuildingType.TRAIN_STATION: BuildingNeed.TRANSPORTATION,
            BuildingType.PARKING_LOT: BuildingNeed.TRANSPORTATION,
            BuildingType.AIRPORT: BuildingNeed.TRANSPORTATION,
        }
        
        need_type = type_to_need.get(building_type)
        if not need_type:
            return DevelopmentPriority.MEDIUM
        
        need_level = self.community_needs.get(need_type, 0.5)
        
        # 城市级别优先级调整
        if need_level > 0.85:
            return DevelopmentPriority.URGENT
        elif need_level > 0.65:
            return DevelopmentPriority.HIGH
        elif need_level > 0.35:
            return DevelopmentPriority.MEDIUM
        else:
            return DevelopmentPriority.LOW
    
    def execute_building_decision(
        self,
        agent_id: str,
        decision: Dict[str, Any],
        consume_agent_resources: bool = False,
        agent_resources: Optional[Dict[ResourceType, float]] = None
    ) -> Dict[str, Any]:
        """
        执行建造决策
        
        Args:
            agent_id: Agent ID
            decision: 建造决策
            consume_agent_resources: 是否从Agent资源扣除（False则从全局扣除）
            agent_resources: Agent的资源（如果从Agent扣除）
        
        Returns:
            执行结果
        """
        building_type = decision["building_type"]
        x, y = decision["location"]
        
        # 如果从Agent资源扣除
        if consume_agent_resources and agent_resources:
            cost = decision["cost"]
            # 检查资源
            for resource_type, amount in cost.items():
                if agent_resources.get(resource_type, 0) < amount:
                    return {
                        "status": "failed",
                        "reason": f"资源不足: 缺少 {amount} {resource_type.value}"
                    }
            
            # 扣除Agent资源
            for resource_type, amount in cost.items():
                agent_resources[resource_type] -= amount
        
        # 创建建筑
        building = self.terrain_engine.create_building(
            building_type=building_type,
            x=x,
            y=y,
            building_id=f"{building_type.value}_{agent_id}_{x}_{y}"
        )
        
        if not building:
            return {
                "status": "failed",
                "reason": "无法在该位置建造"
            }
        
        return {
            "status": "success",
            "building_id": building.id,
            "building_type": building_type.value,
            "location": (x, y),
            "agent": agent_id,
            "cost": decision["cost"],
            "reason": decision["reason"],
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def create_collaborative_project(
        self,
        project_name: str,
        description: str,
        agent_ids: List[str],
        buildings_to_build: List[Tuple[BuildingType, int]]
    ) -> Optional[str]:
        """
        创建协作建造项目
        
        Args:
            project_name: 项目名称
            description: 项目描述
            agent_ids: 参与的Agent列表
            buildings_to_build: 要建造的建筑列表 [(建筑类型, 数量), ...]
        
        Returns:
            项目ID，如果失败则返回None
        """
        buildings_plan = []
        for building_type, count in buildings_to_build:
            buildings_plan.append({
                "type": building_type.value,
                "count": count
            })
        
        project = self.terrain_engine.create_development_project(
            name=project_name,
            description=description,
            buildings_plan=buildings_plan
        )
        
        # 执行项目
        success = self.terrain_engine.execute_project(
            project_id=project.project_id,
            assigned_agents=agent_ids
        )
        
        if success:
            return project.project_id
        return None
    
    def get_building_suggestions_for_agent(
        self,
        agent_id: str,
        agent_personality: Optional[str] = None,
        agent_skills: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        为Agent获取建造建议
        
        返回多个建造选项供Agent选择
        """
        suggestions = []
        
        # 更新需求
        self.update_community_needs()
        
        # 根据社区需求生成建议
        sorted_needs = sorted(
            self.community_needs.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 需求到建筑类型的映射
        need_to_types = {
            BuildingNeed.HOUSING: [BuildingType.HOUSE],
            BuildingNeed.FOOD_PRODUCTION: [BuildingType.FARM],
            BuildingNeed.RESOURCE_EXTRACTION: [BuildingType.MINE],
            BuildingNeed.INFRASTRUCTURE: [BuildingType.ROAD],
            BuildingNeed.COMMERCE: [BuildingType.SHOP],
            BuildingNeed.PUBLIC_SERVICE: [BuildingType.SCHOOL, BuildingType.HOSPITAL],
        }
        
        for need_type, need_level in sorted_needs[:3]:  # 取前3个最高需求
            if need_level < 0.3:
                continue
            
            building_types = need_to_types.get(need_type, [])
            for building_type in building_types:
                # 找到最佳位置
                best_sites = self.terrain_engine.find_optimal_development_sites(
                    building_type, count=1
                )
                
                if not best_sites:
                    continue
                
                x, y, score = best_sites[0]
                template = self.terrain_engine.building_templates.get(building_type, {})
                
                suggestions.append({
                    "building_type": building_type.value,
                    "location": (x, y),
                    "suitability_score": score,
                    "need_type": need_type.value,
                    "need_level": need_level,
                    "cost": template.get("construction_cost", {}),
                    "construction_time": template.get("construction_time", 7),
                    "reason": self._get_building_reason(building_type),
                    "priority": self._calculate_priority(building_type).value
                })
        
        return suggestions

