"""
事件总线系统
用于收集和管理来自不同模块的事件，支持跨模块通信和调试
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json


class EventType(Enum):
    """事件类型"""
    BUILDING = "building"           # 建筑相关事件
    ECONOMIC = "economic"           # 经济相关事件
    SOCIAL = "social"               # 社交相关事件
    WEATHER = "weather"             # 天气相关事件
    AGENT = "agent"                 # Agent相关事件
    TERRAIN = "terrain"             # 地形相关事件
    SYSTEM = "system"               # 系统事件


class EventPriority(Enum):
    """事件优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class GameEvent:
    """游戏事件"""
    event_type: EventType
    subtype: str
    source: str
    timestamp: float
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    agent_id: Optional[str] = None
    location: Optional[tuple] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "event_type": self.event_type.value,
            "subtype": self.subtype,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
            "priority": self.priority.value,
            "agent_id": self.agent_id,
            "location": self.location,
            "human_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        }


class EventBus:
    """事件总线"""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: List[GameEvent] = []
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_stats: Dict[str, int] = {}
        self.lock = threading.Lock()
        
        # 初始化统计信息
        for event_type in EventType:
            self.event_stats[event_type.value] = 0
    
    def publish(self, event: GameEvent):
        """发布事件"""
        with self.lock:
            # 添加事件到列表
            self.events.append(event)
            
            # 限制事件数量
            if len(self.events) > self.max_events:
                self.events.pop(0)
            
            # 更新统计信息
            self.event_stats[event.event_type.value] += 1
            
            # 通知订阅者
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"事件回调失败: {e}")
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """订阅事件类型"""
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """取消订阅"""
        with self.lock:
            if event_type in self.subscribers and callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
    
    def get_recent_events(self, count: int = 100, event_type: Optional[EventType] = None, agent_id: Optional[str] = None) -> List[GameEvent]:
        """获取最近的事件"""
        with self.lock:
            filtered_events = self.events
            
            # 按类型过滤
            if event_type:
                filtered_events = [e for e in filtered_events if e.event_type == event_type]
            
            # 按Agent过滤
            if agent_id:
                filtered_events = [e for e in filtered_events if e.agent_id == agent_id]
            
            # 返回最近的事件
            return filtered_events[-count:] if count > 0 else filtered_events
    
    def get_events_by_subtype(self, subtype: str, count: int = 100) -> List[GameEvent]:
        """获取特定子类型的事件"""
        with self.lock:
            filtered_events = [e for e in self.events if e.subtype == subtype]
            return filtered_events[-count:] if count > 0 else filtered_events
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取事件统计信息"""
        with self.lock:
            return {
                "total_events": len(self.events),
                "event_type_stats": self.event_stats.copy(),
                "recent_activity": {
                    "last_hour": len([e for e in self.events if time.time() - e.timestamp < 3600]),
                    "last_day": len([e for e in self.events if time.time() - e.timestamp < 86400]),
                    "last_week": len([e for e in self.events if time.time() - e.timestamp < 604800])
                }
            }
    
    def clear_events(self, older_than: Optional[float] = None):
        """清理事件"""
        with self.lock:
            if older_than is None:
                self.events.clear()
                self.event_stats = {event_type.value: 0 for event_type in EventType}
            else:
                cutoff_time = time.time() - older_than
                self.events = [e for e in self.events if e.timestamp > cutoff_time]
                
                # 重新计算统计信息
                self.event_stats = {event_type.value: 0 for event_type in EventType}
                for event in self.events:
                    self.event_stats[event.event_type.value] += 1
    
    def export_events(self, filename: str, event_type: Optional[EventType] = None, limit: Optional[int] = None):
        """导出事件到文件"""
        events = self.get_recent_events(count=limit or -1, event_type=event_type)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([event.to_dict() for event in events], f, ensure_ascii=False, indent=2)


# 全局事件总线实例
global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    return global_event_bus


# 便捷的事件发布函数
def publish_building_event(subtype: str, source: str, data: Dict[str, Any], agent_id: Optional[str] = None, location: Optional[tuple] = None):
    """发布建筑事件"""
    event = GameEvent(
        event_type=EventType.BUILDING,
        subtype=subtype,
        source=source,
        timestamp=time.time(),
        data=data,
        agent_id=agent_id,
        location=location
    )
    global_event_bus.publish(event)


def publish_economic_event(subtype: str, source: str, data: Dict[str, Any], agent_id: Optional[str] = None, location: Optional[tuple] = None):
    """发布经济事件"""
    event = GameEvent(
        event_type=EventType.ECONOMIC,
        subtype=subtype,
        source=source,
        timestamp=time.time(),
        data=data,
        agent_id=agent_id,
        location=location
    )
    global_event_bus.publish(event)


def publish_social_event(subtype: str, source: str, data: Dict[str, Any], agent_id: Optional[str] = None, location: Optional[tuple] = None):
    """发布社交事件"""
    event = GameEvent(
        event_type=EventType.SOCIAL,
        subtype=subtype,
        source=source,
        timestamp=time.time(),
        data=data,
        agent_id=agent_id,
        location=location
    )
    global_event_bus.publish(event)


def publish_weather_event(subtype: str, source: str, data: Dict[str, Any], location: Optional[tuple] = None):
    """发布天气事件"""
    event = GameEvent(
        event_type=EventType.WEATHER,
        subtype=subtype,
        source=source,
        timestamp=time.time(),
        data=data,
        location=location
    )
    global_event_bus.publish(event)


def publish_agent_event(subtype: str, source: str, data: Dict[str, Any], agent_id: str, location: Optional[tuple] = None):
    """发布Agent事件"""
    event = GameEvent(
        event_type=EventType.AGENT,
        subtype=subtype,
        source=source,
        timestamp=time.time(),
        data=data,
        agent_id=agent_id,
        location=location
    )
    global_event_bus.publish(event)


def publish_terrain_event(subtype: str, source: str, data: Dict[str, Any], location: Optional[tuple] = None):
    """发布地形事件"""
    event = GameEvent(
        event_type=EventType.TERRAIN,
        subtype=subtype,
        source=source,
        timestamp=time.time(),
        data=data,
        location=location
    )
    global_event_bus.publish(event)


def publish_system_event(subtype: str, source: str, data: Dict[str, Any]):
    """发布系统事件"""
    event = GameEvent(
        event_type=EventType.SYSTEM,
        subtype=subtype,
        source=source,
        timestamp=time.time(),
        data=data
    )
    global_event_bus.publish(event)