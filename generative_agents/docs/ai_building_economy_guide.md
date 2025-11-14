# AI自主建造开拓与经济系统使用指南

## 概述

本系统实现了完整的AI自主建造开拓地图和经济系统，让Agent能够：

1. **自主分析地图**并决定在哪里建造什么建筑
2. **智能管理资源**，进行交易、合成等经济活动
3. **协作建造**大型项目，多个Agent共同完成复杂任务

## 系统架构

### 核心模块

1. **TerrainDevelopmentEngine** (`modules/terrain/terrain_development.py`)
   - 地形生成与管理
   - 建筑建造与维护
   - 资源分配与生产

2. **EconomyEngine** (`modules/economy/economy.py`)
   - 货币系统（钱包）
   - 物品系统（库存）
   - 交易与合成

3. **AIBuildingDecisionEngine** (`modules/decision/ai_building_decision.py`)
   - 分析社区需求
   - 选择建造位置和类型
   - 执行建造决策

4. **AIEconomyBehaviorEngine** (`modules/decision/ai_economy_behavior.py`)
   - 分析经济机会
   - 进行交易谈判
   - 执行合成和资源管理

5. **AICollaborationCoordinator** (`modules/decision/ai_collaboration_coordinator.py`)
   - 协调多Agent协作
   - 管理协作项目
   - 资源共享

## Agent能力

### 1. 自主建造

Agent会：
- **分析社区需求**：检查人口、食物、资源等各方面需求
- **选择建造类型**：根据需求和自身偏好决定建造什么
- **寻找最佳位置**：使用地形分析找到最适合的建造地点
- **执行建造**：消耗资源并开始建造

#### 建造流程

```python
# Agent每小时自动考虑一次建造
decision = agent.consider_building(terrain_engine, building_decision_engine)

if decision:
    # 决策包含：
    # - building_type: 建筑类型
    # - location: (x, y) 位置
    # - cost: 资源成本
    # - reason: 建造原因
    # - priority: 优先级
    
    # 执行建造
    result = agent.execute_building_decision(
        decision, 
        terrain_engine, 
        building_decision_engine
    )
```

#### 可建造的建筑类型

| 建筑类型 | 功能 | 成本示例 |
|---------|-----|---------|
| HOUSE | 增加人口容量 | 木材50, 石材30 |
| FARM | 生产食物 | 木材30, 石材10 |
| MINE | 开采资源 | 木材40, 金属20 |
| FACTORY | 生产能源 | 石材80, 金属50 |
| SHOP | 商业服务 | 木材40, 石材20 |
| ROAD | 改善交通 | 石材20 |
| SCHOOL | 教育服务 | 木材60, 石材40 |
| HOSPITAL | 医疗服务 | 石材70, 金属30 |

### 2. 智能经济行为

Agent会：
- **分析自身需求**：检查库存，确定缺少什么资源
- **寻找交易机会**：与其他Agent交换资源或购买
- **合成物品**：将原材料合成为高价值物品
- **资源管理**：在需要时出售多余物品获取资金

#### 经济行为流程

```python
# Agent每30分钟自动考虑一次经济行为
action = agent.consider_economic_action(
    economy_engine, 
    economy_behavior_engine, 
    other_agents
)

if action:
    # 行动可能是：
    # - 交易（TRADE）
    # - 合成（CRAFT）
    # - 出售（SELL）
    
    result = agent.execute_economic_action(
        action, 
        economy_behavior_engine
    )
```

#### 交易策略

每个Agent有不同的交易策略：

- **AGGRESSIVE（激进）**：追求利润最大化，会压价
- **BALANCED（平衡）**：兼顾利润和关系
- **COOPERATIVE（合作）**：优先考虑共同利益，愿意多付
- **CONSERVATIVE（保守）**：避免风险

### 3. 协作建造

多个Agent可以协作完成大型项目：

