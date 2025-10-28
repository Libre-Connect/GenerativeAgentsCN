"""
AI自主决策系统
实现AI的决策树、行为模式、目标规划和环境适应逻辑
"""

import json
import random
import datetime
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


class DecisionType(Enum):
    """决策类型"""
    SOCIAL = "social"               # 社交决策
    WORK = "work"                   # 工作决策
    SURVIVAL = "survival"           # 生存决策
    DEVELOPMENT = "development"     # 发展决策
    LEISURE = "leisure"             # 休闲决策
    EMERGENCY = "emergency"         # 紧急决策


class GoalType(Enum):
    """目标类型"""
    SHORT_TERM = "short_term"       # 短期目标 (1-7天)
    MEDIUM_TERM = "medium_term"     # 中期目标 (1-4周)
    LONG_TERM = "long_term"         # 长期目标 (1-12个月)
    LIFE_GOAL = "life_goal"         # 人生目标 (1年以上)


class Priority(Enum):
    """优先级"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


class ActionType(Enum):
    """行动类型"""
    MOVE = "move"                   # 移动
    INTERACT = "interact"           # 互动
    BUILD = "build"                 # 建造
    WORK = "work"                   # 工作
    REST = "rest"                   # 休息
    SOCIALIZE = "socialize"         # 社交
    LEARN = "learn"                 # 学习
    PLAN = "plan"                   # 规划


@dataclass
class Goal:
    """目标类"""
    id: str
    name: str
    description: str
    goal_type: GoalType
    priority: Priority
    target_value: float             # 目标值
    current_value: float            # 当前值
    deadline: Optional[datetime.datetime]
    created_at: datetime.datetime
    prerequisites: List[str]        # 前置条件
    sub_goals: List[str]           # 子目标
    progress: float                # 进度 (0-1)
    is_completed: bool
    is_active: bool
    
    def update_progress(self):
        """更新进度"""
        if self.target_value > 0:
            self.progress = min(1.0, self.current_value / self.target_value)
        else:
            self.progress = 1.0 if self.is_completed else 0.0
        
        if self.progress >= 1.0:
            self.is_completed = True
    
    def is_overdue(self) -> bool:
        """检查是否过期"""
        if not self.deadline:
            return False
        return datetime.datetime.now() > self.deadline
    
    def get_urgency(self) -> float:
        """计算紧急程度"""
        if not self.deadline:
            return 0.5
        
        time_left = (self.deadline - datetime.datetime.now()).total_seconds()
        if time_left <= 0:
            return 1.0
        
        # 基于剩余时间和进度计算紧急程度
        expected_progress = 1.0 - (time_left / (24 * 3600 * 7))  # 假设一周完成
        urgency = max(0.0, expected_progress - self.progress)
        return min(1.0, urgency)


@dataclass
class Action:
    """行动类"""
    id: str
    action_type: ActionType
    name: str
    description: str
    duration: int                   # 持续时间（分钟）
    energy_cost: float             # 体力消耗
    prerequisites: Dict[str, Any]   # 前置条件
    effects: Dict[str, float]      # 效果
    success_rate: float            # 成功率
    location: Optional[Tuple[int, int]]  # 位置
    target_agent: Optional[str]    # 目标agent
    target_object: Optional[str]   # 目标对象
    
    def can_execute(self, agent_state: Dict[str, Any]) -> bool:
        """检查是否可以执行"""
        for condition, required_value in self.prerequisites.items():
            if condition not in agent_state:
                return False
            
            current_value = agent_state[condition]
            if isinstance(required_value, (int, float)):
                if current_value < required_value:
                    return False
            elif isinstance(required_value, str):
                if current_value != required_value:
                    return False
            elif isinstance(required_value, list):
                if current_value not in required_value:
                    return False
        
        return True


class DecisionNode(ABC):
    """决策节点抽象基类"""
    
    def __init__(self, node_id: str, name: str):
        self.node_id = node_id
        self.name = name
        self.children: List['DecisionNode'] = []
        self.parent: Optional['DecisionNode'] = None
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> float:
        """评估节点得分"""
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点动作"""
        pass
    
    def add_child(self, child: 'DecisionNode'):
        """添加子节点"""
        child.parent = self
        self.children.append(child)
    
    def get_best_child(self, context: Dict[str, Any]) -> Optional['DecisionNode']:
        """获取最佳子节点"""
        if not self.children:
            return None
        
        best_child = None
        best_score = -float('inf')
        
        for child in self.children:
            score = child.evaluate(context)
            if score > best_score:
                best_score = score
                best_child = child
        
        return best_child


