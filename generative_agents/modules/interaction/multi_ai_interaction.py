"""
多AI交互协作系统
实现AI之间的社交互动、协同建设和关系驱动的特殊行为
"""

import json
import random
import datetime
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


class InteractionType(Enum):
    """交互类型"""
    GREETING = "greeting"           # 问候
    CONVERSATION = "conversation"   # 对话
    COLLABORATION = "collaboration" # 协作
    CONFLICT = "conflict"          # 冲突
    ROMANCE = "romance"            # 浪漫互动
    TRADE = "trade"                # 交易
    HELP = "help"                  # 帮助
    TEACHING = "teaching"          # 教学
    CELEBRATION = "celebration"    # 庆祝
    GOSSIP = "gossip"             # 闲聊


class CollaborationType(Enum):
    """协作类型"""
    BUILDING = "building"          # 建筑协作
    RESOURCE_GATHERING = "resource_gathering"  # 资源收集
    PLANNING = "planning"          # 规划协作
    PROBLEM_SOLVING = "problem_solving"  # 问题解决
    RESEARCH = "research"          # 研究协作
    ENTERTAINMENT = "entertainment"  # 娱乐协作
    EMERGENCY_RESPONSE = "emergency_response"  # 紧急响应


class InteractionOutcome(Enum):
    """交互结果"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    CONFLICT = "conflict"
    NEUTRAL = "neutral"


@dataclass
class InteractionMessage:
    """交互消息"""
    sender_id: str
    receiver_id: str
    message_type: InteractionType
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime.datetime
    requires_response: bool = False
    priority: int = 1  # 1-5, 5最高
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "requires_response": self.requires_response,
            "priority": self.priority
        }


@dataclass
class CollaborationProject:
    """协作项目"""
    project_id: str
    name: str
    description: str
    collaboration_type: CollaborationType
    participants: Set[str]
    leader_id: Optional[str]
    required_skills: List[str]
    required_resources: Dict[str, int]
    target_location: Optional[Tuple[int, int]]
    estimated_duration: int  # 分钟
    progress: float  # 0-1
    status: str  # "planning", "active", "paused", "completed", "cancelled"
    created_at: datetime.datetime
    deadline: Optional[datetime.datetime]
    tasks: List[Dict[str, Any]]
    
    def add_participant(self, agent_id: str):
        """添加参与者"""
        self.participants.add(agent_id)
    
    def remove_participant(self, agent_id: str):
        """移除参与者"""
        self.participants.discard(agent_id)
        if self.leader_id == agent_id:
            # 重新选择领导者
            if self.participants:
                self.leader_id = next(iter(self.participants))
            else:
                self.leader_id = None
    
    def update_progress(self, progress_delta: float):
        """更新进度"""
        self.progress = min(1.0, max(0.0, self.progress + progress_delta))
        if self.progress >= 1.0:
            self.status = "completed"
    
    def is_overdue(self) -> bool:
        """检查是否过期"""
        if not self.deadline:
            return False
        return datetime.datetime.now() > self.deadline
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """获取下一个任务"""
        for task in self.tasks:
            if not task.get("completed", False):
                return task
        return None


@dataclass
class InteractionHistory:
    """交互历史"""
    agent1_id: str
    agent2_id: str
    interactions: List[Dict[str, Any]]
    relationship_changes: List[Dict[str, Any]]
    collaboration_count: int
    conflict_count: int
    last_interaction: Optional[datetime.datetime]
    
    def add_interaction(self, interaction_type: InteractionType, outcome: InteractionOutcome, 
                       details: Dict[str, Any] = None):
        """添加交互记录"""
        interaction = {
            "type": interaction_type.value,
            "outcome": outcome.value,
            "timestamp": datetime.datetime.now().isoformat(),
            "details": details or {}
        }
        self.interactions.append(interaction)
        self.last_interaction = datetime.datetime.now()
        
        # 更新统计
        if interaction_type == InteractionType.COLLABORATION:
            self.collaboration_count += 1
        elif interaction_type == InteractionType.CONFLICT:
            self.conflict_count += 1
    
    def get_interaction_frequency(self, days: int = 7) -> float:
        """获取交互频率"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        recent_interactions = [
            i for i in self.interactions 
            if datetime.datetime.fromisoformat(i["timestamp"]) > cutoff_date
        ]
        return len(recent_interactions) / days
    
    def get_relationship_trend(self) -> str:
        """获取关系趋势"""
        if len(self.relationship_changes) < 2:
            return "stable"
        
        recent_changes = self.relationship_changes[-5:]  # 最近5次变化
        positive_changes = sum(1 for change in recent_changes if change.get("intimacy_delta", 0) > 0)
        negative_changes = sum(1 for change in recent_changes if change.get("intimacy_delta", 0) < 0)
        
        if positive_changes > negative_changes:
            return "improving"
        elif negative_changes > positive_changes:
            return "declining"
        else:
            return "stable"


