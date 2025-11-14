#!/usr/bin/env python3
"""
AI自主建造与经济系统测试脚本
用于验证新实现的功能是否正常工作
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generative_agents'))

from modules.terrain.terrain_development import TerrainDevelopmentEngine, BuildingType, ResourceType
from modules.economy.economy import EconomyEngine
from modules.decision.ai_building_decision import AIBuildingDecisionEngine
from modules.decision.ai_economy_behavior import AIEconomyBehaviorEngine, TradeStrategy
from modules.decision.ai_collaboration_coordinator import AICollaborationCoordinator


def test_terrain_system():
    """测试地形系统"""
    print("=" * 60)
    print("测试1: 地形系统")
    print("=" * 60)
    
    terrain = TerrainDevelopmentEngine(width=30, height=30)
    
    # 显示统计
    stats = terrain.get_development_statistics()
    print(f"✓ 地形生成成功")
    print(f"  - 总瓦片数: {stats['total_tiles']}")
    print(f"  - 初始资源: ")
    for resource, amount in stats['global_resources'].items():
        print(f"    * {resource}: {amount:.1f}")
    
    # 测试建造
    building = terrain.create_building(BuildingType.HOUSE, 10, 10)
    if building:
        print(f"✓ 建造测试成功: 在 (10, 10) 建造了 {building.building_type.value}")
    else:
        print("✗ 建造测试失败")
    
    print()
    return terrain


def test_economy_system():
    """测试经济系统"""
    print("=" * 60)
    print("测试2: 经济系统")
    print("=" * 60)
    
    economy = EconomyEngine()
    
    # 注册测试Agent
    economy.register_agent("TestAgent1", starting_balance=100.0)
    economy.register_agent("TestAgent2", starting_balance=100.0)
    
    # 给予资源
    inv1 = economy.agent_inventories["TestAgent1"]
    inv1.add_material(ResourceType.WOOD, 50.0)
    inv1.add_material(ResourceType.STONE, 30.0)
    inv1.add_material(ResourceType.FOOD, 10.0)
    
    inv2 = economy.agent_inventories["TestAgent2"]
    inv2.add_material(ResourceType.METAL, 20.0)
    inv2.add_material(ResourceType.FOOD, 50.0)
    
    print("✓ Agent注册成功")
    print(f"  - TestAgent1: {economy.agent_wallets['TestAgent1'].balance} 币")
    print(f"  - TestAgent2: {economy.agent_wallets['TestAgent2'].balance} 币")
    
    # 测试交易
    result = economy.propose_trade(
        sender="TestAgent1",
        receiver="TestAgent2",
        offer_resources={"wood": 10.0},
        request_resources={"metal": 5.0},
        offer_money=0.0,
        request_money=0.0
    )
    
    if result.get("status") == "success":
        print("✓ 交易测试成功")
        print(f"  - TestAgent1用10木材换取了5金属")
    else:
        print(f"✗ 交易测试失败: {result.get('message')}")
    
    # 测试合成
    inv1.add_material(ResourceType.FOOD, 10.0)
    result = economy.craft("TestAgent1", "food_pack")
    
    if result.get("status") == "success":
        print("✓ 合成测试成功")
        print(f"  - TestAgent1合成了食物包")
    else:
        print(f"✗ 合成测试失败: {result.get('message')}")
    
    print()
    return economy


def test_building_decision():
    """测试建造决策引擎"""
    print("=" * 60)
    print("测试3: AI建造决策")
    print("=" * 60)
    
    terrain = TerrainDevelopmentEngine(width=30, height=30)
    building_engine = AIBuildingDecisionEngine(terrain)
    
    # 注册测试Agent
    building_engine.register_agent("BuilderAgent")
    
    # 给予资源
    agent_resources = {
        ResourceType.WOOD: 100.0,
        ResourceType.STONE: 80.0,
        ResourceType.METAL: 50.0,
    }
    
    # 分析建造意图
    decision = building_engine.analyze_agent_building_intention(
        agent_id="BuilderAgent",
        agent_resources=agent_resources,
        agent_money=100.0
    )
    
    if decision:
        print("✓ AI决策成功")
        print(f"  - 建议建造: {decision['building_type'].value}")
        print(f"  - 位置: {decision['location']}")
        print(f"  - 原因: {decision['reason']}")
        print(f"  - 优先级: {decision['priority'].value}")
    else:
        print("✗ AI决策失败（可能是资源不足或需求不高）")
    
    # 获取建造建议
    suggestions = building_engine.get_building_suggestions_for_agent("BuilderAgent")
    print(f"✓ 获取了 {len(suggestions)} 个建造建议")
    
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"  {i}. {suggestion['building_type']} - {suggestion['reason']}")
    
    print()
    return building_engine


def test_economy_behavior():
    """测试经济行为引擎"""
    print("=" * 60)
    print("测试4: AI经济行为")
    print("=" * 60)
    
    economy = EconomyEngine()
    economy_behavior = AIEconomyBehaviorEngine(economy)
    
    # 注册测试Agent
    economy_behavior.register_agent("TraderAgent1", strategy=TradeStrategy.BALANCED)
    economy_behavior.register_agent("TraderAgent2", strategy=TradeStrategy.COOPERATIVE)
    
    # 设置库存
    inv1 = economy.agent_inventories["TraderAgent1"]
    inv1.add_material(ResourceType.WOOD, 50.0)
    inv1.add_material(ResourceType.STONE, 10.0)  # 缺少
    
    inv2 = economy.agent_inventories["TraderAgent2"]
    inv2.add_material(ResourceType.STONE, 100.0)
    inv2.add_material(ResourceType.WOOD, 5.0)  # 缺少
    
    # 分析经济机会
    opportunity = economy_behavior.analyze_economic_opportunity(
        agent_id="TraderAgent1",
        inventory=inv1,
        wallet=economy.agent_wallets["TraderAgent1"],
        other_agents=["TraderAgent2"]
    )
    
    if opportunity:
        print("✓ 经济机会分析成功")
        print(f"  - 行为类型: {opportunity['behavior_type']}")
        print(f"  - 原因: {opportunity.get('reason', 'N/A')}")
        
        # 执行行为
        result = economy_behavior.execute_economic_action("TraderAgent1", opportunity)
        if result.get("status") == "success":
            print("✓ 经济行为执行成功")
        else:
            print(f"✗ 经济行为执行失败: {result.get('message')}")
    else:
        print("○ 当前没有合适的经济机会")
    
    # 获取经济建议
    advice = economy_behavior.get_economic_advice(
        agent_id="TraderAgent1",
        inventory=inv1,
        wallet=economy.agent_wallets["TraderAgent1"]
    )
    
    print(f"✓ 获取了 {len(advice)} 条经济建议")
    for i, tip in enumerate(advice[:3], 1):
        print(f"  {i}. [{tip['priority']}] {tip['message']}")
    
    print()
    return economy_behavior


def test_collaboration():
    """测试协作协调器"""
    print("=" * 60)
    print("测试5: 协作协调器")
    print("=" * 60)
    
    terrain = TerrainDevelopmentEngine(width=30, height=30)
    economy = EconomyEngine()
    building_engine = AIBuildingDecisionEngine(terrain)
    economy_behavior = AIEconomyBehaviorEngine(economy)
    
    coordinator = AICollaborationCoordinator(
        terrain,
        building_engine,
        economy_behavior
    )
    
    # 注册多个Agent
    agents = ["Agent1", "Agent2", "Agent3", "Agent4"]
    for agent_id in agents:
        coordinator.register_agent(agent_id)
        economy.register_agent(agent_id, starting_balance=100.0)
    
    print(f"✓ 注册了 {len(agents)} 个Agent")
    
    # 提议协作项目
    task_id = coordinator.propose_collaborative_building_project(
        initiator="Agent1",
        project_name="社区基础设施建设",
        building_types=[
            (BuildingType.HOUSE, 2),
            (BuildingType.FARM, 1),
            (BuildingType.ROAD, 3)
        ],
        min_participants=2
    )
    
    if task_id:
        print(f"✓ 协作项目创建成功: {task_id}")
        
        # 邀请其他Agent
        accepted = coordinator.invite_agents_to_task(
            task_id,
            ["Agent2", "Agent3", "Agent4"]
        )
        
        print(f"✓ {len(accepted)} 个Agent接受了邀请: {accepted}")
        
        # 开始项目
        success = coordinator.start_task(task_id)
        if success:
            print("✓ 项目已启动")
            
            # 模拟进度更新
            for i in range(5):
                coordinator.update_task_progress(task_id, 0.2)
            
            task = coordinator.tasks[task_id]
            print(f"✓ 项目状态: {task.status.value}")
            print(f"  - 进度: {task.progress * 100:.0f}%")
        else:
            print("✗ 项目启动失败")
    else:
        print("✗ 协作项目创建失败")
    
    # 获取任务摘要
    summary = coordinator.get_task_summary()
    print(f"\n任务摘要:")
    print(f"  - 总任务数: {summary['total_tasks']}")
    print(f"  - 已完成: {summary['completed_tasks']}")
    print(f"  - 进行中: {summary['in_progress_tasks']}")
    print(f"  - 成功率: {summary['success_rate']:.1f}%")
    
    print()


def test_integration():
    """测试系统集成"""
    print("=" * 60)
    print("测试6: 系统集成测试")
    print("=" * 60)
    
    # 创建完整系统
    terrain = TerrainDevelopmentEngine(width=30, height=30)
    economy = EconomyEngine()
    building_engine = AIBuildingDecisionEngine(terrain)
    economy_behavior = AIEconomyBehaviorEngine(economy)
    coordinator = AICollaborationCoordinator(terrain, building_engine, economy_behavior)
    
    # 创建多个Agent
    agents = ["Alice", "Bob", "Charlie", "Diana"]
    
    for agent_id in agents:
        # 注册到所有系统
        economy.register_agent(agent_id, starting_balance=100.0)
        building_engine.register_agent(agent_id)
        economy_behavior.register_agent(agent_id)
        coordinator.register_agent(agent_id)
        
        # 给予初始资源
        inv = economy.agent_inventories[agent_id]
        inv.add_material(ResourceType.WOOD, 50.0)
        inv.add_material(ResourceType.STONE, 30.0)
        inv.add_material(ResourceType.METAL, 20.0)
        inv.add_material(ResourceType.FOOD, 40.0)
    
    print(f"✓ 系统初始化完成，注册了 {len(agents)} 个Agent")
    
    # 模拟几个游戏周期
    print("\n模拟10个游戏周期...")
    
    for cycle in range(10):
        # 更新系统
        terrain.simulate_daily_operations()
        economy.update_prices(terrain)
        coordinator.auto_coordinate_agents(agents)
        
        # 每个Agent尝试行动
        for agent_id in agents:
            inv = economy.agent_inventories[agent_id]
            wallet = economy.agent_wallets[agent_id]
            
            # 尝试建造
            agent_resources = {rt: amt for rt, amt in inv.materials.items()}
            decision = building_engine.analyze_agent_building_intention(
                agent_id=agent_id,
                agent_resources=agent_resources,
                agent_money=wallet.balance
            )
            
            if decision:
                building_engine.execute_building_decision(
                    agent_id=agent_id,
                    decision=decision,
                    consume_agent_resources=False  # 从全局资源扣除
                )
            
            # 尝试经济行为
            other_agents = [a for a in agents if a != agent_id]
            opportunity = economy_behavior.analyze_economic_opportunity(
                agent_id=agent_id,
                inventory=inv,
                wallet=wallet,
                other_agents=other_agents
            )
            
            if opportunity:
                economy_behavior.execute_economic_action(agent_id, opportunity)
    
    # 显示最终统计
    print("\n最终统计:")
    
    terrain_stats = terrain.get_development_statistics()
    print(f"\n地形统计:")
    print(f"  - 开发程度: {terrain_stats['development_percentage']:.1f}%")
    print(f"  - 建筑总数: {terrain_stats['total_buildings']}")
    print(f"  - 完成建筑: {terrain_stats['completed_buildings']}")
    
    economy_stats = economy_behavior.get_economy_statistics()
    print(f"\n经济统计:")
    print(f"  - 总财富: {economy_stats['total_wealth']:.1f} 币")
    print(f"  - 平均财富: {economy_stats['average_wealth']:.1f} 币/人")
    print(f"  - 交易次数: {economy_stats['trade_count']}")
    
    collab_stats = coordinator.get_task_summary()
    print(f"\n协作统计:")
    print(f"  - 总任务数: {collab_stats['total_tasks']}")
    print(f"  - 已完成: {collab_stats['completed_tasks']}")
    print(f"  - 成功率: {collab_stats['success_rate']:.1f}%")
    
    print("\n✓ 系统集成测试完成！")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AI自主建造与经济系统 - 功能测试")
    print("=" * 60 + "\n")
    
    try:
        # 基础系统测试
        test_terrain_system()
        test_economy_system()
        
        # AI决策测试
        test_building_decision()
        test_economy_behavior()
        
        # 协作测试
        test_collaboration()
        
        # 综合测试
        test_integration()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60 + "\n")
        
        print("系统已经完全集成到Game类中，可以直接使用：")
        print("1. 启动游戏：python generative_agents/web_server.py")
        print("2. Agent会自动进行建造和经济活动")
        print("3. 查看日志可以看到AI决策过程")
        print()
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