class ConditionNode(DecisionNode):
    """条件节点"""
    
    def __init__(self, node_id: str, name: str, condition_func: Callable[[Dict[str, Any]], bool]):
        super().__init__(node_id, name)
        self.condition_func = condition_func
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """评估条件"""
        return 1.0 if self.condition_func(context) else 0.0
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行条件检查"""
        if self.condition_func(context):
            best_child = self.get_best_child(context)
            if best_child:
                return best_child.execute(context)
        
        return {"success": False, "reason": f"条件 {self.name} 不满足"}


class ActionNode(DecisionNode):
    """行动节点"""
    
    def __init__(self, node_id: str, name: str, action: Action):
        super().__init__(node_id, name)
        self.action = action
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """评估行动价值"""
        agent_state = context.get("agent_state", {})
        
        # 检查是否可以执行
        if not self.action.can_execute(agent_state):
            return 0.0
        
        # 基于多个因素计算得分
        score = self.action.success_rate * 50
        
        # 考虑体力消耗
        current_energy = agent_state.get("energy", 100)
        if current_energy >= self.action.energy_cost:
            score += 20
        else:
            score -= 30
        
        # 考虑目标相关性
        current_goals = context.get("active_goals", [])
        for goal in current_goals:
            if self._action_supports_goal(goal):
                score += goal.priority.value * 10
        
        return score
    
    def _action_supports_goal(self, goal: Goal) -> bool:
        """检查行动是否支持目标"""
        # 简化的目标支持检查
        goal_keywords = goal.name.lower().split()
        action_keywords = self.action.name.lower().split()
        
        return any(keyword in action_keywords for keyword in goal_keywords)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行行动"""
        agent_state = context.get("agent_state", {})
        
        if not self.action.can_execute(agent_state):
            return {"success": False, "reason": "不满足执行条件"}
        
        # 模拟执行结果
        success = random.random() < self.action.success_rate
        
        result = {
            "success": success,
            "action": self.action.name,
            "duration": self.action.duration,
            "energy_cost": self.action.energy_cost
        }
        
        if success:
            result["effects"] = self.action.effects
        
        return result


