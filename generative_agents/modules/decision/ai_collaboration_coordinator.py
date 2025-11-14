"""
AI协作协调器
管理多个Agent之间的协作建造和经济活动
"""

import random
import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

from modules.terrain.terrain_development import (
    TerrainDevelopmentEngine,
    BuildingType,
    ResourceType,
    DevelopmentPriority
)
from modules.decision.ai_building_decision import AIBuildingDecisionEngine
from modules.decision.ai_economy_behavior import AIEconomyBehaviorEngine


class CollaborationStatus(Enum):
    """协作状态"""
    PROPOSED = "proposed"       # 已提议
    ACCEPTED = "accepted"       # 已接受
    IN_PROGRESS = "in_progress" # 进行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 取消


@dataclass
class CollaborationTask:
    """协作任务"""
    task_id: str
    task_type: str              # "building", "resource_gathering", "trade"
    initiator: str              # 发起者
    participants: List[str]     # 参与者
    status: CollaborationStatus
    priority: DevelopmentPriority
    requirements: Dict[str, Any]  # 任务需求
    progress: float             # 进度 (0-1)
    created_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    result: Optional[Dict[str, Any]] = None


class AICollaborationCoordinator:
    """AI协作协调器"""
    
    def __init__(
        self,
        terrain_engine: TerrainDevelopmentEngine,
        building_decision_engine: AIBuildingDecisionEngine,
        economy_behavior_engine: AIEconomyBehaviorEngine
    ):
        self.terrain_engine = terrain_engine
        self.building_decision_engine = building_decision_engine
        self.economy_behavior_engine = economy_behavior_engine
        
        self.tasks: Dict[str, CollaborationTask] = {}
        self.agent_availability: Dict[str, bool] = {}
        self.agent_skills: Dict[str, Dict[str, float]] = {}
    
    def register_agent(self, agent_id: str, skills: Optional[Dict[str, float]] = None):
        """注册Agent"""
        self.agent_availability[agent_id] = True
        
        if skills is None:
            # 默认技能
            skills = {
                "construction": random.uniform(0.5, 1.0),
                "resource_gathering": random.uniform(0.5, 1.0),
                "trading": random.uniform(0.5, 1.0),
                "planning": random.uniform(0.5, 1.0),
            }
        self.agent_skills[agent_id] = skills
    
    def propose_collaborative_building_project(
        self,
        initiator: str,
        project_name: str,
        building_types: List[Tuple[BuildingType, int]],
        min_participants: int = 2
    ) -> Optional[str]:
        """
        提议协作建造项目
        
        Args:
            initiator: 发起者
            project_name: 项目名称
            building_types: 要建造的建筑列表 [(类型, 数量), ...]
            min_participants: 最少参与者数量
        
        Returns:
            任务ID，如果失败则返回None
        """
        # 计算项目需求
        total_resources = {resource: 0.0 for resource in ResourceType}
        estimated_time = 0
        
        for building_type, count in building_types:
            template = self.terrain_engine.building_templates.get(building_type, {})
            cost = template.get("construction_cost", {})
            time = template.get("construction_time", 7)
            
            for resource, amount in cost.items():
                total_resources[resource] += amount * count
            estimated_time += time * count
        
        # 创建任务
        task_id = f"collab_{len(self.tasks)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = CollaborationTask(
            task_id=task_id,
            task_type="building",
            initiator=initiator,
            participants=[initiator],
            status=CollaborationStatus.PROPOSED,
            priority=DevelopmentPriority.MEDIUM,
            requirements={
                "project_name": project_name,
                "building_types": [(bt.value, count) for bt, count in building_types],
                "total_resources": {rt.value: amt for rt, amt in total_resources.items()},
                "estimated_time": estimated_time,
                "min_participants": min_participants
            },
            progress=0.0,
            created_at=datetime.datetime.now()
        )
        
        self.tasks[task_id] = task
        return task_id
    
    def invite_agents_to_task(
        self,
        task_id: str,
        candidate_agents: List[str],
        max_invites: int = 5
    ) -> List[str]:
        """
        邀请Agent加入任务
        
        Returns:
            接受邀请的Agent列表
        """
        task = self.tasks.get(task_id)
        if not task or task.status != CollaborationStatus.PROPOSED:
            return []
        
        accepted_agents = []
        
        # 根据技能和可用性选择候选者
        scored_candidates = []
        for agent_id in candidate_agents:
            if agent_id == task.initiator:
                continue
            if not self.agent_availability.get(agent_id, False):
                continue
            
            # 计算适合度分数
            skills = self.agent_skills.get(agent_id, {})
            score = 0
            
            if task.task_type == "building":
                score = skills.get("construction", 0.5) * 0.6 + skills.get("planning", 0.5) * 0.4
            elif task.task_type == "resource_gathering":
                score = skills.get("resource_gathering", 0.5)
            elif task.task_type == "trade":
                score = skills.get("trading", 0.5)
            
            scored_candidates.append((agent_id, score))
        
        # 排序并选择最佳候选者
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        for agent_id, score in scored_candidates[:max_invites]:
            # 模拟接受概率（基于分数）
            if random.random() < 0.5 + score * 0.3:
                accepted_agents.append(agent_id)
                task.participants.append(agent_id)
                self.agent_availability[agent_id] = False  # 标记为忙碌
        
        # 检查是否满足最小参与者要求
        min_participants = task.requirements.get("min_participants", 2)
        if len(task.participants) >= min_participants:
            task.status = CollaborationStatus.ACCEPTED
        
        return accepted_agents
    
    def start_task(self, task_id: str) -> bool:
        """开始执行任务"""
        task = self.tasks.get(task_id)
        if not task or task.status != CollaborationStatus.ACCEPTED:
            return False
        
        task.status = CollaborationStatus.IN_PROGRESS
        task.started_at = datetime.datetime.now()
        
        # 如果是建造项目，创建对应的地形开发项目
        if task.task_type == "building":
            building_types_raw = task.requirements.get("building_types", [])
            building_types = [
                (BuildingType(bt), count) 
                for bt, count in building_types_raw
            ]
            
            project_id = self.building_decision_engine.create_collaborative_project(
                project_name=task.requirements.get("project_name", "协作项目"),
                description=f"由{len(task.participants)}个Agent协作的建造项目",
                agent_ids=task.participants,
                buildings_to_build=building_types
            )
            
            if project_id:
                task.requirements["terrain_project_id"] = project_id
                return True
        
        return False
    
    def update_task_progress(self, task_id: str, progress_delta: float = 0.05):
        """更新任务进度"""
        task = self.tasks.get(task_id)
        if not task or task.status != CollaborationStatus.IN_PROGRESS:
            return
        
        # 根据参与者数量加速
        efficiency = 1.0 + (len(task.participants) - 1) * 0.15
        actual_progress = progress_delta * efficiency
        
        task.progress = min(1.0, task.progress + actual_progress)
        
        # 如果完成
        if task.progress >= 1.0:
            self.complete_task(task_id)
    
    def complete_task(self, task_id: str):
        """完成任务"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = CollaborationStatus.COMPLETED
        task.progress = 1.0
        task.completed_at = datetime.datetime.now()
        
        # 释放参与者
        for agent_id in task.participants:
            self.agent_availability[agent_id] = True
        
        # 记录结果
        duration = 0
        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds() / 60
        
        task.result = {
            "status": "success",
            "duration_minutes": duration,
            "participants": task.participants,
            "efficiency": 1.0 + (len(task.participants) - 1) * 0.15
        }
    
    def propose_resource_sharing(
        self,
        from_agent: str,
        to_agent: str,
        resources: Dict[ResourceType, float],
        reason: str = "支援"
    ) -> Optional[str]:
        """
        提议资源共享
        
        Returns:
            任务ID
        """
        task_id = f"share_{len(self.tasks)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = CollaborationTask(
            task_id=task_id,
            task_type="resource_sharing",
            initiator=from_agent,
            participants=[from_agent, to_agent],
            status=CollaborationStatus.PROPOSED,
            priority=DevelopmentPriority.MEDIUM,
            requirements={
                "from": from_agent,
                "to": to_agent,
                "resources": {rt.value: amt for rt, amt in resources.items()},
                "reason": reason
            },
            progress=0.0,
            created_at=datetime.datetime.now()
        )
        
        self.tasks[task_id] = task
        
        # 自动接受并执行
        task.status = CollaborationStatus.ACCEPTED
        self._execute_resource_sharing(task)
        
        return task_id
    
    def _execute_resource_sharing(self, task: CollaborationTask):
        """执行资源共享"""
        from_agent = task.requirements["from"]
        to_agent = task.requirements["to"]
        resources_dict = task.requirements["resources"]
        
        # 转换为交易
        result = self.economy_behavior_engine.economy_engine.propose_trade(
            sender=from_agent,
            receiver=to_agent,
            offer_resources=resources_dict,
            request_resources=None,
            offer_items=None,
            request_items=None,
            offer_money=0.0,
            request_money=0.0
        )
        
        if result.get("status") == "success":
            task.status = CollaborationStatus.COMPLETED
            task.progress = 1.0
            task.completed_at = datetime.datetime.now()
            task.result = result
        else:
            task.status = CollaborationStatus.FAILED
            task.result = result
    
    def find_collaborative_opportunities(
        self,
        agent_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        寻找协作机会
        
        Returns:
            协作机会列表
        """
        opportunities = []
        
        # 1. 寻找大型建造项目机会
        stats = self.terrain_engine.get_development_statistics()
        
        # 如果发展程度低，提议建造基础设施
        if stats["development_percentage"] < 20:
            opportunities.append({
                "type": "building",
                "priority": "high",
                "description": "社区发展程度低，需要建造基础设施",
                "suggested_buildings": [
                    (BuildingType.HOUSE, 2),
                    (BuildingType.FARM, 1),
                    (BuildingType.ROAD, 3)
                ],
                "min_participants": 3
            })
        
        # 2. 寻找资源共享机会
        # 检查是否有Agent资源过剩而其他Agent缺乏
        agent_resources = {}
        for agent_id in agent_ids:
            inventory = self.economy_behavior_engine.economy_engine.agent_inventories.get(agent_id)
            if inventory:
                agent_resources[agent_id] = inventory.materials.copy()
        
        # 分析资源分布
        if len(agent_resources) >= 2:
            for resource_type in ResourceType:
                rich_agents = []
                poor_agents = []
                
                for agent_id, resources in agent_resources.items():
                    amount = resources.get(resource_type, 0)
                    if amount > 50:
                        rich_agents.append((agent_id, amount))
                    elif amount < 10:
                        poor_agents.append((agent_id, amount))
                
                if rich_agents and poor_agents:
                    opportunities.append({
                        "type": "resource_sharing",
                        "priority": "medium",
                        "description": f"{resource_type.value}分布不均，建议资源共享",
                        "from_agents": [agent_id for agent_id, _ in rich_agents],
                        "to_agents": [agent_id for agent_id, _ in poor_agents],
                        "resource_type": resource_type
                    })
        
        return opportunities
    
    def auto_coordinate_agents(self, agent_ids: List[str]):
        """
        自动协调Agent的协作活动
        """
        # 更新正在进行的任务
        for task in self.tasks.values():
            if task.status == CollaborationStatus.IN_PROGRESS:
                self.update_task_progress(task.task_id)
        
        # 检查是否需要新的协作
        available_agents = [
            agent_id for agent_id in agent_ids
            if self.agent_availability.get(agent_id, True)
        ]
        
        if len(available_agents) < 2:
            return  # 可用Agent太少
        
        # 随机决定是否发起新协作（10%概率）
        if random.random() > 0.1:
            return
        
        opportunities = self.find_collaborative_opportunities(agent_ids)
        
        if not opportunities:
            return
        
        # 选择一个机会
        opportunity = random.choice(opportunities)
        
        if opportunity["type"] == "building":
            # 随机选择一个发起者
            initiator = random.choice(available_agents)
            
            task_id = self.propose_collaborative_building_project(
                initiator=initiator,
                project_name="社区发展项目",
                building_types=opportunity["suggested_buildings"],
                min_participants=opportunity.get("min_participants", 2)
            )
            
            if task_id:
                # 邀请其他Agent
                other_agents = [a for a in available_agents if a != initiator]
                accepted = self.invite_agents_to_task(task_id, other_agents)
                
                if accepted:
                    self.start_task(task_id)
        
        elif opportunity["type"] == "resource_sharing":
            # 选择一个富裕Agent和一个贫穷Agent
            if opportunity["from_agents"] and opportunity["to_agents"]:
                from_agent = random.choice(opportunity["from_agents"])
                to_agent = random.choice(opportunity["to_agents"])
                resource_type = opportunity["resource_type"]
                
                # 共享10-20单位资源
                amount = random.uniform(10, 20)
                
                self.propose_resource_sharing(
                    from_agent=from_agent,
                    to_agent=to_agent,
                    resources={resource_type: amount},
                    reason=f"支援{resource_type.value}"
                )
    
    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务摘要"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == CollaborationStatus.COMPLETED)
        in_progress_tasks = sum(1 for t in self.tasks.values() if t.status == CollaborationStatus.IN_PROGRESS)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "success_rate": (completed_tasks / max(1, total_tasks)) * 100,
            "recent_tasks": [
                {
                    "task_id": t.task_id,
                    "type": t.task_type,
                    "status": t.status.value,
                    "participants": t.participants,
                    "progress": t.progress
                }
                for t in list(self.tasks.values())[-5:]
            ]
        }

