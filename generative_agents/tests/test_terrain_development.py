"""
地形开拓测试模块
验证地形开发和建设逻辑
"""

import unittest
import json
import datetime
import tempfile
import os
import math
from typing import Dict, List, Any, Tuple

# 导入需要测试的模块
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules', 'social'))

from terrain_development import (
    TerrainType, ResourceType, BuildingType, DevelopmentPriority,
    TerrainTile, Building, DevelopmentProject, TerrainDevelopmentEngine
)


class TestTerrainTile(unittest.TestCase):
    """地形瓦片测试"""
    
    def setUp(self):
        """测试前准备"""
        self.tile = TerrainTile(
            coord=(10, 20),
            terrain_type=TerrainType.GRASSLAND,
            elevation=50,
            resources={ResourceType.WATER: 30, ResourceType.WOOD: 20}
        )
    
    def test_tile_initialization(self):
        """测试瓦片初始化"""
        self.assertEqual(self.tile.coord, (10, 20))
        self.assertEqual(self.tile.terrain_type, TerrainType.GRASSLAND)
        self.assertEqual(self.tile.elevation, 50)
        self.assertEqual(self.tile.resources[ResourceType.WATER], 30)
        self.assertEqual(self.tile.resources[ResourceType.WOOD], 20)
        self.assertTrue(self.tile.buildable)
        self.assertIsNone(self.tile.building)
    
    def test_can_build(self):
        """测试建造可行性"""
        # 可建造的瓦片
        self.assertTrue(self.tile.can_build(BuildingType.HOUSE))
        
        # 已有建筑的瓦片
        self.tile.building = Building(
            building_id="test_house",
            building_type=BuildingType.HOUSE,
            location=(10, 20)
        )
        self.assertFalse(self.tile.can_build(BuildingType.FARM))
        
        # 不可建造的瓦片
        self.tile.building = None
        self.tile.buildable = False
        self.assertFalse(self.tile.can_build(BuildingType.HOUSE))
    
    def test_extract_resource(self):
        """测试资源提取"""
        initial_water = self.tile.resources[ResourceType.WATER]
        extracted = self.tile.extract_resource(ResourceType.WATER, 10)
        
        self.assertEqual(extracted, 10)
        self.assertEqual(self.tile.resources[ResourceType.WATER], initial_water - 10)
        
        # 提取超过可用量
        extracted = self.tile.extract_resource(ResourceType.WATER, 100)
        self.assertEqual(extracted, initial_water - 10)  # 剩余的全部
        self.assertEqual(self.tile.resources[ResourceType.WATER], 0)
    
    def test_add_resource(self):
        """测试添加资源"""
        initial_stone = self.tile.resources.get(ResourceType.STONE, 0)
        self.tile.add_resource(ResourceType.STONE, 50)
        
        self.assertEqual(self.tile.resources[ResourceType.STONE], initial_stone + 50)
    
    def test_get_suitability(self):
        """测试建筑适宜性"""
        # 草地适合房屋和农场
        house_suitability = self.tile.get_suitability(BuildingType.HOUSE)
        farm_suitability = self.tile.get_suitability(BuildingType.FARM)
        
        self.assertGreaterEqual(house_suitability, 0.0)
        self.assertLessEqual(house_suitability, 1.0)
        self.assertGreaterEqual(farm_suitability, 0.0)
        self.assertLessEqual(farm_suitability, 1.0)
        
        # 草地不太适合矿场
        mine_suitability = self.tile.get_suitability(BuildingType.MINE)
        self.assertLess(mine_suitability, house_suitability)
    
    def test_tile_serialization(self):
        """测试瓦片序列化"""
        data = self.tile.to_dict()
        
        # 验证必要字段
        self.assertIn("coord", data)
        self.assertIn("terrain_type", data)
        self.assertIn("elevation", data)
        self.assertIn("resources", data)
        
        # 测试反序列化
        new_tile = TerrainTile.from_dict(data)
        self.assertEqual(new_tile.coord, self.tile.coord)
        self.assertEqual(new_tile.terrain_type, self.tile.terrain_type)
        self.assertEqual(new_tile.elevation, self.tile.elevation)


