"""
调试API模块
提供各种调试接口，用于监控和分析系统状态
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any, Optional
import time

from modules.event_bus import get_event_bus, EventType
from modules.utils import GenerativeAgentsMap, GenerativeAgentsKey
from modules.terrain.terrain_development import BuildingType, ResourceType


# 创建蓝图
api_blueprint = Blueprint('debug_api', __name__)


def get_game():
    """获取游戏实例"""
    return GenerativeAgentsMap.get(GenerativeAgentsKey.GAME)


@api_blueprint.route('/api/agents/<agent_id>/decisions', methods=['GET'])
def get_agent_decisions(agent_id: str):
    """获取Agent的决策历史"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    agent = game.agents.get(agent_id)
    if not agent:
        return jsonify({"error": f"Agent {agent_id} 不存在"}), 404
    
    # 获取最近的事件
    event_bus = get_event_bus()
    recent_events = event_bus.get_recent_events(count=50, agent_id=agent_id)
    
    # 过滤决策相关事件
    decision_events = []
    for event in recent_events:
        if event.event_type in [EventType.BUILDING, EventType.ECONOMIC]:
            decision_events.append(event.to_dict())
    
    return jsonify({
        "agent_id": agent_id,
        "decision_events": decision_events,
        "total_decisions": len(decision_events)
    })


@api_blueprint.route('/api/agents', methods=['GET'])
def get_all_agents():
    """获取所有Agent的信息"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    agents_info = {}
    for agent_id, agent in game.agents.items():
        agents_info[agent_id] = {
            "name": agent.name,
            "currently": agent.scratch.currently if hasattr(agent, 'scratch') else "未知",
            "location": agent.coord if hasattr(agent, 'coord') else None,
            "wallet_balance": agent.wallet.balance if hasattr(agent, 'wallet') else 0.0,
            "inventory_size": len(agent.inventory.materials) if hasattr(agent, 'inventory') else 0
        }
    
    return jsonify({
        "total_agents": len(agents_info),
        "agents": agents_info
    })


@api_blueprint.route('/api/economy/stats', methods=['GET'])
def get_economy_stats():
    """获取经济系统统计信息"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    economy_engine = game.economy_engine
    if not economy_engine:
        return jsonify({"error": "经济引擎未初始化"}), 500
    
    # 获取经济统计
    stats = {
        "total_agents": len(economy_engine.agent_wallets),
        "total_money": sum(economy_engine.agent_wallets.values()),
        "market_prices": {resource.value: price for resource, price in economy_engine.market_prices.items()},
        "global_resources": {resource.value: amount for resource, amount in game.terrain_engine.global_resources.items()},
        "recent_transactions": []
    }
    
    # 获取最近的经济事件
    event_bus = get_event_bus()
    recent_economic_events = event_bus.get_recent_events(count=20, event_type=EventType.ECONOMIC)
    
    for event in recent_economic_events:
        stats["recent_transactions"].append({
            "timestamp": event.timestamp,
            "agent_id": event.agent_id,
            "subtype": event.subtype,
            "data": event.data
        })
    
    return jsonify(stats)


@api_blueprint.route('/api/social/stats', methods=['GET'])
def get_social_stats():
    """获取社交系统统计信息"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    # 获取最近的社会事件
    event_bus = get_event_bus()
    recent_social_events = event_bus.get_recent_events(count=30, event_type=EventType.SOCIAL)
    
    social_stats = {
        "recent_interactions": [],
        "interaction_types": {}
    }
    
    for event in recent_social_events:
        social_stats["recent_interactions"].append({
            "timestamp": event.timestamp,
            "agent_id": event.agent_id,
            "subtype": event.subtype,
            "data": event.data
        })
        
        # 统计交互类型
        subtype = event.subtype
        social_stats["interaction_types"][subtype] = social_stats["interaction_types"].get(subtype, 0) + 1
    
    return jsonify(social_stats)


@api_blueprint.route('/api/terrain/stats', methods=['GET'])
def get_terrain_stats():
    """获取地形系统统计信息"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    terrain_engine = game.terrain_engine
    if not terrain_engine:
        return jsonify({"error": "地形引擎未初始化"}), 500
    
    # 获取地形统计
    stats = terrain_engine.get_development_statistics()
    
    # 添加建筑详情
    building_details = {}
    for building_id, building in terrain_engine.buildings.items():
        building_details[building_id] = {
            "type": building.building_type.value,
            "location": (building.x, building.y),
            "progress": building.construction_progress,
            "is_completed": building.is_completed,
            "efficiency": building.efficiency
        }
    
    # 获取最近的地形事件
    event_bus = get_event_bus()
    recent_terrain_events = event_bus.get_recent_events(count=20, event_type=EventType.TERRAIN)
    
    recent_events = []
    for event in recent_terrain_events:
        recent_events.append({
            "timestamp": event.timestamp,
            "subtype": event.subtype,
            "data": event.data
        })
    
    return jsonify({
        "development_stats": stats,
        "buildings": building_details,
        "recent_events": recent_events
    })


@api_blueprint.route('/api/events/recent', methods=['GET'])
def get_recent_events():
    """获取最近的事件"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    # 获取查询参数
    count = request.args.get('count', 50, type=int)
    event_type = request.args.get('type', None)
    agent_id = request.args.get('agent_id', None)
    
    # 转换事件类型
    if event_type:
        try:
            event_type = EventType(event_type)
        except ValueError:
            return jsonify({"error": f"无效的事件类型: {event_type}"}), 400
    
    # 获取事件
    event_bus = get_event_bus()
    events = event_bus.get_recent_events(count=count, event_type=event_type, agent_id=agent_id)
    
    return jsonify({
        "total_events": len(events),
        "events": [event.to_dict() for event in events]
    })


@api_blueprint.route('/api/events/stats', methods=['GET'])
def get_event_stats():
    """获取事件统计信息"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    event_bus = get_event_bus()
    stats = event_bus.get_statistics()
    
    return jsonify(stats)


@api_blueprint.route('/api/map/info', methods=['GET'])
def get_map_info():
    """获取地图信息"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    from modules.infinite_maze import InfiniteMaze
    if not isinstance(game.maze, InfiniteMaze):
        return jsonify({"error": "当前不是无限地图模式"}), 400
    
    # 获取地图统计
    stats = game.maze.get_statistics()
    
    # 获取活跃区域
    active_chunks = list(game.maze.active_chunks)
    
    # 获取Agent位置
    agent_positions = {}
    for agent_id, pos in game.maze.agent_positions.items():
        agent_positions[agent_id] = {"x": pos[0], "y": pos[1]}
    
    return jsonify({
        "map_stats": stats,
        "active_chunks": active_chunks,
        "agent_positions": agent_positions
    })


@api_blueprint.route('/api/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    game = get_game()
    if not game:
        return jsonify({"error": "游戏未初始化"}), 500
    
    status = {
        "game_name": game.name,
        "total_agents": len(game.agents),
        "systems_initialized": {
            "terrain_engine": game.terrain_engine is not None,
            "economy_engine": game.economy_engine is not None,
            "building_decision_engine": game.building_decision_engine is not None,
            "economy_behavior_engine": game.economy_behavior_engine is not None,
            "collaboration_coordinator": game.collaboration_coordinator is not None,
            "event_bus": True
        },
        "map_type": "infinite" if isinstance(game.maze, InfiniteMaze) else "classic",
        "current_time": time.time()
    }