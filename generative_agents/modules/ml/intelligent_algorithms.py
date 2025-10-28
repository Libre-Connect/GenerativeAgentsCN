"""
机器学习算法集成模块
实现行为预测、关系推荐、建设优化等智能化功能
"""

import json
import numpy as np
import random
import datetime
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from collections import defaultdict, deque


class PredictionType(Enum):
    """预测类型"""
    BEHAVIOR = "behavior"           # 行为预测
    RELATIONSHIP = "relationship"   # 关系预测
    RESOURCE_NEED = "resource_need" # 资源需求预测
    COLLABORATION = "collaboration" # 协作预测
    CONFLICT = "conflict"          # 冲突预测
    DEVELOPMENT = "development"    # 发展预测


class OptimizationType(Enum):
    """优化类型"""
    RESOURCE_ALLOCATION = "resource_allocation"  # 资源分配优化
    BUILDING_PLACEMENT = "building_placement"    # 建筑布局优化
    TASK_SCHEDULING = "task_scheduling"          # 任务调度优化
    RELATIONSHIP_MATCHING = "relationship_matching"  # 关系匹配优化
    ROUTE_PLANNING = "route_planning"            # 路径规划优化


@dataclass
class FeatureVector:
    """特征向量"""
    agent_id: str
    features: Dict[str, float]
    timestamp: datetime.datetime
    context: Dict[str, Any]
    
    def to_array(self, feature_names: List[str]) -> np.ndarray:
        """转换为numpy数组"""
        return np.array([self.features.get(name, 0.0) for name in feature_names])
    
    def normalize(self, feature_ranges: Dict[str, Tuple[float, float]]):
        """归一化特征"""
        for feature_name, value in self.features.items():
            if feature_name in feature_ranges:
                min_val, max_val = feature_ranges[feature_name]
                if max_val > min_val:
                    self.features[feature_name] = (value - min_val) / (max_val - min_val)


@dataclass
class PredictionResult:
    """预测结果"""
    prediction_type: PredictionType
    target_agent: str
    predicted_value: Any
    confidence: float
    features_used: List[str]
    timestamp: datetime.datetime
    metadata: Dict[str, Any]


@dataclass
class OptimizationResult:
    """优化结果"""
    optimization_type: OptimizationType
    solution: Dict[str, Any]
    objective_value: float
    constraints_satisfied: bool
    computation_time: float
    metadata: Dict[str, Any]


