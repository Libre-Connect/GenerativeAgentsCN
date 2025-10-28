"""
社会关系测试模块
验证关系发展逻辑和恋爱流程
"""

import unittest
import json
import datetime
import tempfile
import os
from typing import Dict, List, Any

# 导入需要测试的模块
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules', 'social'))

from relationship import (
    RelationshipType, RelationshipStatus, Relationship, SocialNetwork
)
from romance import (
    RomanceStage, DateType, RomanceEngine
)


class TestRelationship(unittest.TestCase):
    """关系类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.relationship = Relationship(
            agent1_id="alice",
            agent2_id="bob",
            relationship_type=RelationshipType.STRANGER
        )
    
    def test_relationship_initialization(self):
        """测试关系初始化"""
        self.assertEqual(self.relationship.agent1_id, "alice")
        self.assertEqual(self.relationship.agent2_id, "bob")
        self.assertEqual(self.relationship.relationship_type, RelationshipType.STRANGER)
        self.assertEqual(self.relationship.intimacy, 0)
        self.assertEqual(self.relationship.trust, 50)
        self.assertEqual(self.relationship.compatibility, 50)
        self.assertEqual(self.relationship.status, RelationshipStatus.ACTIVE)
    
    def test_intimacy_increase(self):
        """测试亲密度增加"""
        initial_intimacy = self.relationship.intimacy
        self.relationship.increase_intimacy(20)
        self.assertEqual(self.relationship.intimacy, initial_intimacy + 20)
        
        # 测试上限
        self.relationship.increase_intimacy(100)
        self.assertEqual(self.relationship.intimacy, 100)
    
    def test_intimacy_decrease(self):
        """测试亲密度减少"""
        self.relationship.intimacy = 50
        self.relationship.decrease_intimacy(20)
        self.assertEqual(self.relationship.intimacy, 30)
        
        # 测试下限
        self.relationship.decrease_intimacy(100)
        self.assertEqual(self.relationship.intimacy, 0)
    
    def test_relationship_evolution(self):
        """测试关系进化"""
        # 陌生人 -> 朋友
        self.relationship.intimacy = 30
        self.relationship.trust = 60
        self.relationship.evolve_relationship()
        self.assertEqual(self.relationship.relationship_type, RelationshipType.FRIEND)
        
        # 朋友 -> 好友
        self.relationship.intimacy = 60
        self.relationship.trust = 80
        self.relationship.evolve_relationship()
        self.assertEqual(self.relationship.relationship_type, RelationshipType.CLOSE_FRIEND)
        
        # 好友 -> 恋人（需要兼容性）
        self.relationship.intimacy = 80
        self.relationship.trust = 90
        self.relationship.compatibility = 85
        self.relationship.evolve_relationship()
        self.assertEqual(self.relationship.relationship_type, RelationshipType.ROMANTIC)
    
    def test_relationship_decay(self):
        """测试关系衰退"""
        self.relationship.relationship_type = RelationshipType.FRIEND
        self.relationship.intimacy = 40
        self.relationship.trust = 60
        
        # 模拟时间流逝
        self.relationship.last_interaction = datetime.datetime.now() - datetime.timedelta(days=10)
        self.relationship.decay_relationship()
        
        # 检查衰退效果
        self.assertLess(self.relationship.intimacy, 40)
        self.assertLess(self.relationship.trust, 60)
    
    def test_relationship_serialization(self):
        """测试关系序列化"""
        data = self.relationship.to_dict()
        
        # 验证必要字段
        self.assertIn("agent1_id", data)
        self.assertIn("agent2_id", data)
        self.assertIn("relationship_type", data)
        self.assertIn("intimacy", data)
        self.assertIn("trust", data)
        
        # 测试反序列化
        new_relationship = Relationship.from_dict(data)
        self.assertEqual(new_relationship.agent1_id, self.relationship.agent1_id)
        self.assertEqual(new_relationship.agent2_id, self.relationship.agent2_id)
        self.assertEqual(new_relationship.relationship_type, self.relationship.relationship_type)


class TestSocialNetwork(unittest.TestCase):
    """社交网络测试"""
    
    def setUp(self):
        """测试前准备"""
        self.network = SocialNetwork()
        
        # 添加测试关系
        self.network.add_relationship("alice", "bob", RelationshipType.FRIEND)
        self.network.add_relationship("alice", "charlie", RelationshipType.CLOSE_FRIEND)
        self.network.add_relationship("bob", "charlie", RelationshipType.STRANGER)
    
    def test_add_relationship(self):
        """测试添加关系"""
        self.network.add_relationship("alice", "david", RelationshipType.FRIEND)
        
        relationship = self.network.get_relationship("alice", "david")
        self.assertIsNotNone(relationship)
        self.assertEqual(relationship.relationship_type, RelationshipType.FRIEND)
    
    def test_get_relationship(self):
        """测试获取关系"""
        relationship = self.network.get_relationship("alice", "bob")
        self.assertIsNotNone(relationship)
        self.assertEqual(relationship.relationship_type, RelationshipType.FRIEND)
        
        # 测试不存在的关系
        relationship = self.network.get_relationship("alice", "unknown")
        self.assertIsNone(relationship)
    
    def test_get_agent_relationships(self):
        """测试获取agent的所有关系"""
        relationships = self.network.get_agent_relationships("alice")
        self.assertEqual(len(relationships), 2)
        
        # 验证关系对象
        partner_ids = [r.agent2_id if r.agent1_id == "alice" else r.agent1_id for r in relationships]
        self.assertIn("bob", partner_ids)
        self.assertIn("charlie", partner_ids)
    
    def test_get_relationships_by_type(self):
        """测试按类型获取关系"""
        friends = self.network.get_relationships_by_type("alice", RelationshipType.FRIEND)
        self.assertEqual(len(friends), 1)
        
        close_friends = self.network.get_relationships_by_type("alice", RelationshipType.CLOSE_FRIEND)
        self.assertEqual(len(close_friends), 1)
    
    def test_remove_relationship(self):
        """测试移除关系"""
        self.network.remove_relationship("alice", "bob")
        
        relationship = self.network.get_relationship("alice", "bob")
        self.assertIsNone(relationship)
    
    def test_update_relationship(self):
        """测试更新关系"""
        self.network.update_relationship("alice", "bob", intimacy_change=20, trust_change=10)
        
        relationship = self.network.get_relationship("alice", "bob")
        self.assertGreater(relationship.intimacy, 0)
        self.assertGreater(relationship.trust, 50)
    
    def test_simulate_decay(self):
        """测试关系衰退模拟"""
        # 设置一个关系的最后交互时间为很久以前
        relationship = self.network.get_relationship("alice", "bob")
        relationship.last_interaction = datetime.datetime.now() - datetime.timedelta(days=15)
        
        initial_intimacy = relationship.intimacy
        self.network.simulate_decay()
        
        # 验证衰退效果
        self.assertLessEqual(relationship.intimacy, initial_intimacy)
    
    def test_get_network_statistics(self):
        """测试网络统计"""
        stats = self.network.get_network_statistics()
        
        self.assertIn("total_relationships", stats)
        self.assertIn("relationship_types", stats)
        self.assertIn("average_intimacy", stats)
        self.assertEqual(stats["total_relationships"], 3)
    
    def test_save_and_load(self):
        """测试保存和加载"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # 保存
            self.network.save_to_file(temp_file)
            
            # 加载到新网络
            new_network = SocialNetwork()
            new_network.load_from_file(temp_file)
            
            # 验证数据一致性
            self.assertEqual(len(new_network.relationships), len(self.network.relationships))
            
            # 验证具体关系
            original_rel = self.network.get_relationship("alice", "bob")
            loaded_rel = new_network.get_relationship("alice", "bob")
            
            self.assertEqual(original_rel.relationship_type, loaded_rel.relationship_type)
            self.assertEqual(original_rel.intimacy, loaded_rel.intimacy)
            
        finally:
            os.unlink(temp_file)


