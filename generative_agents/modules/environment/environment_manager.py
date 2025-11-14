"""
环境管理器
整合天气系统、昼夜循环和季节变化
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .weather import WeatherSystem, WeatherType
from .time_system import DayNightCycle, SeasonalTimeSystem, TimeOfDay


class EnvironmentManager:
    """环境管理器，统一管理所有环境系统"""
    
    def __init__(self, start_time: Optional[datetime] = None, time_scale: float = 1.0, auto_time_flow: bool = True):
        """
        初始化环境管理器
        
        Args:
            start_time: 开始时间
            time_scale: 时间缩放比例
            auto_time_flow: 是否启用自动时间流逝
        """
        # 初始化时间系统
        self.day_night_cycle = DayNightCycle(start_time, time_scale)
        self.seasonal_system = SeasonalTimeSystem(self.day_night_cycle)
        
        # 初始化天气系统
        self.weather_system = WeatherSystem(start_time)
        
        # 环境历史记录
        self.environment_history: List[Dict] = []
        self.last_update_time = time.time()
        
        # 环境事件
        self.environment_events: List[Dict] = []
        
        # 更新间隔（秒）
        self.update_interval = 1.0
        
        # 自动时间流逝设置
        self.auto_time_flow = auto_time_flow
        self.auto_time_speed = 60.0  # 1分钟现实时间 = 1小时游戏时间
        
        print("=== Environment Manager initialized ===")
    
    def update(self):
        """更新所有环境系统"""
        current_real_time = time.time()
        delta_seconds = current_real_time - self.last_update_time
        
        if delta_seconds >= self.update_interval:
            # 如果启用自动时间流逝，计算游戏时间增量
            if self.auto_time_flow:
                game_time_delta = delta_seconds * self.auto_time_speed
                
                # 更新时间系统
                self.day_night_cycle.update(game_time_delta)
                
                # 更新天气系统的时间
                self.weather_system.current_time = self.day_night_cycle.current_time
                
                # 更新天气系统（传入游戏时间增量）
                self.weather_system.update(game_time_delta)
            else:
                # 手动模式，只更新系统状态
                self.day_night_cycle.update(delta_seconds)
                self.weather_system.update(delta_seconds)
            
            # 调整季节性日照时间
            self.seasonal_system.adjust_daylight_hours()
            
            # 检查环境变化事件
            self._check_environment_events()
            
            # 记录环境历史
            self._record_environment_state()
            
            self.last_update_time = current_real_time
    
    def _check_environment_events(self):
        """检查并生成环境事件"""
        current_data = self.get_environment_data()
        
        # 检查时间段变化
        time_of_day = current_data["time"]["time_of_day"]
        if hasattr(self, '_last_time_of_day') and self._last_time_of_day != time_of_day:
            self.environment_events.append({
                "type": "time_change",
                "timestamp": current_data["time"]["current_time"],
                "description": f"时间段从 {self._last_time_of_day} 变为 {time_of_day}",
                "data": {
                    "from": self._last_time_of_day,
                    "to": time_of_day
                }
            })
        self._last_time_of_day = time_of_day
        
        # 检查天气变化
        weather_type = current_data["weather"]["type"]
        if hasattr(self, '_last_weather_type') and self._last_weather_type != weather_type:
            self.environment_events.append({
                "type": "weather_change",
                "timestamp": current_data["time"]["current_time"],
                "description": f"天气从 {self._last_weather_type} 变为 {weather_type}",
                "data": {
                    "from": self._last_weather_type,
                    "to": weather_type
                }
            })
        self._last_weather_type = weather_type
        
        # 检查极端天气
        if weather_type in ["storm", "heavy_rain", "snow"]:
            self.environment_events.append({
                "type": "extreme_weather",
                "timestamp": current_data["time"]["current_time"],
                "description": f"出现极端天气: {weather_type}",
                "data": {
                    "weather_type": weather_type,
                    "intensity": current_data["weather"]["intensity"]
                }
            })
        
        # 限制事件历史长度
        if len(self.environment_events) > 100:
            self.environment_events = self.environment_events[-50:]
    
    def _record_environment_state(self):
        """记录环境状态到历史"""
        state = self.get_environment_data()
        self.environment_history.append(state)
        
        # 限制历史记录长度
        if len(self.environment_history) > 1000:
            self.environment_history = self.environment_history[-500:]
    
    def get_environment_data(self) -> Dict:
        """获取完整的环境数据"""
        time_data = self.day_night_cycle.get_time_data()
        weather_data = self.weather_system.get_weather_data()
        seasonal_effects = self.seasonal_system.get_seasonal_effects()
        
        # 计算综合环境效果
        combined_effects = self._calculate_combined_effects(time_data, weather_data, seasonal_effects)
        
        return {
            "time": time_data,
            "weather": weather_data,
            "seasonal_effects": seasonal_effects,
            "combined_effects": combined_effects,
            "environment_quality": self._calculate_environment_quality(time_data, weather_data),
            "visibility": self._calculate_visibility(time_data, weather_data),
            "comfort_level": self._calculate_comfort_level(weather_data, seasonal_effects)
        }
    
    def _calculate_combined_effects(self, time_data: Dict, weather_data: Dict, seasonal_effects: Dict) -> Dict:
        """计算综合环境效果"""
        # 基础活动修正
        activity_modifier = time_data["activity_modifier"]
        
        # 天气对活动的影响
        weather_activity_impact = {
            "sunny": 1.2,
            "cloudy": 1.0,
            "rainy": 0.7,
            "heavy_rain": 0.4,
            "storm": 0.2,
            "snow": 0.6,
            "fog": 0.8
        }
        
        weather_modifier = weather_activity_impact.get(weather_data["type"], 1.0)
        
        # 季节性修正
        seasonal_modifier = seasonal_effects.get("activity_modifier", 1.0)
        
        # 综合活动水平
        combined_activity = activity_modifier * weather_modifier * seasonal_modifier
        
        # 光照综合效果
        base_light = time_data["light_intensity"]
        weather_light_impact = {
            "sunny": 1.0,
            "cloudy": 0.7,
            "rainy": 0.5,
            "heavy_rain": 0.3,
            "storm": 0.2,
            "snow": 0.6,
            "fog": 0.4
        }
        
        weather_light_modifier = weather_light_impact.get(weather_data["type"], 1.0)
        combined_light = base_light * weather_light_modifier
        
        return {
            "activity_level": round(max(0.1, min(2.0, combined_activity)), 3),
            "effective_light_intensity": round(max(0.01, min(1.0, combined_light)), 3),
            "movement_speed_modifier": round(combined_activity * 0.8 + 0.2, 3),
            "social_interaction_modifier": round(combined_activity * weather_modifier, 3),
            "mood_impact": round(self._calculate_mood_impact(time_data, weather_data, seasonal_effects), 3)
        }
    
    def _calculate_mood_impact(self, time_data: Dict, weather_data: Dict, seasonal_effects: Dict) -> float:
        """计算环境对情绪的影响"""
        # 基础情绪影响
        base_mood = 0.0
        
        # 时间对情绪的影响
        time_mood_impact = {
            "dawn": 0.1,
            "morning": 0.2,
            "noon": 0.1,
            "afternoon": 0.15,
            "dusk": 0.05,
            "evening": 0.0,
            "night": -0.1
        }
        
        time_mood = time_mood_impact.get(time_data["time_of_day"], 0.0)
        
        # 天气对情绪的影响
        weather_mood_impact = {
            "sunny": 0.3,
            "cloudy": 0.0,
            "rainy": -0.1,
            "heavy_rain": -0.2,
            "storm": -0.3,
            "snow": 0.1,
            "fog": -0.05
        }
        
        weather_mood = weather_mood_impact.get(weather_data["type"], 0.0)
        
        # 季节性情绪影响
        seasonal_mood = seasonal_effects.get("mood_modifier", 0.0)
        
        # 光照对情绪的影响
        light_mood = (time_data["light_intensity"] - 0.5) * 0.2
        
        total_mood = time_mood + weather_mood + seasonal_mood + light_mood
        return max(-1.0, min(1.0, total_mood))
    
    def _calculate_environment_quality(self, time_data: Dict, weather_data: Dict) -> float:
        """计算环境质量指数 (0-1)"""
        # 光照质量
        light_quality = time_data["light_intensity"]
        
        # 天气质量
        weather_quality_map = {
            "sunny": 1.0,
            "cloudy": 0.8,
            "rainy": 0.6,
            "heavy_rain": 0.3,
            "storm": 0.1,
            "snow": 0.7,
            "fog": 0.5
        }
        
        weather_quality = weather_quality_map.get(weather_data["type"], 0.5)
        
        # 温度舒适度
        temp = weather_data["temperature"]
        temp_comfort = 1.0 - abs(temp - 20) / 30  # 20度为最舒适温度
        temp_comfort = max(0.0, min(1.0, temp_comfort))
        
        # 综合质量
        quality = (light_quality * 0.4 + weather_quality * 0.4 + temp_comfort * 0.2)
        return round(quality, 3)
    
    def _calculate_visibility(self, time_data: Dict, weather_data: Dict) -> float:
        """计算能见度 (0-1)"""
        # 基础能见度（基于光照）
        base_visibility = time_data["light_intensity"]
        
        # 天气对能见度的影响
        weather_visibility_impact = {
            "sunny": 1.0,
            "cloudy": 0.9,
            "rainy": 0.7,
            "heavy_rain": 0.4,
            "storm": 0.2,
            "snow": 0.5,
            "fog": 0.1
        }
        
        weather_modifier = weather_visibility_impact.get(weather_data["type"], 1.0)
        
        visibility = base_visibility * weather_modifier
        return round(max(0.01, min(1.0, visibility)), 3)
    
    def _calculate_comfort_level(self, weather_data: Dict, seasonal_effects: Dict) -> float:
        """计算舒适度 (0-1)"""
        # 温度舒适度
        temp = weather_data["temperature"]
        temp_comfort = 1.0 - abs(temp - 22) / 25  # 22度为最舒适温度
        temp_comfort = max(0.0, min(1.0, temp_comfort))
        
        # 湿度舒适度
        humidity = weather_data["humidity"]
        humidity_comfort = 1.0 - abs(humidity - 50) / 50  # 50%为最舒适湿度
        humidity_comfort = max(0.0, min(1.0, humidity_comfort))
        
        # 风速舒适度
        wind_speed = weather_data["wind_speed"]
        wind_comfort = max(0.0, 1.0 - wind_speed / 20)  # 风速超过20km/h开始不舒适
        
        # 综合舒适度
        comfort = (temp_comfort * 0.5 + humidity_comfort * 0.3 + wind_comfort * 0.2)
        return round(comfort, 3)
    
    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """获取最近的环境事件"""
        return self.environment_events[-limit:] if self.environment_events else []
    
    def get_environment_history(self, hours: int = 24) -> List[Dict]:
        """获取指定小时数内的环境历史"""
        if not self.environment_history:
            return []
        
        current_time = datetime.fromisoformat(self.environment_history[-1]["time"]["current_time"])
        cutoff_time = current_time - timedelta(hours=hours)
        
        filtered_history = []
        for record in self.environment_history:
            record_time = datetime.fromisoformat(record["time"]["current_time"])
            if record_time >= cutoff_time:
                filtered_history.append(record)
        
        return filtered_history
    
    def set_weather(self, weather_type: str, intensity: float = 1.0):
        """手动设置天气"""
        try:
            weather_enum = WeatherType(weather_type)
            self.weather_system.set_weather(weather_enum, intensity)
            print(f"Weather set to {weather_type} with intensity {intensity}")
        except ValueError:
            print(f"Invalid weather type: {weather_type}")
    
    def set_time_scale(self, scale: float):
        """设置时间缩放"""
        self.day_night_cycle.set_time_scale(scale)
        print(f"Time scale set to {scale}x")
    
    def advance_time(self, hours: float):
        """快进时间"""
        self.day_night_cycle.advance_time(hours)
        print(f"Time advanced by {hours} hours")
    
    def get_status_summary(self) -> str:
        """获取环境状态摘要"""
        data = self.get_environment_data()
        
        time_info = data["time"]
        weather_info = data["weather"]
        
        summary = f"""环境状态摘要:
时间: {time_info['current_time'][:19]} ({time_info['time_of_day']})
天气: {weather_info['type']} (强度: {weather_info['intensity']})
温度: {weather_info['temperature']}°C
光照强度: {time_info['light_intensity']:.2f}
能见度: {data['visibility']:.2f}
环境质量: {data['environment_quality']:.2f}
舒适度: {data['comfort_level']:.2f}"""
        
        return summary