class UtilityNode(DecisionNode):
    """效用节点"""
    
    def __init__(self, node_id: str, name: str, utility_func: Callable[[Dict[str, Any]], float]):
        super().__init__(node_id, name)
        self.utility_func = utility_func
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """计算效用值"""
        return self.utility_func(context)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行效用计算"""
        utility = self.utility_func(context)
        best_child = self.get_best_child(context)
        
        if best_child:
            result = best_child.execute(context)
            result["utility"] = utility
            return result
        
        return {"success": True, "utility": utility}


class GoalManager:
    """目标管理器"""
    
    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.goal_templates = self._initialize_goal_templates()
    
    def _initialize_goal_templates(self) -> Dict[str, dict]:
        """初始化目标模板"""
        return {
            "find_love": {
                "name": "寻找爱情",
                "description": "找到合适的伴侣并建立恋爱关系",
                "goal_type": GoalType.LONG_TERM,
                "priority": Priority.HIGH,
                "target_value": 1.0
            },
            "build_house": {
                "name": "建造房屋",
                "description": "为自己建造一个舒适的住所",
                "goal_type": GoalType.MEDIUM_TERM,
                "priority": Priority.HIGH,
                "target_value": 1.0
            },
            "make_friends": {
                "name": "结交朋友",
                "description": "扩展社交圈，结交新朋友",
                "goal_type": GoalType.SHORT_TERM,
                "priority": Priority.MEDIUM,
                "target_value": 3.0
            },
            "develop_skills": {
                "name": "技能发展",
                "description": "提升个人技能和能力",
                "goal_type": GoalType.LONG_TERM,
                "priority": Priority.MEDIUM,
                "target_value": 100.0
            },
            "earn_resources": {
                "name": "获取资源",
                "description": "通过工作获取必要的资源",
                "goal_type": GoalType.SHORT_TERM,
                "priority": Priority.HIGH,
                "target_value": 1000.0
            }
        }
    
    def create_goal(self, template_name: str, custom_params: Dict[str, Any] = None) -> Goal:
        """创建目标"""
        if template_name not in self.goal_templates:
            raise ValueError(f"未知的目标模板: {template_name}")
        
        template = self.goal_templates[template_name].copy()
        if custom_params:
            template.update(custom_params)
        
        goal_id = f"{template_name}_{len(self.goals)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        goal = Goal(
            id=goal_id,
            name=template["name"],
            description=template["description"],
            goal_type=GoalType(template["goal_type"]),
            priority=Priority(template["priority"]),
            target_value=template["target_value"],
            current_value=0.0,
            deadline=template.get("deadline"),
            created_at=datetime.datetime.now(),
            prerequisites=template.get("prerequisites", []),
            sub_goals=template.get("sub_goals", []),
            progress=0.0,
            is_completed=False,
            is_active=True
        )
        
        self.goals[goal_id] = goal
        return goal
    
    def update_goal_progress(self, goal_id: str, progress_delta: float):
        """更新目标进度"""
        goal = self.goals.get(goal_id)
        if goal and goal.is_active:
            goal.current_value += progress_delta
            goal.update_progress()
    
    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标"""
        return [goal for goal in self.goals.values() if goal.is_active and not goal.is_completed]
    
    def get_priority_goals(self, max_count: int = 3) -> List[Goal]:
        """获取优先级最高的目标"""
        active_goals = self.get_active_goals()
        
        # 按优先级和紧急程度排序
        def goal_score(goal: Goal) -> float:
            return goal.priority.value * 10 + goal.get_urgency() * 5
        
        active_goals.sort(key=goal_score, reverse=True)
        return active_goals[:max_count]
    
    def complete_goal(self, goal_id: str):
        """完成目标"""
        goal = self.goals.get(goal_id)
        if goal:
            goal.is_completed = True
            goal.is_active = False
            goal.progress = 1.0
    
    def abandon_goal(self, goal_id: str):
        """放弃目标"""
        goal = self.goals.get(goal_id)
        if goal:
            goal.is_active = False