class InteractionRule:
    """交互规则"""
    
    def __init__(self, rule_id: str, name: str, condition: Callable, action: Callable):
        self.rule_id = rule_id
        self.name = name
        self.condition = condition  # 触发条件
        self.action = action        # 执行动作
        self.priority = 1
        self.enabled = True
    
    def check_condition(self, context: Dict[str, Any]) -> bool:
        """检查触发条件"""
        if not self.enabled:
            return False
        return self.condition(context)
    
    def execute_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行动作"""
        return self.action(context)


class CommunicationProtocol:
    """通信协议"""
    
    def __init__(self):
        self.message_queue: Dict[str, List[InteractionMessage]] = {}
        self.broadcast_messages: List[InteractionMessage] = []
        self.message_handlers: Dict[InteractionType, Callable] = {}
        
    def register_handler(self, message_type: InteractionType, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
    
    def send_message(self, message: InteractionMessage):
        """发送消息"""
        if message.receiver_id not in self.message_queue:
            self.message_queue[message.receiver_id] = []
        
        self.message_queue[message.receiver_id].append(message)
        
        # 按优先级排序
        self.message_queue[message.receiver_id].sort(key=lambda m: m.priority, reverse=True)
    
    def broadcast_message(self, message: InteractionMessage):
        """广播消息"""
        self.broadcast_messages.append(message)
    
    def get_messages(self, agent_id: str, max_count: int = 10) -> List[InteractionMessage]:
        """获取消息"""
        messages = []
        
        # 获取直接消息
        if agent_id in self.message_queue:
            messages.extend(self.message_queue[agent_id][:max_count])
            self.message_queue[agent_id] = self.message_queue[agent_id][max_count:]
        
        # 获取广播消息
        for broadcast in self.broadcast_messages:
            if broadcast.sender_id != agent_id:  # 不接收自己的广播
                messages.append(broadcast)
        
        # 清理旧的广播消息
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        self.broadcast_messages = [
            msg for msg in self.broadcast_messages 
            if msg.timestamp > cutoff_time
        ]
        
        return messages[:max_count]
    
    def process_message(self, message: InteractionMessage, receiver_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息"""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            return handler(message, receiver_context)
        else:
            return {"status": "unhandled", "message_type": message.message_type.value}


