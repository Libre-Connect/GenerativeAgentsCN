"""
天气系统模块
提供动态天气变化和环境效果
"""

import random
import math
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Tuple, Optional


class WeatherType(Enum):
    """天气类型枚举"""
    SUNNY = "sunny"          # 晴天
    CLOUDY = "cloudy"        # 多云
    RAINY = "rainy"          # 雨天
    STORMY = "stormy"        # 暴风雨
    SNOWY = "snowy"          # 雪天
    FOGGY = "foggy"          # 雾天
    WINDY = "windy"          # 大风


class Season(Enum):
    """季节枚举"""
    SPRING = "spring"        # 春季
    SUMMER = "summer"        # 夏季
    AUTUMN = "autumn"        # 秋季
    WINTER = "winter"        # 冬季


class WeatherSystem:
    """天气系统类"""
    
    def __init__(self, start_time: Optional[datetime] = None):
        """
        初始化天气系统
        
        Args:
            start_time: 开始时间，默认为当前时间
        """
        self.current_time = start_time or datetime.now()
        self.current_weather = WeatherType.SUNNY
        self.intensity = 1.0     # 天气强度
        self.temperature = 20.0  # 摄氏度
        self.humidity = 50.0     # 湿度百分比
        self.wind_speed = 5.0    # 风速 km/h
        self.visibility = 10.0   # 能见度 km
        self.pressure = 1013.25  # 气压 hPa
        
        # 天气变化参数
        self.weather_change_probability = 0.02  # 每小时天气变化概率（进一步降低频率）
        self.last_weather_change = self.current_time
        self.min_weather_duration = 3.0  # 最小天气持续时间（小时）
        self.weather_stability_factor = 0.85  # 天气稳定性因子
        
        # 天气过渡参数
        self.target_weather = self.current_weather  # 目标天气
        self.target_intensity = self.intensity      # 目标强度
        self.transition_duration = 1.0              # 过渡持续时间（小时）
        self.transition_start_time = self.current_time
        self.is_transitioning = False               # 是否正在过渡
        
        # 季节性天气概率
        self.seasonal_weather_probabilities = {
            Season.SPRING: {
                WeatherType.SUNNY: 0.4,
                WeatherType.CLOUDY: 0.3,
                WeatherType.RAINY: 0.2,
                WeatherType.STORMY: 0.05,
                WeatherType.FOGGY: 0.05
            },
            Season.SUMMER: {
                WeatherType.SUNNY: 0.6,
                WeatherType.CLOUDY: 0.2,
                WeatherType.RAINY: 0.1,
                WeatherType.STORMY: 0.05,
                WeatherType.WINDY: 0.05
            },
            Season.AUTUMN: {
                WeatherType.SUNNY: 0.3,
                WeatherType.CLOUDY: 0.4,
                WeatherType.RAINY: 0.2,
                WeatherType.FOGGY: 0.05,
                WeatherType.WINDY: 0.05
            },
            Season.WINTER: {
                WeatherType.CLOUDY: 0.4,
                WeatherType.SNOWY: 0.3,
                WeatherType.SUNNY: 0.2,
                WeatherType.FOGGY: 0.1
            }
        }
    
    def get_current_season(self) -> Season:
        """获取当前季节"""
        month = self.current_time.month
        if month in [3, 4, 5]:
            return Season.SPRING
        elif month in [6, 7, 8]:
            return Season.SUMMER
        elif month in [9, 10, 11]:
            return Season.AUTUMN
        else:
            return Season.WINTER
    
    def get_time_of_day(self) -> str:
        """获取一天中的时间段"""
        hour = self.current_time.hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def is_daytime(self) -> bool:
        """判断是否为白天"""
        hour = self.current_time.hour
        return 6 <= hour < 18
    
    def get_light_intensity(self) -> float:
        """获取光照强度 (0.0-1.0)"""
        hour = self.current_time.hour
        minute = self.current_time.minute
        time_decimal = hour + minute / 60.0
        
        # 基础光照曲线（正弦波）
        if 6 <= time_decimal <= 18:
            # 白天：6点到18点
            angle = (time_decimal - 6) / 12 * math.pi
            base_intensity = math.sin(angle)
        else:
            # 夜晚
            base_intensity = 0.1
        
        # 天气对光照的影响
        weather_modifiers = {
            WeatherType.SUNNY: 1.0,
            WeatherType.CLOUDY: 0.7,
            WeatherType.RAINY: 0.5,
            WeatherType.STORMY: 0.3,
            WeatherType.SNOWY: 0.6,
            WeatherType.FOGGY: 0.4,
            WeatherType.WINDY: 0.9
        }
        
        return max(0.05, base_intensity * weather_modifiers.get(self.current_weather, 1.0))
    
    def update(self, delta_seconds: float):
        """更新天气系统（兼容环境管理器接口）"""
        time_delta_hours = delta_seconds / 3600.0  # 转换为小时
        self.update_weather(time_delta_hours)
    
    def update_weather(self, time_delta_hours: float = 1.0):
        """
        更新天气状态
        
        Args:
            time_delta_hours: 时间增量（小时）
        """
        # 更新时间
        self.current_time += timedelta(hours=time_delta_hours)
        
        # 处理天气过渡
        if self.is_transitioning:
            self._update_weather_transition()
        
        # 检查是否需要改变天气（只有在不处于过渡状态时）
        if not self.is_transitioning:
            hours_since_change = (self.current_time - self.last_weather_change).total_seconds() / 3600
            
            # 确保天气至少持续最小时间
            if hours_since_change >= self.min_weather_duration:
                # 计算变化概率，时间越长概率越高，但有上限
                base_probability = self.weather_change_probability
                time_factor = min(hours_since_change / 8.0, 2.0)  # 8小时后达到最大倍数
                change_probability = base_probability * time_factor
                
                # 添加天气稳定性检查
                if random.random() < change_probability * (1 - self.weather_stability_factor):
                    self._initiate_weather_change()
        
        # 更新环境参数
        self._update_environmental_parameters()
    
    def _update_weather_transition(self):
        """更新天气过渡状态"""
        transition_elapsed = (self.current_time - self.transition_start_time).total_seconds() / 3600
        
        if transition_elapsed >= self.transition_duration:
            # 过渡完成
            self.current_weather = self.target_weather
            self.intensity = self.target_intensity
            self.is_transitioning = False
            self.last_weather_change = self.current_time
        else:
            # 计算过渡进度（0到1）
            progress = transition_elapsed / self.transition_duration
            # 使用平滑的过渡曲线
            smooth_progress = 0.5 * (1 - math.cos(progress * math.pi))
            
            # 渐进式强度变化
            start_intensity = getattr(self, '_transition_start_intensity', self.intensity)
            self.intensity = start_intensity + (self.target_intensity - start_intensity) * smooth_progress
    
    def _initiate_weather_change(self):
        """启动天气变化过渡"""
        new_weather, new_intensity = self._select_new_weather()
        
        if new_weather != self.current_weather:
            self.target_weather = new_weather
            self.target_intensity = new_intensity
            self._transition_start_intensity = self.intensity
            self.transition_start_time = self.current_time
            self.is_transitioning = True
            
            # 根据天气类型调整过渡时间
            transition_times = {
                (WeatherType.SUNNY, WeatherType.CLOUDY): 0.5,
                (WeatherType.CLOUDY, WeatherType.RAINY): 0.8,
                (WeatherType.RAINY, WeatherType.STORMY): 0.3,
                (WeatherType.STORMY, WeatherType.RAINY): 0.5,
                (WeatherType.CLOUDY, WeatherType.SUNNY): 1.0,
                (WeatherType.RAINY, WeatherType.CLOUDY): 1.2,
            }
            
            # 获取过渡时间，默认1小时
            self.transition_duration = transition_times.get(
                (self.current_weather, new_weather), 1.0
            )
    
    def _select_new_weather(self):
        """选择新的天气类型和强度"""
        current_season = self.get_current_season()
        probabilities = self.seasonal_weather_probabilities[current_season].copy()
        
        # 定义天气转换的合理性矩阵
        weather_transitions = {
            WeatherType.SUNNY: [WeatherType.CLOUDY, WeatherType.WINDY],
            WeatherType.CLOUDY: [WeatherType.SUNNY, WeatherType.RAINY, WeatherType.FOGGY],
            WeatherType.RAINY: [WeatherType.CLOUDY, WeatherType.STORMY, WeatherType.FOGGY],
            WeatherType.STORMY: [WeatherType.RAINY, WeatherType.CLOUDY],
            WeatherType.SNOWY: [WeatherType.CLOUDY, WeatherType.FOGGY],
            WeatherType.FOGGY: [WeatherType.CLOUDY, WeatherType.SUNNY],
            WeatherType.WINDY: [WeatherType.SUNNY, WeatherType.CLOUDY]
        }
        
        # 获取当前天气可能的转换目标
        possible_transitions = weather_transitions.get(self.current_weather, list(probabilities.keys()))
        
        # 过滤出在当前季节可能出现的天气
        valid_transitions = [w for w in possible_transitions if w in probabilities]
        
        if not valid_transitions:
            # 如果没有合理的转换，使用所有可能的天气
            valid_transitions = list(probabilities.keys())
        
        # 根据转换合理性调整权重
        weather_types = valid_transitions
        weights = [probabilities[w] for w in weather_types]
        
        # 避免连续相同天气
        if self.current_weather in weather_types:
            current_index = weather_types.index(self.current_weather)
            weights[current_index] *= 0.05  # 大幅降低当前天气的概率
        
        # 重新归一化权重
        total_weight = sum(weights)
        new_weather = self.current_weather  # 默认保持当前天气
        
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
            new_weather = random.choices(weather_types, weights=weights)[0]
        else:
            # 备用方案：随机选择
            available_weather = [w for w in probabilities.keys() if w != self.current_weather]
            if available_weather:
                new_weather = random.choice(available_weather)
        
        # 生成新的天气强度
        new_intensity = self._generate_weather_intensity(new_weather)
        
        return new_weather, new_intensity
    
    def _generate_weather_intensity(self, weather_type: WeatherType) -> float:
        """根据天气类型生成合适的强度"""
        intensity_ranges = {
            WeatherType.SUNNY: (0.8, 1.0),
            WeatherType.CLOUDY: (0.4, 0.8),
            WeatherType.RAINY: (0.3, 0.9),
            WeatherType.STORMY: (0.7, 1.0),
            WeatherType.SNOWY: (0.4, 0.9),
            WeatherType.FOGGY: (0.2, 0.6),
            WeatherType.WINDY: (0.5, 0.9)
        }
        
        min_intensity, max_intensity = intensity_ranges.get(weather_type, (0.5, 1.0))
        return random.uniform(min_intensity, max_intensity)
    
    def _update_environmental_parameters(self):
        """更新环境参数"""
        season = self.get_current_season()
        
        # 基础温度（根据季节）
        base_temperatures = {
            Season.SPRING: 15.0,
            Season.SUMMER: 25.0,
            Season.AUTUMN: 10.0,
            Season.WINTER: 0.0
        }
        base_temp = base_temperatures[season]
        
        # 昼夜温差
        hour = self.current_time.hour
        if 6 <= hour <= 14:
            # 白天升温
            temp_modifier = (hour - 6) / 8 * 8  # 最高+8度
        elif 14 < hour <= 18:
            # 下午降温
            temp_modifier = 8 - (hour - 14) / 4 * 3  # 降3度
        else:
            # 夜晚
            temp_modifier = 5 - (24 - hour if hour > 18 else 6 - hour) / 12 * 5  # 最低-5度
        
        # 天气对温度的影响
        weather_temp_modifiers = {
            WeatherType.SUNNY: 3,
            WeatherType.CLOUDY: 0,
            WeatherType.RAINY: -3,
            WeatherType.STORMY: -5,
            WeatherType.SNOWY: -8,
            WeatherType.FOGGY: -2,
            WeatherType.WINDY: -2
        }
        
        self.temperature = base_temp + temp_modifier + weather_temp_modifiers.get(self.current_weather, 0)
        
        # 更新其他参数
        self._update_humidity()
        self._update_wind_speed()
        self._update_visibility()
        self._update_pressure()
    
    def _update_humidity(self):
        """更新湿度"""
        weather_humidity = {
            WeatherType.SUNNY: 40,
            WeatherType.CLOUDY: 60,
            WeatherType.RAINY: 85,
            WeatherType.STORMY: 90,
            WeatherType.SNOWY: 75,
            WeatherType.FOGGY: 95,
            WeatherType.WINDY: 45
        }
        
        target_humidity = weather_humidity.get(self.current_weather, 50)
        # 平滑过渡
        self.humidity += (target_humidity - self.humidity) * 0.1
    
    def _update_wind_speed(self):
        """更新风速"""
        weather_wind = {
            WeatherType.SUNNY: 5,
            WeatherType.CLOUDY: 8,
            WeatherType.RAINY: 15,
            WeatherType.STORMY: 35,
            WeatherType.SNOWY: 20,
            WeatherType.FOGGY: 3,
            WeatherType.WINDY: 25
        }
        
        target_wind = weather_wind.get(self.current_weather, 5)
        # 添加随机波动
        self.wind_speed = target_wind + random.uniform(-3, 3)
        self.wind_speed = max(0, self.wind_speed)
    
    def _update_visibility(self):
        """更新能见度"""
        weather_visibility = {
            WeatherType.SUNNY: 15,
            WeatherType.CLOUDY: 12,
            WeatherType.RAINY: 5,
            WeatherType.STORMY: 2,
            WeatherType.SNOWY: 3,
            WeatherType.FOGGY: 0.5,
            WeatherType.WINDY: 10
        }
        
        self.visibility = weather_visibility.get(self.current_weather, 10)
    
    def _update_pressure(self):
        """更新气压"""
        weather_pressure = {
            WeatherType.SUNNY: 1020,
            WeatherType.CLOUDY: 1015,
            WeatherType.RAINY: 1005,
            WeatherType.STORMY: 995,
            WeatherType.SNOWY: 1010,
            WeatherType.FOGGY: 1013,
            WeatherType.WINDY: 1008
        }
        
        target_pressure = weather_pressure.get(self.current_weather, 1013)
        # 平滑过渡
        self.pressure += (target_pressure - self.pressure) * 0.05
    
    def get_weather_effects(self) -> Dict:
        """获取天气对环境的影响"""
        effects = {
            "movement_speed_modifier": 1.0,
            "visibility_modifier": 1.0,
            "social_activity_modifier": 1.0,
            "terrain_growth_modifier": 1.0,
            "mood_modifier": 0.0
        }
        
        # 根据天气类型调整效果
        if self.current_weather == WeatherType.SUNNY:
            effects["social_activity_modifier"] = 1.2
            effects["mood_modifier"] = 0.1
        elif self.current_weather == WeatherType.RAINY:
            effects["movement_speed_modifier"] = 0.8
            effects["social_activity_modifier"] = 0.7
            effects["terrain_growth_modifier"] = 1.3
            effects["mood_modifier"] = -0.1
        elif self.current_weather == WeatherType.STORMY:
            effects["movement_speed_modifier"] = 0.6
            effects["visibility_modifier"] = 0.3
            effects["social_activity_modifier"] = 0.4
            effects["mood_modifier"] = -0.2
        elif self.current_weather == WeatherType.SNOWY:
            effects["movement_speed_modifier"] = 0.7
            effects["visibility_modifier"] = 0.6
            effects["social_activity_modifier"] = 0.8
            effects["terrain_growth_modifier"] = 0.5
        elif self.current_weather == WeatherType.FOGGY:
            effects["visibility_modifier"] = 0.2
            effects["movement_speed_modifier"] = 0.9
            effects["mood_modifier"] = -0.05
        elif self.current_weather == WeatherType.WINDY:
            effects["movement_speed_modifier"] = 0.9
            effects["social_activity_modifier"] = 0.9
        
        return effects
    
    def get_weather_data(self) -> Dict:
        """获取完整的天气数据"""
        data = {
            "current_time": self.current_time.isoformat(),
            "type": self.current_weather.value,
            "weather_type": self.current_weather.value,  # 保持兼容性
            "season": self.get_current_season().value,
            "time_of_day": self.get_time_of_day(),
            "is_daytime": self.is_daytime(),
            "light_intensity": self.get_light_intensity(),
            "temperature": round(self.temperature, 1),
            "humidity": round(self.humidity, 1),
            "wind_speed": round(self.wind_speed, 1),
            "visibility": round(self.visibility, 1),
            "pressure": round(self.pressure, 1),
            "intensity": round(self.intensity, 2),
            "effects": self.get_weather_effects()
        }
        
        # 添加过渡状态信息
        if self.is_transitioning:
            transition_elapsed = (self.current_time - self.transition_start_time).total_seconds() / 3600
            progress = min(transition_elapsed / self.transition_duration, 1.0)
            
            data.update({
                "is_transitioning": True,
                "target_weather": self.target_weather.value,
                "target_intensity": round(self.target_intensity, 2),
                "transition_progress": round(progress, 2),
                "transition_duration": self.transition_duration
            })
        else:
            data["is_transitioning"] = False
            
        return data
    
    def set_weather(self, weather_type: WeatherType, intensity: float = 1.0):
        """手动设置天气类型和强度"""
        self.current_weather = weather_type
        self.intensity = max(0.1, min(2.0, intensity))  # 限制强度范围
        self._update_environmental_parameters()
    
    def advance_time(self, hours: float):
        """快进时间"""
        self.update_weather(hours)