class TestBuilding(unittest.TestCase):
    """建筑测试"""
    
    def setUp(self):
        """测试前准备"""
        self.building = Building(
            building_id="test_house_001",
            building_type=BuildingType.HOUSE,
            location=(15, 25),
            owner_id="alice"
        )
    
    def test_building_initialization(self):
        """测试建筑初始化"""
        self.assertEqual(self.building.building_id, "test_house_001")
        self.assertEqual(self.building.building_type, BuildingType.HOUSE)
        self.assertEqual(self.building.location, (15, 25))
        self.assertEqual(self.building.owner_id, "alice")
        self.assertEqual(self.building.construction_progress, 0)
        self.assertFalse(self.building.is_completed)
    
    def test_construction_progress(self):
        """测试建造进度"""
        # 增加建造进度
        self.building.add_construction_progress(30)
        self.assertEqual(self.building.construction_progress, 30)
        self.assertFalse(self.building.is_completed)
        
        # 完成建造
        self.building.add_construction_progress(70)
        self.assertEqual(self.building.construction_progress, 100)
        self.assertTrue(self.building.is_completed)
        
        # 超过100%
        self.building.add_construction_progress(20)
        self.assertEqual(self.building.construction_progress, 100)
    
    def test_get_required_resources(self):
        """测试获取所需资源"""
        required = self.building.get_required_resources()
        
        self.assertIsInstance(required, dict)
        self.assertGreater(len(required), 0)
        
        # 房屋应该需要木材和石材
        self.assertIn(ResourceType.WOOD, required)
        self.assertIn(ResourceType.STONE, required)
    
    def test_get_construction_time(self):
        """测试获取建造时间"""
        time_needed = self.building.get_construction_time()
        
        self.assertIsInstance(time_needed, int)
        self.assertGreater(time_needed, 0)
    
    def test_get_maintenance_cost(self):
        """测试获取维护成本"""
        cost = self.building.get_maintenance_cost()
        
        self.assertIsInstance(cost, dict)
        # 维护成本可能为空（新建筑）
        for resource_type, amount in cost.items():
            self.assertGreaterEqual(amount, 0)
    
    def test_building_serialization(self):
        """测试建筑序列化"""
        data = self.building.to_dict()
        
        # 验证必要字段
        self.assertIn("building_id", data)
        self.assertIn("building_type", data)
        self.assertIn("location", data)
        self.assertIn("construction_progress", data)
        
        # 测试反序列化
        new_building = Building.from_dict(data)
        self.assertEqual(new_building.building_id, self.building.building_id)
        self.assertEqual(new_building.building_type, self.building.building_type)
        self.assertEqual(new_building.location, self.building.location)


