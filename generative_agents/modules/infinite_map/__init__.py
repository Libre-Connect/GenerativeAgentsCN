"""
无限地图系统
支持动态加载、程序化生成和100+agents
"""

from .chunk_manager import ChunkManager, ChunkData, BiomeType
from .procedural_terrain import ProceduralTerrainGenerator, SimplexNoise
from .infinite_maze import InfiniteMaze, create_infinite_maze

__all__ = [
    'ChunkManager',
    'ChunkData',
    'BiomeType',
    'ProceduralTerrainGenerator',
    'SimplexNoise',
    'InfiniteMaze',
    'create_infinite_maze'
]

