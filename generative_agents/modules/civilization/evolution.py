import random
from datetime import datetime
from typing import Dict, List, Optional


class CivilizationEvolution:
    def __init__(self):
        self.eras = [
            {
                "key": "prehistoric",
                "name": "采猎时代",
                "emoji": "🪵",
                "tech_threshold": 12.0,
                "base_pop_growth": 0.001,
                "base_tech_growth": 0.4,
                "base_econ_growth": 0.25,
                "base_culture_growth": 0.15,
            },
            {
                "key": "agricultural",
                "name": "农业时代",
                "emoji": "🌾",
                "tech_threshold": 35.0,
                "base_pop_growth": 0.004,
                "base_tech_growth": 1.1,
                "base_econ_growth": 0.8,
                "base_culture_growth": 0.45,
            },
            {
                "key": "industrial",
                "name": "工业时代",
                "emoji": "🏭",
                "tech_threshold": 60.0,
                "base_pop_growth": 0.006,
                "base_tech_growth": 1.8,
                "base_econ_growth": 1.6,
                "base_culture_growth": 0.6,
            },
            {
                "key": "information",
                "name": "信息时代",
                "emoji": "💻",
                "tech_threshold": 85.0,
                "base_pop_growth": 0.003,
                "base_tech_growth": 2.2,
                "base_econ_growth": 2.0,
                "base_culture_growth": 1.1,
            },
            {
                "key": "ai",
                "name": "智能时代",
                "emoji": "🤖",
                "tech_threshold": 100.0,
                "base_pop_growth": 0.002,
                "base_tech_growth": 2.8,
                "base_econ_growth": 2.5,
                "base_culture_growth": 1.5,
            },
        ]

        self.current_era_index = 0
        self.population = 120.0
        self.tech_index = 8.0
        self.economy_index = 12.0
        self.culture_index = 6.0
        self.stability = 62.0
        self.governance = "部落联盟"
        self.infrastructure_level = 1.0

        self.last_game_time: Optional[datetime] = None
        self.events: List[Dict] = []
        self._event_hour_accumulator = 0.0

        self._rng = random.Random(9527)
        # AI 自主行动配置
        self.auto_actions_enabled = True
        self._auto_action_accumulator = 0.0

    def _clamp(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _current_era(self) -> Dict:
        return self.eras[self.current_era_index]

    def _progress_to_next_era(self) -> float:
        era = self._current_era()
        cur_threshold = 0.0 if self.current_era_index == 0 else self.eras[self.current_era_index - 1]["tech_threshold"]
        next_threshold = era["tech_threshold"]
        span = max(0.1, next_threshold - cur_threshold)
        progress = (self.tech_index - cur_threshold) / span
        return self._clamp(progress * 100.0, 0.0, 100.0)

    def update(self, current_time_iso: str, env_data: Optional[Dict] = None):
        try:
            current_time = datetime.fromisoformat(current_time_iso)
        except Exception:
            # 如果解析失败则跳过本次更新
            return

        if self.last_game_time is None:
            self.last_game_time = current_time
            return

        delta_seconds = (current_time - self.last_game_time).total_seconds()
        if delta_seconds <= 0:
            return

        delta_hours = delta_seconds / 3600.0
        self.last_game_time = current_time
        self._event_hour_accumulator += delta_hours
        self._auto_action_accumulator += delta_hours

        env_quality = 0.7
        activity = 1.0
        comfort = 0.7
        if env_data:
            env_quality = float(env_data.get("environment_quality", env_quality))
            combined = env_data.get("combined_effects", {})
            activity = float(combined.get("activity_level", activity))
            comfort = float(env_data.get("comfort_level", comfort))

        era = self._current_era()

        pop_growth_rate = era["base_pop_growth"] * (0.5 + env_quality) * activity
        self.population *= (1.0 + pop_growth_rate * delta_hours)
        self.population = self._clamp(self.population, 50.0, 1_000_000_000.0)

        tech_growth = era["base_tech_growth"] * (0.5 + env_quality)
        self.tech_index += tech_growth * delta_hours
        self.tech_index = self._clamp(self.tech_index, 0.0, 100.0)

        econ_growth = era["base_econ_growth"] * (0.5 + env_quality) * (self.population ** 0.001)
        self.economy_index += econ_growth * delta_hours
        self.economy_index = self._clamp(self.economy_index, 0.0, 1000.0)

        culture_growth = era["base_culture_growth"] * (0.5 + comfort)
        noise = self._rng.uniform(-0.05, 0.15)
        self.culture_index += (culture_growth + noise) * delta_hours
        self.culture_index = self._clamp(self.culture_index, 0.0, 1000.0)

        stability_drift = -0.02 * delta_hours + 0.04 * delta_hours * (env_quality - 0.5)
        stability_noise = self._rng.uniform(-0.05, 0.05) * delta_hours
        self.stability = self._clamp(self.stability + stability_drift + stability_noise, 0.0, 100.0)

        # 基建随经济与时间缓慢提升
        infra_growth = 0.02 * delta_hours * (self.economy_index / 100.0)
        self.infrastructure_level = self._clamp(self.infrastructure_level + infra_growth, 0.0, 100.0)

        self._maybe_transition_era(current_time_iso)
        self._maybe_change_governance()

        # AI 自主行动：根据文明状态定期触发行动
        self._maybe_auto_action(current_time_iso, env_data)

        if self._event_hour_accumulator >= 6.0:
            self._event_hour_accumulator = 0.0
            self._generate_development_event(current_time_iso)

    def _maybe_transition_era(self, ts: str):
        if self.current_era_index >= len(self.eras) - 1:
            return
        next_threshold = self.eras[self.current_era_index]["tech_threshold"]
        if self.tech_index >= next_threshold:
            prev = self.eras[self.current_era_index]
            self.current_era_index = min(self.current_era_index + 1, len(self.eras) - 1)
            cur = self.eras[self.current_era_index]
            self.events.append({
                "timestamp": ts,
                "era": cur["key"],
                "type": "milestone",
                "title": f"文明进入{cur['name']}",
                "description": f"从{prev['name']}迈进{cur['name']}，社会组织与生产力提升。",
            })
            if len(self.events) > 200:
                self.events = self.events[-120:]

    def _maybe_change_governance(self):
        era_key = self._current_era()["key"]
        if era_key == "prehistoric":
            self.governance = "部落联盟"
        elif era_key == "agricultural":
            self.governance = "城邦/王朝"
        elif era_key == "industrial":
            self.governance = "民族国家"
        elif era_key == "information":
            self.governance = "全球化治理"
        else:
            self.governance = "算法协治"

    def _generate_development_event(self, ts: str):
        era = self._current_era()
        key = era["key"]
        candidates = {
            "prehistoric": ["发现火种", "驯化动物", "石器改良"],
            "agricultural": ["灌溉系统建成", "轮作推广", "村落扩张"],
            "industrial": ["蒸汽机投产", "铁路铺设", "工厂密集化"],
            "information": ["互联网普及", "移动终端普及", "云计算成熟"],
            "ai": ["智能城市试点", "通用AI突破", "自治生产线"],
        }
        title = self._rng.choice(candidates.get(key, ["社会变迁"]))
        impact = {
            "population": round(self.population * self._rng.uniform(0.0005, 0.003), 2),
            "economy": round(self.economy_index * self._rng.uniform(0.005, 0.03), 2),
            "tech": round(self.tech_index * self._rng.uniform(0.01, 0.05), 2),
        }
        self.population = self.population + impact["population"]
        self.economy_index = self.economy_index + impact["economy"]
        self.tech_index = self.tech_index + impact["tech"]
        self.events.append({
            "timestamp": ts,
            "era": era["key"],
            "type": "development",
            "title": title,
            "description": f"{title}，推动社会发展。",
            "impact": impact,
        })
        if len(self.events) > 200:
            self.events = self.events[-120:]

    def _maybe_auto_action(self, ts: str, env_data: Optional[Dict]):
        if not self.auto_actions_enabled:
            return
        # 每 2 小时触发一次自主行动
        if self._auto_action_accumulator < 2.0:
            return
        self._auto_action_accumulator = 0.0

        era = self._current_era()
        next_threshold = era["tech_threshold"]
        # 简单启发式选择行动
        if self.stability < 45.0:
            self.apply_directive("稳定", intensity=1.2)
            return
        tech_gap = max(0.0, next_threshold - self.tech_index)
        if tech_gap > 8.0:
            self.apply_directive("科研", intensity=1.0)
            return
        # 经济目标随时代提升
        econ_target = 100.0 + self.current_era_index * 80.0
        if self.economy_index < econ_target:
            # 早期偏建设，后期偏部署
            if self.current_era_index <= 2:
                self.apply_directive("建设", intensity=1.0)
            else:
                self.apply_directive("部署", intensity=1.0)
            return
        if self.culture_index < 70.0:
            self.apply_directive("宣传", intensity=1.0)
            return
        # 默认：随机多样化
        self.apply_directive(self._rng.choice(["建设", "科研", "部署", "宣传"]) , intensity=self._rng.uniform(0.8, 1.3))

    def get_state(self) -> Dict:
        era = self._current_era()
        return {
            "era_key": era["key"],
            "era_name": era["name"],
            "era_emoji": era["emoji"],
            "population": int(self.population),
            "tech_index": round(self.tech_index, 2),
            "economy_index": round(self.economy_index, 2),
            "culture_index": round(self.culture_index, 2),
            "stability": round(self.stability, 2),
            "governance": self.governance,
            "infrastructure_level": round(self.infrastructure_level, 2),
            "auto_actions_enabled": self.auto_actions_enabled,
            "progress_to_next_era": round(self._progress_to_next_era(), 2),
            "current_time": self.last_game_time.isoformat() if self.last_game_time else None,
        }

    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        return self.events[-limit:] if self.events else []

    def apply_directive(self, action: str, intensity: float = 1.0, metadata: Optional[Dict] = None) -> Dict:
        """应用AI指令以影响文明指标，并记录事件。
        支持的指令：建设(build)、科研(research)、稳定(stabilize)、政策(policy)、宣传(broadcast)、部署(deploy)
        """
        action = (action or "").strip().lower()
        try:
            intensity = max(0.1, float(intensity))
        except Exception:
            intensity = 1.0

        ts = datetime.utcnow().isoformat()
        impact = {"population": 0.0, "economy": 0.0, "tech": 0.0, "culture": 0.0, "stability": 0.0}
        title = ""
        desc = ""

        if action in ("build", "建设", "建造"):
            econ = 2.0 * intensity
            pop = 0.5 * intensity
            stab = 0.2 * intensity
            self.economy_index += econ
            self.population += pop
            self.stability = self._clamp(self.stability + stab, 0.0, 100.0)
            self.infrastructure_level = self._clamp(self.infrastructure_level + 0.5 * intensity, 0.0, 100.0)
            title = "AI 指令：建设"
            desc = "推进基础设施与生产能力建设。"
            impact.update({"economy": econ, "population": pop, "stability": stab})
        elif action in ("research", "科研", "研究"):
            tech = 2.2 * intensity
            cult = 1.0 * intensity
            self.tech_index = self._clamp(self.tech_index + tech, 0.0, 100.0)
            self.culture_index += cult
            title = "AI 指令：科研"
            desc = "加速科技研发与知识传播。"
            impact.update({"tech": tech, "culture": cult})
        elif action in ("stabilize", "稳定", "维稳"):
            stab = 3.0 * intensity
            self.stability = self._clamp(self.stability + stab, 0.0, 100.0)
            title = "AI 指令：稳定"
            desc = "提升社会稳定度与秩序。"
            impact.update({"stability": stab})
        elif action in ("policy", "政策", "治理"):
            new_gov = None
            if metadata and isinstance(metadata, dict):
                new_gov = metadata.get("governance")
            if not new_gov:
                options = ["部落联盟", "城邦/王朝", "民族国家", "全球化治理", "算法协治"]
                try:
                    idx = options.index(self.governance)
                    new_gov = options[(idx + 1) % len(options)]
                except Exception:
                    new_gov = "全球化治理"
            self.governance = new_gov
            stab = 1.5 * intensity
            self.stability = self._clamp(self.stability + stab, 0.0, 100.0)
            title = f"AI 指令：政策调整 -> {new_gov}"
            desc = "调整治理模式以适配文明阶段。"
            impact.update({"stability": stab})
        elif action in ("broadcast", "宣传", "发布"):
            cult = 1.5 * intensity
            self.culture_index += cult
            title = "AI 指令：宣传"
            desc = "广泛发布指令与叙事，提升文化影响力。"
            impact.update({"culture": cult})
        elif action in ("deploy", "部署", "应用"):
            econ = 1.4 * intensity
            tech = 0.6 * intensity
            self.economy_index += econ
            self.tech_index = self._clamp(self.tech_index + tech, 0.0, 100.0)
            self.infrastructure_level = self._clamp(self.infrastructure_level + 0.3 * intensity, 0.0, 100.0)
            title = "AI 指令：部署"
            desc = "将技术应用到生产与社会系统。"
            impact.update({"economy": econ, "tech": tech})
        else:
            title = f"AI 指令：{action or '未知'}"
            desc = "指令已记录，但未定义具体效果。"

        era = self._current_era()
        event = {
            "timestamp": ts,
            "era": era["key"],
            "type": "directive",
            "title": title,
            "description": desc,
            "impact": {k: round(v, 2) for k, v in impact.items()},
        }
        self.events.append(event)
        if len(self.events) > 200:
            self.events = self.events[-120:]
        # 指令可能促成时代跃迁，进行一次检查
        self._maybe_transition_era(ts)
        return event