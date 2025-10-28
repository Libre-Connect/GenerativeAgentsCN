"""
恋爱关系模拟模块
实现AI之间完整的恋爱流程：相识、约会、表白、交往、结婚等
"""

import random
import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .relationship import Relationship, RelationshipType, SocialNetwork, RelationshipEvent


class RomanceStage(Enum):
    """恋爱阶段"""
    INITIAL_ATTRACTION = "initial_attraction"    # 初次吸引
    GETTING_TO_KNOW = "getting_to_know"         # 相互了解
    DEVELOPING_FEELINGS = "developing_feelings"   # 产生感情
    CONFESSION_READY = "confession_ready"        # 准备表白
    DATING = "dating"                           # 约会阶段
    RELATIONSHIP = "relationship"               # 正式交往
    ENGAGEMENT = "engagement"                   # 订婚
    MARRIAGE = "marriage"                       # 结婚


class DateType(Enum):
    """约会类型"""
    COFFEE_DATE = "coffee_date"                 # 咖啡约会
    DINNER_DATE = "dinner_date"                 # 晚餐约会
    MOVIE_DATE = "movie_date"                   # 看电影
    WALK_DATE = "walk_date"                     # 散步约会
    ACTIVITY_DATE = "activity_date"             # 活动约会
    ROMANTIC_DATE = "romantic_date"             # 浪漫约会
    GROUP_DATE = "group_date"                   # 群体约会


@dataclass
class RomanceEvent:
    """恋爱事件"""
    event_type: str
    description: str
    success_rate: float
    intimacy_bonus: float
    attraction_bonus: float
    satisfaction_bonus: float
    requirements: Dict[str, float]  # 触发条件