class TestDevelopmentProject(unittest.TestCase):
    """开发项目测试"""
    
    def setUp(self):
        """测试前准备"""
        self.project = DevelopmentProject(
            project_id="village_expansion_001",
            project_type="settlement_expansion",
            target_area=[(10, 10), (20, 20)],
            priority=DevelopmentPriority.HIGH,
            initiator_id="alice"
        )
    
    def test_project_initialization(self):
        """测试项目初始化"""
        self.assertEqual(self.project.project_id, "village_expansion_001")
        self.assertEqual(self.project.project_type, "settlement_expansion")
        self.assertEqual(self.project.target_area, [(10, 10), (20, 20)])
        self.assertEqual(self.project.priority, DevelopmentPriority.HIGH)
        self.assertEqual(self.project.initiator_id, "alice")
        self.assertEqual(self.project.progress, 0)
        self.assertFalse(self.project.is_completed)
    
    def test_add_task(self):
        """测试添加任务"""
        task = {
            "task_id": "clear_land_001",
            "task_type": "terrain_modification",
            "description": "Clear trees in area (10,10) to (15,15)",
            "required_resources": {ResourceType.TOOL: 2},
            "estimated_time": 5
        }
        
        self.project.add_task(task)
        self.assertEqual(len(self.project.tasks), 1)
        self.assertEqual(self.project.tasks[0]["task_id"], "clear_land_001")
    
    def test_complete_task(self):
        """测试完成任务"""
        # 添加任务
        task1 = {"task_id": "task1", "progress": 0}
        task2 = {"task_id": "task2", "progress": 0}
        self.project.tasks = [task1, task2]
        
        # 完成第一个任务
        result = self.project.complete_task("task1")
        self.assertTrue(result)
        self.assertEqual(self.project.tasks[0]["progress"], 100)
        
        # 尝试完成不存在的任务
        result = self.project.complete_task("nonexistent")
        self.assertFalse(result)
    
    def test_update_progress(self):
        """测试更新进度"""
        # 添加任务
        self.project.tasks = [
            {"task_id": "task1", "progress": 100},
            {"task_id": "task2", "progress": 50},
            {"task_id": "task3", "progress": 0}
        ]
        
        self.project.update_progress()
        
        # 进度应该是所有任务进度的平均值
        expected_progress = (100 + 50 + 0) / 3
        self.assertEqual(self.project.progress, expected_progress)
        self.assertFalse(self.project.is_completed)
        
        # 所有任务完成
        for task in self.project.tasks:
            task["progress"] = 100
        
        self.project.update_progress()
        self.assertEqual(self.project.progress, 100)
        self.assertTrue(self.project.is_completed)
    
    def test_get_required_resources(self):
        """测试获取所需资源"""
        # 添加有资源需求的任务
        self.project.tasks = [
            {"required_resources": {ResourceType.WOOD: 10, ResourceType.STONE: 5}},
            {"required_resources": {ResourceType.WOOD: 5, ResourceType.TOOL: 2}}
        ]
        
        total_resources = self.project.get_required_resources()
        
        self.assertEqual(total_resources[ResourceType.WOOD], 15)
        self.assertEqual(total_resources[ResourceType.STONE], 5)
        self.assertEqual(total_resources[ResourceType.TOOL], 2)
    
    def test_project_serialization(self):
        """测试项目序列化"""
        data = self.project.to_dict()
        
        # 验证必要字段
        self.assertIn("project_id", data)
        self.assertIn("project_type", data)
        self.assertIn("target_area", data)
        self.assertIn("priority", data)
        
        # 测试反序列化
        new_project = DevelopmentProject.from_dict(data)
        self.assertEqual(new_project.project_id, self.project.project_id)
        self.assertEqual(new_project.project_type, self.project.project_type)
        self.assertEqual(new_project.priority, self.project.priority)