```python
# 发起协作项目
task_id = collaboration_coordinator.propose_collaborative_building_project(
    initiator="Agent1",
    project_name="社区发展项目",
    building_types=[
        (BuildingType.HOUSE, 3),
        (BuildingType.FARM, 2),
        (BuildingType.ROAD, 5)
    ],
    min_participants=3
)

# 邀请其他Agent
accepted = collaboration_coordinator.invite_agents_to_task(
    task_id, 
    ["Agent2", "Agent3", "Agent4"]
)

# 开始项目
collaboration_coordinator.start_task(task_id)
```

#### 协作优势

- **效率提升**：每增加一个参与者，效率提升15%
- **资源共享**：参与者可以共享资源
- **技能互补**：不同Agent的技能可以互补

## 系统特性

### 动态价格系统

资源和物品的价格会根据供需关系动态调整：

```python
# 价格受稀缺度影响
scarcity = 1000.0 / (resource_amount + 1.0)
price = base_price * (0.6 + min(2.0, scarcity))
```

- 资源越少，价格越高
- 鼓励Agent生产稀缺资源
- 形成自然的市场机制

### 社区需求分析

系统会自动分析社区的各种需求：

1. **住房需求**：人口接近容量时需求增加
2. **食物需求**：基于人口和食物储备
3. **资源需求**：基于资源稀缺度
4. **基础设施需求**：基于道路密度
5. **商业需求**：基于商店数量
6. **公共服务需求**：基于学校、医院数量

### 地形分析

系统会智能分析地形适合建造什么：

```python
# 地形适宜性评分
potential_score = (
    terrain_score * 30 +      # 地形类型
    resource_score * 25 +      # 资源丰富度
    accessibility * 20 +       # 可达性
    neighbor_score * 15 +      # 邻近发展情况
    (1 - development_level) * 10  # 未开发程度
)
```

## 使用示例

### 1. 基础使用

在Game初始化后，所有系统会自动运行：

```python
game = create_game(name, static_root, config, conversation, logger)

# 系统会自动：
# 1. 初始化地形（60x60地图）
# 2. 为每个Agent分配初始资源
# 3. 注册Agent到各个决策引擎
# 4. 在每次agent_think时执行AI决策
```

### 2. 查看Agent状态

```python
agent = game.get_agent("Agent名称")

# 查看库存
materials = agent.inventory.materials  # {ResourceType: amount}
items = agent.inventory.items          # {ItemType: count}

# 查看钱包
balance = agent.wallet.balance
```

### 3. 查看系统统计

```python
# 地形开发统计
terrain_stats = game.terrain_engine.get_development_statistics()
# 包含：
# - total_tiles: 总瓦片数
# - developed_tiles: 已开发瓦片数
# - total_buildings: 建筑总数
# - population: 人口信息
# - resources: 全局资源

# 经济统计
economy_stats = game.economy_behavior_engine.get_economy_statistics()
# 包含：
# - total_wealth: 总财富
# - average_wealth: 平均财富
# - trade_count: 交易次数

# 协作统计
collab_stats = game.collaboration_coordinator.get_task_summary()
# 包含：
# - total_tasks: 总任务数
# - completed_tasks: 完成任务数
# - success_rate: 成功率
```

### 4. 手动触发建造

```python
# 获取建造建议
suggestions = game.building_decision_engine.get_building_suggestions_for_agent(
    agent_id="Agent1"
)

# 选择一个建议并执行
if suggestions:
    suggestion = suggestions[0]
    decision = {
        "building_type": BuildingType(suggestion["building_type"]),
        "location": suggestion["location"],
        "cost": suggestion["cost"],
        "reason": suggestion["reason"]
    }
    
    result = agent.execute_building_decision(
        decision,
        game.terrain_engine,
        game.building_decision_engine
    )
```

### 5. 手动触发交易