class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self):
        self.feature_definitions = self._initialize_feature_definitions()
    
    def _initialize_feature_definitions(self) -> Dict[str, dict]:
        """初始化特征定义"""
        return {
            # 基础状态特征
            "energy_level": {"type": "continuous", "range": (0, 100)},
            "happiness_level": {"type": "continuous", "range": (0, 100)},
            "health_level": {"type": "continuous", "range": (0, 100)},
            "resource_amount": {"type": "continuous", "range": (0, 1000)},
            
            # 社交特征
            "relationship_count": {"type": "discrete", "range": (0, 50)},
            "intimacy_average": {"type": "continuous", "range": (0, 100)},
            "social_activity_frequency": {"type": "continuous", "range": (0, 10)},
            "conflict_count": {"type": "discrete", "range": (0, 20)},
            
            # 行为特征
            "work_frequency": {"type": "continuous", "range": (0, 1)},
            "rest_frequency": {"type": "continuous", "range": (0, 1)},
            "social_frequency": {"type": "continuous", "range": (0, 1)},
            "exploration_frequency": {"type": "continuous", "range": (0, 1)},
            
            # 环境特征
            "location_x": {"type": "continuous", "range": (-100, 100)},
            "location_y": {"type": "continuous", "range": (-100, 100)},
            "nearby_agents_count": {"type": "discrete", "range": (0, 10)},
            "nearby_buildings_count": {"type": "discrete", "range": (0, 20)},
            
            # 时间特征
            "hour_of_day": {"type": "discrete", "range": (0, 23)},
            "day_of_week": {"type": "discrete", "range": (0, 6)},
            "season": {"type": "discrete", "range": (0, 3)},
            
            # 目标特征
            "active_goals_count": {"type": "discrete", "range": (0, 10)},
            "goal_completion_rate": {"type": "continuous", "range": (0, 1)},
            "priority_goal_urgency": {"type": "continuous", "range": (0, 1)}
        }
    
    def extract_features(self, agent_data: Dict[str, Any], 
                        context_data: Dict[str, Any] = None) -> FeatureVector:
        """提取特征"""
        features = {}
        
        # 基础状态特征
        features["energy_level"] = agent_data.get("energy", 50)
        features["happiness_level"] = agent_data.get("happiness", 50)
        features["health_level"] = agent_data.get("health", 100)
        features["resource_amount"] = agent_data.get("resources", 100)
        
        # 社交特征
        relationships = agent_data.get("relationships", {})
        features["relationship_count"] = len(relationships)
        
        if relationships:
            intimacy_values = [r.get("intimacy", 0) for r in relationships.values()]
            features["intimacy_average"] = sum(intimacy_values) / len(intimacy_values)
        else:
            features["intimacy_average"] = 0
        
        # 行为特征（基于历史数据）
        behavior_history = agent_data.get("behavior_history", [])
        if behavior_history:
            total_actions = len(behavior_history)
            work_actions = sum(1 for b in behavior_history if b.get("action_type") == "work")
            rest_actions = sum(1 for b in behavior_history if b.get("action_type") == "rest")
            social_actions = sum(1 for b in behavior_history if b.get("action_type") == "socialize")
            
            features["work_frequency"] = work_actions / total_actions
            features["rest_frequency"] = rest_actions / total_actions
            features["social_frequency"] = social_actions / total_actions
        else:
            features["work_frequency"] = 0.3
            features["rest_frequency"] = 0.3
            features["social_frequency"] = 0.2
        
        # 环境特征
        location = agent_data.get("location", (0, 0))
        features["location_x"] = location[0]
        features["location_y"] = location[1]
        
        if context_data:
            features["nearby_agents_count"] = len(context_data.get("nearby_agents", []))
            features["nearby_buildings_count"] = len(context_data.get("nearby_buildings", []))
        else:
            features["nearby_agents_count"] = 0
            features["nearby_buildings_count"] = 0
        
        # 时间特征
        now = datetime.datetime.now()
        features["hour_of_day"] = now.hour
        features["day_of_week"] = now.weekday()
        features["season"] = (now.month - 1) // 3  # 0-3 representing seasons
        
        # 目标特征
        goals = agent_data.get("goals", [])
        active_goals = [g for g in goals if g.get("is_active", False)]
        features["active_goals_count"] = len(active_goals)
        
        if active_goals:
            completion_rates = [g.get("progress", 0) for g in active_goals]
            features["goal_completion_rate"] = sum(completion_rates) / len(completion_rates)
            
            # 计算最高优先级目标的紧急程度
            priority_goals = sorted(active_goals, key=lambda g: g.get("priority", 1), reverse=True)
            if priority_goals:
                features["priority_goal_urgency"] = self._calculate_goal_urgency(priority_goals[0])
            else:
                features["priority_goal_urgency"] = 0
        else:
            features["goal_completion_rate"] = 1.0
            features["priority_goal_urgency"] = 0
        
        return FeatureVector(
            agent_id=agent_data.get("agent_id", "unknown"),
            features=features,
            timestamp=datetime.datetime.now(),
            context=context_data or {}
        )
    
    def _calculate_goal_urgency(self, goal: Dict[str, Any]) -> float:
        """计算目标紧急程度"""
        deadline = goal.get("deadline")
        if not deadline:
            return 0.5
        
        if isinstance(deadline, str):
            deadline = datetime.datetime.fromisoformat(deadline)
        
        time_left = (deadline - datetime.datetime.now()).total_seconds()
        if time_left <= 0:
            return 1.0
        
        # 基于剩余时间和进度计算紧急程度
        progress = goal.get("progress", 0)
        expected_progress = 1.0 - (time_left / (7 * 24 * 3600))  # 假设一周完成
        urgency = max(0.0, expected_progress - progress)
        return min(1.0, urgency)
    
    def get_feature_names(self) -> List[str]:
        """获取特征名称列表"""
        return list(self.feature_definitions.keys())
    
    def get_feature_ranges(self) -> Dict[str, Tuple[float, float]]:
        """获取特征范围"""
        return {name: def_info["range"] for name, def_info in self.feature_definitions.items()}