class TestTerrainDevelopmentEngine(unittest.TestCase):
    """地形开发引擎测试"""
    
    def setUp(self):
        """测试前准备"""
        self.engine = TerrainDevelopmentEngine()
        
        # 创建测试地形
        self.create_test_terrain()
    
    def create_test_terrain(self):
        """创建测试地形"""
        # 创建一个10x10的测试区域
        for x in range(10):
            for y in range(10):
                # 创建不同类型的地形
                if x < 3:
                    terrain_type = TerrainType.FOREST
                    resources = {ResourceType.WOOD: 50, ResourceType.WATER: 10}
                elif x < 6:
                    terrain_type = TerrainType.GRASSLAND
                    resources = {ResourceType.WATER: 30, ResourceType.FOOD: 20}
                else:
                    terrain_type = TerrainType.MOUNTAIN
                    resources = {ResourceType.STONE: 60, ResourceType.METAL: 30}
                
                tile = TerrainTile(
                    coord=(x, y),
                    terrain_type=terrain_type,
                    elevation=abs(x - 5) * 10 + abs(y - 5) * 5,
                    resources=resources
                )
                
                self.engine.terrain_map[(x, y)] = tile
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        self.assertIsInstance(self.engine.terrain_map, dict)
        self.assertIsInstance(self.engine.buildings, dict)
        self.assertIsInstance(self.engine.projects, dict)
        self.assertEqual(len(self.engine.terrain_map), 100)  # 10x10
    
    def test_get_tile(self):
        """测试获取瓦片"""
        tile = self.engine.get_tile((5, 5))
        self.assertIsNotNone(tile)
        self.assertEqual(tile.coord, (5, 5))
        
        # 不存在的瓦片
        tile = self.engine.get_tile((100, 100))
        self.assertIsNone(tile)
    
    def test_analyze_terrain(self):
        """测试地形分析"""
        analysis = self.engine.analyze_terrain((3, 3), radius=2)
        
        self.assertIsInstance(analysis, dict)
        self.assertIn("terrain_types", analysis)
        self.assertIn("average_elevation", analysis)
        self.assertIn("total_resources", analysis)
        self.assertIn("buildable_tiles", analysis)
        
        # 验证分析结果的合理性
        self.assertGreater(analysis["buildable_tiles"], 0)
        self.assertIsInstance(analysis["total_resources"], dict)
    
    def test_find_suitable_location(self):
        """测试寻找合适位置"""
        # 寻找建造房屋的位置
        location = self.engine.find_suitable_location(
            BuildingType.HOUSE,
            search_area=[(2, 2), (8, 8)]
        )
        
        if location:
            self.assertIsInstance(location, tuple)
            self.assertEqual(len(location), 2)
            
            # 验证位置在搜索区域内
            x, y = location
            self.assertGreaterEqual(x, 2)
            self.assertLessEqual(x, 8)
            self.assertGreaterEqual(y, 2)
            self.assertLessEqual(y, 8)
            
            # 验证位置可建造
            tile = self.engine.get_tile(location)
            self.assertTrue(tile.can_build(BuildingType.HOUSE))
    
    def test_plan_building(self):
        """测试建筑规划"""
        plan = self.engine.plan_building(
            BuildingType.HOUSE,
            owner_id="alice",
            preferred_location=(5, 5)
        )
        
        self.assertIsInstance(plan, dict)
        self.assertIn("building_type", plan)
        self.assertIn("location", plan)
        self.assertIn("required_resources", plan)
        self.assertIn("construction_time", plan)
        self.assertIn("suitability_score", plan)
        
        # 验证规划的合理性
        self.assertEqual(plan["building_type"], BuildingType.HOUSE)
        self.assertIsInstance(plan["required_resources"], dict)
        self.assertGreater(plan["construction_time"], 0)
    
    def test_construct_building(self):
        """测试建造建筑"""
        # 先规划建筑
        plan = self.engine.plan_building(
            BuildingType.HOUSE,
            owner_id="alice",
            preferred_location=(5, 5)
        )
        
        # 建造建筑
        result = self.engine.construct_building(plan)
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("building_id", result)
        
        if result["success"]:
            building_id = result["building_id"]
            
            # 验证建筑已添加
            self.assertIn(building_id, self.engine.buildings)
            
            # 验证瓦片状态更新
            location = plan["location"]
            tile = self.engine.get_tile(location)
            self.assertIsNotNone(tile.building)
            self.assertEqual(tile.building.building_id, building_id)
    
    def test_create_development_project(self):
        """测试创建开发项目"""
        project = self.engine.create_development_project(
            project_type="settlement_expansion",
            target_area=[(4, 4), (6, 6)],
            priority=DevelopmentPriority.HIGH,
            initiator_id="alice"
        )
        
        self.assertIsInstance(project, DevelopmentProject)
        self.assertEqual(project.project_type, "settlement_expansion")
        self.assertEqual(project.priority, DevelopmentPriority.HIGH)
        self.assertEqual(project.initiator_id, "alice")
        
        # 验证项目已添加到引擎
        self.assertIn(project.project_id, self.engine.projects)
    
    def test_execute_project_task(self):
        """测试执行项目任务"""
        # 创建项目
        project = self.engine.create_development_project(
            project_type="resource_extraction",
            target_area=[(2, 2), (3, 3)],
            priority=DevelopmentPriority.MEDIUM,
            initiator_id="bob"
        )
        
        # 添加任务
        task = {
            "task_id": "extract_wood_001",
            "task_type": "resource_extraction",
            "target_location": (2, 2),
            "resource_type": ResourceType.WOOD,
            "amount": 20,
            "progress": 0
        }
        project.add_task(task)
        
        # 执行任务
        result = self.engine.execute_project_task(project.project_id, "extract_wood_001")
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        
        if result["success"]:
            # 验证任务进度更新
            updated_task = None
            for t in project.tasks:
                if t["task_id"] == "extract_wood_001":
                    updated_task = t
                    break
            
            self.assertIsNotNone(updated_task)
            self.assertGreater(updated_task["progress"], 0)
    
    def test_allocate_resources(self):
        """测试资源分配"""
        # 创建资源需求
        demands = [
            {
                "demand_id": "house_construction",
                "resources": {ResourceType.WOOD: 30, ResourceType.STONE: 20},
                "priority": 3
            },
            {
                "demand_id": "farm_construction", 
                "resources": {ResourceType.WOOD: 20, ResourceType.TOOL: 5},
                "priority": 2
            }
        ]
        
        allocation = self.engine.allocate_resources(demands)
        
        self.assertIsInstance(allocation, dict)
        self.assertIn("allocations", allocation)
        self.assertIn("remaining_resources", allocation)
        self.assertIn("satisfaction_rate", allocation)
        
        # 验证分配结果
        allocations = allocation["allocations"]
        self.assertIsInstance(allocations, dict)
    
    def test_optimize_layout(self):
        """测试布局优化"""
        # 定义建筑需求
        building_plans = [
            {"type": BuildingType.HOUSE, "count": 3},
            {"type": BuildingType.FARM, "count": 2},
            {"type": BuildingType.WORKSHOP, "count": 1}
        ]
        
        optimization = self.engine.optimize_layout(
            building_plans,
            area=[(3, 3), (7, 7)]
        )
        
        self.assertIsInstance(optimization, dict)
        self.assertIn("layout", optimization)
        self.assertIn("efficiency_score", optimization)
        self.assertIn("resource_accessibility", optimization)
        
        # 验证布局合理性
        layout = optimization["layout"]
        self.assertIsInstance(layout, list)
        
        for building_plan in layout:
            self.assertIn("type", building_plan)
            self.assertIn("location", building_plan)
            self.assertIn("score", building_plan)
    
    def test_simulate_development(self):
        """测试开发模拟"""
        # 创建开发项目
        project = self.engine.create_development_project(
            project_type="village_development",
            target_area=[(4, 4), (6, 6)],
            priority=DevelopmentPriority.HIGH,
            initiator_id="alice"
        )
        
        # 添加多个任务
        tasks = [
            {
                "task_id": "clear_land",
                "task_type": "terrain_modification",
                "progress": 0,
                "estimated_time": 3
            },
            {
                "task_id": "build_house",
                "task_type": "construction",
                "progress": 0,
                "estimated_time": 5
            }
        ]
        
        for task in tasks:
            project.add_task(task)
        
        # 模拟开发过程
        simulation_result = self.engine.simulate_development(
            project.project_id,
            time_steps=10
        )
        
        self.assertIsInstance(simulation_result, dict)
        self.assertIn("final_progress", simulation_result)
        self.assertIn("time_taken", simulation_result)
        self.assertIn("resources_consumed", simulation_result)
        self.assertIn("events", simulation_result)
        
        # 验证模拟结果
        self.assertGreaterEqual(simulation_result["final_progress"], 0)
        self.assertLessEqual(simulation_result["final_progress"], 100)
    
    def test_get_development_statistics(self):
        """测试获取开发统计"""
        # 创建一些建筑和项目
        self.engine.construct_building({
            "building_type": BuildingType.HOUSE,
            "location": (5, 5),
            "owner_id": "alice"
        })
        
        self.engine.create_development_project(
            project_type="expansion",
            target_area=[(7, 7), (9, 9)],
            priority=DevelopmentPriority.LOW,
            initiator_id="bob"
        )
        
        stats = self.engine.get_development_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("total_buildings", stats)
        self.assertIn("building_types", stats)
        self.assertIn("total_projects", stats)
        self.assertIn("project_status", stats)
        self.assertIn("terrain_utilization", stats)
        self.assertIn("resource_distribution", stats)
        
        # 验证统计数据
        self.assertGreaterEqual(stats["total_buildings"], 1)
        self.assertGreaterEqual(stats["total_projects"], 1)
    
    def test_save_and_load(self):
        """测试保存和加载"""
        # 添加一些数据
        self.engine.construct_building({
            "building_type": BuildingType.HOUSE,
            "location": (5, 5),
            "owner_id": "alice"
        })
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # 保存
            self.engine.save_to_file(temp_file)
            
            # 创建新引擎并加载
            new_engine = TerrainDevelopmentEngine()
            new_engine.load_from_file(temp_file)
            
            # 验证数据一致性
            self.assertEqual(len(new_engine.terrain_map), len(self.engine.terrain_map))
            self.assertEqual(len(new_engine.buildings), len(self.engine.buildings))
            
            # 验证具体数据
            original_tile = self.engine.get_tile((5, 5))
            loaded_tile = new_engine.get_tile((5, 5))
            
            if original_tile and loaded_tile:
                self.assertEqual(original_tile.terrain_type, loaded_tile.terrain_type)
                self.assertEqual(original_tile.elevation, loaded_tile.elevation)
            
        finally:
            os.unlink(temp_file)


