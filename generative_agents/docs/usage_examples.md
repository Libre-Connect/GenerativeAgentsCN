# AI社会模拟系统使用示例

## 目录
1. [快速开始](#快速开始)
2. [社会关系模拟示例](#社会关系模拟示例)
3. [恋爱关系发展示例](#恋爱关系发展示例)
4. [地形开拓建造示例](#地形开拓建造示例)
5. [AI自主决策示例](#ai自主决策示例)
6. [多AI协作示例](#多ai协作示例)
7. [机器学习应用示例](#机器学习应用示例)
8. [完整模拟场景](#完整模拟场景)
9. [高级用法](#高级用法)
10. [故障排除](#故障排除)

## 快速开始

### 环境准备

```bash
# 克隆项目
git clone https://github.com/your-repo/GenerativeAgentsCN-1.git
cd GenerativeAgentsCN-1

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_database.py

# 启动系统
python main.py
```

### 基础配置

```python
# config/simulation_config.py
SIMULATION_CONFIG = {
    "world_size": (50, 50),
    "initial_agents": 10,
    "time_step_duration": 1.0,  # 秒
    "auto_save_interval": 300,  # 5分钟
    "max_relationships_per_agent": 20,
    "romance_enabled": True,
    "terrain_development_enabled": True,
    "ml_algorithms_enabled": True
}
```

### 创建第一个模拟

```python
from generative_agents.modules.social.relationship import SocialNetwork
from generative_agents.modules.social.romance import RomanceEngine
from generative_agents.modules.social.terrain_development import TerrainDevelopmentEngine
from generative_agents.modules.social.autonomous_decision import AutonomousDecisionEngine
from generative_agents.modules.social.multi_ai_interaction import MultiAIInteractionEngine

# 初始化系统
def initialize_simulation():
    # 创建核心引擎
    social_network = SocialNetwork()
    romance_engine = RomanceEngine(social_network)
    terrain_engine = TerrainDevelopmentEngine()
    decision_engine = AutonomousDecisionEngine()
    interaction_engine = MultiAIInteractionEngine(social_network)
    
    # 创建AI代理
    agents = []
    for i in range(5):
        agent_id = f"agent_{i:03d}"
        agents.append(agent_id)
        
        # 初始化代理的决策系统
        decision_engine.initialize_agent(agent_id)
    
    return {
        "social_network": social_network,
        "romance_engine": romance_engine,
        "terrain_engine": terrain_engine,
        "decision_engine": decision_engine,
        "interaction_engine": interaction_engine,
        "agents": agents
    }

# 运行基础模拟
simulation = initialize_simulation()
print("AI社会模拟系统初始化完成！")
```

## 社会关系模拟示例

### 示例1: 建立友谊关系

```python
from generative_agents.modules.social.relationship import SocialNetwork, RelationshipType

def friendship_development_example():
    """演示友谊关系的建立和发展过程"""
    
    social_network = SocialNetwork()
    
    # 创建两个AI代理
    alice = "agent_alice"
    bob = "agent_bob"
    
    print("=== 友谊发展示例 ===")
    
    # 1. 初次相遇 - 建立陌生人关系
    social_network.add_relationship(
        alice, bob, 
        RelationshipType.STRANGER,
        initial_intimacy=5.0,
        initial_trust=10.0
    )
    
    relationship = social_network.get_relationship(alice, bob)
    print(f"初次相遇: {relationship.relationship_type.value}, 亲密度: {relationship.intimacy:.1f}")
    
    # 2. 多次积极互动
    for i in range(5):
        social_network.update_relationship(
            alice, bob,
            intimacy_change=8.0,
            trust_change=6.0,
            interaction_type="positive_chat"
        )
        
        relationship = social_network.get_relationship(alice, bob)
        print(f"互动 {i+1}: {relationship.relationship_type.value}, 亲密度: {relationship.intimacy:.1f}")
    
    # 3. 特殊事件 - 互相帮助
    social_network.update_relationship(
        alice, bob,
        intimacy_change=15.0,
        trust_change=20.0,
        interaction_type="mutual_help",
        event_description="Bob帮助Alice建造房屋"
    )
    
    relationship = social_network.get_relationship(alice, bob)
    print(f"互相帮助后: {relationship.relationship_type.value}, 亲密度: {relationship.intimacy:.1f}, 信任度: {relationship.trust:.1f}")
    
    # 4. 查看关系历史
    print("\n关系发展历史:")
    for event in relationship.relationship_events[-3:]:
        print(f"- {event.timestamp.strftime('%Y-%m-%d %H:%M')}: {event.event_type} - {event.description}")

# 运行示例
friendship_development_example()
```

### 示例2: 复杂社交网络

```python
def complex_social_network_example():
    """演示复杂社交网络的建立和分析"""
    
    social_network = SocialNetwork()
    
    # 创建一个小社区
    agents = [f"agent_{i:03d}" for i in range(8)]
    
    print("=== 复杂社交网络示例 ===")
    
    # 建立各种关系
    relationships_data = [
        ("agent_000", "agent_001", RelationshipType.FRIEND, 70, 65),
        ("agent_000", "agent_002", RelationshipType.NEIGHBOR, 45, 50),
        ("agent_001", "agent_003", RelationshipType.COLLEAGUE, 55, 60),
        ("agent_002", "agent_004", RelationshipType.FAMILY, 90, 95),
        ("agent_003", "agent_005", RelationshipType.CLOSE_FRIEND, 85, 80),
        ("agent_004", "agent_006", RelationshipType.ACQUAINTANCE, 25, 30),
        ("agent_005", "agent_007", RelationshipType.FRIEND, 60, 55),
        ("agent_006", "agent_007", RelationshipType.NEIGHBOR, 40, 45),
    ]
    
    for agent_a, agent_b, rel_type, intimacy, trust in relationships_data:
        social_network.add_relationship(
            agent_a, agent_b, rel_type,
            initial_intimacy=intimacy,
            initial_trust=trust
        )
    
    # 分析社交网络
    print("\n社交网络统计:")
    stats = social_network.get_network_statistics()
    print(f"总关系数: {stats['total_relationships']}")
    print(f"平均亲密度: {stats['average_intimacy']:.1f}")
    print(f"平均信任度: {stats['average_trust']:.1f}")
    
    print("\n关系类型分布:")
    for rel_type, count in stats['relationship_type_distribution'].items():
        print(f"- {rel_type}: {count}")
    
    # 分析特定代理的社交网络
    agent_id = "agent_000"
    relationships = social_network.get_agent_relationships(agent_id)
    
    print(f"\n{agent_id} 的社交关系:")
    for rel in relationships:
        other_agent = rel.agent_b if rel.agent_a == agent_id else rel.agent_a
        print(f"- {other_agent}: {rel.relationship_type.value} (亲密度: {rel.intimacy:.1f})")

# 运行示例
complex_social_network_example()
```

## 恋爱关系发展示例

### 示例1: 完整恋爱流程

```python
from generative_agents.modules.social.romance import RomanceEngine, RomanceStage, DateType

def complete_romance_example():
    """演示完整的恋爱发展流程"""
    
    social_network = SocialNetwork()
    romance_engine = RomanceEngine(social_network)
    
    # 创建两个AI代理
    alice = "agent_alice"
    bob = "agent_bob"
    
    print("=== 完整恋爱流程示例 ===")
    
    # 1. 初始关系建立
    social_network.add_relationship(
        alice, bob, RelationshipType.ACQUAINTANCE,
        initial_intimacy=20.0, initial_trust=25.0
    )
    
    # 2. 检查恋爱潜力
    potential = romance_engine.check_romance_potential(alice, bob)
    print(f"恋爱潜力评估: {potential:.1f}%")
    
    if potential > 60:
        # 3. 发起恋爱关系
        success = romance_engine.initiate_romance(alice, bob)
        if success:
            print("恋爱关系发起成功！")
            
            # 4. 规划和执行约会
            for i in range(3):
                date_types = [DateType.CASUAL_DATE, DateType.ROMANTIC_DATE, DateType.ADVENTURE_DATE]
                date_type = date_types[i]
                
                date_plan = romance_engine.plan_date(alice, bob, date_type)
                print(f"\n约会 {i+1} 计划:")
                print(f"- 类型: {date_type.value}")
                print(f"- 活动: {date_plan['activity']}")
                print(f"- 地点: {date_plan['location']}")
                print(f"- 成功概率: {date_plan['success_probability']:.1%}")
                
                # 执行约会
                date_result = romance_engine.execute_date(alice, bob, date_plan)
                print(f"约会结果: {'成功' if date_result['success'] else '失败'}")
                print(f"关系影响: +{date_result['intimacy_change']:.1f} 亲密度")
                
                # 检查关系状态
                relationship = social_network.get_relationship(alice, bob)
                print(f"当前亲密度: {relationship.intimacy:.1f}")
            
            # 5. 尝试表白
            if relationship.intimacy > 70:
                confession_result = romance_engine.attempt_confession(alice, bob)
                if confession_result['success']:
                    print("\n表白成功！关系升级为恋人")
                    
                    # 6. 继续发展关系
                    for _ in range(5):
                        romance_engine.trigger_romance_event(alice, bob)
                    
                    # 7. 尝试求婚
                    relationship = social_network.get_relationship(alice, bob)
                    if relationship.intimacy > 90:
                        proposal_result = romance_engine.attempt_proposal(alice, bob)
                        if proposal_result['success']:
                            print("\n求婚成功！")
                            
                            # 8. 举办婚礼
                            wedding_result = romance_engine.plan_wedding(alice, bob)
                            print(f"婚礼计划: {wedding_result['style']}")
                            print(f"预计费用: {wedding_result['cost']}")
                            
                            execute_result = romance_engine.execute_wedding(alice, bob, wedding_result)
                            if execute_result['success']:
                                print("婚礼举办成功！两人正式结为夫妻")

# 运行示例
complete_romance_example()
```

### 示例2: 多角恋爱关系

```python
def love_triangle_example():
    """演示复杂的多角恋爱关系"""
    
    social_network = SocialNetwork()
    romance_engine = RomanceEngine(social_network)
    
    # 创建三个AI代理
    alice = "agent_alice"
    bob = "agent_bob"
    charlie = "agent_charlie"
    
    print("=== 三角恋情示例 ===")
    
    # 建立初始关系
    for agent_a, agent_b in [(alice, bob), (alice, charlie), (bob, charlie)]:
        social_network.add_relationship(
            agent_a, agent_b, RelationshipType.FRIEND,
            initial_intimacy=50.0, initial_trust=45.0
        )
    
    # Alice对Bob和Charlie都有好感
    romance_engine.initiate_romance(alice, bob)
    romance_engine.initiate_romance(alice, charlie)
    
    print("Alice同时对Bob和Charlie产生了好感...")
    
    # 分别发展关系
    for week in range(4):
        print(f"\n第 {week+1} 周:")
        
        # Alice与Bob约会
        bob_date = romance_engine.plan_date(alice, bob, DateType.ROMANTIC_DATE)
        bob_result = romance_engine.execute_date(alice, bob, bob_date)
        
        # Alice与Charlie约会
        charlie_date = romance_engine.plan_date(alice, charlie, DateType.CASUAL_DATE)
        charlie_result = romance_engine.execute_date(alice, charlie, charlie_date)
        
        # 检查关系状态
        bob_rel = social_network.get_relationship(alice, bob)
        charlie_rel = social_network.get_relationship(alice, charlie)
        
        print(f"Alice-Bob 亲密度: {bob_rel.intimacy:.1f}")
        print(f"Alice-Charlie 亲密度: {charlie_rel.intimacy:.1f}")
        
        # 如果Bob和Charlie发现了三角关系
        if week == 2:
            print("Bob和Charlie发现了三角关系，产生了竞争...")
            # 处理关系冲突
            conflict_result = romance_engine.handle_relationship_conflict(
                alice, bob, charlie, "love_triangle"
            )
            print(f"冲突处理结果: {conflict_result['resolution']}")
    
    # 最终选择
    bob_rel = social_network.get_relationship(alice, bob)
    charlie_rel = social_network.get_relationship(alice, charlie)
    
    if bob_rel.intimacy > charlie_rel.intimacy:
        print(f"\nAlice最终选择了Bob (亲密度: {bob_rel.intimacy:.1f})")
        # 结束与Charlie的恋爱关系
        social_network.update_relationship(
            alice, charlie,
            intimacy_change=-30.0,
            interaction_type="relationship_end"
        )
    else:
        print(f"\nAlice最终选择了Charlie (亲密度: {charlie_rel.intimacy:.1f})")
        # 结束与Bob的恋爱关系
        social_network.update_relationship(
            alice, bob,
            intimacy_change=-30.0,
            interaction_type="relationship_end"
        )

# 运行示例
love_triangle_example()
```

## 地形开拓建造示例

### 示例1: 基础建设流程

```python
from generative_agents.modules.social.terrain_development import (
    TerrainDevelopmentEngine, TerrainType, BuildingType, ResourceType
)

def basic_construction_example():
    """演示基础的地形开发和建设流程"""
    
    terrain_engine = TerrainDevelopmentEngine()
    
    print("=== 基础建设流程示例 ===")
    
    # 1. 初始化地形
    terrain_engine.initialize_terrain(width=20, height=20)
    
    # 2. 分析地形
    analysis = terrain_engine.analyze_region(0, 0, 10, 10)
    print("地形分析结果:")
    print(f"- 可建造区域: {analysis['buildable_tiles']} 块")
    print(f"- 主要地形: {analysis['dominant_terrain']}")
    print(f"- 资源分布: {analysis['resource_summary']}")
    
    # 3. 选择建设地点
    suitable_locations = terrain_engine.find_suitable_locations(
        BuildingType.HOUSE, 
        region=(0, 0, 10, 10),
        count=3
    )
    
    print(f"\n找到 {len(suitable_locations)} 个适合建房的地点:")
    for i, location in enumerate(suitable_locations):
        print(f"- 地点 {i+1}: {location['coord']}, 适宜度: {location['suitability']:.2f}")
    
    # 4. 创建建设项目
    project = terrain_engine.create_development_project(
        "新手村建设",
        region=(0, 0, 10, 10),
        manager_id="agent_001"
    )
    
    # 添加建设阶段
    project.add_phase("基础设施", [
        (BuildingType.HOUSE, 3),
        (BuildingType.FARM, 1),
        (BuildingType.WORKSHOP, 1)
    ])
    
    print(f"\n创建项目: {project.name}")
    print(f"项目ID: {project.project_id}")
    
    # 5. 执行建设
    for phase_index in range(len(project.phases)):
        phase = project.phases[phase_index]
        print(f"\n执行阶段: {phase.phase_name}")
        
        # 分配资源
        resource_allocation = {
            ResourceType.WOOD: 100,
            ResourceType.STONE: 80,
            ResourceType.TOOLS: 20
        }
        
        # 执行阶段
        result = terrain_engine.execute_project_phase(
            project.project_id,
            phase_index,
            resource_allocation
        )
        
        print(f"阶段执行结果: {'成功' if result['success'] else '失败'}")
        if result['success']:
            print(f"- 完成建筑: {len(result['completed_buildings'])} 座")
            print(f"- 消耗资源: {result['resource_consumption']}")
            print(f"- 剩余资源: {result['remaining_resources']}")
    
    # 6. 查看最终结果
    final_status = terrain_engine.get_project_status(project.project_id)
    print(f"\n项目最终状态: {final_status['status']}")
    print(f"总体进度: {final_status['overall_progress']:.1%}")

# 运行示例
basic_construction_example()
```

### 示例2: 复杂城市规划

```python
def city_planning_example():
    """演示复杂的城市规划和发展"""
    
    terrain_engine = TerrainDevelopmentEngine()
    
    print("=== 城市规划示例 ===")
    
    # 1. 大规模地形初始化
    terrain_engine.initialize_terrain(width=50, height=50)
    
    # 2. 城市分区规划
    districts = {
        "residential": (5, 5, 20, 20),    # 居住区
        "commercial": (25, 5, 40, 15),    # 商业区
        "industrial": (5, 25, 20, 40),    # 工业区
        "recreational": (25, 25, 40, 40)  # 休闲区
    }
    
    print("城市分区规划:")
    for district_name, bounds in districts.items():
        print(f"- {district_name}: {bounds}")
    
    # 3. 分区开发
    for district_name, (x1, y1, x2, y2) in districts.items():
        print(f"\n开发 {district_name} 区域...")
        
        # 分析区域特性
        analysis = terrain_engine.analyze_region(x1, y1, x2, y2)
        
        # 根据区域类型选择建筑
        if district_name == "residential":
            buildings = [(BuildingType.HOUSE, 15), (BuildingType.SCHOOL, 2)]
        elif district_name == "commercial":
            buildings = [(BuildingType.MARKET, 5), (BuildingType.WORKSHOP, 3)]
        elif district_name == "industrial":
            buildings = [(BuildingType.MINE, 3), (BuildingType.WORKSHOP, 5)]
        else:  # recreational
            buildings = [(BuildingType.TEMPLE, 2)]
        
        # 创建区域开发项目
        project = terrain_engine.create_development_project(
            f"{district_name}区开发",
            region=(x1, y1, x2, y2),
            manager_id="city_planner"
        )
        
        project.add_phase(f"{district_name}建设", buildings)
        
        # 计算所需资源
        total_resources = terrain_engine.calculate_project_resources(project)
        print(f"所需资源: {total_resources}")
        
        # 执行开发（简化版）
        if terrain_engine.check_resource_availability(total_resources):
            result = terrain_engine.execute_project_phase(
                project.project_id, 0, total_resources
            )
            print(f"开发结果: {'成功' if result['success'] else '失败'}")
    
    # 4. 基础设施连接
    print("\n建设基础设施连接...")
    
    # 建设道路网络
    road_network = terrain_engine.plan_road_network(districts)
    terrain_engine.build_infrastructure(road_network)
    
    # 5. 城市统计
    city_stats = terrain_engine.get_city_statistics()
    print("\n城市发展统计:")
    print(f"- 总建筑数: {city_stats['total_buildings']}")
    print(f"- 人口容量: {city_stats['population_capacity']}")
    print(f"- 经济产出: {city_stats['economic_output']}")
    print(f"- 资源消耗: {city_stats['resource_consumption']}")

# 运行示例
city_planning_example()
```

## AI自主决策示例

### 示例1: 基础决策流程

```python
from generative_agents.modules.social.autonomous_decision import (
    AutonomousDecisionEngine, GoalType, ActionType, Priority
)

def basic_decision_example():
    """演示AI的基础决策制定流程"""
    
    decision_engine = AutonomousDecisionEngine()
    agent_id = "agent_alice"
    
    print("=== AI自主决策示例 ===")
    
    # 1. 初始化AI代理
    decision_engine.initialize_agent(agent_id)
    
    # 2. 设置初始状态
    initial_state = {
        "location": (10, 15),
        "resources": {
            "food": 20,
            "water": 30,
            "tools": 5
        },
        "satisfaction": 0.6,
        "health": 0.8,
        "energy": 0.7
    }
    
    decision_engine.update_agent_state(agent_id, initial_state)
    
    # 3. 设置目标
    goals = [
        {
            "goal_type": GoalType.SURVIVAL,
            "description": "维持基本生存需求",
            "priority": Priority.HIGH,
            "target_values": {"food": 50, "water": 60}
        },
        {
            "goal_type": GoalType.SOCIAL,
            "description": "建立3个朋友关系",
            "priority": Priority.MEDIUM,
            "target_values": {"friend_count": 3}
        },
        {
            "goal_type": GoalType.EXPANSION,
            "description": "建造自己的房屋",
            "priority": Priority.LOW,
            "target_values": {"house_built": True}
        }
    ]
    
    for goal in goals:
        decision_engine.add_goal(agent_id, goal)
    
    print(f"为 {agent_id} 设置了 {len(goals)} 个目标")
    
    # 4. 模拟决策过程
    for time_step in range(10):
        print(f"\n时间步 {time_step + 1}:")
        
        # 获取当前状态
        current_state = decision_engine.get_agent_state(agent_id)
        print(f"当前状态: 食物={current_state['resources']['food']}, "
              f"满意度={current_state['satisfaction']:.2f}")
        
        # 制定决策
        decision = decision_engine.make_decision(agent_id)
        
        if decision:
            print(f"决策: {decision['action_type']} - {decision['description']}")
            print(f"预期结果: {decision['expected_outcome']}")
            
            # 执行决策
            execution_result = decision_engine.execute_decision(agent_id, decision)
            
            if execution_result['success']:
                print(f"执行成功: {execution_result['actual_outcome']}")
                
                # 更新状态
                new_state = decision_engine.apply_decision_effects(
                    agent_id, execution_result
                )
                print(f"新状态: 食物={new_state['resources']['food']}, "
                      f"满意度={new_state['satisfaction']:.2f}")
            else:
                print(f"执行失败: {execution_result['failure_reason']}")
        else:
            print("无可用决策选项")
        
        # 检查目标完成情况
        goal_progress = decision_engine.check_goal_progress(agent_id)
        completed_goals = [g for g in goal_progress if g['completed']]
        if completed_goals:
            print(f"完成目标: {[g['description'] for g in completed_goals]}")

# 运行示例
basic_decision_example()
```

### 示例2: 复杂行为模式

```python
def complex_behavior_example():
    """演示复杂的AI行为模式和适应性"""
    
    decision_engine = AutonomousDecisionEngine()
    
    # 创建不同性格的AI代理
    agents = {
        "social_butterfly": {
            "personality": {"extraversion": 0.9, "openness": 0.8},
            "behavior_pattern": "SOCIAL_BUTTERFLY"
        },
        "builder": {
            "personality": {"conscientiousness": 0.9, "openness": 0.7},
            "behavior_pattern": "BUILDER"
        },
        "explorer": {
            "personality": {"openness": 0.9, "extraversion": 0.6},
            "behavior_pattern": "EXPLORER"
        }
    }
    
    print("=== 复杂行为模式示例 ===")
    
    # 初始化所有代理
    for agent_id, config in agents.items():
        decision_engine.initialize_agent(agent_id)
        decision_engine.set_personality(agent_id, config["personality"])
        decision_engine.set_behavior_pattern(agent_id, config["behavior_pattern"])
        
        print(f"初始化 {agent_id}: {config['behavior_pattern']}")
    
    # 模拟环境变化和代理适应
    scenarios = [
        {
            "name": "资源丰富期",
            "environment": {"resource_abundance": 0.8, "social_opportunities": 0.7},
            "duration": 5
        },
        {
            "name": "资源稀缺期", 
            "environment": {"resource_abundance": 0.3, "social_opportunities": 0.4},
            "duration": 5
        },
        {
            "name": "社交活跃期",
            "environment": {"resource_abundance": 0.6, "social_opportunities": 0.9},
            "duration": 5
        }
    ]
    
    for scenario in scenarios:
        print(f"\n=== {scenario['name']} ===")
        
        # 更新环境
        decision_engine.update_environment(scenario["environment"])
        
        # 观察各代理的行为适应
        for time_step in range(scenario["duration"]):
            print(f"\n时间步 {time_step + 1}:")
            
            for agent_id in agents.keys():
                # 代理根据环境和性格做出决策
                decision = decision_engine.make_decision(agent_id)
                
                if decision:
                    print(f"{agent_id}: {decision['action_type']} "
                          f"(优先级: {decision['priority']:.2f})")
                    
                    # 执行并学习
                    result = decision_engine.execute_decision(agent_id, decision)
                    decision_engine.learn_from_outcome(agent_id, decision, result)
        
        # 分析行为模式变化
        print(f"\n{scenario['name']} 行为统计:")
        for agent_id in agents.keys():
            behavior_stats = decision_engine.get_behavior_statistics(agent_id)
            print(f"{agent_id}:")
            print(f"  - 主要行为: {behavior_stats['most_common_action']}")
            print(f"  - 成功率: {behavior_stats['success_rate']:.2%}")
            print(f"  - 适应度: {behavior_stats['adaptation_score']:.2f}")

# 运行示例
complex_behavior_example()
```

## 多AI协作示例

### 示例1: 协作建设项目

```python
from generative_agents.modules.social.multi_ai_interaction import (
    MultiAIInteractionEngine, CollaborationType, InteractionType
)

def collaborative_construction_example():
    """演示多AI协作建设项目"""
    
    social_network = SocialNetwork()
    interaction_engine = MultiAIInteractionEngine(social_network)
    
    # 创建AI团队
    team_members = ["architect", "builder_1", "builder_2", "resource_manager", "coordinator"]
    
    print("=== 协作建设项目示例 ===")
    
    # 1. 建立团队关系
    for i, member_a in enumerate(team_members):
        for member_b in team_members[i+1:]:
            social_network.add_relationship(
                member_a, member_b, RelationshipType.COLLEAGUE,
                initial_intimacy=40.0, initial_trust=50.0
            )
    
    print(f"建立了 {len(team_members)} 人的建设团队")
    
    # 2. 创建协作项目
    project = interaction_engine.create_collaboration_project(
        project_name="社区中心建设",
        collaboration_type=CollaborationType.CONSTRUCTION,
        initiator_id="architect",
        description="建设一个多功能社区中心",
        max_participants=5
    )
    
    # 3. 团队成员加入项目
    for member in team_members[1:]:  # 除了发起者
        join_result = interaction_engine.join_collaboration(
            project.project_id, member,
            contribution={"skills": ["construction"], "time_commitment": 0.8}
        )
        print(f"{member} 加入项目: {'成功' if join_result['success'] else '失败'}")
    
    # 4. 项目规划阶段
    print("\n=== 项目规划阶段 ===")
    
    # 架构师发布设计方案
    design_message = interaction_engine.send_message(
        "architect", None,  # 广播消息
        InteractionType.PROJECT_COMMUNICATION,
        "社区中心设计方案已完成，请大家查看并提供反馈",
        context={"project_id": project.project_id, "phase": "design"}
    )
    
    # 团队成员响应
    for member in ["builder_1", "builder_2", "resource_manager"]:
        response = interaction_engine.send_message(
            member, "architect",
            InteractionType.PROJECT_COMMUNICATION,
            f"设计方案看起来不错，{member} 准备就绪",
            context={"project_id": project.project_id, "response_to": design_message.message_id}
        )
    
    # 5. 资源分配阶段
    print("\n=== 资源分配阶段 ===")
    
    # 资源管理员分配任务
    task_assignments = {
        "builder_1": {"task": "地基建设", "resources": {"stone": 100, "tools": 10}},
        "builder_2": {"task": "墙体建设", "resources": {"wood": 150, "tools": 15}},
        "coordinator": {"task": "进度协调", "resources": {"time": 40}}
    }
    
    for assignee, assignment in task_assignments.items():
        interaction_engine.send_message(
            "resource_manager", assignee,
            InteractionType.TASK_ASSIGNMENT,
            f"任务分配: {assignment['task']}",
            context={"assignment": assignment, "project_id": project.project_id}
        )
    
    # 6. 建设执行阶段
    print("\n=== 建设执行阶段 ===")
    
    for week in range(4):
        print(f"\n第 {week + 1} 周:")
        
        # 模拟工作进展
        for member in ["builder_1", "builder_2"]:
            # 工作进展报告
            progress_report = interaction_engine.send_message(
                member, "coordinator",
                InteractionType.PROGRESS_REPORT,
                f"{member} 本周完成了 25% 的工作",
                context={"progress": 0.25, "week": week + 1}
            )
            
            # 协调员响应
            if week < 3:
                interaction_engine.send_message(
                    "coordinator", member,
                    InteractionType.PROJECT_COMMUNICATION,
                    "进展良好，请继续保持",
                    context={"encouragement": True}
                )
        
        # 检查协作效果
        collaboration_stats = interaction_engine.get_collaboration_statistics(project.project_id)
        print(f"团队协作效率: {collaboration_stats['efficiency']:.2%}")
        print(f"沟通频率: {collaboration_stats['communication_frequency']:.1f} 次/周")
        
        # 处理可能的冲突
        if week == 2:  # 模拟中期冲突
            conflict_message = interaction_engine.send_message(
                "builder_1", "builder_2",
                InteractionType.CONFLICT,
                "我觉得你的建设方法不够高效",
                context={"conflict_type": "work_method"}
            )
            
            # 协调员介入
            resolution = interaction_engine.handle_collaboration_conflict(
                project.project_id, "coordinator", 
                ["builder_1", "builder_2"], "work_method_dispute"
            )
            print(f"冲突解决: {resolution['resolution_method']}")
    
    # 7. 项目完成
    print("\n=== 项目完成 ===")
    
    completion_result = interaction_engine.complete_collaboration_project(project.project_id)
    
    if completion_result['success']:
        print("社区中心建设成功完成！")
        print(f"项目评分: {completion_result['project_rating']:.1f}/10")
        print(f"团队满意度: {completion_result['team_satisfaction']:.2%}")
        
        # 庆祝活动
        celebration = interaction_engine.send_message(
            "coordinator", None,  # 广播
            InteractionType.CELEBRATION,
            "项目成功完成，感谢大家的努力！让我们一起庆祝！",
            context={"project_id": project.project_id, "celebration_type": "completion"}
        )
        
        # 更新团队关系
        for member_a in team_members:
            for member_b in team_members:
                if member_a != member_b:
                    social_network.update_relationship(
                        member_a, member_b,
                        intimacy_change=10.0,
                        trust_change=15.0,
                        interaction_type="successful_collaboration"
                    )

# 运行示例
collaborative_construction_example()
```

### 示例2: 社区治理协作

```python
def community_governance_example():
    """演示社区治理中的多AI协作"""
    
    social_network = SocialNetwork()
    interaction_engine = MultiAIInteractionEngine(social_network)
    
    # 创建社区成员
    community_members = [
        "mayor", "council_member_1", "council_member_2", 
        "citizen_1", "citizen_2", "citizen_3", "citizen_4"
    ]
    
    print("=== 社区治理协作示例 ===")
    
    # 1. 建立社区关系网络
    # 政府官员之间的关系
    for official in ["mayor", "council_member_1", "council_member_2"]:
        for other in ["mayor", "council_member_1", "council_member_2"]:
            if official != other:
                social_network.add_relationship(
                    official, other, RelationshipType.COLLEAGUE,
                    initial_intimacy=60.0, initial_trust=70.0
                )
    
    # 市民之间的关系
    citizens = ["citizen_1", "citizen_2", "citizen_3", "citizen_4"]
    for i, citizen_a in enumerate(citizens):
        for citizen_b in citizens[i+1:]:
            social_network.add_relationship(
                citizen_a, citizen_b, RelationshipType.NEIGHBOR,
                initial_intimacy=45.0, initial_trust=50.0
            )
    
    print("建立了社区关系网络")
    
    # 2. 社区议题讨论
    print("\n=== 社区议题讨论 ===")
    
    # 市长提出新政策议题
    policy_proposal = interaction_engine.send_message(
        "mayor", None,  # 广播给所有人
        InteractionType.ANNOUNCEMENT,
        "提议在社区中心建设新的公园，欢迎大家提供意见",
        context={
            "policy_type": "infrastructure",
            "proposal": "community_park",
            "voting_period": 7
        }
    )
    
    # 3. 公众意见收集
    print("\n收集公众意见:")
    
    citizen_opinions = [
        ("citizen_1", "支持", "公园能提供休闲空间，对社区有益"),
        ("citizen_2", "反对", "担心建设成本过高，影响税收"),
        ("citizen_3", "支持", "孩子们需要更多的游乐场所"),
        ("citizen_4", "中立", "需要更多细节信息才能决定")
    ]
    
    for citizen, stance, reason in citizen_opinions:
        opinion_message = interaction_engine.send_message(
            citizen, "mayor",
            InteractionType.OPINION_SHARING,
            f"关于公园建设，我的立场是{stance}: {reason}",
            context={
                "policy_response": True,
                "stance": stance,
                "proposal_id": policy_proposal.message_id
            }
        )
        print(f"{citizen}: {stance} - {reason}")
    
    # 4. 议会讨论
    print("\n=== 议会讨论 ===")
    
    # 创建议会讨论协作项目
    council_discussion = interaction_engine.create_collaboration_project(
        project_name="公园建设政策讨论",
        collaboration_type=CollaborationType.DECISION_MAKING,
        initiator_id="mayor",
        description="讨论和决定公园建设政策",
        max_participants=3
    )
    
    # 议会成员加入讨论
    for member in ["council_member_1", "council_member_2"]:
        interaction_engine.join_collaboration(
            council_discussion.project_id, member,
            contribution={"role": "council_member", "voting_power": 1}
        )
    
    # 议会成员发表意见
    council_opinions = [
        ("council_member_1", "我认为应该优先考虑市民的支持度"),
        ("council_member_2", "需要详细的财务分析和环境影响评估")
    ]
    
    for member, opinion in council_opinions:
        interaction_engine.send_message(
            member, None,
            InteractionType.DEBATE,
            opinion,
            context={"discussion_id": council_discussion.project_id}
        )
        print(f"{member}: {opinion}")
    
    # 5. 投票决策
    print("\n=== 投票决策 ===")
    
    # 统计民意
    support_count = sum(1 for _, stance, _ in citizen_opinions if stance == "支持")
    total_citizens = len(citizen_opinions)
    public_support = support_count / total_citizens
    
    print(f"公众支持率: {public_support:.1%}")
    
    # 议会投票
    if public_support > 0.5:
        vote_result = "通过"
        # 更新支持者关系
        for citizen, stance, _ in citizen_opinions:
            if stance == "支持":
                social_network.update_relationship(
                    citizen, "mayor",
                    intimacy_change=5.0,
                    trust_change=8.0,
                    interaction_type="policy_agreement"
                )
    else:
        vote_result = "否决"
        # 更新反对者关系
        for citizen, stance, _ in citizen_opinions:
            if stance == "反对":
                social_network.update_relationship(
                    citizen, "mayor",
                    intimacy_change=-3.0,
                    trust_change=-2.0,
                    interaction_type="policy_disagreement"
                )
    
    # 6. 结果公布
    result_announcement = interaction_engine.send_message(
        "mayor", None,
        InteractionType.ANNOUNCEMENT,
        f"经过充分讨论和投票，公园建设提案{vote_result}",
        context={
            "decision_result": vote_result,
            "public_support": public_support,
            "implementation_timeline": "6个月" if vote_result == "通过" else None
        }
    )
    
    print(f"\n决策结果: 公园建设提案{vote_result}")
    
    # 7. 后续行动
    if vote_result == "通过":
        print("\n开始实施公园建设...")
        
        # 创建建设协作项目
        park_construction = interaction_engine.create_collaboration_project(
            project_name="社区公园建设",
            collaboration_type=CollaborationType.CONSTRUCTION,
            initiator_id="mayor",
            description="实施社区公园建设项目"
        )
        
        # 邀请支持者参与建设
        for citizen, stance, _ in citizen_opinions:
            if stance == "支持":
                interaction_engine.send_message(
                    "mayor", citizen,
                    InteractionType.INVITATION,
                    "邀请您参与公园建设的志愿工作",
                    context={"project_id": park_construction.project_id}
                )

# 运行示例
community_governance_example()
```

## 机器学习应用示例

### 示例1: 行为预测和优化

```python
from generative_agents.modules.ml.intelligent_algorithms import (
    IntelligentAlgorithmEngine, PredictionType, OptimizationType
)

def behavior_prediction_example():
    """演示AI行为预测和优化"""
    
    ml_engine = IntelligentAlgorithmEngine()
    
    print("=== AI行为预测示例 ===")
    
    # 1. 准备训练数据
    training_data = []
    
    # 模拟历史行为数据
    for i in range(100):
        agent_features = {
            "personality_openness": random.uniform(0.3, 0.9),
            "personality_extraversion": random.uniform(0.2, 0.8),
            "current_satisfaction": random.uniform(0.4, 0.9),
            "social_connections": random.randint(2, 15),
            "resource_level": random.uniform(0.3, 1.0),
            "time_of_day": random.randint(0, 23)
        }
        
        # 基于特征生成行为标签
        if agent_features["current_satisfaction"] < 0.6:
            behavior = "SEEK_SOCIAL_INTERACTION"
        elif agent_features["resource_level"] < 0.5:
            behavior = "GATHER_RESOURCES"
        elif agent_features["personality_openness"] > 0.7:
            behavior = "EXPLORE_NEW_AREA"
        else:
            behavior = "BUILD_INFRASTRUCTURE"
        
        training_data.append((agent_features, behavior))
    
    # 2. 训练预测模型
    print("训练行为预测模型...")
    ml_engine.train_behavior_predictor(training_data)
    
    # 3. 测试预测
    test_agent = "agent_test"
    test_features = {
        "personality_openness": 0.8,
        "personality_extraversion": 0.6,
        "current_satisfaction": 0.4,
        "social_connections": 5,
        "resource_level": 0.7,
        "time_of_day": 14
    }
    
    prediction = ml_engine.predict_behavior(test_agent, test_features)
    
    print(f"\n预测结果:")
    print(f"代理: {test_agent}")
    print(f"特征: {test_features}")
    print(f"预测行为: {prediction['predicted_behavior']}")
    print(f"置信度: {prediction['confidence']:.2%}")
    print(f"备选行为: {prediction['alternative_behaviors']}")
    
    # 4. 行为优化建议
    optimization_result = ml_engine.optimize_behavior(
        test_agent, test_features, 
        target_outcome="increase_satisfaction"
    )
    
    print(f"\n行为优化建议:")
    print(f"推荐行为: {optimization_result['recommended_behavior']}")
    print(f"预期效果: {optimization_result['expected_outcome']}")
    print(f"优化理由: {optimization_result['reasoning']}")

# 运行示例
behavior_prediction_example()
```

### 示例2: 关系推荐系统

```python
def relationship_recommendation_example():
    """演示智能关系推荐系统"""
    
    ml_engine = IntelligentAlgorithmEngine()
    social_network = SocialNetwork()
    
    print("=== 关系推荐系统示例 ===")
    
    # 1. 创建AI代理群体
    agents_data = {
        "alice": {
            "personality": {"openness": 0.8, "extraversion": 0.7, "agreeableness": 0.9},
            "interests": ["reading", "music", "gardening"],
            "skills": {"social": 8, "creative": 7, "analytical": 6}
        },
        "bob": {
            "personality": {"openness": 0.6, "extraversion": 0.5, "agreeableness": 0.7},
            "interests": ["sports", "technology", "cooking"],
            "skills": {"social": 6, "technical": 9, "physical": 8}
        },
        "charlie": {
            "personality": {"openness": 0.9, "extraversion": 0.8, "agreeableness": 0.8},
            "interests": ["art", "music", "travel"],
            "skills": {"creative": 9, "social": 7, "cultural": 8}
        },
        "diana": {
            "personality": {"openness": 0.7, "extraversion": 0.4, "agreeableness": 0.6},
            "interests": ["reading", "technology", "science"],
            "skills": {"analytical": 9, "technical": 8, "research": 7}
        },
        "eve": {
            "personality": {"openness": 0.5, "extraversion": 0.9, "agreeableness": 0.8},
            "interests": ["sports", "socializing", "events"],
            "skills": {"social": 9, "leadership": 8, "physical": 7}
        }
    }
    
    # 2. 建立一些现有关系
    existing_relationships = [
        ("alice", "charlie", RelationshipType.FRIEND, 70, 65),
        ("bob", "eve", RelationshipType.ACQUAINTANCE, 40, 45),
        ("diana", "alice", RelationshipType.COLLEAGUE, 55, 60)
    ]
    
    for agent_a, agent_b, rel_type, intimacy, trust in existing_relationships:
        social_network.add_relationship(
            agent_a, agent_b, rel_type,
            initial_intimacy=intimacy, initial_trust=trust
        )
    
    print("建立了基础社交网络")
    
    # 3. 为每个代理生成关系推荐
    for agent_id, agent_data in agents_data.items():
        print(f"\n=== {agent_id} 的关系推荐 ===")
        
        # 获取候选代理（排除已有关系的代理）
        existing_relations = social_network.get_agent_relationships(agent_id)
        existing_agents = {rel.agent_b if rel.agent_a == agent_id else rel.agent_a 
                          for rel in existing_relations}
        
        candidates = [other_id for other_id in agents_data.keys() 
                     if other_id != agent_id and other_id not in existing_agents]
        
        if not candidates:
            print("没有可推荐的新关系")
            continue
        
        # 生成推荐
        recommendations = ml_engine.recommend_relationships(
            agent_id, agent_data, candidates, agents_data
        )
        
        print(f"为 {agent_id} 推荐的关系:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec['candidate_id']}")
            print(f"   兼容性评分: {rec['compatibility_score']:.2f}")
            print(f"   推荐理由: {rec['reasons']}")
            print(f"   建议活动: {rec['suggested_activities']}")
            print()
    
    # 4. 模拟关系建立过程
    print("=== 模拟关系建立 ===")
    
    # 选择一个高兼容性的推荐进行模拟
    alice_recommendations = ml_engine.recommend_relationships(
        "alice", agents_data["alice"], 
        ["bob", "diana", "eve"], agents_data
    )
    
    best_match = alice_recommendations[0]
    target_agent = best_match['candidate_id']
    
    print(f"Alice 决定与 {target_agent} 建立关系")
    print(f"兼容性预测: {best_match['compatibility_score']:.2f}")
    
    # 建立关系
    social_network.add_relationship(
        "alice", target_agent, RelationshipType.ACQUAINTANCE,
        initial_intimacy=20.0, initial_trust=25.0
    )
    
    # 模拟关系发展
    for week in range(4):
        # 根据兼容性预测关系发展
        compatibility = best_match['compatibility_score']
        intimacy_gain = compatibility * 0.1 + random.uniform(-0.02, 0.02)
        trust_gain = compatibility * 0.08 + random.uniform(-0.01, 0.03)
        
        social_network.update_relationship(
            "alice", target_agent,
            intimacy_change=intimacy_gain * 10,
            trust_change=trust_gain * 10,
            interaction_type="recommended_interaction"
        )
        
        relationship = social_network.get_relationship("alice", target_agent)
        print(f"第 {week+1} 周: 亲密度 {relationship.intimacy:.1f}, "
              f"信任度 {relationship.trust:.1f}")
    
    # 5. 验证推荐效果
    final_relationship = social_network.get_relationship("alice", target_agent)
    actual_compatibility = (final_relationship.intimacy + final_relationship.trust) / 200
    
    print(f"\n推荐效果验证:")
    print(f"预测兼容性: {best_match['compatibility_score']:.2f}")
    print(f"实际兼容性: {actual_compatibility:.2f}")
    print(f"预测准确度: {1 - abs(best_match['compatibility_score'] - actual_compatibility):.2%}")
    
    # 6. 更新推荐模型
    feedback_data = {
        "agent_id": "alice",
        "recommended_agent": target_agent,
        "predicted_compatibility": best_match['compatibility_score'],
        "actual_compatibility": actual_compatibility,
        "relationship_success": actual_compatibility > 0.6
    }
    
    ml_engine.update_recommendation_model(feedback_data)
    print("推荐模型已根据反馈进行更新")

# 运行示例
relationship_recommendation_example()
```

## 完整模拟场景

### 示例: 虚拟村庄发展

```python
import random
import time
from datetime import datetime, timedelta

def complete_village_simulation():
    """完整的虚拟村庄发展模拟"""
    
    print("=== 虚拟村庄发展完整模拟 ===")
    
    # 初始化所有系统
    social_network = SocialNetwork()
    romance_engine = RomanceEngine(social_network)
    terrain_engine = TerrainDevelopmentEngine()
    decision_engine = AutonomousDecisionEngine()
    interaction_engine = MultiAIInteractionEngine(social_network)
    ml_engine = IntelligentAlgorithmEngine()
    
    # 创建村民
    villagers = []
    villager_data = {}
    
    for i in range(8):
        villager_id = f"villager_{i:02d}"
        villagers.append(villager_id)
        
        # 随机生成村民特征
        villager_data[villager_id] = {
            "name": f"村民{i+1}",
            "personality": {
                "openness": random.uniform(0.3, 0.9),
                "extraversion": random.uniform(0.2, 0.8),
                "agreeableness": random.uniform(0.4, 0.9),
                "conscientiousness": random.uniform(0.3, 0.8)
            },
            "skills": {
                "farming": random.randint(1, 10),
                "building": random.randint(1, 10),
                "social": random.randint(1, 10),
                "crafting": random.randint(1, 10)
            },
            "location": (random.randint(5, 15), random.randint(5, 15)),
            "resources": {
                "food": random.randint(10, 30),
                "wood": random.randint(5, 20),
                "stone": random.randint(3, 15),
                "tools": random.randint(1, 5)
            }
        }
        
        # 初始化决策系统
        decision_engine.initialize_agent(villager_id)
        decision_engine.set_personality(villager_id, villager_data[villager_id]["personality"])
    
    print(f"创建了 {len(villagers)} 个村民")
    
    # 初始化地形
    terrain_engine.initialize_terrain(width=30, height=30)
    print("初始化了 30x30 的地形")
    
    # 模拟村庄发展过程
    simulation_days = 30
    current_date = datetime.now()
    
    for day in range(simulation_days):
        print(f"\n=== 第 {day + 1} 天 ({current_date.strftime('%Y-%m-%d')}) ===")
        
        # 每日活动模拟
        daily_events = []
        
        # 1. AI决策和行动
        for villager_id in villagers:
            # 获取当前状态
            current_state = villager_data[villager_id]
            
            # AI做出决策
            decision = decision_engine.make_decision(villager_id)
            
            if decision:
                action_type = decision['action_type']
                
                if action_type == "SOCIAL_INTERACTION":
                    # 社交互动
                    target_villager = random.choice([v for v in villagers if v != villager_id])
                    
                    # 发送消息
                    message = interaction_engine.send_message(
                        villager_id, target_villager,
                        InteractionType.CHAT,
                        "你好，今天过得怎么样？"
                    )
                    
                    # 更新关系
                    if not social_network.get_relationship(villager_id, target_villager):
                        social_network.add_relationship(
                            villager_id, target_villager, RelationshipType.ACQUAINTANCE,
                            initial_intimacy=15.0, initial_trust=20.0
                        )
                    else:
                        social_network.update_relationship(
                            villager_id, target_villager,
                            intimacy_change=random.uniform(2, 8),
                            trust_change=random.uniform(1, 5),
                            interaction_type="daily_chat"
                        )
                    
                    daily_events.append(f"{villager_data[villager_id]['name']} 与 {villager_data[target_villager]['name']} 聊天")
                
                elif action_type == "BUILD_INFRASTRUCTURE":
                    # 建设活动
                    location = current_state["location"]
                    
                    # 尝试建造房屋
                    if current_state["resources"]["wood"] >= 10 and current_state["resources"]["stone"] >= 5:
                        building_result = terrain_engine.place_building(
                            BuildingType.HOUSE, location[0], location[1], villager_id
                        )
                        
                        if building_result['success']:
                            # 消耗资源
                            villager_data[villager_id]["resources"]["wood"] -= 10
                            villager_data[villager_id]["resources"]["stone"] -= 5
                            daily_events.append(f"{villager_data[villager_id]['name']} 建造了一座房屋")
                
                elif action_type == "GATHER_RESOURCES":
                    # 资源收集
                    resource_gain = {
                        "food": random.randint(3, 8),
                        "wood": random.randint(2, 6),
                        "stone": random.randint(1, 4)
                    }
                    
                    for resource, amount in resource_gain.items():
                        villager_data[villager_id]["resources"][resource] += amount
                    
                    daily_events.append(f"{villager_data[villager_id]['name']} 收集了资源")
        
        # 2. 恋爱关系发展
        if day % 3 == 0:  # 每3天检查一次恋爱关系
            for villager_a in villagers:
                for villager_b in villagers:
                    if villager_a < villager_b:  # 避免重复检查
                        relationship = social_network.get_relationship(villager_a, villager_b)
                        
                        if relationship and relationship.intimacy > 60:
                            # 检查恋爱潜力
                            romance_potential = romance_engine.check_romance_potential(villager_a, villager_b)
                            
                            if romance_potential > 70 and relationship.relationship_type != RelationshipType.LOVER:
                                # 发起恋爱关系
                                success = romance_engine.initiate_romance(villager_a, villager_b)
                                if success:
                                    daily_events.append(
                                        f"{villager_data[villager_a]['name']} 和 {villager_data[villager_b]['name']} 开始恋爱"
                                    )
        
        # 3. 协作项目
        if day % 7 == 0 and day > 0:  # 每周启动一个协作项目
            # 选择项目发起者
            initiator = random.choice(villagers)
            
            # 创建村庄改善项目
            project = interaction_engine.create_collaboration_project(
                project_name=f"村庄改善项目-第{day//7}周",
                collaboration_type=CollaborationType.CONSTRUCTION,
                initiator_id=initiator,
                description="改善村庄基础设施"
            )
            
            # 邀请其他村民参与
            participants = random.sample([v for v in villagers if v != initiator], 3)
            for participant in participants:
                interaction_engine.join_collaboration(
                    project.project_id, participant,
                    contribution={"time": 0.5, "resources": "available"}
                )
            
            daily_events.append(f"启动了新的协作项目，由{villager_data[initiator]['name']}发起")
        
        # 4. 机器学习优化
        if day % 5 == 0:  # 每5天进行一次行为优化
            for villager_id in villagers:
                # 提取特征
                features = ml_engine.extract_features(villager_id, villager_data[villager_id])
                
                # 预测最优行为
                prediction = ml_engine.predict_behavior(villager_id, features)
                
                # 应用优化建议
                if prediction['confidence'] > 0.7:
                    decision_engine.update_behavior_pattern(
                        villager_id, prediction['predicted_behavior']
                    )
        
        # 5. 显示当日事件
        if daily_events:
            print("今日事件:")
            for event in daily_events[:5]:  # 只显示前5个事件
                print(f"- {event}")
        
        # 6. 每周统计
        if (day + 1) % 7 == 0:
            week_num = (day + 1) // 7
            print(f"\n=== 第 {week_num} 周统计 ===")
            
            # 社交网络统计
            network_stats = social_network.get_network_statistics()
            print(f"关系总数: {network_stats['total_relationships']}")
            print(f"平均亲密度: {network_stats['average_intimacy']:.1f}")
            
            # 恋爱关系统计
            love_relationships = [
                rel for rel in social_network.relationships.values()
                if rel.relationship_type == RelationshipType.LOVER
            ]
            print(f"恋爱关系: {len(love_relationships)} 对")
            
            # 建筑统计
            building_count = len(terrain_engine.buildings)
            print(f"建筑总数: {building_count}")
            
            # 资源统计
            total_resources = {}
            for villager_data_item in villager_data.values():
                for resource, amount in villager_data_item["resources"].items():
                    total_resources[resource] = total_resources.get(resource, 0) + amount
            
            print(f"村庄总资源: {total_resources}")
        
        # 更新日期
        current_date += timedelta(days=1)
        
        # 短暂暂停以便观察
        time.sleep(0.1)
    
    # 最终统计
    print(f"\n=== 模拟结束 - 村庄发展总结 ===")
    
    final_stats = {
        "simulation_days": simulation_days,
        "total_villagers": len(villagers),
        "total_relationships": len(social_network.relationships),
        "love_relationships": len([
            rel for rel in social_network.relationships.values()
            if rel.relationship_type == RelationshipType.LOVER
        ]),
        "total_buildings": len(terrain_engine.buildings),
        "collaboration_projects": len(interaction_engine.collaboration_projects)
    }
    
    print(f"模拟天数: {final_stats['simulation_days']}")
    print(f"村民总数: {final_stats['total_villagers']}")
    print(f"关系总数: {final_stats['total_relationships']}")
    print(f"恋爱关系: {final_stats['love_relationships']} 对")
    print(f"建筑总数: {final_stats['total_buildings']}")
    print(f"协作项目: {final_stats['collaboration_projects']} 个")
    
    # 保存模拟结果
    social_network.save_to_file("village_simulation_social_network.json")
    terrain_engine.save_state("village_simulation_terrain.json")
    
    print("\n模拟结果已保存到文件")
    
    return final_stats

# 运行完整模拟
if __name__ == "__main__":
    complete_village_simulation()
```

## 高级用法

### 自定义AI行为模式

```python
def custom_behavior_pattern():
    """创建自定义AI行为模式"""
    
    decision_engine = AutonomousDecisionEngine()
    
    # 定义自定义行为模式
    custom_pattern = {
        "pattern_name": "ARTIST",
        "description": "专注于创作和艺术表达的AI",
        "behavior_weights": {
            "CREATE_ART": 0.4,
            "SOCIAL_INTERACTION": 0.3,
            "GATHER_INSPIRATION": 0.2,
            "SHARE_CREATION": 0.1
        },
        "decision_factors": {
            "creativity_level": 0.5,
            "social_energy": 0.3,
            "inspiration_need": 0.2
        }
    }
    
    # 注册自定义模式
    decision_engine.register_behavior_pattern(custom_pattern)
    
    # 应用到AI代理
    artist_agent = "artist_001"
    decision_engine.initialize_agent(artist_agent)
    decision_engine.set_behavior_pattern(artist_agent, "ARTIST")
    
    print("创建了自定义艺术家行为模式")
```

### 扩展关系类型

```python
def extend_relationship_types():
    """扩展关系类型系统"""
    
    # 定义新的关系类型
    class ExtendedRelationshipType(Enum):
        MENTOR = "mentor"           # 导师关系
        STUDENT = "student"         # 学生关系
        BUSINESS_PARTNER = "business_partner"  # 商业伙伴
        RIVAL = "rival"             # 竞争对手
        ALLY = "ally"               # 盟友
    
    # 扩展关系系统
    social_network = SocialNetwork()
    social_network.register_relationship_type(ExtendedRelationshipType.MENTOR)
    social_network.register_relationship_type(ExtendedRelationshipType.BUSINESS_PARTNER)
    
    print("扩展了关系类型系统")
```

## 故障排除

### 常见问题解决

```python
def troubleshooting_guide():
    """故障排除指南"""
    
    print("=== 常见问题解决方案 ===")
    
    problems_solutions = {
        "AI决策卡死": [
            "检查决策树是否存在循环",
            "验证目标设置是否合理",
            "重置AI状态并重新初始化"
        ],
        "关系更新失败": [
            "确认代理ID存在",
            "检查关系类型是否有效",
            "验证亲密度和信任度数值范围"
        ],
        "地形建设错误": [
            "检查建设位置是否可用",
            "验证资源是否充足",
            "确认建筑类型与地形兼容"
        ],
        "性能问题": [
            "减少同时运行的AI数量",
            "优化决策频率",
            "启用缓存机制"
        ]
    }
    
    for problem, solutions in problems_solutions.items():
        print(f"\n问题: {problem}")
        for i, solution in enumerate(solutions, 1):
            print(f"  {i}. {solution}")

# 运行故障排除指南
troubleshooting_guide()
```

### 性能监控

```python
def performance_monitoring():
    """性能监控示例"""
    
    import psutil
    import time
    
    def monitor_system_performance():
        """监控系统性能"""
        
        start_time = time.time()
        
        # 运行模拟
        simulation = initialize_simulation()
        
        # 监控指标
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"性能监控结果:")
        print(f"- 执行时间: {execution_time:.2f} 秒")
        print(f"- CPU使用率: {cpu_usage:.1f}%")
        print(f"- 内存使用率: {memory_usage:.1f}%")
        
        return {
            "execution_time": execution_time,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage
        }
    
    return monitor_system_performance()

# 运行性能监控
performance_monitoring()
```

## 结语

本文档提供了AI社会模拟系统的详细使用示例，涵盖了从基础功能到高级应用的各个方面。通过这些示例，您可以：

1. **快速上手**: 使用基础示例了解系统功能
2. **深入学习**: 通过复杂示例掌握高级特性
3. **实际应用**: 参考完整场景进行项目开发
4. **问题解决**: 利用故障排除指南解决常见问题

系统具有高度的可扩展性和灵活性，您可以根据具体需求进行定制和扩展。如需更多帮助，请参考API文档和系统设计文档。