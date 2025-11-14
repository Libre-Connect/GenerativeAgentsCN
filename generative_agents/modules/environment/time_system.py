"""
时间和昼夜循环系统
管理模拟世界的时间流逝和昼夜变化
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from enum import Enum


class TimeOfDay(Enum):
    """一天中的时间段"""
    DAWN = "dawn"           # 黎明 (5:00-7:00)
    MORNING = "morning"     # 上午 (7:00-12:00)
    NOON = "noon"          # 正午 (12:00-13:00)
    AFTERNOON = "afternoon" # 下午 (13:00-17:00)
    DUSK = "dusk"          # 黄昏 (17:00-19:00)
    EVENING = "evening"     # 傍晚 (19:00-22:00)
    NIGHT = "night"        # 夜晚 (22:00-5:00)


class DayNightCycle:
    """昼夜循环系统"""
    
    def __init__(self, start_time: Optional[datetime] = None, time_scale: float = 1.0):
        """
        初始化昼夜循环系统
        
        Args:
            start_time: 开始时间，默认为当前时间
            time_scale: 时间缩放比例，1.0为正常速度，2.0为2倍速
        """
        self.current_time = start_time or datetime.now()
        self.time_scale = time_scale
        self.day_length_hours = 24  # 一天的小时数
        
        # 日出日落时间（可根据季节调整）
        self.sunrise_hour = 6.0
        self.sunset_hour = 18.0
        
        # 光照参数
        self.max_light_intensity = 1.0
        self.min_light_intensity = 0.05
        
        # 颜色温度参数（开尔文）
        self.daylight_temperature = 5500
        self.sunset_temperature = 3000
        self.night_temperature = 2700
    
    def update(self, delta_seconds: float):
        """
        更新时间系统
        
        Args:
            delta_seconds: 实际经过的秒数
        """
        # 根据时间缩放计算模拟时间增量
        simulated_seconds = delta_seconds * self.time_scale
        self.current_time += timedelta(seconds=simulated_seconds)
    
    def get_time_of_day(self) -> TimeOfDay:
        """获取当前时间段"""
        hour = self.current_time.hour
        minute = self.current_time.minute
        time_decimal = hour + minute / 60.0
        
        if 5.0 <= time_decimal < 7.0:
            return TimeOfDay.DAWN
        elif 7.0 <= time_decimal < 12.0:
            return TimeOfDay.MORNING
        elif 12.0 <= time_decimal < 13.0:
            return TimeOfDay.NOON
        elif 13.0 <= time_decimal < 17.0:
            return TimeOfDay.AFTERNOON
        elif 17.0 <= time_decimal < 19.0:
            return TimeOfDay.DUSK
        elif 19.0 <= time_decimal < 22.0:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def is_daytime(self) -> bool:
        """判断是否为白天"""
        time_of_day = self.get_time_of_day()
        return time_of_day in [TimeOfDay.DAWN, TimeOfDay.MORNING, TimeOfDay.NOON, TimeOfDay.AFTERNOON]
    
    def get_sun_position(self) -> Tuple[float, float]:
        """
        获取太阳位置（方位角和高度角）
        
        Returns:
            Tuple[float, float]: (方位角, 高度角) 单位：度
        """
        hour = self.current_time.hour
        minute = self.current_time.minute
        time_decimal = hour + minute / 60.0
        
        # 简化的太阳位置计算
        # 假设太阳从东方升起（90度），正午在南方（180度），西方落下（270度）
        
        if self.sunrise_hour <= time_decimal <= self.sunset_hour:
            # 白天：太阳在地平线上
            day_progress = (time_decimal - self.sunrise_hour) / (self.sunset_hour - self.sunrise_hour)
            
            # 方位角：从东（90度）到西（270度）
            azimuth = 90 + day_progress * 180
            
            # 高度角：正弦曲线，正午最高
            elevation = math.sin(day_progress * math.pi) * 90
        else:
            # 夜晚：太阳在地平线下
            if time_decimal < self.sunrise_hour:
                # 午夜到日出
                night_progress = (time_decimal + 24 - self.sunset_hour) / (24 - self.sunset_hour + self.sunrise_hour)
            else:
                # 日落到午夜
                night_progress = (time_decimal - self.sunset_hour) / (24 - self.sunset_hour + self.sunrise_hour)
            
            azimuth = 270 + night_progress * 180
            if azimuth >= 360:
                azimuth -= 360
            
            elevation = -30  # 太阳在地平线下30度
        
        return azimuth, elevation
    
    def get_light_intensity(self) -> float:
        """
        获取当前光照强度 (0.0-1.0)
        """
        hour = self.current_time.hour
        minute = self.current_time.minute
        time_decimal = hour + minute / 60.0
        
        if self.sunrise_hour <= time_decimal <= self.sunset_hour:
            # 白天光照计算
            day_progress = (time_decimal - self.sunrise_hour) / (self.sunset_hour - self.sunrise_hour)
            
            # 使用正弦曲线模拟光照变化
            intensity = math.sin(day_progress * math.pi)
            
            # 日出日落时的渐变效果
            if day_progress < 0.1:  # 日出后1小时内
                fade_factor = day_progress / 0.1
                intensity *= fade_factor
            elif day_progress > 0.9:  # 日落前1小时内
                fade_factor = (1.0 - day_progress) / 0.1
                intensity *= fade_factor
            
            return max(self.min_light_intensity, intensity * self.max_light_intensity)
        else:
            # 夜晚光照
            return self.min_light_intensity
    
    def get_ambient_color(self) -> Tuple[float, float, float]:
        """
        获取环境光颜色 (RGB, 0.0-1.0)
        """
        time_of_day = self.get_time_of_day()
        light_intensity = self.get_light_intensity()
        
        if time_of_day == TimeOfDay.DAWN:
            # 黎明：橙红色
            r, g, b = 1.0, 0.7, 0.4
        elif time_of_day in [TimeOfDay.MORNING, TimeOfDay.NOON, TimeOfDay.AFTERNOON]:
            # 白天：白色/淡蓝色
            r, g, b = 1.0, 1.0, 0.9
        elif time_of_day == TimeOfDay.DUSK:
            # 黄昏：橙色
            r, g, b = 1.0, 0.6, 0.3
        elif time_of_day == TimeOfDay.EVENING:
            # 傍晚：深橙色
            r, g, b = 0.8, 0.4, 0.2
        else:
            # 夜晚：深蓝色
            r, g, b = 0.1, 0.1, 0.3
        
        # 根据光照强度调整颜色
        r *= light_intensity
        g *= light_intensity
        b *= light_intensity
        
        return r, g, b
    
    def get_color_temperature(self) -> float:
        """
        获取色温（开尔文）
        """
        time_of_day = self.get_time_of_day()
        
        if time_of_day in [TimeOfDay.MORNING, TimeOfDay.NOON, TimeOfDay.AFTERNOON]:
            return self.daylight_temperature
        elif time_of_day in [TimeOfDay.DAWN, TimeOfDay.DUSK, TimeOfDay.EVENING]:
            return self.sunset_temperature
        else:
            return self.night_temperature
    
    def get_shadow_length_factor(self) -> float:
        """
        获取阴影长度因子
        太阳高度角越低，阴影越长
        """
        _, elevation = self.get_sun_position()
        
        if elevation <= 0:
            return 10.0  # 夜晚，极长阴影
        
        # 阴影长度与太阳高度角成反比
        shadow_factor = 1.0 / math.tan(math.radians(max(elevation, 5)))
        return min(shadow_factor, 10.0)
    
    def get_activity_modifier(self) -> float:
        """
        获取活动修正因子
        不同时间段人们的活动水平不同
        """
        time_of_day = self.get_time_of_day()
        
        activity_levels = {
            TimeOfDay.DAWN: 0.3,
            TimeOfDay.MORNING: 0.8,
            TimeOfDay.NOON: 0.9,
            TimeOfDay.AFTERNOON: 1.0,
            TimeOfDay.DUSK: 0.7,
            TimeOfDay.EVENING: 0.6,
            TimeOfDay.NIGHT: 0.2
        }
        
        return activity_levels.get(time_of_day, 0.5)
    
    def set_time_scale(self, scale: float):
        """设置时间缩放比例"""
        self.time_scale = max(0.1, scale)  # 最小0.1倍速
    
    def set_time(self, new_time: datetime):
        """设置当前时间"""
        self.current_time = new_time
    
    def advance_time(self, hours: float):
        """快进时间"""
        self.current_time += timedelta(hours=hours)
    
    def get_time_data(self) -> Dict:
        """获取完整的时间数据"""
        azimuth, elevation = self.get_sun_position()
        r, g, b = self.get_ambient_color()
        
        return {
            "current_time": self.current_time.isoformat(),
            "time_of_day": self.get_time_of_day().value,
            "is_daytime": self.is_daytime(),
            "light_intensity": round(self.get_light_intensity(), 3),
            "sun_position": {
                "azimuth": round(azimuth, 1),
                "elevation": round(elevation, 1)
            },
            "ambient_color": {
                "r": round(r, 3),
                "g": round(g, 3),
                "b": round(b, 3)
            },
            "color_temperature": self.get_color_temperature(),
            "shadow_length_factor": round(self.get_shadow_length_factor(), 2),
            "activity_modifier": round(self.get_activity_modifier(), 2),
            "time_scale": self.time_scale
        }


class SeasonalTimeSystem:
    """季节性时间系统"""
    
    def __init__(self, day_night_cycle: DayNightCycle):
        """
        初始化季节性时间系统
        
        Args:
            day_night_cycle: 昼夜循环系统实例
        """
        self.day_night_cycle = day_night_cycle
    
    def get_season_from_date(self, date: datetime) -> str:
        """根据日期获取季节"""
        month = date.month
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "autumn"
        else:
            return "winter"
    
    def adjust_daylight_hours(self):
        """根据季节调整日照时间"""
        current_season = self.get_season_from_date(self.day_night_cycle.current_time)
        month = self.day_night_cycle.current_time.month
        
        # 简化的季节性日照调整
        if current_season == "summer":
            # 夏季：日照时间长
            self.day_night_cycle.sunrise_hour = 5.5
            self.day_night_cycle.sunset_hour = 18.5
        elif current_season == "winter":
            # 冬季：日照时间短
            self.day_night_cycle.sunrise_hour = 7.0
            self.day_night_cycle.sunset_hour = 17.0
        else:
            # 春秋季：中等日照时间
            self.day_night_cycle.sunrise_hour = 6.0
            self.day_night_cycle.sunset_hour = 18.0
    
    def get_seasonal_effects(self) -> Dict:
        """获取季节性效果"""
        season = self.get_season_from_date(self.day_night_cycle.current_time)
        
        effects = {
            "spring": {
                "growth_rate_modifier": 1.3,
                "temperature_modifier": 0,
                "activity_modifier": 1.1,
                "mood_modifier": 0.1
            },
            "summer": {
                "growth_rate_modifier": 1.5,
                "temperature_modifier": 5,
                "activity_modifier": 1.2,
                "mood_modifier": 0.15
            },
            "autumn": {
                "growth_rate_modifier": 0.8,
                "temperature_modifier": -3,
                "activity_modifier": 0.9,
                "mood_modifier": -0.05
            },
            "winter": {
                "growth_rate_modifier": 0.3,
                "temperature_modifier": -8,
                "activity_modifier": 0.7,
                "mood_modifier": -0.1
            }
        }
        
        return effects.get(season, {})