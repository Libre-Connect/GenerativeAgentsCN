"""
社会关系模拟核心模块
实现AI之间的复杂社会关系网络，包括恋爱、友谊、工作等多种关系类型
"""

import json
import math
import random
import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


class RelationshipType(Enum):
    """关系类型枚举"""
    STRANGER = "stranger"           # 陌生人
    ACQUAINTANCE = "acquaintance"   # 熟人
    FRIEND = "friend"               # 朋友
    CLOSE_FRIEND = "close_friend"   # 密友
    COLLEAGUE = "colleague"         # 同事
    NEIGHBOR = "neighbor"           # 邻居
    ROMANTIC_INTEREST = "romantic_interest"  # 暗恋对象
    DATING = "dating"               # 约会中
    BOYFRIEND_GIRLFRIEND = "boyfriend_girlfriend"  # 男女朋友
    ENGAGED = "engaged"             # 订婚
    MARRIED = "married"             # 已婚
    EX_PARTNER = "ex_partner"       # 前任
    ENEMY = "enemy"                 # 敌人
    FAMILY = "family"               # 家人


class RelationshipStatus(Enum):
    """关系状态"""
    DEVELOPING = "developing"       # 发展中
    STABLE = "stable"              # 稳定
    DECLINING = "declining"        # 衰退中
    CONFLICTED = "conflicted"      # 冲突中
    ENDED = "ended"                # 已结束


@dataclass
class RelationshipEvent:
    """关系事件记录"""
    timestamp: datetime.datetime
    event_type: str
    description: str
    intimacy_change: float
    participants: List[str]
    location: Optional[str] = None
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'description': self.description,
            'intimacy_change': self.intimacy_change,
            'participants': self.participants,
            'location': self.location
        }