class BehaviorPredictor:
    """行为预测器"""
    
    def __init__(self, feature_extractor: FeatureExtractor):
        self.feature_extractor = feature_extractor
        self.behavior_patterns = {}
        self.prediction_history = deque(maxlen=1000)
        self.model_weights = self._initialize_weights()
    
    def _initialize_weights(self) -> Dict[str, np.ndarray]:
        """初始化模型权重"""
        feature_count = len(self.feature_extractor.get_feature_names())
        
        # 为不同行为类型初始化权重
        behavior_types = ["work", "rest", "socialize", "explore", "build", "help"]
        weights = {}
        
        for behavior in behavior_types:
            # 随机初始化权重，然后根据行为类型调整
            w = np.random.normal(0, 0.1, feature_count)
            
            # 根据行为类型调整权重偏向
            feature_names = self.feature_extractor.get_feature_names()
            for i, feature_name in enumerate(feature_names):
                if behavior == "work" and "resource" in feature_name:
                    w[i] += 0.5  # 工作行为与资源相关
                elif behavior == "rest" and "energy" in feature_name:
                    w[i] -= 0.5  # 休息行为与低能量相关
                elif behavior == "socialize" and "social" in feature_name:
                    w[i] += 0.3  # 社交行为与社交需求相关
                elif behavior == "explore" and "location" in feature_name:
                    w[i] += 0.2  # 探索行为与位置相关
            
            weights[behavior] = w
        
        return weights
    
    def predict_behavior(self, agent_data: Dict[str, Any], 
                        context_data: Dict[str, Any] = None) -> PredictionResult:
        """预测行为"""
        # 提取特征
        features = self.feature_extractor.extract_features(agent_data, context_data)
        feature_array = features.to_array(self.feature_extractor.get_feature_names())
        
        # 计算每种行为的得分
        behavior_scores = {}
        for behavior, weights in self.model_weights.items():
            score = np.dot(feature_array, weights)
            # 应用sigmoid激活函数
            behavior_scores[behavior] = 1 / (1 + np.exp(-score))
        
        # 选择得分最高的行为
        predicted_behavior = max(behavior_scores, key=behavior_scores.get)
        confidence = behavior_scores[predicted_behavior]
        
        # 添加随机性
        if confidence < 0.7:
            # 如果置信度不高，增加随机选择的可能性
            if random.random() < 0.3:
                predicted_behavior = random.choice(list(behavior_scores.keys()))
                confidence = 0.5
        
        result = PredictionResult(
            prediction_type=PredictionType.BEHAVIOR,
            target_agent=features.agent_id,
            predicted_value=predicted_behavior,
            confidence=confidence,
            features_used=self.feature_extractor.get_feature_names(),
            timestamp=datetime.datetime.now(),
            metadata={
                "all_scores": behavior_scores,
                "feature_values": features.features
            }
        )
        
        self.prediction_history.append(result)
        return result
    
    def update_model(self, actual_behavior: str, prediction_result: PredictionResult, 
                    learning_rate: float = 0.01):
        """更新模型"""
        if actual_behavior not in self.model_weights:
            return
        
        # 获取特征向量
        feature_values = prediction_result.metadata.get("feature_values", {})
        feature_array = np.array([
            feature_values.get(name, 0.0) 
            for name in self.feature_extractor.get_feature_names()
        ])
        
        # 计算预测误差
        predicted_behavior = prediction_result.predicted_value
        
        # 更新正确行为的权重（增强）
        if actual_behavior in self.model_weights:
            self.model_weights[actual_behavior] += learning_rate * feature_array
        
        # 更新错误预测的权重（减弱）
        if predicted_behavior != actual_behavior and predicted_behavior in self.model_weights:
            self.model_weights[predicted_behavior] -= learning_rate * feature_array * 0.5
    
    def get_prediction_accuracy(self, recent_count: int = 100) -> float:
        """获取预测准确率"""
        if len(self.prediction_history) < 10:
            return 0.5  # 默认准确率
        
        recent_predictions = list(self.prediction_history)[-recent_count:]
        # 这里需要实际的行为数据来计算准确率
        # 简化实现，返回基于置信度的估计准确率
        avg_confidence = sum(p.confidence for p in recent_predictions) / len(recent_predictions)
        return avg_confidence


