"""generative_agents.game"""

import os
import copy

from modules.utils import GenerativeAgentsMap, GenerativeAgentsKey
from modules import utils
from .maze import Maze
from .infinite_maze import InfiniteMaze
from .agent import Agent
from .environment.environment_manager import EnvironmentManager
from .terrain.terrain_development import TerrainDevelopmentEngine
from .economy.economy import EconomyEngine
from .decision.ai_building_decision import AIBuildingDecisionEngine
from .decision.ai_economy_behavior import AIEconomyBehaviorEngine
from .decision.ai_collaboration_coordinator import AICollaborationCoordinator
from .event_bus import EventBus, get_event_bus, publish_building_event, publish_economic_event, publish_system_event


class Game:
    """The Game"""

    def __init__(self, name, static_root, config, conversation, logger=None):
        self.name = name
        self.static_root = static_root
        self.record_iterval = config.get("record_iterval", 30)
        self.logger = logger or utils.IOLogger()
        
        # 初始化事件总线
        self.event_bus = get_event_bus()
        self.logger.info("事件总线已初始化")
        
        # 选择地图类型：infinite或classic
        map_type = config.get("map_type", "infinite")
        if map_type == "infinite":
            # 使用无限地图
            maze_config = {
                "world": config.get("world", "InfiniteWorld"),
                "tile_size": 32,
                "tile_address_keys": ["world", "sector", "arena", "game_object"]
            }
            self.maze = InfiniteMaze(maze_config, self.logger, chunk_size=32)
            self.logger.info("使用无限扩展地图系统")
        else:
            # 使用经典固定地图
            self.maze = Maze(self.load_static(config["maze"]["path"]), self.logger)
            self.logger.info("使用经典固定地图")
        
        self.conversation = conversation
        
        # 初始化环境管理器
        self.environment_manager = EnvironmentManager()
        
        # 初始化地形开拓系统
        self.terrain_engine = TerrainDevelopmentEngine(width=60, height=60)
        self.logger.info("地形开拓系统已初始化")
        
        # 初始化经济系统
        self.economy_engine = EconomyEngine()
        self.logger.info("经济系统已初始化")
        
        # 初始化AI决策引擎（稍后在创建agents后初始化）
        self.building_decision_engine = None
        self.economy_behavior_engine = None
        self.collaboration_coordinator = None
        
        self.agents = {}
        if "agent_base" in config:
            agent_base = config["agent_base"]
        else:
            agent_base = {}
        storage_root = os.path.join(f"results/checkpoints/{name}", "storage")
        if not os.path.isdir(storage_root):
            os.makedirs(storage_root)
        for name, agent in config["agents"].items():
            agent_config = utils.update_dict(
                copy.deepcopy(agent_base), self.load_static(agent["config_path"])
            )
            agent_config = utils.update_dict(agent_config, agent)

            agent_config["storage_root"] = os.path.join(storage_root, name)
            self.agents[name] = Agent(agent_config, self.maze, self.conversation, self.logger, game=self)
        
        # 现在agents创建完成，初始化AI决策引擎
        self._initialize_ai_systems()

    def _initialize_ai_systems(self):
        """初始化AI决策系统"""
        # 初始化建造决策引擎
        self.building_decision_engine = AIBuildingDecisionEngine(self.terrain_engine)
        
        # 初始化经济行为引擎
        self.economy_behavior_engine = AIEconomyBehaviorEngine(self.economy_engine)
        
        # 初始化协作协调器
        self.collaboration_coordinator = AICollaborationCoordinator(
            self.terrain_engine,
            self.building_decision_engine,
            self.economy_behavior_engine
        )
        
        # 为每个Agent注册到各个系统
        from modules.terrain.terrain_development import ResourceType
        for agent_name, agent in self.agents.items():
            # 注册到经济引擎
            self.economy_engine.register_agent(agent_name, starting_balance=100.0)
            
            # 给予初始资源
            agent.inventory.add_material(ResourceType.WOOD, 50.0)
            agent.inventory.add_material(ResourceType.STONE, 30.0)
            agent.inventory.add_material(ResourceType.METAL, 20.0)
            agent.inventory.add_material(ResourceType.FOOD, 40.0)
            agent.inventory.add_material(ResourceType.WATER, 50.0)
            
            # 注册到建造决策引擎
            self.building_decision_engine.register_agent(agent_name)
            
            # 注册到经济行为引擎
            self.economy_behavior_engine.register_agent(agent_name)
            
            # 注册到协作协调器
            self.collaboration_coordinator.register_agent(agent_name)
        
        self.logger.info(f"AI决策系统已初始化，注册了 {len(self.agents)} 个Agent")
    
    def terrain_to_world_coord(self, terrain_x: int, terrain_y: int) -> tuple:
        """将地形坐标转换为世界坐标
        
        Args:
            terrain_x: 地形引擎中的x坐标
            terrain_y: 地形引擎中的y坐标
            
        Returns:
            (world_x, world_y) 世界坐标
        """
        # 将地形坐标映射到世界坐标，使用中心偏移
        # 地形引擎使用60x60网格，我们将其映射到世界坐标的中心区域
        center_offset = 1000  # 中心偏移量
        world_x = terrain_x * 5 + center_offset  # 每个地形格子对应5个世界坐标单位
        world_y = terrain_y * 5 + center_offset
        return (world_x, world_y)
    
    def world_to_terrain_coord(self, world_x: int, world_y: int) -> tuple:
        """将世界坐标转换为地形坐标
        
        Args:
            world_x: 世界坐标x
            world_y: 世界坐标y
            
        Returns:
            (terrain_x, terrain_y) 地形坐标，如果超出范围返回None
        """
        center_offset = 1000
        terrain_x = (world_x - center_offset) // 5
        terrain_y = (world_y - center_offset) // 5
        
        # 检查是否在地形引擎范围内（0-59）
        if 0 <= terrain_x < 60 and 0 <= terrain_y < 60:
            return (terrain_x, terrain_y)
        return None
    
    def place_building_on_map(self, building_type: str, terrain_x: int, terrain_y: int, building_id: str = None, progress: float = 0.0):
        """在无限地图上放置建筑
        
        Args:
            building_type: 建筑类型
            terrain_x: 地形坐标x
            terrain_y: 地形坐标y
            building_id: 建筑ID（可选）
            progress: 建造进度（0.0-1.0）
        """
        if not isinstance(self.maze, InfiniteMaze):
            return
        
        # 将地形坐标转换为世界坐标
        world_x, world_y = self.terrain_to_world_coord(terrain_x, terrain_y)
        
        # 创建建筑事件
        from modules.memory.event import Event
        status = "建造中" if progress < 1.0 else "已完成"
        event = Event(
            subject=building_type,
            description=f"AI自主建造: {building_type} ({status} {progress*100:.1f}%)",
            address=[self.maze.world, "buildings", building_id or f"{building_type}_{terrain_x}_{terrain_y}"]
        )
        
        # 在地图上放置建筑事件
        self.maze.update_obj((world_x, world_y), event)
        
        # 设置该位置的地形类型为建筑
        tile = self.maze.tile_at((world_x, world_y))
        if tile:
            tile.tile_type = "building"
            tile.add_event(event)
        
        self.logger.info(f"建筑 {building_type} 已放置到地图坐标 ({world_x}, {world_y})，进度: {progress*100:.1f}%")
    
    def update_building_progress_on_map(self):
        """更新地图上所有建筑的建造进度"""
        if not isinstance(self.maze, InfiniteMaze):
            return
        
        # 遍历地形引擎中的所有建筑
        for building_id, building in self.terrain_engine.buildings.items():
            if building.construction_progress < 1.0:  # 未完成的建筑
                # 获取建筑坐标
                terrain_x, terrain_y = building.x, building.y
                building_type = building.building_type.value
                progress = building.construction_progress
                
                # 更新地图上的建筑状态
                self.place_building_on_map(building_type, terrain_x, terrain_y, building_id, progress)

    def get_agent(self, name):
        return self.agents[name]

    def agent_think(self, name, status):
        # 更新环境管理器
        self.environment_manager.update()
        
        # 更新地形和经济系统
        self._update_ai_systems()
        
        agent = self.get_agent(name)
        
        # 如果使用无限地图，更新agent位置
        if isinstance(self.maze, InfiniteMaze):
            coord = status.get("coord", agent.coord)
            if coord:
                self.maze.update_agent_position(name, coord[0], coord[1])
        
        # AI建造决策
        self._process_agent_building_decision(agent)
        
        # AI经济决策
        self._process_agent_economic_decision(agent)
        
        # 执行常规思考
        plan = agent.think(status, self.agents)
        info = {
            "currently": agent.scratch.currently,
            "associate": agent.associate.abstract(),
            "concepts": {c.node_id: c.abstract() for c in agent.concepts},
            "chats": [
                {"name": "self" if n == agent.name else n, "chat": c}
                for n, c in agent.chats
            ],
            "action": agent.action.abstract(),
            "schedule": agent.schedule.abstract(),
            "address": agent.get_tile().get_address(as_list=False),
        }
        if (
            utils.get_timer().daily_duration() - agent.last_record
        ) > self.record_iterval:
            info["record"] = True
            agent.last_record = utils.get_timer().daily_duration()
        else:
            info["record"] = False
        if agent.llm_available():
            info["llm"] = agent._llm.get_summary()
        title = "{}.summary @ {}".format(
            name, utils.get_timer().get_date("%Y%m%d-%H:%M:%S")
        )
        self.logger.info("\n{}\n{}\n".format(utils.split_line(title), agent))
        return {"plan": plan, "info": info}

    def load_static(self, path):
        return utils.load_dict(os.path.join(self.static_root, path))

    def _update_ai_systems(self):
        """更新AI系统"""
        # 更新地形系统
        self.terrain_engine.simulate_daily_operations()
        
        # 更新经济价格
        self.economy_engine.update_prices(self.terrain_engine)
        
        # 协调Agent协作
        if self.collaboration_coordinator:
            agent_ids = list(self.agents.keys())
            self.collaboration_coordinator.auto_coordinate_agents(agent_ids)
        
        # 更新地图上的建筑进度
        self.update_building_progress_on_map()
        
        # 如果使用无限地图，定期清理不活跃的chunks
        if isinstance(self.maze, InfiniteMaze):
            # 每100次更新清理一次
            if not hasattr(self, '_cleanup_counter'):
                self._cleanup_counter = 0
            self._cleanup_counter += 1
            if self._cleanup_counter >= 100:
                self.maze.cleanup_inactive_chunks(keep_distance=5)
                self._cleanup_counter = 0
    
    def _process_agent_building_decision(self, agent):
        """处理Agent的建造决策"""
        if not self.building_decision_engine:
            return
        
        # 获取Agent当前坐标（如果可用）
        agent_coord = None
        if hasattr(agent, 'coord') and agent.coord:
            # 将Agent的世界坐标转换为地形坐标
            if isinstance(self.maze, InfiniteMaze):
                agent_coord = self.world_to_terrain_coord(agent.coord[0], agent.coord[1])
        
        # 考虑建造 - 传入Agent坐标以支持就近选址
        decision = agent.consider_building(
            self.terrain_engine,
            self.building_decision_engine,
            agent_coord=agent_coord
        )
        
        if decision:
            # 执行建造
            result = agent.execute_building_decision(
                decision,
                self.terrain_engine,
                self.building_decision_engine
            )
            
            # 如果建造成功，同步到地图
            if result and result.get("success"):
                building_type = decision.get("building_type")
                terrain_x = decision.get("x")
                terrain_y = decision.get("y")
                building_id = result.get("building_id")
                
                if building_type and terrain_x is not None and terrain_y is not None:
                    # 获取建筑进度（如果是新建筑，进度为0）
                    building = self.terrain_engine.buildings.get(building_id)
                    progress = building.construction_progress if building else 0.0
                    
                    self.place_building_on_map(
                        building_type, 
                        terrain_x, 
                        terrain_y, 
                        building_id,
                        progress
                    )
                    
                    # 发布建筑事件
                    publish_building_event(
                        subtype="building_started" if progress == 0.0 else "building_progress",
                        source="game._process_agent_building_decision",
                        data={
                            "agent_name": agent.name,
                            "building_type": building_type,
                            "location": (terrain_x, terrain_y),
                            "progress": progress,
                            "building_id": building_id
                        },
                        agent_id=agent.name,
                        location=(terrain_x, terrain_y)
                    )
                    
                    self.logger.info(f"Agent {agent.name} 成功建造 {building_type} 在 ({terrain_x}, {terrain_y})")
    
    def _process_agent_economic_decision(self, agent):
        """处理Agent的经济决策"""
        if not self.economy_behavior_engine:
            return
        
        # 获取其他Agent列表
        other_agents = [name for name in self.agents.keys() if name != agent.name]
        
        # 考虑经济行为
        action = agent.consider_economic_action(
            self.economy_engine,
            self.economy_behavior_engine,
            other_agents
        )
        
        if action:
            # 执行经济行为
            result = agent.execute_economic_action(
                action,
                self.economy_behavior_engine
            )
    
    def reset_game(self):
        for a_name, agent in self.agents.items():
            agent.reset()
            title = "{}.reset".format(a_name)
            self.logger.info("\n{}\n{}\n".format(utils.split_line(title), agent))


def create_game(name, static_root, config, conversation, logger=None):
    """Create the game"""

    utils.set_timer(**config.get("time", {}))
    GenerativeAgentsMap.set(GenerativeAgentsKey.GAME, Game(name, static_root, config, conversation, logger=logger))
    return GenerativeAgentsMap.get(GenerativeAgentsKey.GAME)


def get_game():
    """Get the gloabl game"""

    return GenerativeAgentsMap.get(GenerativeAgentsKey.GAME)