```python
# 获取经济建议
advice = game.economy_behavior_engine.get_economic_advice(
    agent_id="Agent1",
    inventory=agent.inventory,
    wallet=agent.wallet
)

# 分析交易机会
opportunity = game.economy_behavior_engine.analyze_economic_opportunity(
    agent_id="Agent1",
    inventory=agent.inventory,
    wallet=agent.wallet,
    other_agents=["Agent2", "Agent3"]
)

if opportunity:
    result = agent.execute_economic_action(
        opportunity,
        game.economy_behavior_engine
    )
```

## 配置选项

### 调整AI决策频率

在Agent类中修改：

```python
# 建造检查间隔（分钟）
agent._last_building_check_interval = 60  # 默认每小时

# 经济行为检查间隔（分钟）
agent._last_economy_check_interval = 30  # 默认每30分钟
```

### 调整Agent偏好

```python
# 设置建造偏好
game.building_decision_engine.agent_building_preferences["Agent1"] = {
    BuildingType.HOUSE.value: 0.5,    # 更喜欢建房子
    BuildingType.FARM.value: 0.3,
    BuildingType.MINE.value: 0.2,
}

# 设置交易策略
from modules.decision.ai_economy_behavior import TradeStrategy
game.economy_behavior_engine.agent_strategies["Agent1"] = TradeStrategy.COOPERATIVE
```

### 调整初始资源

修改Game类的`_initialize_ai_systems`方法：

```python
agent.inventory.add_material(ResourceType.WOOD, 100.0)  # 增加初始木材
agent.inventory.add_material(ResourceType.STONE, 50.0)
# ... 等等
```

## 监控与调试

### 查看Agent日志

所有AI决策都会记录到日志：

```
[INFO] Agent1 建造了 house 在位置 (15, 23)，原因：增加人口容量，满足住房需求
[INFO] Agent2 执行了经济行为 trade：需要 food 资源
[INFO] Agent3 采集了资源：wood: 2.5, stone: 1.8
```

### 查看协作任务

```python
tasks = game.collaboration_coordinator.tasks

for task_id, task in tasks.items():
    print(f"任务: {task.requirements['project_name']}")
    print(f"状态: {task.status.value}")
    print(f"进度: {task.progress * 100:.1f}%")
    print(f"参与者: {task.participants}")
```

### 性能优化

如果Agent数量很多，可以：

1. **增加检查间隔**：减少AI决策频率
2. **限制协作数量**：减少同时进行的协作项目
3. **简化地形**：减小地图大小

```python
# 减小地图
game.terrain_engine = TerrainDevelopmentEngine(width=30, height=30)

# 减少协作频率
# 在AICollaborationCoordinator.auto_coordinate_agents中修改概率
if random.random() > 0.05:  # 从0.1降到0.05
    return
```

## 常见问题

### Q: Agent不建造建筑？

A: 检查：
1. Agent是否有足够资源
2. 建造检查间隔是否太长
3. 社区需求是否足够高

### Q: 交易总是失败？

A: 检查：
1. 两个Agent的库存和钱包余额
2. 交易对象是否有所需资源
3. 查看失败原因的错误消息

### Q: 协作项目没有进展？

A: 检查：
1. 项目状态是否为IN_PROGRESS
2. 参与者是否足够（min_participants）
3. 是否有足够的全局资源

## 未来扩展

可以进一步添加：

1. **高级建筑**：科技建筑、文化建筑等
2. **科技树**：解锁新建筑和物品
3. **自然灾害**：考验Agent的应对能力
4. **市场系统**：中央市场进行大规模交易
5. **外交系统**：Agent之间的联盟和竞争

## 总结

该系统实现了真正的AI自主决策，Agent能够：
- ✅ 自主分析并决定建造内容和位置
- ✅ 智能管理资源和进行经济活动
- ✅ 与其他Agent协作完成大型项目
- ✅ 根据社区需求动态调整行为
- ✅ 形成复杂的经济和社会互动

系统已经完全集成到Game主循环中，无需额外配置即可自动运行！

