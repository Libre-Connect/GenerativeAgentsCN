"""
无限地图API
为前端提供动态地图数据
"""

from flask import jsonify
from typing import Dict, List, Tuple


def get_visible_map_data(maze, center_x: int, center_y: int, radius: int = 50) -> Dict:
    """
    获取可见区域的地图数据
    
    Args:
        maze: InfiniteMaze实例
        center_x: 中心X坐标
        center_y: 中心Y坐标
        radius: 可见半径
    
    Returns:
        地图数据字典
    """
    tiles_data = []
    
    # 获取范围内的瓦片
    for y in range(center_y - radius, center_y + radius + 1):
        for x in range(center_x - radius, center_x + radius + 1):
            tile = maze.tile_at((x, y))
            if tile:
                tile_info = {
                    "x": x,
                    "y": y,
                    "type": tile.tile_type,
                    "collision": tile.collision,
                    "events": [
                        {
                            "subject": e.subject,
                            "emoji": getattr(e, 'emoji', ''),
                        }
                        for e in tile.get_events()
                    ] if hasattr(tile, 'get_events') else []
                }
                tiles_data.append(tile_info)
    
    return {
        "center": {"x": center_x, "y": center_y},
        "radius": radius,
        "tiles": tiles_data,
        "tile_count": len(tiles_data)
    }


def get_chunk_data(maze, chunk_x: int, chunk_y: int) -> Dict:
    """
    获取单个chunk的数据
    
    Args:
        maze: InfiniteMaze实例
        chunk_x: Chunk X坐标
        chunk_y: Chunk Y坐标
    
    Returns:
        Chunk数据
    """
    chunk_coord = (chunk_x, chunk_y)
    
    if chunk_coord not in maze.chunks:
        maze._generate_chunk(chunk_x, chunk_y)
    
    chunk = maze.chunks[chunk_coord]
    
    tiles_data = []
    for (local_x, local_y), tile in chunk.tiles.items():
        world_x = chunk_x * maze.chunk_size + local_x
        world_y = chunk_y * maze.chunk_size + local_y
        
        tiles_data.append({
            "local_x": local_x,
            "local_y": local_y,
            "world_x": world_x,
            "world_y": world_y,
            "type": tile.tile_type,
            "collision": tile.collision
        })
    
    return {
        "chunk_x": chunk_x,
        "chunk_y": chunk_y,
        "chunk_size": maze.chunk_size,
        "tiles": tiles_data,
        "is_generated": chunk.is_generated
    }


def get_map_statistics(maze) -> Dict:
    """获取地图统计信息"""
    stats = maze.get_statistics()
    
    # 添加agent分布信息
    agent_distribution = {}
    for agent_id, (x, y) in maze.agent_positions.items():
        chunk_coord = maze._world_to_chunk_coord(x, y)
        chunk_key = f"{chunk_coord[0]},{chunk_coord[1]}"
        if chunk_key not in agent_distribution:
            agent_distribution[chunk_key] = []
        agent_distribution[chunk_key].append(agent_id)
    
    stats["agent_distribution"] = agent_distribution
    
    return stats


def setup_infinite_maze_routes(app, game):
    """
    为Flask app添加无限地图相关的路由
    
    Args:
        app: Flask app实例
        game: Game实例
    """
    from flask import request
    from modules.infinite_maze import InfiniteMaze
    
    @app.route("/api/infinite_map/visible", methods=["GET"])
    def get_visible_map():
        """获取可见区域的地图"""
        if not isinstance(game.maze, InfiniteMaze):
            return jsonify({"error": "Not using infinite map"}), 400
        
        center_x = int(request.args.get("x", 0))
        center_y = int(request.args.get("y", 0))
        radius = int(request.args.get("radius", 50))
        
        data = get_visible_map_data(game.maze, center_x, center_y, radius)
        return jsonify(data)
    
    @app.route("/api/infinite_map/chunk/<int:chunk_x>/<int:chunk_y>", methods=["GET"])
    def get_chunk(chunk_x, chunk_y):
        """获取指定chunk的数据"""
        if not isinstance(game.maze, InfiniteMaze):
            return jsonify({"error": "Not using infinite map"}), 400
        
        data = get_chunk_data(game.maze, chunk_x, chunk_y)
        return jsonify(data)
    
    @app.route("/api/infinite_map/statistics", methods=["GET"])
    def get_statistics():
        """获取地图统计信息"""
        if not isinstance(game.maze, InfiniteMaze):
            return jsonify({"error": "Not using infinite map"}), 400
        
        stats = get_map_statistics(game.maze)
        return jsonify(stats)
    
    @app.route("/api/infinite_map/agents", methods=["GET"])
    def get_agent_positions():
        """获取所有agent的位置"""
        if not isinstance(game.maze, InfiniteMaze):
            return jsonify({"error": "Not using infinite map"}), 400
        
        positions = {
            agent_id: {"x": x, "y": y}
            for agent_id, (x, y) in game.maze.agent_positions.items()
        }
        return jsonify(positions)
    
    @app.route("/api/infinite_map/spawn_point", methods=["GET"])
    def get_spawn_point():
        """获取出生点"""
        return jsonify({"x": 0, "y": 0})
    
    @app.route("/api/infinite_map/tile/<int:x>/<int:y>", methods=["GET"])
    def get_tile_info(x, y):
        """获取指定瓦片的详细信息"""
        if not isinstance(game.maze, InfiniteMaze):
            return jsonify({"error": "Not using infinite map"}), 400
        
        tile = game.maze.tile_at((x, y))
        if not tile:
            return jsonify({"error": "Tile not found"}), 404
        
        return jsonify({
            "x": x,
            "y": y,
            "type": tile.tile_type,
            "collision": tile.collision,
            "address": tile.get_address(as_list=False),
            "events": [
                {
                    "subject": e.subject,
                    "predicate": getattr(e, 'predicate', ''),
                    "object": getattr(e, 'object', ''),
                    "emoji": getattr(e, 'emoji', ''),
                }
                for e in tile.get_events()
            ] if hasattr(tile, 'get_events') else []
        })