class TestRomanceEngine(unittest.TestCase):
    """恋爱引擎测试"""
    
    def setUp(self):
        """测试前准备"""
        self.romance_engine = RomanceEngine()
        self.social_network = SocialNetwork()
        
        # 创建测试agents
        self.agent1_data = {
            "agent_id": "alice",
            "personality": {"romantic": 0.8, "outgoing": 0.7},
            "interests": ["music", "art", "travel"],
            "location": (10, 10)
        }
        
        self.agent2_data = {
            "agent_id": "bob", 
            "personality": {"romantic": 0.7, "outgoing": 0.6},
            "interests": ["music", "sports", "cooking"],
            "location": (12, 11)
        }
    
    def test_check_romance_potential(self):
        """测试恋爱潜力检查"""
        potential = self.romance_engine.check_romance_potential(
            self.agent1_data, self.agent2_data
        )
        
        self.assertIsInstance(potential, float)
        self.assertGreaterEqual(potential, 0.0)
        self.assertLessEqual(potential, 1.0)
        
        # 有共同兴趣的agents应该有更高的潜力
        self.assertGreater(potential, 0.3)  # 因为有共同兴趣"music"
    
    def test_initiate_romance(self):
        """测试发起恋爱"""
        # 先建立朋友关系
        self.social_network.add_relationship("alice", "bob", RelationshipType.FRIEND)
        relationship = self.social_network.get_relationship("alice", "bob")
        relationship.intimacy = 60
        relationship.trust = 70
        relationship.compatibility = 80
        
        result = self.romance_engine.initiate_romance(
            "alice", "bob", self.social_network
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        
        if result["success"]:
            # 验证关系类型改变
            updated_relationship = self.social_network.get_relationship("alice", "bob")
            self.assertEqual(updated_relationship.relationship_type, RelationshipType.ROMANTIC)
    
    def test_plan_date(self):
        """测试约会规划"""
        date_plan = self.romance_engine.plan_date(
            self.agent1_data, self.agent2_data, DateType.CASUAL
        )
        
        self.assertIsInstance(date_plan, dict)
        self.assertIn("date_type", date_plan)
        self.assertIn("activity", date_plan)
        self.assertIn("location", date_plan)
        self.assertIn("duration", date_plan)
        
        # 验证约会类型
        self.assertEqual(date_plan["date_type"], DateType.CASUAL)
    
    def test_execute_date(self):
        """测试执行约会"""
        date_plan = {
            "date_type": DateType.CASUAL,
            "activity": "coffee_chat",
            "location": "cafe",
            "duration": 2
        }
        
        result = self.romance_engine.execute_date(
            "alice", "bob", date_plan, self.social_network
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("intimacy_change", result)
        self.assertIn("experience_rating", result)
        
        # 验证约会结果的合理性
        self.assertGreaterEqual(result["experience_rating"], 1)
        self.assertLessEqual(result["experience_rating"], 10)
    
    def test_attempt_confession(self):
        """测试表白"""
        # 建立高亲密度关系
        self.social_network.add_relationship("alice", "bob", RelationshipType.CLOSE_FRIEND)
        relationship = self.social_network.get_relationship("alice", "bob")
        relationship.intimacy = 80
        relationship.trust = 85
        relationship.compatibility = 90
        
        result = self.romance_engine.attempt_confession(
            "alice", "bob", self.social_network
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("response", result)
        
        # 高亲密度应该有较高的成功率
        if result["success"]:
            updated_relationship = self.social_network.get_relationship("alice", "bob")
            self.assertEqual(updated_relationship.relationship_type, RelationshipType.ROMANTIC)
    
    def test_propose_marriage(self):
        """测试求婚"""
        # 建立恋爱关系
        self.social_network.add_relationship("alice", "bob", RelationshipType.ROMANTIC)
        relationship = self.social_network.get_relationship("alice", "bob")
        relationship.intimacy = 95
        relationship.trust = 95
        relationship.compatibility = 90
        
        # 添加恋爱历史
        self.romance_engine.romance_history[("alice", "bob")] = {
            "stage": RomanceStage.DATING,
            "start_date": datetime.datetime.now() - datetime.timedelta(days=100),
            "events": [{"type": "date", "date": datetime.datetime.now() - datetime.timedelta(days=50)}]
        }
        
        result = self.romance_engine.propose_marriage(
            "alice", "bob", self.social_network
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("response", result)
    
    def test_handle_relationship_conflict(self):
        """测试处理关系冲突"""
        # 建立恋爱关系
        self.social_network.add_relationship("alice", "bob", RelationshipType.ROMANTIC)
        
        conflict_data = {
            "type": "jealousy",
            "severity": 0.6,
            "description": "Alice saw Bob talking to another woman"
        }
        
        result = self.romance_engine.handle_relationship_conflict(
            "alice", "bob", conflict_data, self.social_network
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("resolution", result)
        self.assertIn("relationship_impact", result)
        
        # 验证冲突对关系的影响
        relationship = self.social_network.get_relationship("alice", "bob")
        # 冲突应该对关系产生一定影响
        self.assertIsInstance(result["relationship_impact"], dict)
    
    def test_get_romance_advice(self):
        """测试获取恋爱建议"""
        # 建立关系
        self.social_network.add_relationship("alice", "bob", RelationshipType.FRIEND)
        
        advice = self.romance_engine.get_romance_advice(
            "alice", "bob", self.social_network
        )
        
        self.assertIsInstance(advice, dict)
        self.assertIn("suggestions", advice)
        self.assertIn("next_steps", advice)
        self.assertIn("compatibility_analysis", advice)
        
        # 验证建议的合理性
        self.assertIsInstance(advice["suggestions"], list)
        self.assertGreater(len(advice["suggestions"]), 0)


class TestRomanceIntegration(unittest.TestCase):
    """恋爱系统集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.romance_engine = RomanceEngine()
        self.social_network = SocialNetwork()
        
        # 创建多个测试agents
        self.agents_data = {
            "alice": {
                "agent_id": "alice",
                "personality": {"romantic": 0.9, "outgoing": 0.8, "patience": 0.7},
                "interests": ["music", "art", "travel", "reading"],
                "location": (10, 10),
                "age": 25
            },
            "bob": {
                "agent_id": "bob",
                "personality": {"romantic": 0.8, "outgoing": 0.6, "patience": 0.8},
                "interests": ["music", "sports", "cooking", "travel"],
                "location": (12, 11),
                "age": 27
            },
            "charlie": {
                "agent_id": "charlie",
                "personality": {"romantic": 0.6, "outgoing": 0.9, "patience": 0.5},
                "interests": ["sports", "gaming", "technology"],
                "location": (15, 8),
                "age": 24
            }
        }
    
    def test_complete_romance_flow(self):
        """测试完整恋爱流程"""
        alice_data = self.agents_data["alice"]
        bob_data = self.agents_data["bob"]
        
        # 1. 检查恋爱潜力
        potential = self.romance_engine.check_romance_potential(alice_data, bob_data)
        self.assertGreater(potential, 0.5)  # 应该有较高潜力
        
        # 2. 建立初始关系
        self.social_network.add_relationship("alice", "bob", RelationshipType.STRANGER)
        
        # 3. 发展友谊
        for _ in range(5):
            self.social_network.update_relationship("alice", "bob", intimacy_change=10, trust_change=8)
        
        relationship = self.social_network.get_relationship("alice", "bob")
        relationship.evolve_relationship()
        
        # 4. 规划和执行约会
        date_plan = self.romance_engine.plan_date(alice_data, bob_data, DateType.CASUAL)
        date_result = self.romance_engine.execute_date("alice", "bob", date_plan, self.social_network)
        
        self.assertTrue(date_result["success"])
        
        # 5. 继续发展关系
        for _ in range(3):
            self.social_network.update_relationship("alice", "bob", intimacy_change=15, trust_change=10)
        
        relationship.evolve_relationship()
        
        # 6. 尝试表白
        if relationship.intimacy >= 70:
            confession_result = self.romance_engine.attempt_confession("alice", "bob", self.social_network)
            
            if confession_result["success"]:
                # 7. 恋爱阶段
                self.assertEqual(relationship.relationship_type, RelationshipType.ROMANTIC)
                
                # 8. 更多约会
                romantic_date_plan = self.romance_engine.plan_date(alice_data, bob_data, DateType.ROMANTIC)
                romantic_date_result = self.romance_engine.execute_date("alice", "bob", romantic_date_plan, self.social_network)
                
                # 9. 长期发展后考虑求婚
                for _ in range(10):
                    self.social_network.update_relationship("alice", "bob", intimacy_change=2, trust_change=1)
                
                if relationship.intimacy >= 90:
                    proposal_result = self.romance_engine.propose_marriage("alice", "bob", self.social_network)
                    
                    if proposal_result["success"]:
                        self.assertEqual(relationship.relationship_type, RelationshipType.MARRIED)
    
    def test_multiple_agents_romance_network(self):
        """测试多agent恋爱网络"""
        # 建立多个关系
        relationships = [
            ("alice", "bob"),
            ("alice", "charlie"),
            ("bob", "charlie")
        ]
        
        for agent1, agent2 in relationships:
            self.social_network.add_relationship(agent1, agent2, RelationshipType.STRANGER)
            
            # 检查恋爱潜力
            potential = self.romance_engine.check_romance_potential(
                self.agents_data[agent1], self.agents_data[agent2]
            )
            
            # 根据潜力发展关系
            if potential > 0.6:
                # 高潜力：快速发展
                for _ in range(8):
                    self.social_network.update_relationship(agent1, agent2, intimacy_change=12, trust_change=10)
            elif potential > 0.4:
                # 中等潜力：缓慢发展
                for _ in range(5):
                    self.social_network.update_relationship(agent1, agent2, intimacy_change=8, trust_change=6)
            
            # 进化关系
            relationship = self.social_network.get_relationship(agent1, agent2)
            relationship.evolve_relationship()
        
        # 检查网络状态
        stats = self.social_network.get_network_statistics()
        self.assertEqual(stats["total_relationships"], 3)
        
        # 验证不同类型的关系都存在
        relationship_types = stats["relationship_types"]
        self.assertGreater(sum(relationship_types.values()), 0)


def run_social_relationship_tests():
    """运行所有社会关系测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestRelationship,
        TestSocialNetwork,
        TestRomanceEngine,
        TestRomanceIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("开始运行社会关系测试...")
    result = run_social_relationship_tests()
    
    if result.wasSuccessful():
        print("\n✅ 所有社会关系测试通过！")
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        
        for test, traceback in result.failures:
            print(f"\n失败测试: {test}")
            print(traceback)
        
        for test, traceback in result.errors:
            print(f"\n错误测试: {test}")
            print(traceback)