class WeatherHistory:
    """天气历史记录类"""
    
    def __init__(self, max_records: int = 168):  # 一周的小时数
        """
        初始化天气历史
        
        Args:
            max_records: 最大记录数量
        """
        self.max_records = max_records
        self.history: List[Dict] = []
    
    def add_record(self, weather_data: Dict):
        """添加天气记录"""
        self.history.append(weather_data.copy())
        
        # 保持记录数量在限制内
        if len(self.history) > self.max_records:
            self.history.pop(0)
    
    def get_history(self, hours: int = 24) -> List[Dict]:
        """获取指定小时数的历史记录"""
        return self.history[-hours:] if hours <= len(self.history) else self.history
    
    def get_weather_statistics(self, hours: int = 24) -> Dict:
        """获取天气统计信息"""
        recent_history = self.get_history(hours)
        
        if not recent_history:
            return {}
        
        # 统计天气类型分布
        weather_counts = {}
        total_temp = 0
        total_humidity = 0
        
        for record in recent_history:
            weather_type = record.get("weather_type", "unknown")
            weather_counts[weather_type] = weather_counts.get(weather_type, 0) + 1
            total_temp += record.get("temperature", 0)
            total_humidity += record.get("humidity", 0)
        
        return {
            "weather_distribution": weather_counts,
            "average_temperature": round(total_temp / len(recent_history), 1),
            "average_humidity": round(total_humidity / len(recent_history), 1),
            "total_records": len(recent_history)
        }