class Relationship:
    """关系类 - 表示两个AI之间的关系"""
    
    def __init__(self, agent1_id: str, agent2_id: str, 
                 relationship_type: RelationshipType = RelationshipType.STRANGER):
        self.agent1_id = agent1_id
        self.agent2_id = agent2_id
        self.relationship_type = relationship_type
        self.status = RelationshipStatus.DEVELOPING
        
        # 亲密度系统 (0-100)
        self.intimacy_level = self._get_initial_intimacy(relationship_type)
        self.trust_level = 50.0      # 信任度 (0-100)
        self.compatibility = random.uniform(30, 90)  # 兼容性 (0-100)
        
        # 关系历史
        self.created_at = datetime.datetime.now()
        self.last_interaction = self.created_at
        self.interaction_count = 0
        self.events_history: List[RelationshipEvent] = []
        
        # 关系特征
        self.shared_interests = []
        self.conflicts = []
        self.memorable_moments = []
        
        # 恋爱关系特有属性
        self.romantic_attraction = 0.0  # 浪漫吸引力 (0-100)
        self.relationship_satisfaction = 50.0  # 关系满意度 (0-100)
        
    def _get_initial_intimacy(self, rel_type: RelationshipType) -> float:
        """根据关系类型获取初始亲密度"""
        intimacy_map = {
            RelationshipType.STRANGER: 0.0,
            RelationshipType.ACQUAINTANCE: 15.0,
            RelationshipType.FRIEND: 40.0,
            RelationshipType.CLOSE_FRIEND: 70.0,
            RelationshipType.COLLEAGUE: 25.0,
            RelationshipType.NEIGHBOR: 20.0,
            RelationshipType.ROMANTIC_INTEREST: 30.0,
            RelationshipType.DATING: 50.0,
            RelationshipType.BOYFRIEND_GIRLFRIEND: 75.0,
            RelationshipType.ENGAGED: 85.0,
            RelationshipType.MARRIED: 90.0,
            RelationshipType.EX_PARTNER: 20.0,
            RelationshipType.ENEMY: 5.0,
            RelationshipType.FAMILY: 80.0,
        }
        return intimacy_map.get(rel_type, 0.0)
    
    def update_intimacy(self, change: float, reason: str = ""):
        """更新亲密度"""
        old_intimacy = self.intimacy_level
        self.intimacy_level = max(0, min(100, self.intimacy_level + change))
        
        # 记录事件
        event = RelationshipEvent(
            timestamp=datetime.datetime.now(),
            event_type="intimacy_change",
            description=f"亲密度变化: {old_intimacy:.1f} -> {self.intimacy_level:.1f} ({reason})",
            intimacy_change=change,
            participants=[self.agent1_id, self.agent2_id]
        )
        self.events_history.append(event)
        
        # 检查是否需要升级关系类型
        self._check_relationship_evolution()
    
    def _check_relationship_evolution(self):
        """检查关系是否需要进化"""
        current_intimacy = self.intimacy_level
        
        # 关系升级逻辑
        if self.relationship_type == RelationshipType.STRANGER and current_intimacy >= 15:
            self._evolve_relationship(RelationshipType.ACQUAINTANCE)
        elif self.relationship_type == RelationshipType.ACQUAINTANCE and current_intimacy >= 40:
            self._evolve_relationship(RelationshipType.FRIEND)
        elif self.relationship_type == RelationshipType.FRIEND and current_intimacy >= 70:
            self._evolve_relationship(RelationshipType.CLOSE_FRIEND)
        
        # 恋爱关系升级
        elif (self.relationship_type == RelationshipType.ROMANTIC_INTEREST and 
              current_intimacy >= 50 and self.romantic_attraction >= 60):
            self._evolve_relationship(RelationshipType.DATING)
        elif (self.relationship_type == RelationshipType.DATING and 
              current_intimacy >= 75 and self.relationship_satisfaction >= 70):
            self._evolve_relationship(RelationshipType.BOYFRIEND_GIRLFRIEND)
        elif (self.relationship_type == RelationshipType.BOYFRIEND_GIRLFRIEND and 
              current_intimacy >= 85 and self.relationship_satisfaction >= 80):
            self._evolve_relationship(RelationshipType.ENGAGED)
        elif (self.relationship_type == RelationshipType.ENGAGED and 
              current_intimacy >= 90 and self.relationship_satisfaction >= 85):
            self._evolve_relationship(RelationshipType.MARRIED)
        
        # 关系降级逻辑
        elif current_intimacy < 10 and self.relationship_type != RelationshipType.ENEMY:
            if self.relationship_type in [RelationshipType.DATING, RelationshipType.BOYFRIEND_GIRLFRIEND,
                                        RelationshipType.ENGAGED]:
                self._evolve_relationship(RelationshipType.EX_PARTNER)
            else:
                self._evolve_relationship(RelationshipType.STRANGER)
    
    def _evolve_relationship(self, new_type: RelationshipType):
        """关系类型进化"""
        old_type = self.relationship_type
        self.relationship_type = new_type
        
        event = RelationshipEvent(
            timestamp=datetime.datetime.now(),
            event_type="relationship_evolution",
            description=f"关系升级: {old_type.value} -> {new_type.value}",
            intimacy_change=0,
            participants=[self.agent1_id, self.agent2_id]
        )
        self.events_history.append(event)
    
    def add_interaction(self, interaction_type: str, description: str, 
                       intimacy_change: float = 0, location: str = None):
        """添加互动记录"""
        self.interaction_count += 1
        self.last_interaction = datetime.datetime.now()
        
        if intimacy_change != 0:
            self.update_intimacy(intimacy_change, f"{interaction_type}: {description}")
        
        event = RelationshipEvent(
            timestamp=self.last_interaction,
            event_type=interaction_type,
            description=description,
            intimacy_change=intimacy_change,
            participants=[self.agent1_id, self.agent2_id],
            location=location
        )
        self.events_history.append(event)
    
    def get_relationship_strength(self) -> float:
        """计算关系强度 (综合指标)"""
        # 综合亲密度、信任度、兼容性和互动频率
        interaction_factor = min(1.0, self.interaction_count / 50.0)
        time_factor = max(0.1, 1.0 - (datetime.datetime.now() - self.last_interaction).days / 365.0)
        
        strength = (
            self.intimacy_level * 0.4 +
            self.trust_level * 0.3 +
            self.compatibility * 0.2 +
            interaction_factor * 50 * 0.1
        ) * time_factor
        
        return min(100.0, strength)
    
    def is_romantic(self) -> bool:
        """判断是否为恋爱关系"""
        romantic_types = {
            RelationshipType.ROMANTIC_INTEREST,
            RelationshipType.DATING,
            RelationshipType.BOYFRIEND_GIRLFRIEND,
            RelationshipType.ENGAGED,
            RelationshipType.MARRIED
        }
        return self.relationship_type in romantic_types
    
    def can_develop_romance(self) -> bool:
        """判断是否可以发展恋爱关系"""
        if self.is_romantic() or self.relationship_type == RelationshipType.EX_PARTNER:
            return False
        return (self.intimacy_level >= 30 and 
                self.trust_level >= 40 and 
                self.compatibility >= 50)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'agent1_id': self.agent1_id,
            'agent2_id': self.agent2_id,
            'relationship_type': self.relationship_type.value,
            'status': self.status.value,
            'intimacy_level': self.intimacy_level,
            'trust_level': self.trust_level,
            'compatibility': self.compatibility,
            'romantic_attraction': self.romantic_attraction,
            'relationship_satisfaction': self.relationship_satisfaction,
            'created_at': self.created_at.isoformat(),
            'last_interaction': self.last_interaction.isoformat(),
            'interaction_count': self.interaction_count,
            'shared_interests': self.shared_interests,
            'conflicts': self.conflicts,
            'memorable_moments': self.memorable_moments,
            'events_history': [event.to_dict() for event in self.events_history[-10:]]  # 只保存最近10个事件
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建关系对象"""
        rel = cls(data['agent1_id'], data['agent2_id'])
        rel.relationship_type = RelationshipType(data['relationship_type'])
        rel.status = RelationshipStatus(data['status'])
        rel.intimacy_level = data['intimacy_level']
        rel.trust_level = data['trust_level']
        rel.compatibility = data['compatibility']
        rel.romantic_attraction = data.get('romantic_attraction', 0.0)
        rel.relationship_satisfaction = data.get('relationship_satisfaction', 50.0)
        rel.created_at = datetime.datetime.fromisoformat(data['created_at'])
        rel.last_interaction = datetime.datetime.fromisoformat(data['last_interaction'])
        rel.interaction_count = data['interaction_count']
        rel.shared_interests = data.get('shared_interests', [])
        rel.conflicts = data.get('conflicts', [])
        rel.memorable_moments = data.get('memorable_moments', [])
        return rel


class SocialNetwork:
    """社交网络管理器 - 管理所有AI之间的关系"""
    
    def __init__(self):
        self.relationships: Dict[Tuple[str, str], Relationship] = {}
        self.agents: Dict[str, dict] = {}  # 存储agent基本信息
    
    def _get_relationship_key(self, agent1_id: str, agent2_id: str) -> Tuple[str, str]:
        """获取关系键值（确保顺序一致）"""
        return tuple(sorted([agent1_id, agent2_id]))
    
    def add_agent(self, agent_id: str, agent_info: dict):
        """添加agent到社交网络"""
        self.agents[agent_id] = agent_info
    
    def get_relationship(self, agent1_id: str, agent2_id: str) -> Optional[Relationship]:
        """获取两个agent之间的关系"""
        key = self._get_relationship_key(agent1_id, agent2_id)
        return self.relationships.get(key)
    
    def create_relationship(self, agent1_id: str, agent2_id: str, 
                          rel_type: RelationshipType = RelationshipType.STRANGER) -> Relationship:
        """创建新的关系"""
        key = self._get_relationship_key(agent1_id, agent2_id)
        if key in self.relationships:
            return self.relationships[key]
        
        relationship = Relationship(agent1_id, agent2_id, rel_type)
        self.relationships[key] = relationship
        return relationship
    
    def get_agent_relationships(self, agent_id: str) -> List[Relationship]:
        """获取某个agent的所有关系"""
        relationships = []
        for rel in self.relationships.values():
            if agent_id in [rel.agent1_id, rel.agent2_id]:
                relationships.append(rel)
        return relationships
    
    def get_relationships_by_type(self, agent_id: str, rel_type: RelationshipType) -> List[Relationship]:
        """获取某个agent的特定类型关系"""
        return [rel for rel in self.get_agent_relationships(agent_id) 
                if rel.relationship_type == rel_type]
    
    def find_potential_partners(self, agent_id: str) -> List[str]:
        """寻找潜在的恋爱对象"""
        potential_partners = []
        agent_relationships = self.get_agent_relationships(agent_id)
        
        for other_agent_id in self.agents.keys():
            if other_agent_id == agent_id:
                continue
                
            # 检查是否已有关系
            existing_rel = self.get_relationship(agent_id, other_agent_id)
            if existing_rel and existing_rel.can_develop_romance():
                potential_partners.append(other_agent_id)
            elif not existing_rel:
                # 创建初始关系并检查兼容性
                temp_rel = Relationship(agent_id, other_agent_id)
                if temp_rel.compatibility >= 60:  # 兼容性阈值
                    potential_partners.append(other_agent_id)
        
        return potential_partners
    
    def simulate_relationship_decay(self):
        """模拟关系衰退（时间流逝的影响）"""
        current_time = datetime.datetime.now()
        
        for relationship in self.relationships.values():
            days_since_interaction = (current_time - relationship.last_interaction).days
            
            if days_since_interaction > 7:  # 超过7天没有互动
                decay_rate = min(0.5, days_since_interaction * 0.01)
                relationship.update_intimacy(-decay_rate, "时间流逝导致的关系衰退")
    
    def get_network_statistics(self) -> dict:
        """获取社交网络统计信息"""
        total_relationships = len(self.relationships)
        relationship_types = {}
        
        for rel in self.relationships.values():
            rel_type = rel.relationship_type.value
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        romantic_relationships = sum(1 for rel in self.relationships.values() if rel.is_romantic())
        
        return {
            'total_agents': len(self.agents),
            'total_relationships': total_relationships,
            'romantic_relationships': romantic_relationships,
            'relationship_types': relationship_types,
            'average_intimacy': sum(rel.intimacy_level for rel in self.relationships.values()) / max(1, total_relationships)
        }
    
    def save_to_file(self, filepath: str):
        """保存社交网络到文件"""
        data = {
            'agents': self.agents,
            'relationships': {
                f"{key[0]}_{key[1]}": rel.to_dict() 
                for key, rel in self.relationships.items()
            }
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载社交网络"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.agents = data.get('agents', {})
            self.relationships = {}
            
            for key_str, rel_data in data.get('relationships', {}).items():
                agent1_id, agent2_id = key_str.split('_', 1)
                key = self._get_relationship_key(agent1_id, agent2_id)
                self.relationships[key] = Relationship.from_dict(rel_data)
                
        except FileNotFoundError:
            pass  # 文件不存在时忽略