class CollaborationManager:
    """协作管理器"""
    
    def __init__(self):
        self.projects: Dict[str, CollaborationProject] = {}
        self.project_templates = self._initialize_project_templates()
    
    def _initialize_project_templates(self) -> Dict[str, dict]:
        """初始化项目模板"""
        return {
            "house_building": {
                "name": "房屋建造",
                "description": "协作建造一座房屋",
                "collaboration_type": CollaborationType.BUILDING,
                "required_skills": ["construction", "planning"],
                "required_resources": {"wood": 100, "stone": 50, "tools": 10},
                "estimated_duration": 480,  # 8小时
                "tasks": [
                    {"name": "地基挖掘", "duration": 120, "required_participants": 2},
                    {"name": "框架搭建", "duration": 180, "required_participants": 3},
                    {"name": "墙体建造", "duration": 120, "required_participants": 2},
                    {"name": "屋顶安装", "duration": 60, "required_participants": 2}
                ]
            },
            "resource_expedition": {
                "name": "资源探险",
                "description": "组队探索和收集资源",
                "collaboration_type": CollaborationType.RESOURCE_GATHERING,
                "required_skills": ["exploration", "survival"],
                "required_resources": {"food": 20, "tools": 5},
                "estimated_duration": 240,  # 4小时
                "tasks": [
                    {"name": "路线规划", "duration": 30, "required_participants": 1},
                    {"name": "资源搜索", "duration": 150, "required_participants": 3},
                    {"name": "资源运输", "duration": 60, "required_participants": 2}
                ]
            },
            "community_event": {
                "name": "社区活动",
                "description": "组织社区庆祝活动",
                "collaboration_type": CollaborationType.ENTERTAINMENT,
                "required_skills": ["organization", "creativity"],
                "required_resources": {"food": 50, "decorations": 20},
                "estimated_duration": 180,  # 3小时
                "tasks": [
                    {"name": "活动策划", "duration": 60, "required_participants": 2},
                    {"name": "场地布置", "duration": 60, "required_participants": 4},
                    {"name": "活动执行", "duration": 60, "required_participants": 5}
                ]
            }
        }
    
    def create_project(self, template_name: str, initiator_id: str, 
                      custom_params: Dict[str, Any] = None) -> CollaborationProject:
        """创建协作项目"""
        if template_name not in self.project_templates:
            raise ValueError(f"未知的项目模板: {template_name}")
        
        template = self.project_templates[template_name].copy()
        if custom_params:
            template.update(custom_params)
        
        project_id = f"{template_name}_{len(self.projects)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        project = CollaborationProject(
            project_id=project_id,
            name=template["name"],
            description=template["description"],
            collaboration_type=CollaborationType(template["collaboration_type"]),
            participants={initiator_id},
            leader_id=initiator_id,
            required_skills=template["required_skills"],
            required_resources=template["required_resources"],
            target_location=template.get("target_location"),
            estimated_duration=template["estimated_duration"],
            progress=0.0,
            status="planning",
            created_at=datetime.datetime.now(),
            deadline=template.get("deadline"),
            tasks=template["tasks"]
        )
        
        self.projects[project_id] = project
        return project
    
    def join_project(self, project_id: str, agent_id: str) -> bool:
        """加入项目"""
        project = self.projects.get(project_id)
        if project and project.status in ["planning", "active"]:
            project.add_participant(agent_id)
            return True
        return False
    
    def leave_project(self, project_id: str, agent_id: str) -> bool:
        """离开项目"""
        project = self.projects.get(project_id)
        if project and agent_id in project.participants:
            project.remove_participant(agent_id)
            if not project.participants:
                project.status = "cancelled"
            return True
        return False
    
    def start_project(self, project_id: str) -> bool:
        """开始项目"""
        project = self.projects.get(project_id)
        if project and project.status == "planning":
            project.status = "active"
            return True
        return False
    
    def complete_task(self, project_id: str, task_name: str, participants: List[str]) -> bool:
        """完成任务"""
        project = self.projects.get(project_id)
        if not project:
            return False
        
        for task in project.tasks:
            if task["name"] == task_name and not task.get("completed", False):
                task["completed"] = True
                task["completed_by"] = participants
                task["completed_at"] = datetime.datetime.now().isoformat()
                
                # 更新项目进度
                completed_tasks = sum(1 for t in project.tasks if t.get("completed", False))
                project.progress = completed_tasks / len(project.tasks)
                
                if project.progress >= 1.0:
                    project.status = "completed"
                
                return True
        
        return False
    
    def get_available_projects(self, agent_id: str) -> List[CollaborationProject]:
        """获取可用项目"""
        available = []
        for project in self.projects.values():
            if (project.status in ["planning", "active"] and 
                agent_id not in project.participants and
                len(project.participants) < 10):  # 最大参与者限制
                available.append(project)
        return available
    
    def get_agent_projects(self, agent_id: str) -> List[CollaborationProject]:
        """获取agent参与的项目"""
        return [
            project for project in self.projects.values()
            if agent_id in project.participants and project.status != "cancelled"
        ]