class RelationshipRecommender:
    """关系推荐器"""
    
    def __init__(self, feature_extractor: FeatureExtractor):
        self.feature_extractor = feature_extractor
        self.compatibility_matrix = {}
        self.relationship_success_history = {}
    
    def calculate_compatibility(self, agent1_data: Dict[str, Any], 
                              agent2_data: Dict[str, Any]) -> float:
        """计算兼容性"""
        # 提取两个agent的特征
        features1 = self.feature_extractor.extract_features(agent1_data)
        features2 = self.feature_extractor.extract_features(agent2_data)
        
        compatibility_score = 0.0
        total_weight = 0.0
        
        # 计算特征相似性和互补性
        compatibility_factors = {
            # 相似性因子（值越接近越好）
            "energy_level": {"weight": 0.1, "type": "similarity"},
            "happiness_level": {"weight": 0.2, "type": "similarity"},
            "social_frequency": {"weight": 0.3, "type": "similarity"},
            "goal_completion_rate": {"weight": 0.2, "type": "similarity"},
            
            # 互补性因子（差异可能有益）
            "work_frequency": {"weight": 0.1, "type": "complementary"},
            "resource_amount": {"weight": 0.1, "type": "complementary"}
        }
        
        for feature_name, factor_info in compatibility_factors.items():
            if feature_name in features1.features and feature_name in features2.features:
                value1 = features1.features[feature_name]
                value2 = features2.features[feature_name]
                weight = factor_info["weight"]
                
                if factor_info["type"] == "similarity":
                    # 相似性：差异越小越好
                    feature_ranges = self.feature_extractor.get_feature_ranges()
                    if feature_name in feature_ranges:
                        range_size = feature_ranges[feature_name][1] - feature_ranges[feature_name][0]
                        normalized_diff = abs(value1 - value2) / range_size
                        similarity = 1.0 - normalized_diff
                    else:
                        similarity = 1.0 - abs(value1 - value2) / max(abs(value1), abs(value2), 1.0)
                    
                    compatibility_score += weight * similarity
                
                elif factor_info["type"] == "complementary":
                    # 互补性：适度差异有益
                    feature_ranges = self.feature_extractor.get_feature_ranges()
                    if feature_name in feature_ranges:
                        range_size = feature_ranges[feature_name][1] - feature_ranges[feature_name][0]
                        normalized_diff = abs(value1 - value2) / range_size
                        # 适度差异（0.2-0.8）得分最高
                        if 0.2 <= normalized_diff <= 0.8:
                            complementary = 1.0
                        else:
                            complementary = 1.0 - abs(normalized_diff - 0.5) * 2
                    else:
                        complementary = 0.5
                    
                    compatibility_score += weight * complementary
                
                total_weight += weight
        
        # 归一化得分
        if total_weight > 0:
            compatibility_score /= total_weight
        
        # 添加位置因子
        location1 = features1.features.get("location_x", 0), features1.features.get("location_y", 0)
        location2 = features2.features.get("location_x", 0), features2.features.get("location_y", 0)
        distance = math.sqrt((location1[0] - location2[0])**2 + (location1[1] - location2[1])**2)
        
        # 距离越近，兼容性加成越高
        distance_factor = max(0, 1.0 - distance / 50.0)  # 50单位内有加成
        compatibility_score = compatibility_score * 0.8 + distance_factor * 0.2
        
        return max(0.0, min(1.0, compatibility_score))
    
    def recommend_relationships(self, agent_id: str, agent_data: Dict[str, Any],
                              all_agents_data: Dict[str, Dict[str, Any]],
                              relationship_type: str = "friend") -> List[Tuple[str, float]]:
        """推荐关系"""
        recommendations = []
        
        for other_id, other_data in all_agents_data.items():
            if other_id == agent_id:
                continue
            
            # 检查是否已有关系
            existing_relationships = agent_data.get("relationships", {})
            if other_id in existing_relationships:
                continue
            
            # 计算兼容性
            compatibility = self.calculate_compatibility(agent_data, other_data)
            
            # 根据关系类型调整得分
            if relationship_type == "romantic":
                # 恋爱关系需要更高的兼容性
                compatibility = compatibility * 0.8 + 0.2 if compatibility > 0.6 else compatibility * 0.5
            elif relationship_type == "work":
                # 工作关系更注重技能互补
                work_compatibility = self._calculate_work_compatibility(agent_data, other_data)
                compatibility = compatibility * 0.6 + work_compatibility * 0.4
            
            recommendations.append((other_id, compatibility))
        
        # 按兼容性排序
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:10]  # 返回前10个推荐
    
    def _calculate_work_compatibility(self, agent1_data: Dict[str, Any], 
                                    agent2_data: Dict[str, Any]) -> float:
        """计算工作兼容性"""
        # 简化的工作兼容性计算
        skills1 = set(agent1_data.get("skills", {}).keys())
        skills2 = set(agent2_data.get("skills", {}).keys())
        
        if not skills1 and not skills2:
            return 0.5
        
        # 技能互补性
        complementary_skills = len(skills1.symmetric_difference(skills2))
        common_skills = len(skills1.intersection(skills2))
        
        # 既要有共同技能，也要有互补技能
        if len(skills1) + len(skills2) == 0:
            return 0.5
        
        complementary_ratio = complementary_skills / (len(skills1) + len(skills2))
        common_ratio = common_skills / max(len(skills1), len(skills2), 1)
        
        return complementary_ratio * 0.6 + common_ratio * 0.4
    
    def update_relationship_success(self, agent1_id: str, agent2_id: str, 
                                  success_score: float):
        """更新关系成功记录"""
        pair_key = tuple(sorted([agent1_id, agent2_id]))
        if pair_key not in self.relationship_success_history:
            self.relationship_success_history[pair_key] = []
        
        self.relationship_success_history[pair_key].append({
            "score": success_score,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # 限制历史记录长度
        if len(self.relationship_success_history[pair_key]) > 10:
            self.relationship_success_history[pair_key] = self.relationship_success_history[pair_key][-5:]


class DevelopmentOptimizer:
    """发展优化器"""
    
    def __init__(self):
        self.optimization_history = []
        self.terrain_analysis = {}
    
    def optimize_building_placement(self, available_locations: List[Tuple[int, int]],
                                  building_requirements: Dict[str, Any],
                                  existing_buildings: List[Dict[str, Any]]) -> OptimizationResult:
        """优化建筑布局"""
        start_time = datetime.datetime.now()
        
        building_type = building_requirements.get("type", "house")
        required_resources = building_requirements.get("resources", {})
        
        best_location = None
        best_score = -float('inf')
        
        for location in available_locations:
            score = self._evaluate_building_location(
                location, building_type, existing_buildings
            )
            
            if score > best_score:
                best_score = score
                best_location = location
        
        computation_time = (datetime.datetime.now() - start_time).total_seconds()
        
        result = OptimizationResult(
            optimization_type=OptimizationType.BUILDING_PLACEMENT,
            solution={
                "location": best_location,
                "building_type": building_type,
                "expected_score": best_score
            },
            objective_value=best_score,
            constraints_satisfied=best_location is not None,
            computation_time=computation_time,
            metadata={
                "evaluated_locations": len(available_locations),
                "building_requirements": building_requirements
            }
        )
        
        self.optimization_history.append(result)
        return result
    
    def _evaluate_building_location(self, location: Tuple[int, int], 
                                  building_type: str,
                                  existing_buildings: List[Dict[str, Any]]) -> float:
        """评估建筑位置"""
        x, y = location
        score = 0.0
        
        # 基础地形适宜性
        terrain_score = self._get_terrain_suitability(location, building_type)
        score += terrain_score * 0.4
        
        # 与现有建筑的距离关系
        distance_score = self._calculate_distance_score(location, existing_buildings, building_type)
        score += distance_score * 0.3
        
        # 资源可达性
        resource_score = self._calculate_resource_accessibility(location)
        score += resource_score * 0.2
        
        # 发展潜力
        development_score = self._calculate_development_potential(location)
        score += development_score * 0.1
        
        return score
    
    def _get_terrain_suitability(self, location: Tuple[int, int], building_type: str) -> float:
        """获取地形适宜性"""
        # 简化的地形适宜性计算
        x, y = location
        
        # 基于位置的简单地形模拟
        elevation = abs(math.sin(x * 0.1) * math.cos(y * 0.1)) * 100
        slope = abs(math.sin(x * 0.2) * math.cos(y * 0.15)) * 45
        
        if building_type == "house":
            # 房屋适合平坦地形
            return max(0, 1.0 - slope / 45.0)
        elif building_type == "farm":
            # 农场适合低海拔平地
            return max(0, (1.0 - elevation / 100.0) * (1.0 - slope / 30.0))
        elif building_type == "mine":
            # 矿场适合山地
            return min(1.0, elevation / 50.0)
        else:
            return 0.5
    
    def _calculate_distance_score(self, location: Tuple[int, int],
                                existing_buildings: List[Dict[str, Any]],
                                building_type: str) -> float:
        """计算距离得分"""
        x, y = location
        
        if not existing_buildings:
            return 0.5
        
        # 计算到各类建筑的距离
        distances = {
            "house": [],
            "farm": [],
            "workshop": [],
            "market": []
        }
        
        for building in existing_buildings:
            bx, by = building.get("location", (0, 0))
            distance = math.sqrt((x - bx)**2 + (y - by)**2)
            btype = building.get("type", "unknown")
            
            if btype in distances:
                distances[btype].append(distance)
        
        score = 0.0
        
        if building_type == "house":
            # 房屋希望靠近市场，但不要太拥挤
            if distances["market"]:
                min_market_distance = min(distances["market"])
                score += max(0, 1.0 - min_market_distance / 20.0) * 0.5
            
            if distances["house"]:
                min_house_distance = min(distances["house"])
                # 不要太近也不要太远
                if 3 <= min_house_distance <= 10:
                    score += 0.5
                else:
                    score += max(0, 1.0 - abs(min_house_distance - 6.5) / 6.5) * 0.5
        
        elif building_type == "farm":
            # 农场希望远离建筑密集区
            if distances["house"]:
                min_house_distance = min(distances["house"])
                score += min(1.0, min_house_distance / 15.0)
        
        return score
    
    def _calculate_resource_accessibility(self, location: Tuple[int, int]) -> float:
        """计算资源可达性"""
        x, y = location
        
        # 简化的资源分布模拟
        water_distance = abs(x % 20 - 10) + abs(y % 20 - 10)  # 模拟水源
        forest_distance = abs((x + 10) % 30 - 15) + abs((y + 10) % 30 - 15)  # 模拟森林
        
        water_score = max(0, 1.0 - water_distance / 20.0)
        forest_score = max(0, 1.0 - forest_distance / 25.0)
        
        return (water_score + forest_score) / 2.0
    
    def _calculate_development_potential(self, location: Tuple[int, int]) -> float:
        """计算发展潜力"""
        x, y = location
        
        # 基于位置的发展潜力（靠近中心区域潜力更大）
        center_distance = math.sqrt(x**2 + y**2)
        development_potential = max(0, 1.0 - center_distance / 50.0)
        
        return development_potential
    
    def optimize_resource_allocation(self, available_resources: Dict[str, int],
                                   resource_demands: List[Dict[str, Any]]) -> OptimizationResult:
        """优化资源分配"""
        start_time = datetime.datetime.now()
        
        # 简化的资源分配算法
        allocation = {}
        remaining_resources = available_resources.copy()
        
        # 按优先级排序需求
        sorted_demands = sorted(resource_demands, 
                              key=lambda d: d.get("priority", 1), reverse=True)
        
        total_satisfaction = 0.0
        
        for demand in sorted_demands:
            demand_id = demand.get("id", "unknown")
            required_resources = demand.get("resources", {})
            priority = demand.get("priority", 1)
            
            # 检查是否能满足需求
            can_satisfy = True
            for resource_type, amount in required_resources.items():
                if remaining_resources.get(resource_type, 0) < amount:
                    can_satisfy = False
                    break
            
            if can_satisfy:
                # 分配资源
                allocation[demand_id] = required_resources.copy()
                for resource_type, amount in required_resources.items():
                    remaining_resources[resource_type] -= amount
                
                total_satisfaction += priority
            else:
                # 部分满足
                partial_allocation = {}
                for resource_type, amount in required_resources.items():
                    available = remaining_resources.get(resource_type, 0)
                    allocated = min(amount, available)
                    if allocated > 0:
                        partial_allocation[resource_type] = allocated
                        remaining_resources[resource_type] -= allocated
                
                if partial_allocation:
                    allocation[demand_id] = partial_allocation
                    satisfaction_ratio = sum(partial_allocation.values()) / sum(required_resources.values())
                    total_satisfaction += priority * satisfaction_ratio
        
        computation_time = (datetime.datetime.now() - start_time).total_seconds()
        
        result = OptimizationResult(
            optimization_type=OptimizationType.RESOURCE_ALLOCATION,
            solution={
                "allocation": allocation,
                "remaining_resources": remaining_resources
            },
            objective_value=total_satisfaction,
            constraints_satisfied=True,
            computation_time=computation_time,
            metadata={
                "total_demands": len(resource_demands),
                "satisfied_demands": len(allocation)
            }
        )
        
        self.optimization_history.append(result)
        return result
    
    def optimize_task_scheduling(self, tasks: List[Dict[str, Any]],
                               agents: List[str],
                               time_horizon: int = 24) -> OptimizationResult:
        """优化任务调度"""
        start_time = datetime.datetime.now()
        
        # 简化的任务调度算法
        schedule = {agent_id: [] for agent_id in agents}
        unassigned_tasks = tasks.copy()
        
        # 按优先级和截止时间排序任务
        def task_priority(task):
            priority = task.get("priority", 1)
            deadline = task.get("deadline", time_horizon)
            return priority * 10 + (time_horizon - deadline)
        
        sorted_tasks = sorted(tasks, key=task_priority, reverse=True)
        
        total_value = 0.0
        
        for task in sorted_tasks:
            task_id = task.get("id", "unknown")
            duration = task.get("duration", 1)
            required_skills = task.get("required_skills", [])
            value = task.get("value", 1)
            
            # 找到最适合的agent
            best_agent = None
            best_score = -1
            
            for agent_id in agents:
                # 检查agent是否有足够时间
                current_workload = sum(t.get("duration", 1) for t in schedule[agent_id])
                if current_workload + duration > time_horizon:
                    continue
                
                # 计算适合度得分
                score = self._calculate_agent_task_fit(agent_id, task)
                
                if score > best_score:
                    best_score = score
                    best_agent = agent_id
            
            if best_agent:
                schedule[best_agent].append(task)
                total_value += value
                unassigned_tasks.remove(task)
        
        computation_time = (datetime.datetime.now() - start_time).total_seconds()
        
        result = OptimizationResult(
            optimization_type=OptimizationType.TASK_SCHEDULING,
            solution={
                "schedule": schedule,
                "unassigned_tasks": unassigned_tasks
            },
            objective_value=total_value,
            constraints_satisfied=len(unassigned_tasks) == 0,
            computation_time=computation_time,
            metadata={
                "total_tasks": len(tasks),
                "assigned_tasks": len(tasks) - len(unassigned_tasks)
            }
        )
        
        self.optimization_history.append(result)
        return result
    
    def _calculate_agent_task_fit(self, agent_id: str, task: Dict[str, Any]) -> float:
        """计算agent与任务的适合度"""
        # 简化的适合度计算
        required_skills = task.get("required_skills", [])
        
        # 这里应该从agent数据中获取技能信息
        # 简化实现，返回随机适合度
        base_score = random.uniform(0.3, 1.0)
        
        # 如果任务需要特定技能，调整得分
        if required_skills:
            # 假设agent有一定概率拥有所需技能
            skill_match_probability = 0.7
            if random.random() < skill_match_probability:
                base_score *= 1.2
            else:
                base_score *= 0.8
        
        return base_score


class IntelligentAlgorithmEngine:
    """智能算法引擎"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.behavior_predictor = BehaviorPredictor(self.feature_extractor)
        self.relationship_recommender = RelationshipRecommender(self.feature_extractor)
        self.development_optimizer = DevelopmentOptimizer()
        
        self.prediction_cache = {}
        self.optimization_cache = {}
        self.learning_enabled = True
    
    def predict_agent_behavior(self, agent_id: str, agent_data: Dict[str, Any],
                             context_data: Dict[str, Any] = None) -> PredictionResult:
        """预测agent行为"""
        cache_key = f"behavior_{agent_id}_{hash(str(agent_data))}"
        
        if cache_key in self.prediction_cache:
            cached_result = self.prediction_cache[cache_key]
            # 检查缓存是否过期（5分钟）
            if (datetime.datetime.now() - cached_result.timestamp).total_seconds() < 300:
                return cached_result
        
        result = self.behavior_predictor.predict_behavior(agent_data, context_data)
        self.prediction_cache[cache_key] = result
        
        return result
    
    def recommend_relationships(self, agent_id: str, agent_data: Dict[str, Any],
                              all_agents_data: Dict[str, Dict[str, Any]],
                              relationship_type: str = "friend") -> List[Tuple[str, float]]:
        """推荐关系"""
        return self.relationship_recommender.recommend_relationships(
            agent_id, agent_data, all_agents_data, relationship_type
        )
    
    def optimize_development(self, optimization_type: str, 
                           optimization_params: Dict[str, Any]) -> OptimizationResult:
        """优化发展"""
        if optimization_type == "building_placement":
            return self.development_optimizer.optimize_building_placement(
                optimization_params.get("available_locations", []),
                optimization_params.get("building_requirements", {}),
                optimization_params.get("existing_buildings", [])
            )
        elif optimization_type == "resource_allocation":
            return self.development_optimizer.optimize_resource_allocation(
                optimization_params.get("available_resources", {}),
                optimization_params.get("resource_demands", [])
            )
        elif optimization_type == "task_scheduling":
            return self.development_optimizer.optimize_task_scheduling(
                optimization_params.get("tasks", []),
                optimization_params.get("agents", []),
                optimization_params.get("time_horizon", 24)
            )
        else:
            raise ValueError(f"未知的优化类型: {optimization_type}")
    
    def update_learning(self, feedback_data: Dict[str, Any]):
        """更新学习"""
        if not self.learning_enabled:
            return
        
        feedback_type = feedback_data.get("type")
        
        if feedback_type == "behavior_feedback":
            # 更新行为预测模型
            actual_behavior = feedback_data.get("actual_behavior")
            prediction_result = feedback_data.get("prediction_result")
            
            if actual_behavior and prediction_result:
                self.behavior_predictor.update_model(actual_behavior, prediction_result)
        
        elif feedback_type == "relationship_feedback":
            # 更新关系推荐模型
            agent1_id = feedback_data.get("agent1_id")
            agent2_id = feedback_data.get("agent2_id")
            success_score = feedback_data.get("success_score", 0.5)
            
            if agent1_id and agent2_id:
                self.relationship_recommender.update_relationship_success(
                    agent1_id, agent2_id, success_score
                )
    
    def get_algorithm_statistics(self) -> Dict[str, Any]:
        """获取算法统计信息"""
        behavior_accuracy = self.behavior_predictor.get_prediction_accuracy()
        
        return {
            "behavior_prediction": {
                "accuracy": behavior_accuracy,
                "total_predictions": len(self.behavior_predictor.prediction_history)
            },
            "relationship_recommendation": {
                "total_recommendations": len(self.relationship_recommender.relationship_success_history)
            },
            "development_optimization": {
                "total_optimizations": len(self.development_optimizer.optimization_history)
            },
            "cache_status": {
                "prediction_cache_size": len(self.prediction_cache),
                "optimization_cache_size": len(self.optimization_cache)
            },
            "learning_enabled": self.learning_enabled
        }
    
    def save_to_file(self, filepath: str):
        """保存算法引擎状态到文件"""
        data = {
            "behavior_predictor": {
                "model_weights": {
                    behavior: weights.tolist() 
                    for behavior, weights in self.behavior_predictor.model_weights.items()
                },
                "prediction_history": [
                    {
                        "prediction_type": p.prediction_type.value,
                        "target_agent": p.target_agent,
                        "predicted_value": p.predicted_value,
                        "confidence": p.confidence,
                        "timestamp": p.timestamp.isoformat(),
                        "metadata": p.metadata
                    }
                    for p in list(self.behavior_predictor.prediction_history)[-50:]  # 只保存最近50个
                ]
            },
            "relationship_recommender": {
                "relationship_success_history": {
                    f"{key[0]}_{key[1]}": history
                    for key, history in self.relationship_recommender.relationship_success_history.items()
                }
            },
            "development_optimizer": {
                "optimization_history": [
                    {
                        "optimization_type": opt.optimization_type.value,
                        "objective_value": opt.objective_value,
                        "constraints_satisfied": opt.constraints_satisfied,
                        "computation_time": opt.computation_time,
                        "metadata": opt.metadata
                    }
                    for opt in self.development_optimizer.optimization_history[-20:]  # 只保存最近20个
                ]
            },
            "learning_enabled": self.learning_enabled
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载算法引擎状态"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载行为预测器
            behavior_data = data.get("behavior_predictor", {})
            model_weights = behavior_data.get("model_weights", {})
            
            for behavior, weights_list in model_weights.items():
                self.behavior_predictor.model_weights[behavior] = np.array(weights_list)
            
            # 加载关系推荐器
            relationship_data = data.get("relationship_recommender", {})
            success_history = relationship_data.get("relationship_success_history", {})
            
            for key_str, history in success_history.items():
                agent1_id, agent2_id = key_str.split("_", 1)
                pair_key = tuple(sorted([agent1_id, agent2_id]))
                self.relationship_recommender.relationship_success_history[pair_key] = history
            
            # 加载其他设置
            self.learning_enabled = data.get("learning_enabled", True)
            
        except FileNotFoundError:
            pass  # 文件不存在时忽略