class BehaviorPattern:
    """行为模式"""
    
    def __init__(self, pattern_id: str, name: str):
        self.pattern_id = pattern_id
        self.name = name
        self.triggers: List[Callable[[Dict[str, Any]], bool]] = []
        self.actions: List[Action] = []
        self.weight = 1.0
        self.cooldown = 0  # 冷却时间（分钟）
        self.last_executed: Optional[datetime.datetime] = None
    
    def add_trigger(self, trigger_func: Callable[[Dict[str, Any]], bool]):
        """添加触发条件"""
        self.triggers.append(trigger_func)
    
    def add_action(self, action: Action):
        """添加行动"""
        self.actions.append(action)
    
    def is_triggered(self, context: Dict[str, Any]) -> bool:
        """检查是否被触发"""
        if self.is_on_cooldown():
            return False
        
        return all(trigger(context) for trigger in self.triggers)
    
    def is_on_cooldown(self) -> bool:
        """检查是否在冷却中"""
        if not self.last_executed or self.cooldown <= 0:
            return False
        
        time_passed = (datetime.datetime.now() - self.last_executed).total_seconds() / 60
        return time_passed < self.cooldown
    
    def execute(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行行为模式"""
        results = []
        
        for action in self.actions:
            if action.can_execute(context.get("agent_state", {})):
                # 模拟执行
                success = random.random() < action.success_rate
                result = {
                    "action": action.name,
                    "success": success,
                    "duration": action.duration,
                    "energy_cost": action.energy_cost
                }
                
                if success:
                    result["effects"] = action.effects
                
                results.append(result)
        
        self.last_executed = datetime.datetime.now()
        return results


class AutonomousDecisionEngine:
    """自主决策引擎"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.goal_manager = GoalManager()
        self.decision_tree: Optional[DecisionNode] = None
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}
        self.agent_state = self._initialize_agent_state()
        self.decision_history: List[dict] = []
        
        # 初始化决策树和行为模式
        self._build_decision_tree()
        self._initialize_behavior_patterns()
    
    def _initialize_agent_state(self) -> Dict[str, Any]:
        """初始化agent状态"""
        return {
            "energy": 100.0,
            "happiness": 50.0,
            "social_need": 50.0,
            "work_motivation": 50.0,
            "health": 100.0,
            "resources": 100.0,
            "location": (0, 0),
            "current_activity": "idle",
            "relationships": {},
            "skills": {},
            "inventory": {}
        }
    
    def _build_decision_tree(self):
        """构建决策树"""
        # 根节点
        root = UtilityNode("root", "决策根节点", 
                          lambda ctx: self._calculate_overall_utility(ctx))
        
        # 紧急情况分支
        emergency_branch = ConditionNode("emergency", "紧急情况", 
                                       lambda ctx: self._check_emergency(ctx))
        
        # 基本需求分支
        basic_needs_branch = ConditionNode("basic_needs", "基本需求", 
                                         lambda ctx: self._check_basic_needs(ctx))
        
        # 社交需求分支
        social_branch = ConditionNode("social", "社交需求", 
                                    lambda ctx: self._check_social_needs(ctx))
        
        # 工作发展分支
        work_branch = ConditionNode("work", "工作发展", 
                                  lambda ctx: self._check_work_needs(ctx))
        
        # 休闲娱乐分支
        leisure_branch = ConditionNode("leisure", "休闲娱乐", 
                                     lambda ctx: self._check_leisure_needs(ctx))
        
        # 添加子节点
        root.add_child(emergency_branch)
        root.add_child(basic_needs_branch)
        root.add_child(social_branch)
        root.add_child(work_branch)
        root.add_child(leisure_branch)
        
        # 为每个分支添加具体行动
        self._add_emergency_actions(emergency_branch)
        self._add_basic_need_actions(basic_needs_branch)
        self._add_social_actions(social_branch)
        self._add_work_actions(work_branch)
        self._add_leisure_actions(leisure_branch)
        
        self.decision_tree = root
    
    def _calculate_overall_utility(self, context: Dict[str, Any]) -> float:
        """计算整体效用"""
        state = context.get("agent_state", self.agent_state)
        
        # 基于各种需求计算效用
        energy_utility = state.get("energy", 0) / 100.0
        happiness_utility = state.get("happiness", 0) / 100.0
        social_utility = state.get("social_need", 0) / 100.0
        health_utility = state.get("health", 0) / 100.0
        
        return (energy_utility + happiness_utility + social_utility + health_utility) / 4.0
    
    def _check_emergency(self, context: Dict[str, Any]) -> bool:
        """检查紧急情况"""
        state = context.get("agent_state", self.agent_state)
        return (state.get("health", 100) < 20 or 
                state.get("energy", 100) < 10 or
                state.get("resources", 100) < 5)
    
    def _check_basic_needs(self, context: Dict[str, Any]) -> bool:
        """检查基本需求"""
        state = context.get("agent_state", self.agent_state)
        return (state.get("energy", 100) < 50 or 
                state.get("health", 100) < 70 or
                state.get("resources", 100) < 30)
    
    def _check_social_needs(self, context: Dict[str, Any]) -> bool:
        """检查社交需求"""
        state = context.get("agent_state", self.agent_state)
        return state.get("social_need", 50) > 70
    
    def _check_work_needs(self, context: Dict[str, Any]) -> bool:
        """检查工作需求"""
        state = context.get("agent_state", self.agent_state)
        return (state.get("work_motivation", 50) > 60 or
                state.get("resources", 100) < 50)
    
    def _check_leisure_needs(self, context: Dict[str, Any]) -> bool:
        """检查休闲需求"""
        state = context.get("agent_state", self.agent_state)
        return (state.get("happiness", 50) < 40 or
                state.get("energy", 100) > 80)
    
    def _add_emergency_actions(self, parent: DecisionNode):
        """添加紧急行动"""
        # 寻求医疗帮助
        seek_help = Action(
            id="seek_medical_help",
            action_type=ActionType.INTERACT,
            name="寻求医疗帮助",
            description="前往医院或寻找医生",
            duration=60,
            energy_cost=20,
            prerequisites={"health": 50},  # 健康值低于50时触发
            effects={"health": 30},
            success_rate=0.8,
            location=None,
            target_agent=None,
            target_object="hospital"
        )
        
        parent.add_child(ActionNode("emergency_medical", "紧急医疗", seek_help))
    
    def _add_basic_need_actions(self, parent: DecisionNode):
        """添加基本需求行动"""
        # 休息
        rest_action = Action(
            id="rest",
            action_type=ActionType.REST,
            name="休息",
            description="休息恢复体力",
            duration=120,
            energy_cost=-50,  # 负值表示恢复
            prerequisites={},
            effects={"energy": 50, "health": 10},
            success_rate=0.95,
            location=None,
            target_agent=None,
            target_object=None
        )
        
        parent.add_child(ActionNode("rest", "休息", rest_action))
    
    def _add_social_actions(self, parent: DecisionNode):
        """添加社交行动"""
        # 社交互动
        socialize_action = Action(
            id="socialize",
            action_type=ActionType.SOCIALIZE,
            name="社交互动",
            description="与其他人进行社交活动",
            duration=90,
            energy_cost=15,
            prerequisites={"energy": 20},
            effects={"social_need": -30, "happiness": 20},
            success_rate=0.8,
            location=None,
            target_agent=None,
            target_object=None
        )
        
        parent.add_child(ActionNode("socialize", "社交", socialize_action))
    
    def _add_work_actions(self, parent: DecisionNode):
        """添加工作行动"""
        # 工作
        work_action = Action(
            id="work",
            action_type=ActionType.WORK,
            name="工作",
            description="进行工作获取资源",
            duration=240,
            energy_cost=40,
            prerequisites={"energy": 50},
            effects={"resources": 50, "work_motivation": -20},
            success_rate=0.9,
            location=None,
            target_agent=None,
            target_object=None
        )
        
        parent.add_child(ActionNode("work", "工作", work_action))
    
    def _add_leisure_actions(self, parent: DecisionNode):
        """添加休闲行动"""
        # 娱乐
        leisure_action = Action(
            id="leisure",
            action_type=ActionType.LEISURE,
            name="娱乐活动",
            description="进行娱乐活动放松心情",
            duration=120,
            energy_cost=20,
            prerequisites={"energy": 30},
            effects={"happiness": 30, "social_need": 10},
            success_rate=0.85,
            location=None,
            target_agent=None,
            target_object=None
        )
        
        parent.add_child(ActionNode("leisure", "娱乐", leisure_action))
    
    def _initialize_behavior_patterns(self):
        """初始化行为模式"""
        # 社交行为模式
        social_pattern = BehaviorPattern("social_pattern", "社交行为")
        social_pattern.add_trigger(lambda ctx: ctx.get("agent_state", {}).get("social_need", 0) > 80)
        social_pattern.weight = 1.5
        social_pattern.cooldown = 60  # 1小时冷却
        
        # 工作行为模式
        work_pattern = BehaviorPattern("work_pattern", "工作行为")
        work_pattern.add_trigger(lambda ctx: ctx.get("agent_state", {}).get("resources", 0) < 20)
        work_pattern.weight = 2.0
        work_pattern.cooldown = 30
        
        self.behavior_patterns["social"] = social_pattern
        self.behavior_patterns["work"] = work_pattern
    
    def make_decision(self, external_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """做出决策"""
        # 准备决策上下文
        context = {
            "agent_state": self.agent_state.copy(),
            "active_goals": self.goal_manager.get_active_goals(),
            "priority_goals": self.goal_manager.get_priority_goals(),
            "timestamp": datetime.datetime.now()
        }
        
        if external_context:
            context.update(external_context)
        
        # 首先检查行为模式
        triggered_patterns = []
        for pattern in self.behavior_patterns.values():
            if pattern.is_triggered(context):
                triggered_patterns.append(pattern)
        
        # 如果有触发的行为模式，选择权重最高的
        if triggered_patterns:
            best_pattern = max(triggered_patterns, key=lambda p: p.weight)
            decision_result = {
                "decision_type": "behavior_pattern",
                "pattern": best_pattern.name,
                "actions": best_pattern.execute(context)
            }
        else:
            # 使用决策树
            if self.decision_tree:
                decision_result = self.decision_tree.execute(context)
                decision_result["decision_type"] = "decision_tree"
            else:
                decision_result = {"decision_type": "default", "action": "idle"}
        
        # 记录决策历史
        decision_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "context": context,
            "decision": decision_result
        }
        self.decision_history.append(decision_record)
        
        # 限制历史记录长度
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-50:]
        
        return decision_result
    
    def update_agent_state(self, state_changes: Dict[str, Any]):
        """更新agent状态"""
        for key, value in state_changes.items():
            if key in self.agent_state:
                if isinstance(value, (int, float)) and isinstance(self.agent_state[key], (int, float)):
                    self.agent_state[key] += value
                    # 限制数值范围
                    if key in ["energy", "health", "happiness"]:
                        self.agent_state[key] = max(0, min(100, self.agent_state[key]))
                else:
                    self.agent_state[key] = value
    
    def add_goal(self, template_name: str, custom_params: Dict[str, Any] = None) -> Goal:
        """添加目标"""
        return self.goal_manager.create_goal(template_name, custom_params)
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """获取决策统计信息"""
        if not self.decision_history:
            return {"total_decisions": 0}
        
        decision_types = {}
        action_types = {}
        
        for record in self.decision_history:
            decision = record["decision"]
            decision_type = decision.get("decision_type", "unknown")
            decision_types[decision_type] = decision_types.get(decision_type, 0) + 1
            
            # 统计行动类型
            if "actions" in decision:
                for action in decision["actions"]:
                    action_name = action.get("action", "unknown")
                    action_types[action_name] = action_types.get(action_name, 0) + 1
            elif "action" in decision:
                action_name = decision["action"]
                action_types[action_name] = action_types.get(action_name, 0) + 1
        
        return {
            "total_decisions": len(self.decision_history),
            "decision_types": decision_types,
            "action_types": action_types,
            "current_state": self.agent_state.copy(),
            "active_goals": len(self.goal_manager.get_active_goals()),
            "completed_goals": len([g for g in self.goal_manager.goals.values() if g.is_completed])
        }
    
    def save_to_file(self, filepath: str):
        """保存决策引擎状态到文件"""
        data = {
            "agent_id": self.agent_id,
            "agent_state": self.agent_state,
            "goals": {
                goal_id: {
                    "id": goal.id,
                    "name": goal.name,
                    "description": goal.description,
                    "goal_type": goal.goal_type.value,
                    "priority": goal.priority.value,
                    "target_value": goal.target_value,
                    "current_value": goal.current_value,
                    "deadline": goal.deadline.isoformat() if goal.deadline else None,
                    "created_at": goal.created_at.isoformat(),
                    "prerequisites": goal.prerequisites,
                    "sub_goals": goal.sub_goals,
                    "progress": goal.progress,
                    "is_completed": goal.is_completed,
                    "is_active": goal.is_active
                }
                for goal_id, goal in self.goal_manager.goals.items()
            },
            "decision_history": self.decision_history[-20:]  # 只保存最近20个决策
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载决策引擎状态"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.agent_id = data.get("agent_id", self.agent_id)
            self.agent_state = data.get("agent_state", self.agent_state)
            self.decision_history = data.get("decision_history", [])
            
            # 加载目标
            goals_data = data.get("goals", {})
            self.goal_manager.goals = {}
            
            for goal_id, goal_data in goals_data.items():
                goal = Goal(
                    id=goal_data["id"],
                    name=goal_data["name"],
                    description=goal_data["description"],
                    goal_type=GoalType(goal_data["goal_type"]),
                    priority=Priority(goal_data["priority"]),
                    target_value=goal_data["target_value"],
                    current_value=goal_data["current_value"],
                    deadline=datetime.datetime.fromisoformat(goal_data["deadline"]) if goal_data["deadline"] else None,
                    created_at=datetime.datetime.fromisoformat(goal_data["created_at"]),
                    prerequisites=goal_data["prerequisites"],
                    sub_goals=goal_data["sub_goals"],
                    progress=goal_data["progress"],
                    is_completed=goal_data["is_completed"],
                    is_active=goal_data["is_active"]
                )
                self.goal_manager.goals[goal_id] = goal
                
        except FileNotFoundError:
            pass  # 文件不存在时忽略