class MultiAIInteractionEngine:
    """多AI交互引擎"""
    
    def __init__(self):
        self.communication = CommunicationProtocol()
        self.collaboration_manager = CollaborationManager()
        self.interaction_rules: List[InteractionRule] = []
        self.interaction_histories: Dict[Tuple[str, str], InteractionHistory] = {}
        self.agent_contexts: Dict[str, Dict[str, Any]] = {}
        
        # 初始化交互规则和消息处理器
        self._initialize_interaction_rules()
        self._initialize_message_handlers()
    
    def _initialize_interaction_rules(self):
        """初始化交互规则"""
        # 问候规则
        greeting_rule = InteractionRule(
            "greeting_rule",
            "问候规则",
            lambda ctx: self._should_greet(ctx),
            lambda ctx: self._perform_greeting(ctx)
        )
        greeting_rule.priority = 3
        
        # 协作邀请规则
        collaboration_rule = InteractionRule(
            "collaboration_rule", 
            "协作邀请规则",
            lambda ctx: self._should_collaborate(ctx),
            lambda ctx: self._initiate_collaboration(ctx)
        )
        collaboration_rule.priority = 4
        
        # 帮助规则
        help_rule = InteractionRule(
            "help_rule",
            "帮助规则", 
            lambda ctx: self._should_help(ctx),
            lambda ctx: self._offer_help(ctx)
        )
        help_rule.priority = 5
        
        # 冲突解决规则
        conflict_rule = InteractionRule(
            "conflict_rule",
            "冲突解决规则",
            lambda ctx: self._has_conflict(ctx),
            lambda ctx: self._resolve_conflict(ctx)
        )
        conflict_rule.priority = 5
        
        self.interaction_rules.extend([greeting_rule, collaboration_rule, help_rule, conflict_rule])
    
    def _initialize_message_handlers(self):
        """初始化消息处理器"""
        self.communication.register_handler(InteractionType.GREETING, self._handle_greeting)
        self.communication.register_handler(InteractionType.CONVERSATION, self._handle_conversation)
        self.communication.register_handler(InteractionType.COLLABORATION, self._handle_collaboration)
        self.communication.register_handler(InteractionType.HELP, self._handle_help)
        self.communication.register_handler(InteractionType.TRADE, self._handle_trade)
        self.communication.register_handler(InteractionType.CONFLICT, self._handle_conflict)
    
    def register_agent(self, agent_id: str, initial_context: Dict[str, Any] = None):
        """注册agent"""
        self.agent_contexts[agent_id] = initial_context or {}
    
    def update_agent_context(self, agent_id: str, context_updates: Dict[str, Any]):
        """更新agent上下文"""
        if agent_id in self.agent_contexts:
            self.agent_contexts[agent_id].update(context_updates)
    
    def process_interactions(self, agent_id: str) -> List[Dict[str, Any]]:
        """处理agent的交互"""
        results = []
        
        # 获取agent上下文
        agent_context = self.agent_contexts.get(agent_id, {})
        
        # 处理接收到的消息
        messages = self.communication.get_messages(agent_id)
        for message in messages:
            result = self.communication.process_message(message, agent_context)
            result["message_id"] = f"{message.sender_id}_{message.timestamp.isoformat()}"
            results.append(result)
            
            # 记录交互历史
            self._record_interaction(message.sender_id, agent_id, message.message_type, 
                                   InteractionOutcome.SUCCESS, result)
        
        # 检查交互规则
        for rule in sorted(self.interaction_rules, key=lambda r: r.priority, reverse=True):
            context = {
                "agent_id": agent_id,
                "agent_context": agent_context,
                "nearby_agents": self._get_nearby_agents(agent_id),
                "current_projects": self.collaboration_manager.get_agent_projects(agent_id)
            }
            
            if rule.check_condition(context):
                rule_result = rule.execute_action(context)
                rule_result["rule_triggered"] = rule.name
                results.append(rule_result)
        
        return results
    
    def _get_nearby_agents(self, agent_id: str, radius: float = 5.0) -> List[str]:
        """获取附近的agents"""
        agent_context = self.agent_contexts.get(agent_id, {})
        agent_location = agent_context.get("location", (0, 0))
        
        nearby = []
        for other_id, other_context in self.agent_contexts.items():
            if other_id == agent_id:
                continue
            
            other_location = other_context.get("location", (0, 0))
            distance = math.sqrt(
                (agent_location[0] - other_location[0]) ** 2 + 
                (agent_location[1] - other_location[1]) ** 2
            )
            
            if distance <= radius:
                nearby.append(other_id)
        
        return nearby
    
    def _should_greet(self, context: Dict[str, Any]) -> bool:
        """检查是否应该问候"""
        agent_id = context["agent_id"]
        nearby_agents = context["nearby_agents"]
        
        for other_id in nearby_agents:
            history_key = tuple(sorted([agent_id, other_id]))
            history = self.interaction_histories.get(history_key)
            
            if not history or not history.last_interaction:
                return True
            
            # 如果超过一天没有交互，则问候
            time_since_last = datetime.datetime.now() - history.last_interaction
            if time_since_last.total_seconds() > 24 * 3600:
                return True
        
        return False
    
    def _perform_greeting(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行问候"""
        agent_id = context["agent_id"]
        nearby_agents = context["nearby_agents"]
        
        if not nearby_agents:
            return {"action": "no_one_to_greet"}
        
        target_id = random.choice(nearby_agents)
        
        # 发送问候消息
        greeting_message = InteractionMessage(
            sender_id=agent_id,
            receiver_id=target_id,
            message_type=InteractionType.GREETING,
            content=f"你好！我是{agent_id}",
            metadata={"greeting_type": "casual"},
            timestamp=datetime.datetime.now(),
            requires_response=True,
            priority=2
        )
        
        self.communication.send_message(greeting_message)
        
        return {
            "action": "greeting_sent",
            "target": target_id,
            "message": greeting_message.content
        }
    
    def _should_collaborate(self, context: Dict[str, Any]) -> bool:
        """检查是否应该协作"""
        agent_id = context["agent_id"]
        agent_context = context["agent_context"]
        current_projects = context["current_projects"]
        
        # 如果已经参与太多项目，不再发起新协作
        if len(current_projects) >= 3:
            return False
        
        # 如果资源充足且有建设需求，考虑协作
        resources = agent_context.get("resources", 0)
        work_motivation = agent_context.get("work_motivation", 50)
        
        return resources > 50 and work_motivation > 60 and random.random() < 0.3
    
    def _initiate_collaboration(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """发起协作"""
        agent_id = context["agent_id"]
        nearby_agents = context["nearby_agents"]
        
        if not nearby_agents:
            return {"action": "no_collaborators_available"}
        
        # 选择协作项目类型
        project_types = ["house_building", "resource_expedition", "community_event"]
        project_type = random.choice(project_types)
        
        # 创建项目
        project = self.collaboration_manager.create_project(project_type, agent_id)
        
        # 邀请附近的agents
        for target_id in nearby_agents[:3]:  # 最多邀请3个
            invitation = InteractionMessage(
                sender_id=agent_id,
                receiver_id=target_id,
                message_type=InteractionType.COLLABORATION,
                content=f"邀请你参与项目: {project.name}",
                metadata={
                    "project_id": project.project_id,
                    "project_type": project_type,
                    "invitation_type": "collaboration"
                },
                timestamp=datetime.datetime.now(),
                requires_response=True,
                priority=4
            )
            
            self.communication.send_message(invitation)
        
        return {
            "action": "collaboration_initiated",
            "project_id": project.project_id,
            "project_name": project.name,
            "invitations_sent": len(nearby_agents[:3])
        }
    
    def _should_help(self, context: Dict[str, Any]) -> bool:
        """检查是否应该提供帮助"""
        agent_context = context["agent_context"]
        nearby_agents = context["nearby_agents"]
        
        # 如果自己状态良好且附近有人，考虑帮助
        energy = agent_context.get("energy", 50)
        happiness = agent_context.get("happiness", 50)
        
        return energy > 70 and happiness > 60 and len(nearby_agents) > 0 and random.random() < 0.2
    
    def _offer_help(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """提供帮助"""
        agent_id = context["agent_id"]
        nearby_agents = context["nearby_agents"]
        
        if not nearby_agents:
            return {"action": "no_one_needs_help"}
        
        target_id = random.choice(nearby_agents)
        
        help_message = InteractionMessage(
            sender_id=agent_id,
            receiver_id=target_id,
            message_type=InteractionType.HELP,
            content="需要帮助吗？我可以协助你",
            metadata={"help_type": "general_assistance"},
            timestamp=datetime.datetime.now(),
            requires_response=True,
            priority=3
        )
        
        self.communication.send_message(help_message)
        
        return {
            "action": "help_offered",
            "target": target_id
        }
    
    def _has_conflict(self, context: Dict[str, Any]) -> bool:
        """检查是否有冲突"""
        agent_id = context["agent_id"]
        
        # 检查是否有冲突历史
        for history in self.interaction_histories.values():
            if (agent_id in [history.agent1_id, history.agent2_id] and 
                history.conflict_count > history.collaboration_count):
                return True
        
        return False
    
    def _resolve_conflict(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """解决冲突"""
        agent_id = context["agent_id"]
        
        # 找到冲突对象
        conflict_target = None
        for history in self.interaction_histories.values():
            if (agent_id in [history.agent1_id, history.agent2_id] and 
                history.conflict_count > history.collaboration_count):
                conflict_target = history.agent2_id if history.agent1_id == agent_id else history.agent1_id
                break
        
        if not conflict_target:
            return {"action": "no_conflict_to_resolve"}
        
        # 发送和解消息
        peace_message = InteractionMessage(
            sender_id=agent_id,
            receiver_id=conflict_target,
            message_type=InteractionType.CONVERSATION,
            content="我们能否化解之前的误会？",
            metadata={"conversation_type": "conflict_resolution"},
            timestamp=datetime.datetime.now(),
            requires_response=True,
            priority=4
        )
        
        self.communication.send_message(peace_message)
        
        return {
            "action": "conflict_resolution_attempted",
            "target": conflict_target
        }
    
    def _handle_greeting(self, message: InteractionMessage, receiver_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理问候消息"""
        # 回复问候
        response = InteractionMessage(
            sender_id=message.receiver_id,
            receiver_id=message.sender_id,
            message_type=InteractionType.GREETING,
            content=f"你好！很高兴见到你",
            metadata={"response_to": message.sender_id},
            timestamp=datetime.datetime.now(),
            priority=2
        )
        
        self.communication.send_message(response)
        
        return {
            "status": "greeting_responded",
            "response_sent": True
        }
    
    def _handle_conversation(self, message: InteractionMessage, receiver_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理对话消息"""
        conversation_type = message.metadata.get("conversation_type", "general")
        
        if conversation_type == "conflict_resolution":
            # 接受和解
            response = InteractionMessage(
                sender_id=message.receiver_id,
                receiver_id=message.sender_id,
                message_type=InteractionType.CONVERSATION,
                content="好的，让我们重新开始",
                metadata={"conversation_type": "peace_accepted"},
                timestamp=datetime.datetime.now(),
                priority=3
            )
            
            self.communication.send_message(response)
            
            return {
                "status": "conflict_resolved",
                "peace_accepted": True
            }
        
        return {
            "status": "conversation_acknowledged"
        }
    
    def _handle_collaboration(self, message: InteractionMessage, receiver_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理协作消息"""
        project_id = message.metadata.get("project_id")
        invitation_type = message.metadata.get("invitation_type")
        
        if invitation_type == "collaboration" and project_id:
            # 决定是否接受邀请
            energy = receiver_context.get("energy", 50)
            work_motivation = receiver_context.get("work_motivation", 50)
            
            accept_probability = (energy + work_motivation) / 200.0
            accept_invitation = random.random() < accept_probability
            
            if accept_invitation:
                success = self.collaboration_manager.join_project(project_id, message.receiver_id)
                
                response = InteractionMessage(
                    sender_id=message.receiver_id,
                    receiver_id=message.sender_id,
                    message_type=InteractionType.COLLABORATION,
                    content="我接受你的协作邀请！",
                    metadata={
                        "project_id": project_id,
                        "response_type": "invitation_accepted"
                    },
                    timestamp=datetime.datetime.now(),
                    priority=4
                )
                
                self.communication.send_message(response)
                
                return {
                    "status": "invitation_accepted",
                    "project_joined": success
                }
            else:
                response = InteractionMessage(
                    sender_id=message.receiver_id,
                    receiver_id=message.sender_id,
                    message_type=InteractionType.COLLABORATION,
                    content="抱歉，我现在无法参与",
                    metadata={
                        "project_id": project_id,
                        "response_type": "invitation_declined"
                    },
                    timestamp=datetime.datetime.now(),
                    priority=3
                )
                
                self.communication.send_message(response)
                
                return {
                    "status": "invitation_declined"
                }
        
        return {
            "status": "collaboration_processed"
        }
    
    def _handle_help(self, message: InteractionMessage, receiver_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理帮助消息"""
        # 检查是否需要帮助
        energy = receiver_context.get("energy", 50)
        resources = receiver_context.get("resources", 50)
        
        needs_help = energy < 30 or resources < 20
        
        if needs_help:
            response = InteractionMessage(
                sender_id=message.receiver_id,
                receiver_id=message.sender_id,
                message_type=InteractionType.HELP,
                content="是的，我需要帮助，谢谢你！",
                metadata={"help_accepted": True},
                timestamp=datetime.datetime.now(),
                priority=4
            )
        else:
            response = InteractionMessage(
                sender_id=message.receiver_id,
                receiver_id=message.sender_id,
                message_type=InteractionType.HELP,
                content="谢谢你的好意，我现在还好",
                metadata={"help_accepted": False},
                timestamp=datetime.datetime.now(),
                priority=2
            )
        
        self.communication.send_message(response)
        
        return {
            "status": "help_responded",
            "help_accepted": needs_help
        }
    
    def _handle_trade(self, message: InteractionMessage, receiver_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理交易消息"""
        # 简化的交易处理
        return {
            "status": "trade_considered"
        }
    
    def _handle_conflict(self, message: InteractionMessage, receiver_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理冲突消息"""
        # 简化的冲突处理
        return {
            "status": "conflict_acknowledged"
        }
    
    def _record_interaction(self, agent1_id: str, agent2_id: str, interaction_type: InteractionType,
                          outcome: InteractionOutcome, details: Dict[str, Any] = None):
        """记录交互历史"""
        history_key = tuple(sorted([agent1_id, agent2_id]))
        
        if history_key not in self.interaction_histories:
            self.interaction_histories[history_key] = InteractionHistory(
                agent1_id=agent1_id,
                agent2_id=agent2_id,
                interactions=[],
                relationship_changes=[],
                collaboration_count=0,
                conflict_count=0,
                last_interaction=None
            )
        
        history = self.interaction_histories[history_key]
        history.add_interaction(interaction_type, outcome, details)
    
    def get_interaction_statistics(self) -> Dict[str, Any]:
        """获取交互统计"""
        total_interactions = sum(len(h.interactions) for h in self.interaction_histories.values())
        total_collaborations = sum(h.collaboration_count for h in self.interaction_histories.values())
        total_conflicts = sum(h.conflict_count for h in self.interaction_histories.values())
        
        active_projects = len([p for p in self.collaboration_manager.projects.values() 
                             if p.status == "active"])
        completed_projects = len([p for p in self.collaboration_manager.projects.values() 
                                if p.status == "completed"])
        
        return {
            "total_interactions": total_interactions,
            "total_collaborations": total_collaborations,
            "total_conflicts": total_conflicts,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "registered_agents": len(self.agent_contexts),
            "interaction_pairs": len(self.interaction_histories)
        }
    
    def save_to_file(self, filepath: str):
        """保存交互引擎状态到文件"""
        data = {
            "agent_contexts": self.agent_contexts,
            "projects": {
                pid: {
                    "project_id": p.project_id,
                    "name": p.name,
                    "description": p.description,
                    "collaboration_type": p.collaboration_type.value,
                    "participants": list(p.participants),
                    "leader_id": p.leader_id,
                    "required_skills": p.required_skills,
                    "required_resources": p.required_resources,
                    "target_location": p.target_location,
                    "estimated_duration": p.estimated_duration,
                    "progress": p.progress,
                    "status": p.status,
                    "created_at": p.created_at.isoformat(),
                    "deadline": p.deadline.isoformat() if p.deadline else None,
                    "tasks": p.tasks
                }
                for pid, p in self.collaboration_manager.projects.items()
            },
            "interaction_histories": {
                f"{key[0]}_{key[1]}": {
                    "agent1_id": h.agent1_id,
                    "agent2_id": h.agent2_id,
                    "interactions": h.interactions[-10:],  # 只保存最近10个交互
                    "collaboration_count": h.collaboration_count,
                    "conflict_count": h.conflict_count,
                    "last_interaction": h.last_interaction.isoformat() if h.last_interaction else None
                }
                for key, h in self.interaction_histories.items()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载交互引擎状态"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.agent_contexts = data.get("agent_contexts", {})
            
            # 加载项目
            projects_data = data.get("projects", {})
            self.collaboration_manager.projects = {}
            
            for pid, project_data in projects_data.items():
                project = CollaborationProject(
                    project_id=project_data["project_id"],
                    name=project_data["name"],
                    description=project_data["description"],
                    collaboration_type=CollaborationType(project_data["collaboration_type"]),
                    participants=set(project_data["participants"]),
                    leader_id=project_data["leader_id"],
                    required_skills=project_data["required_skills"],
                    required_resources=project_data["required_resources"],
                    target_location=project_data["target_location"],
                    estimated_duration=project_data["estimated_duration"],
                    progress=project_data["progress"],
                    status=project_data["status"],
                    created_at=datetime.datetime.fromisoformat(project_data["created_at"]),
                    deadline=datetime.datetime.fromisoformat(project_data["deadline"]) if project_data["deadline"] else None,
                    tasks=project_data["tasks"]
                )
                self.collaboration_manager.projects[pid] = project
            
            # 加载交互历史
            histories_data = data.get("interaction_histories", {})
            self.interaction_histories = {}
            
            for key_str, history_data in histories_data.items():
                agent1_id, agent2_id = key_str.split("_", 1)
                history_key = tuple(sorted([agent1_id, agent2_id]))
                
                history = InteractionHistory(
                    agent1_id=history_data["agent1_id"],
                    agent2_id=history_data["agent2_id"],
                    interactions=history_data["interactions"],
                    relationship_changes=[],
                    collaboration_count=history_data["collaboration_count"],
                    conflict_count=history_data["conflict_count"],
                    last_interaction=datetime.datetime.fromisoformat(history_data["last_interaction"]) if history_data["last_interaction"] else None
                )
                self.interaction_histories[history_key] = history
                
        except FileNotFoundError:
            pass  # 文件不存在时忽略