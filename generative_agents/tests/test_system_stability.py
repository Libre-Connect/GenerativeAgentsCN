"""
系统稳定性和集成测试模块
验证整个AI社会模拟系统的稳定性和各模块间的协作
"""

import unittest
import json
import time
import threading
import tempfile
import os
import random
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入需要测试的模块
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules', 'social'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules', 'ml'))

from relationship import RelationshipType, SocialNetwork, Relationship
from romance import RomanceEngine, RomanceStage
from terrain_development import TerrainDevelopmentEngine, BuildingType, TerrainType
from autonomous_decision import AutonomousDecisionEngine, GoalType, DecisionType
from multi_ai_interaction import MultiAIInteractionEngine, InteractionType
from intelligent_algorithms import IntelligentAlgorithmEngine, PredictionType


class TestSystemStability(unittest.TestCase):
    """系统稳定性测试"""
    
    def setUp(self):
        """测试前准备"""
        self.social_network = SocialNetwork()
        self.romance_engine = RomanceEngine()
        self.terrain_engine = TerrainDevelopmentEngine()
        self.decision_engine = AutonomousDecisionEngine()
        self.interaction_engine = MultiAIInteractionEngine()
        self.ml_engine = IntelligentAlgorithmEngine()
        
        # 创建测试AI agents
        self.test_agents = ["alice", "bob", "charlie", "diana", "eve"]
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """设置测试环境"""
        # 初始化社会网络
        for agent in self.test_agents:
            for other_agent in self.test_agents:
                if agent != other_agent:
                    self.social_network.add_relationship(agent, other_agent, RelationshipType.STRANGER)
        
        # 创建基础地形
        for x in range(20):
            for y in range(20):
                terrain_type = random.choice(list(TerrainType))
                self.terrain_engine.create_tile(x, y, terrain_type)
        
        # 初始化决策引擎
        for agent in self.test_agents:
            self.decision_engine.initialize_agent(agent)
        
        # 初始化交互引擎
        for agent in self.test_agents:
            self.interaction_engine.register_agent(agent)
    
    def test_memory_usage_stability(self):
        """测试内存使用稳定性"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 执行大量操作
        for i in range(1000):
            # 社会关系操作
            agent1 = random.choice(self.test_agents)
            agent2 = random.choice(self.test_agents)
            if agent1 != agent2:
                self.social_network.update_relationship(agent1, agent2, intimacy_change=random.randint(-5, 5))
            
            # 地形操作
            x, y = random.randint(0, 19), random.randint(0, 19)
            tile = self.terrain_engine.get_tile((x, y))
            if tile:
                self.terrain_engine.analyze_terrain((x, y), radius=2)
            
            # 决策操作
            agent = random.choice(self.test_agents)
            self.decision_engine.make_decision(agent)
            
            # 每100次操作检查一次内存
            if i % 100 == 0:
                gc.collect()  # 强制垃圾回收
                current_memory = process.memory_info().rss
                memory_growth = (current_memory - initial_memory) / initial_memory
                
                # 内存增长不应超过50%
                self.assertLess(memory_growth, 0.5, 
                    f"Memory growth too high: {memory_growth:.2%} at iteration {i}")
    
    def test_concurrent_access_safety(self):
        """测试并发访问安全性"""
        errors = []
        
        def social_operations():
            try:
                for _ in range(100):
                    agent1 = random.choice(self.test_agents)
                    agent2 = random.choice(self.test_agents)
                    if agent1 != agent2:
                        self.social_network.update_relationship(
                            agent1, agent2, 
                            intimacy_change=random.randint(-3, 3)
                        )
                        time.sleep(0.001)  # 模拟处理时间
            except Exception as e:
                errors.append(f"Social operations error: {e}")
        
        def terrain_operations():
            try:
                for _ in range(100):
                    x, y = random.randint(0, 19), random.randint(0, 19)
                    self.terrain_engine.analyze_terrain((x, y), radius=1)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Terrain operations error: {e}")
        
        def decision_operations():
            try:
                for _ in range(100):
                    agent = random.choice(self.test_agents)
                    self.decision_engine.make_decision(agent)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Decision operations error: {e}")
        
        # 启动并发线程
        threads = []
        for operation in [social_operations, terrain_operations, decision_operations]:
            for _ in range(3):  # 每种操作3个线程
                thread = threading.Thread(target=operation)
                threads.append(thread)
                thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)  # 30秒超时
        
        # 检查是否有错误
        if errors:
            self.fail(f"Concurrent access errors: {errors}")
    
    def test_long_running_stability(self):
        """测试长时间运行稳定性"""
        start_time = time.time()
        operation_count = 0
        errors = []
        
        # 运行5秒的连续操作
        while time.time() - start_time < 5:
            try:
                # 随机选择操作类型
                operation_type = random.choice([
                    'social_update', 'romance_check', 'terrain_analysis', 
                    'decision_making', 'interaction'
                ])
                
                if operation_type == 'social_update':
                    agent1, agent2 = random.sample(self.test_agents, 2)
                    self.social_network.update_relationship(
                        agent1, agent2, 
                        intimacy_change=random.randint(-2, 2)
                    )
                
                elif operation_type == 'romance_check':
                    agent1, agent2 = random.sample(self.test_agents, 2)
                    self.romance_engine.check_romance_potential(agent1, agent2)
                
                elif operation_type == 'terrain_analysis':
                    x, y = random.randint(0, 19), random.randint(0, 19)
                    self.terrain_engine.analyze_terrain((x, y), radius=2)
                
                elif operation_type == 'decision_making':
                    agent = random.choice(self.test_agents)
                    self.decision_engine.make_decision(agent)
                
                elif operation_type == 'interaction':
                    agent1, agent2 = random.sample(self.test_agents, 2)
                    self.interaction_engine.send_message(
                        agent1, agent2, "test_message", InteractionType.CASUAL_CHAT
                    )
                
                operation_count += 1
                
                # 每1000次操作检查一次状态
                if operation_count % 1000 == 0:
                    # 验证系统状态一致性
                    self.verify_system_consistency()
                
            except Exception as e:
                errors.append(f"Operation {operation_count} ({operation_type}): {e}")
                if len(errors) > 10:  # 如果错误太多，停止测试
                    break
        
        print(f"Completed {operation_count} operations in {time.time() - start_time:.2f} seconds")
        
        # 检查错误率
        error_rate = len(errors) / operation_count if operation_count > 0 else 1
        self.assertLess(error_rate, 0.01, f"Error rate too high: {error_rate:.2%}, errors: {errors[:5]}")
    
    def verify_system_consistency(self):
        """验证系统状态一致性"""
        # 检查社会网络一致性
        for agent in self.test_agents:
            relationships = self.social_network.get_relationships(agent)
            for rel in relationships:
                # 关系应该是双向的
                reverse_rel = self.social_network.get_relationship(rel.agent_b, rel.agent_a)
                if reverse_rel:
                    self.assertEqual(rel.relationship_type, reverse_rel.relationship_type)
        
        # 检查地形数据一致性
        for x in range(20):
            for y in range(20):
                tile = self.terrain_engine.get_tile((x, y))
                if tile:
                    self.assertEqual(tile.coord, (x, y))
                    self.assertGreaterEqual(tile.elevation, 0)
    
    def test_error_recovery(self):
        """测试错误恢复能力"""
        # 模拟各种错误情况
        
        # 1. 无效输入测试
        try:
            self.social_network.add_relationship("", "", RelationshipType.FRIEND)
        except:
            pass  # 应该能处理无效输入
        
        try:
            self.terrain_engine.get_tile((-1, -1))
        except:
            pass  # 应该能处理无效坐标
        
        try:
            self.decision_engine.make_decision("")
        except:
            pass  # 应该能处理无效agent
        
        # 2. 资源耗尽测试
        # 模拟内存不足情况
        large_data = []
        try:
            for i in range(10000):
                large_data.append([0] * 1000)
                if i % 1000 == 0:
                    # 在内存压力下执行正常操作
                    agent1, agent2 = random.sample(self.test_agents, 2)
                    self.social_network.update_relationship(agent1, agent2, intimacy_change=1)
        except MemoryError:
            pass  # 内存不足是可以接受的
        finally:
            del large_data  # 清理内存
        
        # 3. 验证系统仍然正常工作
        agent1, agent2 = random.sample(self.test_agents, 2)
        result = self.social_network.update_relationship(agent1, agent2, intimacy_change=5)
        self.assertTrue(result)
    
    def test_data_persistence_integrity(self):
        """测试数据持久化完整性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一些复杂的系统状态
            for i in range(10):
                agent1, agent2 = random.sample(self.test_agents, 2)
                self.social_network.update_relationship(
                    agent1, agent2, 
                    intimacy_change=random.randint(-10, 10)
                )
            
            # 保存状态
            social_file = os.path.join(temp_dir, "social.json")
            terrain_file = os.path.join(temp_dir, "terrain.json")
            
            self.social_network.save_to_file(social_file)
            self.terrain_engine.save_to_file(terrain_file)
            
            # 记录原始状态
            original_relationships = {}
            for agent in self.test_agents:
                original_relationships[agent] = self.social_network.get_relationships(agent)
            
            # 清空并重新加载
            self.social_network = SocialNetwork()
            self.terrain_engine = TerrainDevelopmentEngine()
            
            self.social_network.load_from_file(social_file)
            self.terrain_engine.load_from_file(terrain_file)
            
            # 验证数据完整性
            for agent in self.test_agents:
                loaded_relationships = self.social_network.get_relationships(agent)
                original_count = len(original_relationships[agent])
                loaded_count = len(loaded_relationships)
                
                # 关系数量应该一致
                self.assertEqual(original_count, loaded_count)


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.social_network = SocialNetwork()
        self.romance_engine = RomanceEngine()
        self.terrain_engine = TerrainDevelopmentEngine()
        self.decision_engine = AutonomousDecisionEngine()
        self.interaction_engine = MultiAIInteractionEngine()
        self.ml_engine = IntelligentAlgorithmEngine()
        
        self.test_agents = ["alice", "bob", "charlie", "diana"]
        self.setup_integrated_environment()
    
    def setup_integrated_environment(self):
        """设置集成测试环境"""
        # 创建复杂的社会网络
        relationships = [
            ("alice", "bob", RelationshipType.FRIEND),
            ("alice", "charlie", RelationshipType.ACQUAINTANCE),
            ("bob", "diana", RelationshipType.COLLEAGUE),
            ("charlie", "diana", RelationshipType.NEIGHBOR)
        ]
        
        for agent1, agent2, rel_type in relationships:
            self.social_network.add_relationship(agent1, agent2, rel_type)
        
        # 创建地形和建筑
        self.create_test_terrain()
        
        # 初始化所有引擎
        for agent in self.test_agents:
            self.decision_engine.initialize_agent(agent)
            self.interaction_engine.register_agent(agent)
    
    def create_test_terrain(self):
        """创建测试地形"""
        # 创建一个小村庄的地形
        terrain_layout = [
            # 中心区域 - 村庄广场
            ((10, 10), TerrainType.GRASSLAND, BuildingType.MARKET),
            ((9, 10), TerrainType.GRASSLAND, None),
            ((11, 10), TerrainType.GRASSLAND, None),
            
            # 住宅区
            ((8, 8), TerrainType.GRASSLAND, BuildingType.HOUSE),
            ((12, 8), TerrainType.GRASSLAND, BuildingType.HOUSE),
            ((8, 12), TerrainType.GRASSLAND, BuildingType.HOUSE),
            ((12, 12), TerrainType.GRASSLAND, BuildingType.HOUSE),
            
            # 农业区
            ((6, 10), TerrainType.GRASSLAND, BuildingType.FARM),
            ((14, 10), TerrainType.GRASSLAND, BuildingType.FARM),
            
            # 工业区
            ((10, 6), TerrainType.GRASSLAND, BuildingType.WORKSHOP),
            
            # 资源区
            ((5, 5), TerrainType.FOREST, None),
            ((15, 15), TerrainType.MOUNTAIN, BuildingType.MINE)
        ]
        
        for (x, y), terrain_type, building_type in terrain_layout:
            tile = self.terrain_engine.create_tile(x, y, terrain_type)
            
            if building_type:
                building_plan = self.terrain_engine.plan_building(
                    building_type,
                    owner_id=random.choice(self.test_agents),
                    preferred_location=(x, y)
                )
                self.terrain_engine.construct_building(building_plan)
    
    def test_social_terrain_integration(self):
        """测试社会关系与地形开发的集成"""
        # 1. 基于社会关系规划建筑位置
        alice_friends = [rel.agent_b for rel in self.social_network.get_relationships("alice") 
                        if rel.relationship_type == RelationshipType.FRIEND]
        
        if alice_friends:
            friend = alice_friends[0]
            
            # Alice想在朋友附近建房子
            friend_buildings = []
            for building in self.terrain_engine.buildings.values():
                if building.owner_id == friend:
                    friend_buildings.append(building)
            
            if friend_buildings:
                friend_location = friend_buildings[0].location
                
                # 在朋友附近寻找建筑位置
                nearby_location = self.terrain_engine.find_suitable_location(
                    BuildingType.HOUSE,
                    search_area=[(friend_location[0]-3, friend_location[1]-3),
                                (friend_location[0]+3, friend_location[1]+3)]
                )
                
                if nearby_location:
                    # 规划并建造房屋
                    house_plan = self.terrain_engine.plan_building(
                        BuildingType.HOUSE,
                        owner_id="alice",
                        preferred_location=nearby_location
                    )
                    
                    result = self.terrain_engine.construct_building(house_plan)
                    self.assertTrue(result["success"])
                    
                    # 验证社会关系影响建筑选址
                    distance = ((nearby_location[0] - friend_location[0])**2 + 
                               (nearby_location[1] - friend_location[1])**2)**0.5
                    self.assertLessEqual(distance, 5)  # 应该在朋友附近
    
    def test_romance_terrain_integration(self):
        """测试恋爱关系与地形的集成"""
        # 1. 发展恋爱关系
        self.romance_engine.initiate_romance("alice", "bob")
        
        # 2. 规划约会地点
        date_location = self.terrain_engine.find_suitable_location(
            BuildingType.MARKET,  # 市场作为约会地点
            search_area=[(8, 8), (12, 12)]
        )
        
        if date_location:
            # 3. 执行约会
            date_result = self.romance_engine.plan_date("alice", "bob", date_location)
            self.assertIsInstance(date_result, dict)
            self.assertIn("success", date_result)
            
            # 4. 约会成功后，考虑共同建造房屋
            if date_result.get("success"):
                # 寻找适合情侣的建筑位置
                couple_location = self.terrain_engine.find_suitable_location(
                    BuildingType.HOUSE,
                    search_area=[(9, 9), (11, 11)]
                )
                
                if couple_location:
                    house_plan = self.terrain_engine.plan_building(
                        BuildingType.HOUSE,
                        owner_id="alice_bob_couple",
                        preferred_location=couple_location
                    )
                    
                    result = self.terrain_engine.construct_building(house_plan)
                    self.assertTrue(result["success"])
    
    def test_decision_making_integration(self):
        """测试决策系统与其他模块的集成"""
        # 1. 基于社会关系做决策
        alice_relationships = self.social_network.get_relationships("alice")
        
        # Alice根据社会关系决定行动
        decision = self.decision_engine.make_decision("alice")
        self.assertIsInstance(decision, dict)
        
        # 2. 基于地形状况做决策
        terrain_analysis = self.terrain_engine.analyze_terrain((10, 10), radius=3)
        
        # 根据地形分析调整决策
        if terrain_analysis["buildable_tiles"] > 5:
            # 如果有足够的可建造区域，考虑扩张
            expansion_decision = self.decision_engine.evaluate_goal("alice", GoalType.EXPANSION)
            self.assertIsInstance(expansion_decision, dict)
        
        # 3. 基于机器学习预测做决策
        behavior_prediction = self.ml_engine.predict_behavior("alice", "bob")
        
        if behavior_prediction.confidence > 0.7:
            # 高置信度预测影响决策
            interaction_decision = self.decision_engine.make_decision(
                "alice", 
                context={"prediction": behavior_prediction}
            )
            self.assertIsInstance(interaction_decision, dict)
    
    def test_multi_agent_collaboration(self):
        """测试多agent协作"""
        # 1. 创建协作项目
        collaboration_project = self.terrain_engine.create_development_project(
            project_type="community_development",
            target_area=[(8, 8), (12, 12)],
            priority=self.terrain_engine.DevelopmentPriority.HIGH,
            initiator_id="alice"
        )
        
        # 2. 邀请其他agent参与
        participants = ["bob", "charlie", "diana"]
        for participant in participants:
            invitation_result = self.interaction_engine.send_message(
                "alice", participant,
                f"Join community development project: {collaboration_project.project_id}",
                InteractionType.COLLABORATION_REQUEST
            )
            self.assertTrue(invitation_result)
        
        # 3. 分配任务
        tasks = [
            {"agent": "alice", "task": "project_management"},
            {"agent": "bob", "task": "resource_gathering"},
            {"agent": "charlie", "task": "construction"},
            {"agent": "diana", "task": "planning"}
        ]
        
        for task_info in tasks:
            task = {
                "task_id": f"{task_info['task']}_{task_info['agent']}",
                "task_type": task_info["task"],
                "assigned_agent": task_info["agent"],
                "progress": 0
            }
            collaboration_project.add_task(task)
        
        # 4. 模拟协作执行
        for task in collaboration_project.tasks:
            # 每个agent执行自己的任务
            agent = task["assigned_agent"]
            
            # 基于agent的社会关系和能力执行任务
            agent_relationships = self.social_network.get_relationships(agent)
            collaboration_bonus = len([r for r in agent_relationships 
                                     if r.relationship_type in [RelationshipType.FRIEND, RelationshipType.COLLEAGUE]]) * 0.1
            
            # 模拟任务执行
            task["progress"] = min(100, 50 + collaboration_bonus * 100)
        
        # 5. 验证协作结果
        collaboration_project.update_progress()
        self.assertGreater(collaboration_project.progress, 50)
        
        # 6. 协作成功后增强社会关系
        for i, agent1 in enumerate(participants):
            for agent2 in participants[i+1:]:
                self.social_network.update_relationship(
                    agent1, agent2, 
                    intimacy_change=5,  # 协作增强关系
                    trust_change=3
                )
    
    def test_machine_learning_integration(self):
        """测试机器学习与其他模块的集成"""
        # 1. 收集训练数据
        training_data = []
        
        for _ in range(50):
            # 模拟agent行为
            agent1, agent2 = random.sample(self.test_agents, 2)
            
            # 获取特征
            relationship = self.social_network.get_relationship(agent1, agent2)
            terrain_analysis = self.terrain_engine.analyze_terrain((10, 10), radius=2)
            
            features = {
                "intimacy": relationship.intimacy if relationship else 0,
                "trust": relationship.trust if relationship else 0,
                "buildable_tiles": terrain_analysis["buildable_tiles"],
                "resource_abundance": sum(terrain_analysis["total_resources"].values())
            }
            
            # 模拟行为结果
            behavior_outcome = random.choice(["cooperation", "competition", "neutral"])
            
            training_data.append((features, behavior_outcome))
        
        # 2. 训练模型
        self.ml_engine.update_behavior_model(training_data)
        
        # 3. 使用预测结果影响决策
        for agent in self.test_agents:
            for other_agent in self.test_agents:
                if agent != other_agent:
                    prediction = self.ml_engine.predict_behavior(agent, other_agent)
                    
                    # 基于预测调整交互策略
                    if prediction.prediction == "cooperation" and prediction.confidence > 0.8:
                        # 高置信度合作预测，增加互动
                        self.interaction_engine.send_message(
                            agent, other_agent,
                            "Let's work together!",
                            InteractionType.COLLABORATION_REQUEST
                        )
                    elif prediction.prediction == "competition" and prediction.confidence > 0.8:
                        # 高置信度竞争预测，保持距离
                        pass
        
        # 4. 验证预测准确性
        correct_predictions = 0
        total_predictions = 0
        
        for agent1 in self.test_agents:
            for agent2 in self.test_agents:
                if agent1 != agent2:
                    prediction = self.ml_engine.predict_behavior(agent1, agent2)
                    
                    # 模拟实际行为（简化）
                    relationship = self.social_network.get_relationship(agent1, agent2)
                    if relationship and relationship.intimacy > 70:
                        actual_behavior = "cooperation"
                    elif relationship and relationship.intimacy < 30:
                        actual_behavior = "competition"
                    else:
                        actual_behavior = "neutral"
                    
                    if prediction.prediction == actual_behavior:
                        correct_predictions += 1
                    total_predictions += 1
        
        if total_predictions > 0:
            accuracy = correct_predictions / total_predictions
            self.assertGreater(accuracy, 0.3)  # 至少30%准确率
    
    def test_complete_simulation_cycle(self):
        """测试完整的模拟周期"""
        simulation_steps = 20
        
        for step in range(simulation_steps):
            print(f"Simulation step {step + 1}/{simulation_steps}")
            
            # 1. 每个agent做决策
            for agent in self.test_agents:
                decision = self.decision_engine.make_decision(agent)
                
                # 根据决策执行行动
                if decision.get("action_type") == "social_interaction":
                    target = decision.get("target_agent")
                    if target and target in self.test_agents:
                        self.interaction_engine.send_message(
                            agent, target,
                            "Hello!",
                            InteractionType.CASUAL_CHAT
                        )
                
                elif decision.get("action_type") == "construction":
                    location = decision.get("target_location")
                    if location:
                        building_plan = self.terrain_engine.plan_building(
                            BuildingType.HOUSE,
                            owner_id=agent,
                            preferred_location=location
                        )
                        self.terrain_engine.construct_building(building_plan)
            
            # 2. 更新社会关系
            for agent1 in self.test_agents:
                for agent2 in self.test_agents:
                    if agent1 != agent2:
                        # 随机的关系变化
                        if random.random() < 0.1:  # 10%概率
                            self.social_network.update_relationship(
                                agent1, agent2,
                                intimacy_change=random.randint(-2, 2)
                            )
            
            # 3. 检查恋爱发展
            for agent1 in self.test_agents:
                for agent2 in self.test_agents:
                    if agent1 != agent2:
                        if random.random() < 0.05:  # 5%概率检查恋爱潜力
                            self.romance_engine.check_romance_potential(agent1, agent2)
            
            # 4. 地形开发
            if random.random() < 0.3:  # 30%概率进行地形开发
                agent = random.choice(self.test_agents)
                project = self.terrain_engine.create_development_project(
                    project_type="expansion",
                    target_area=[(8, 8), (12, 12)],
                    priority=self.terrain_engine.DevelopmentPriority.MEDIUM,
                    initiator_id=agent
                )
            
            # 5. 验证系统状态
            self.verify_simulation_state()
        
        # 最终验证
        final_stats = self.get_simulation_statistics()
        self.assertGreater(final_stats["total_interactions"], 0)
        self.assertGreater(final_stats["total_relationships"], 0)
    
    def verify_simulation_state(self):
        """验证模拟状态"""
        # 检查数据一致性
        for agent in self.test_agents:
            relationships = self.social_network.get_relationships(agent)
            for rel in relationships:
                self.assertIn(rel.agent_a, self.test_agents)
                self.assertIn(rel.agent_b, self.test_agents)
                self.assertGreaterEqual(rel.intimacy, 0)
                self.assertLessEqual(rel.intimacy, 100)
    
    def get_simulation_statistics(self):
        """获取模拟统计信息"""
        stats = {
            "total_relationships": 0,
            "total_interactions": 0,
            "total_buildings": len(self.terrain_engine.buildings),
            "total_projects": len(self.terrain_engine.projects)
        }
        
        for agent in self.test_agents:
            relationships = self.social_network.get_relationships(agent)
            stats["total_relationships"] += len(relationships)
        
        # 获取交互统计
        interaction_history = self.interaction_engine.get_interaction_history()
        stats["total_interactions"] = len(interaction_history)
        
        return stats


def run_system_stability_tests():
    """运行所有系统稳定性测试"""
    # 设置随机种子
    random.seed(42)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestSystemStability,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("开始运行系统稳定性和集成测试...")
    result = run_system_stability_tests()
    
    if result.wasSuccessful():
        print("\n✅ 所有系统稳定性测试通过！")
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        
        for test, traceback in result.failures:
            print(f"\n失败测试: {test}")
            print(traceback)
        
        for test, traceback in result.errors:
            print(f"\n错误测试: {test}")
            print(traceback)