class RomanceEngine:
    """恋爱引擎 - 处理恋爱相关的逻辑"""
    
    def __init__(self, social_network: SocialNetwork):
        self.social_network = social_network
        self.romance_events = self._initialize_romance_events()
        self.date_activities = self._initialize_date_activities()
    
    def _initialize_romance_events(self) -> Dict[str, RomanceEvent]:
        """初始化恋爱事件"""
        return {
            "first_meeting": RomanceEvent(
                event_type="first_meeting",
                description="初次相遇",
                success_rate=0.8,
                intimacy_bonus=5.0,
                attraction_bonus=random.uniform(10, 30),
                satisfaction_bonus=0,
                requirements={}
            ),
            "casual_chat": RomanceEvent(
                event_type="casual_chat",
                description="随意聊天",
                success_rate=0.9,
                intimacy_bonus=2.0,
                attraction_bonus=1.0,
                satisfaction_bonus=1.0,
                requirements={"intimacy": 10}
            ),
            "deep_conversation": RomanceEvent(
                event_type="deep_conversation",
                description="深入交谈",
                success_rate=0.7,
                intimacy_bonus=8.0,
                attraction_bonus=5.0,
                satisfaction_bonus=3.0,
                requirements={"intimacy": 25, "trust": 30}
            ),
            "confession": RomanceEvent(
                event_type="confession",
                description="表白",
                success_rate=0.6,
                intimacy_bonus=15.0,
                attraction_bonus=10.0,
                satisfaction_bonus=20.0,
                requirements={"intimacy": 40, "attraction": 50, "trust": 40}
            ),
            "first_kiss": RomanceEvent(
                event_type="first_kiss",
                description="初吻",
                success_rate=0.8,
                intimacy_bonus=20.0,
                attraction_bonus=15.0,
                satisfaction_bonus=25.0,
                requirements={"intimacy": 60, "attraction": 60, "relationship_type": "dating"}
            ),
            "proposal": RomanceEvent(
                event_type="proposal",
                description="求婚",
                success_rate=0.7,
                intimacy_bonus=25.0,
                attraction_bonus=5.0,
                satisfaction_bonus=30.0,
                requirements={"intimacy": 80, "satisfaction": 75, "relationship_type": "boyfriend_girlfriend"}
            ),
            "wedding": RomanceEvent(
                event_type="wedding",
                description="婚礼",
                success_rate=0.95,
                intimacy_bonus=30.0,
                attraction_bonus=10.0,
                satisfaction_bonus=40.0,
                requirements={"relationship_type": "engaged"}
            )
        }
    
    def _initialize_date_activities(self) -> Dict[DateType, dict]:
        """初始化约会活动"""
        return {
            DateType.COFFEE_DATE: {
                "name": "咖啡约会",
                "intimacy_bonus": 3.0,
                "satisfaction_bonus": 2.0,
                "success_rate": 0.85,
                "duration": 2,  # 小时
                "cost": "low",
                "requirements": {"intimacy": 15}
            },
            DateType.DINNER_DATE: {
                "name": "晚餐约会",
                "intimacy_bonus": 5.0,
                "satisfaction_bonus": 4.0,
                "success_rate": 0.8,
                "duration": 3,
                "cost": "medium",
                "requirements": {"intimacy": 25}
            },
            DateType.MOVIE_DATE: {
                "name": "电影约会",
                "intimacy_bonus": 4.0,
                "satisfaction_bonus": 3.0,
                "success_rate": 0.9,
                "duration": 3,
                "cost": "medium",
                "requirements": {"intimacy": 20}
            },
            DateType.WALK_DATE: {
                "name": "散步约会",
                "intimacy_bonus": 6.0,
                "satisfaction_bonus": 5.0,
                "success_rate": 0.75,
                "duration": 2,
                "cost": "free",
                "requirements": {"intimacy": 30, "trust": 40}
            },
            DateType.ROMANTIC_DATE: {
                "name": "浪漫约会",
                "intimacy_bonus": 10.0,
                "satisfaction_bonus": 8.0,
                "success_rate": 0.7,
                "duration": 4,
                "cost": "high",
                "requirements": {"intimacy": 50, "attraction": 60}
            }
        }
    
    def check_romance_potential(self, agent1_id: str, agent2_id: str) -> float:
        """检查两个AI的恋爱潜力"""
        relationship = self.social_network.get_relationship(agent1_id, agent2_id)
        if not relationship:
            # 创建临时关系来评估潜力
            temp_rel = Relationship(agent1_id, agent2_id)
            compatibility = temp_rel.compatibility
        else:
            compatibility = relationship.compatibility
            
        # 基于兼容性、当前关系状态等因素计算潜力
        potential = compatibility
        
        if relationship:
            if relationship.is_romantic():
                potential += 20  # 已有恋爱关系加分
            elif relationship.relationship_type == RelationshipType.FRIEND:
                potential += 10  # 朋友关系有一定加分
            elif relationship.relationship_type == RelationshipType.EX_PARTNER:
                potential -= 30  # 前任关系减分
        
        return max(0, min(100, potential))
    
    def initiate_romance(self, agent1_id: str, agent2_id: str) -> bool:
        """发起恋爱关系"""
        potential = self.check_romance_potential(agent1_id, agent2_id)
        
        if potential < 50:  # 潜力不足
            return False
        
        relationship = self.social_network.get_relationship(agent1_id, agent2_id)
        if not relationship:
            relationship = self.social_network.create_relationship(agent1_id, agent2_id)
        
        # 触发初次相遇事件
        success = self._trigger_romance_event(relationship, "first_meeting")
        
        if success and relationship.romantic_attraction >= 30:
            relationship.relationship_type = RelationshipType.ROMANTIC_INTEREST
            relationship.add_interaction(
                "romance_initiation",
                f"{agent1_id} 对 {agent2_id} 产生了好感",
                intimacy_change=5.0
            )
            return True
        
        return False
    
    def _trigger_romance_event(self, relationship: Relationship, event_type: str) -> bool:
        """触发恋爱事件"""
        if event_type not in self.romance_events:
            return False
        
        event = self.romance_events[event_type]
        
        # 检查触发条件
        if not self._check_event_requirements(relationship, event.requirements):
            return False
        
        # 计算成功率
        success_rate = event.success_rate
        
        # 基于兼容性调整成功率
        compatibility_factor = relationship.compatibility / 100.0
        success_rate *= (0.5 + 0.5 * compatibility_factor)
        
        # 随机判断是否成功
        if random.random() > success_rate:
            return False
        
        # 应用事件效果
        relationship.update_intimacy(event.intimacy_bonus, f"恋爱事件: {event.description}")
        relationship.romantic_attraction += event.attraction_bonus
        relationship.relationship_satisfaction += event.satisfaction_bonus
        
        # 限制数值范围
        relationship.romantic_attraction = max(0, min(100, relationship.romantic_attraction))
        relationship.relationship_satisfaction = max(0, min(100, relationship.relationship_satisfaction))
        
        # 记录事件
        relationship.add_interaction(
            event_type,
            event.description,
            intimacy_change=0  # 已经在上面更新过了
        )
        
        return True
    
    def _check_event_requirements(self, relationship: Relationship, requirements: Dict[str, float]) -> bool:
        """检查事件触发条件"""
        for req_type, req_value in requirements.items():
            if req_type == "intimacy" and relationship.intimacy_level < req_value:
                return False
            elif req_type == "trust" and relationship.trust_level < req_value:
                return False
            elif req_type == "attraction" and relationship.romantic_attraction < req_value:
                return False
            elif req_type == "satisfaction" and relationship.relationship_satisfaction < req_value:
                return False
            elif req_type == "relationship_type" and relationship.relationship_type.value != req_value:
                return False
        
        return True
    
    def plan_date(self, agent1_id: str, agent2_id: str, date_type: DateType = None) -> Optional[dict]:
        """规划约会"""
        relationship = self.social_network.get_relationship(agent1_id, agent2_id)
        if not relationship or not relationship.is_romantic():
            return None
        
        # 如果没有指定约会类型，自动选择合适的
        if date_type is None:
            date_type = self._suggest_date_type(relationship)
        
        if date_type not in self.date_activities:
            return None
        
        activity = self.date_activities[date_type]
        
        # 检查约会条件
        if not self._check_event_requirements(relationship, activity["requirements"]):
            return None
        
        # 创建约会计划
        date_plan = {
            "type": date_type.value,
            "name": activity["name"],
            "participants": [agent1_id, agent2_id],
            "planned_time": datetime.datetime.now() + datetime.timedelta(hours=random.randint(1, 24)),
            "duration": activity["duration"],
            "cost": activity["cost"],
            "expected_intimacy_bonus": activity["intimacy_bonus"],
            "expected_satisfaction_bonus": activity["satisfaction_bonus"],
            "success_rate": activity["success_rate"]
        }
        
        return date_plan
    
    def execute_date(self, date_plan: dict) -> bool:
        """执行约会"""
        agent1_id, agent2_id = date_plan["participants"]
        relationship = self.social_network.get_relationship(agent1_id, agent2_id)
        
        if not relationship:
            return False
        
        date_type = DateType(date_plan["type"])
        activity = self.date_activities[date_type]
        
        # 计算约会成功率
        base_success_rate = activity["success_rate"]
        compatibility_factor = relationship.compatibility / 100.0
        attraction_factor = relationship.romantic_attraction / 100.0
        
        final_success_rate = base_success_rate * (0.3 + 0.4 * compatibility_factor + 0.3 * attraction_factor)
        
        success = random.random() < final_success_rate
        
        if success:
            # 约会成功
            intimacy_bonus = activity["intimacy_bonus"] * random.uniform(0.8, 1.2)
            satisfaction_bonus = activity["satisfaction_bonus"] * random.uniform(0.8, 1.2)
            
            relationship.update_intimacy(intimacy_bonus, f"成功的{activity['name']}")
            relationship.relationship_satisfaction += satisfaction_bonus
            relationship.romantic_attraction += random.uniform(1, 3)
            
            description = f"成功的{activity['name']} - 两人度过了愉快的时光"
        else:
            # 约会失败
            intimacy_penalty = activity["intimacy_bonus"] * -0.3
            satisfaction_penalty = activity["satisfaction_bonus"] * -0.5
            
            relationship.update_intimacy(intimacy_penalty, f"失败的{activity['name']}")
            relationship.relationship_satisfaction += satisfaction_penalty
            
            description = f"失败的{activity['name']} - 约会没有达到预期效果"
        
        # 限制数值范围
        relationship.romantic_attraction = max(0, min(100, relationship.romantic_attraction))
        relationship.relationship_satisfaction = max(0, min(100, relationship.relationship_satisfaction))
        
        # 记录约会事件
        relationship.add_interaction(
            "date",
            description,
            intimacy_change=0  # 已经在update_intimacy中处理
        )
        
        return success
    
    def _suggest_date_type(self, relationship: Relationship) -> DateType:
        """根据关系状态建议约会类型"""
        intimacy = relationship.intimacy_level
        attraction = relationship.romantic_attraction
        
        if intimacy < 30:
            return DateType.COFFEE_DATE
        elif intimacy < 50:
            return random.choice([DateType.COFFEE_DATE, DateType.MOVIE_DATE, DateType.DINNER_DATE])
        elif intimacy < 70:
            return random.choice([DateType.DINNER_DATE, DateType.WALK_DATE, DateType.ACTIVITY_DATE])
        else:
            return random.choice([DateType.ROMANTIC_DATE, DateType.DINNER_DATE, DateType.ACTIVITY_DATE])
    
    def attempt_confession(self, confessor_id: str, target_id: str) -> bool:
        """尝试表白"""
        relationship = self.social_network.get_relationship(confessor_id, target_id)
        if not relationship:
            return False
        
        # 检查表白条件
        if (relationship.intimacy_level < 40 or 
            relationship.romantic_attraction < 50 or 
            relationship.trust_level < 40):
            return False
        
        success = self._trigger_romance_event(relationship, "confession")
        
        if success:
            relationship.relationship_type = RelationshipType.DATING
            relationship.add_interaction(
                "confession_success",
                f"{confessor_id} 向 {target_id} 表白成功",
                intimacy_change=0
            )
        else:
            relationship.add_interaction(
                "confession_failed",
                f"{confessor_id} 向 {target_id} 表白被拒绝",
                intimacy_change=-10.0
            )
        
        return success
    
    def attempt_proposal(self, proposer_id: str, target_id: str) -> bool:
        """尝试求婚"""
        relationship = self.social_network.get_relationship(proposer_id, target_id)
        if not relationship or relationship.relationship_type != RelationshipType.BOYFRIEND_GIRLFRIEND:
            return False
        
        success = self._trigger_romance_event(relationship, "proposal")
        
        if success:
            relationship.relationship_type = RelationshipType.ENGAGED
            relationship.add_interaction(
                "proposal_success",
                f"{proposer_id} 向 {target_id} 求婚成功",
                intimacy_change=0
            )
        else:
            relationship.add_interaction(
                "proposal_failed",
                f"{proposer_id} 向 {target_id} 求婚被拒绝",
                intimacy_change=-15.0
            )
        
        return success
    
    def plan_wedding(self, agent1_id: str, agent2_id: str) -> Optional[dict]:
        """规划婚礼"""
        relationship = self.social_network.get_relationship(agent1_id, agent2_id)
        if not relationship or relationship.relationship_type != RelationshipType.ENGAGED:
            return None
        
        wedding_plan = {
            "participants": [agent1_id, agent2_id],
            "planned_date": datetime.datetime.now() + datetime.timedelta(days=random.randint(30, 365)),
            "venue": random.choice(["教堂", "海滩", "花园", "酒店", "户外"]),
            "guest_count": random.randint(20, 100),
            "style": random.choice(["传统", "现代", "简约", "奢华", "主题"])
        }
        
        return wedding_plan
    
    def execute_wedding(self, wedding_plan: dict) -> bool:
        """执行婚礼"""
        agent1_id, agent2_id = wedding_plan["participants"]
        relationship = self.social_network.get_relationship(agent1_id, agent2_id)
        
        if not relationship or relationship.relationship_type != RelationshipType.ENGAGED:
            return False
        
        success = self._trigger_romance_event(relationship, "wedding")
        
        if success:
            relationship.relationship_type = RelationshipType.MARRIED
            relationship.add_interaction(
                "wedding",
                f"{agent1_id} 和 {target_id} 举行了婚礼",
                intimacy_change=0
            )
        
        return success
    
    def handle_relationship_conflict(self, agent1_id: str, agent2_id: str, conflict_type: str) -> dict:
        """处理关系冲突"""
        relationship = self.social_network.get_relationship(agent1_id, agent2_id)
        if not relationship:
            return {"resolved": False, "reason": "关系不存在"}
        
        # 冲突严重程度
        conflict_severity = random.uniform(0.3, 1.0)
        
        # 基于关系强度和兼容性计算解决概率
        resolution_chance = (
            relationship.trust_level * 0.4 +
            relationship.compatibility * 0.3 +
            relationship.relationship_satisfaction * 0.3
        ) / 100.0
        
        # 调整解决概率
        resolution_chance *= (1.0 - conflict_severity * 0.5)
        
        resolved = random.random() < resolution_chance
        
        if resolved:
            # 冲突解决
            intimacy_change = -conflict_severity * 5  # 轻微损失
            satisfaction_change = conflict_severity * 2  # 解决后的满足感
            
            relationship.update_intimacy(intimacy_change, f"解决了{conflict_type}冲突")
            relationship.relationship_satisfaction += satisfaction_change
            
            result = {
                "resolved": True,
                "method": random.choice(["沟通", "妥协", "道歉", "理解"]),
                "intimacy_change": intimacy_change,
                "satisfaction_change": satisfaction_change
            }
        else:
            # 冲突未解决
            intimacy_change = -conflict_severity * 15
            satisfaction_change = -conflict_severity * 10
            
            relationship.update_intimacy(intimacy_change, f"未解决的{conflict_type}冲突")
            relationship.relationship_satisfaction += satisfaction_change
            relationship.conflicts.append({
                "type": conflict_type,
                "timestamp": datetime.datetime.now().isoformat(),
                "severity": conflict_severity,
                "resolved": False
            })
            
            result = {
                "resolved": False,
                "reason": random.choice(["沟通不畅", "价值观差异", "情绪激动", "误解加深"]),
                "intimacy_change": intimacy_change,
                "satisfaction_change": satisfaction_change
            }
        
        # 限制数值范围
        relationship.relationship_satisfaction = max(0, min(100, relationship.relationship_satisfaction))
        
        # 记录冲突事件
        relationship.add_interaction(
            "conflict",
            f"{conflict_type}冲突 - {'已解决' if resolved else '未解决'}",
            intimacy_change=0
        )
        
        return result
    
    def get_romance_suggestions(self, agent_id: str) -> List[dict]:
        """获取恋爱建议"""
        suggestions = []
        relationships = self.social_network.get_agent_relationships(agent_id)
        
        for rel in relationships:
            other_agent = rel.agent2_id if rel.agent1_id == agent_id else rel.agent1_id
            
            if rel.is_romantic():
                # 为现有恋爱关系提供建议
                if rel.relationship_type == RelationshipType.ROMANTIC_INTEREST:
                    if rel.intimacy_level >= 40 and rel.romantic_attraction >= 50:
                        suggestions.append({
                            "type": "confession",
                            "target": other_agent,
                            "description": f"可以考虑向{other_agent}表白",
                            "success_probability": 0.6
                        })
                
                elif rel.relationship_type == RelationshipType.DATING:
                    # 建议约会活动
                    suggested_date = self._suggest_date_type(rel)
                    suggestions.append({
                        "type": "date",
                        "target": other_agent,
                        "description": f"建议与{other_agent}进行{self.date_activities[suggested_date]['name']}",
                        "date_type": suggested_date.value
                    })
                
                elif rel.relationship_type == RelationshipType.BOYFRIEND_GIRLFRIEND:
                    if rel.intimacy_level >= 80 and rel.relationship_satisfaction >= 75:
                        suggestions.append({
                            "type": "proposal",
                            "target": other_agent,
                            "description": f"可以考虑向{other_agent}求婚",
                            "success_probability": 0.7
                        })
            
            elif rel.can_develop_romance():
                # 为可能发展恋爱关系的建议
                suggestions.append({
                    "type": "romance_initiation",
                    "target": other_agent,
                    "description": f"可以尝试与{other_agent}发展恋爱关系",
                    "romance_potential": self.check_romance_potential(agent_id, other_agent)
                })
        
        return suggestions