class TestTerrainDevelopmentIntegration(unittest.TestCase):
    """地形开发集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.engine = TerrainDevelopmentEngine()
        self.create_realistic_terrain()
    
    def create_realistic_terrain(self):
        """创建真实的地形"""
        # 创建一个20x20的更大测试区域
        for x in range(20):
            for y in range(20):
                # 基于位置创建真实的地形分布
                distance_from_center = math.sqrt((x - 10)**2 + (y - 10)**2)
                
                if distance_from_center < 3:
                    # 中心区域 - 平原
                    terrain_type = TerrainType.GRASSLAND
                    elevation = 20 + random.randint(-5, 5)
                    resources = {
                        ResourceType.WATER: random.randint(20, 40),
                        ResourceType.FOOD: random.randint(15, 30)
                    }
                elif distance_from_center < 6:
                    # 中间区域 - 森林
                    terrain_type = TerrainType.FOREST
                    elevation = 30 + random.randint(-10, 10)
                    resources = {
                        ResourceType.WOOD: random.randint(40, 70),
                        ResourceType.WATER: random.randint(10, 25)
                    }
                elif distance_from_center < 9:
                    # 外围区域 - 山地
                    terrain_type = TerrainType.MOUNTAIN
                    elevation = 60 + random.randint(-15, 20)
                    resources = {
                        ResourceType.STONE: random.randint(50, 80),
                        ResourceType.METAL: random.randint(20, 40)
                    }
                else:
                    # 边缘区域 - 荒地
                    terrain_type = TerrainType.DESERT
                    elevation = 40 + random.randint(-20, 15)
                    resources = {
                        ResourceType.STONE: random.randint(10, 30)
                    }
                
                tile = TerrainTile(
                    coord=(x, y),
                    terrain_type=terrain_type,
                    elevation=elevation,
                    resources=resources
                )
                
                self.engine.terrain_map[(x, y)] = tile
    
    def test_complete_settlement_development(self):
        """测试完整的定居点开发"""
        # 1. 分析地形，选择定居点位置
        center_analysis = self.engine.analyze_terrain((10, 10), radius=3)
        self.assertGreater(center_analysis["buildable_tiles"], 5)
        
        # 2. 创建定居点开发项目
        settlement_project = self.engine.create_development_project(
            project_type="settlement_establishment",
            target_area=[(8, 8), (12, 12)],
            priority=DevelopmentPriority.HIGH,
            initiator_id="community"
        )
        
        # 3. 规划基础建筑
        building_plans = [
            {"type": BuildingType.HOUSE, "count": 4},
            {"type": BuildingType.FARM, "count": 2},
            {"type": BuildingType.WORKSHOP, "count": 1},
            {"type": BuildingType.MARKET, "count": 1}
        ]
        
        layout_optimization = self.engine.optimize_layout(
            building_plans,
            area=[(8, 8), (12, 12)]
        )
        
        self.assertGreater(layout_optimization["efficiency_score"], 0.5)
        
        # 4. 执行建造
        constructed_buildings = []
        for building_plan in layout_optimization["layout"]:
            construction_plan = self.engine.plan_building(
                building_plan["type"],
                owner_id="community",
                preferred_location=building_plan["location"]
            )
            
            result = self.engine.construct_building(construction_plan)
            if result["success"]:
                constructed_buildings.append(result["building_id"])
        
        # 验证建造结果
        self.assertGreater(len(constructed_buildings), 0)
        
        # 5. 检查定居点统计
        stats = self.engine.get_development_statistics()
        self.assertGreater(stats["total_buildings"], 0)
        self.assertIn(BuildingType.HOUSE, stats["building_types"])
    
    def test_resource_extraction_and_management(self):
        """测试资源提取和管理"""
        # 1. 分析资源分布
        resource_analysis = {}
        for x in range(20):
            for y in range(20):
                tile = self.engine.get_tile((x, y))
                if tile:
                    for resource_type, amount in tile.resources.items():
                        if resource_type not in resource_analysis:
                            resource_analysis[resource_type] = []
                        resource_analysis[resource_type].append((x, y, amount))
        
        # 2. 找到最佳资源提取位置
        best_wood_location = None
        max_wood = 0
        
        if ResourceType.WOOD in resource_analysis:
            for x, y, amount in resource_analysis[ResourceType.WOOD]:
                if amount > max_wood:
                    max_wood = amount
                    best_wood_location = (x, y)
        
        if best_wood_location:
            # 3. 创建资源提取项目
            extraction_project = self.engine.create_development_project(
                project_type="resource_extraction",
                target_area=[best_wood_location, best_wood_location],
                priority=DevelopmentPriority.MEDIUM,
                initiator_id="resource_manager"
            )
            
            # 4. 添加提取任务
            extraction_task = {
                "task_id": "wood_extraction_001",
                "task_type": "resource_extraction",
                "target_location": best_wood_location,
                "resource_type": ResourceType.WOOD,
                "amount": min(max_wood, 30),
                "progress": 0
            }
            extraction_project.add_task(extraction_task)
            
            # 5. 执行提取
            result = self.engine.execute_project_task(
                extraction_project.project_id,
                "wood_extraction_001"
            )
            
            self.assertTrue(result["success"])
            
            # 6. 验证资源变化
            tile = self.engine.get_tile(best_wood_location)
            self.assertLess(tile.resources[ResourceType.WOOD], max_wood)
    
    def test_infrastructure_development(self):
        """测试基础设施开发"""
        # 1. 规划道路网络
        road_project = self.engine.create_development_project(
            project_type="infrastructure_development",
            target_area=[(5, 5), (15, 15)],
            priority=DevelopmentPriority.HIGH,
            initiator_id="city_planner"
        )
        
        # 2. 添加道路建设任务
        road_tasks = []
        for i in range(5, 16):
            # 水平道路
            road_tasks.append({
                "task_id": f"road_h_{i}",
                "task_type": "infrastructure",
                "target_location": (i, 10),
                "infrastructure_type": "road",
                "progress": 0
            })
            
            # 垂直道路
            road_tasks.append({
                "task_id": f"road_v_{i}",
                "task_type": "infrastructure", 
                "target_location": (10, i),
                "infrastructure_type": "road",
                "progress": 0
            })
        
        for task in road_tasks:
            road_project.add_task(task)
        
        # 3. 模拟道路建设
        simulation_result = self.engine.simulate_development(
            road_project.project_id,
            time_steps=20
        )
        
        self.assertGreater(simulation_result["final_progress"], 0)
        
        # 4. 验证基础设施对后续建设的影响
        # 在道路附近建造建筑应该有更高的适宜性
        road_adjacent_location = (11, 10)
        road_plan = self.engine.plan_building(
            BuildingType.HOUSE,
            owner_id="resident",
            preferred_location=road_adjacent_location
        )
        
        remote_location = (2, 2)
        remote_plan = self.engine.plan_building(
            BuildingType.HOUSE,
            owner_id="resident",
            preferred_location=remote_location
        )
        
        # 道路附近的建筑应该有更高的适宜性分数
        self.assertGreaterEqual(
            road_plan["suitability_score"],
            remote_plan["suitability_score"] * 0.8  # 允许一定误差
        )
    
    def test_multi_agent_collaborative_development(self):
        """测试多agent协作开发"""
        # 1. 创建多个开发项目，模拟不同agent的需求
        projects = []
        
        # Alice的住宅项目
        alice_project = self.engine.create_development_project(
            project_type="residential_development",
            target_area=[(7, 7), (9, 9)],
            priority=DevelopmentPriority.HIGH,
            initiator_id="alice"
        )
        projects.append(alice_project)
        
        # Bob的农业项目
        bob_project = self.engine.create_development_project(
            project_type="agricultural_development",
            target_area=[(12, 12), (15, 15)],
            priority=DevelopmentPriority.MEDIUM,
            initiator_id="bob"
        )
        projects.append(bob_project)
        
        # Charlie的工业项目
        charlie_project = self.engine.create_development_project(
            project_type="industrial_development",
            target_area=[(5, 15), (8, 18)],
            priority=DevelopmentPriority.LOW,
            initiator_id="charlie"
        )
        projects.append(charlie_project)
        
        # 2. 为每个项目添加任务
        # Alice的任务
        alice_project.add_task({
            "task_id": "alice_house_1",
            "task_type": "construction",
            "building_type": BuildingType.HOUSE,
            "location": (8, 8),
            "progress": 0
        })
        
        # Bob的任务
        bob_project.add_task({
            "task_id": "bob_farm_1",
            "task_type": "construction",
            "building_type": BuildingType.FARM,
            "location": (13, 13),
            "progress": 0
        })
        
        # Charlie的任务
        charlie_project.add_task({
            "task_id": "charlie_workshop_1",
            "task_type": "construction",
            "building_type": BuildingType.WORKSHOP,
            "location": (6, 16),
            "progress": 0
        })
        
        # 3. 模拟资源竞争和分配
        all_demands = []
        for project in projects:
            required_resources = project.get_required_resources()
            all_demands.append({
                "demand_id": project.project_id,
                "resources": required_resources,
                "priority": project.priority.value
            })
        
        allocation_result = self.engine.allocate_resources(all_demands)
        
        # 4. 验证资源分配的公平性
        self.assertGreater(allocation_result["satisfaction_rate"], 0.3)
        
        # 5. 按优先级执行项目
        for project in sorted(projects, key=lambda p: p.priority.value, reverse=True):
            if project.project_id in allocation_result["allocations"]:
                # 模拟项目执行
                simulation_result = self.engine.simulate_development(
                    project.project_id,
                    time_steps=10
                )
                
                self.assertGreater(simulation_result["final_progress"], 0)
        
        # 6. 检查最终开发状态
        final_stats = self.engine.get_development_statistics()
        self.assertGreater(final_stats["total_projects"], 2)
        
        # 验证不同类型的建筑都有建造
        building_types = final_stats["building_types"]
        self.assertGreater(len(building_types), 0)


def run_terrain_development_tests():
    """运行所有地形开发测试"""
    import random
    random.seed(42)  # 设置随机种子以确保测试结果可重现
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestTerrainTile,
        TestBuilding,
        TestDevelopmentProject,
        TestTerrainDevelopmentEngine,
        TestTerrainDevelopmentIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("开始运行地形开发测试...")
    result = run_terrain_development_tests()
    
    if result.wasSuccessful():
        print("\n✅ 所有地形开发测试通过！")
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        
        for test, traceback in result.failures:
            print(f"\n失败测试: {test}")
            print(traceback)
        
        for test, traceback in result.errors:
            print(f"\n错误测试: {test}")
            print(traceback)