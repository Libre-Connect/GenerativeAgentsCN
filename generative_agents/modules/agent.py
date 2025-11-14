"""generative_agents.agent"""

import os
import math
import random
import datetime

from modules import memory, prompt, utils
from modules.model.llm_model import create_llm_model
from modules.model.image_model import create_image_model
from modules.economy.economy import Inventory, Wallet
from modules.memory.associate import Concept
from modules.terrain.terrain_development import ResourceType


class Agent:
    def __init__(self, config, maze, conversation, logger, game=None):
        self.name = config["name"]
        self.maze = maze
        self.conversation = conversation
        self._llm = None
        self._image_model = None
        self.logger = logger
        self.game = game  # 游戏实例，用于访问环境管理器

        # agent config
        self.percept_config = config["percept"]
        self.think_config = config["think"]
        self.chat_iter = config["chat_iter"]

        # memory
        self.spatial = memory.Spatial(**config["spatial"])
        self.schedule = memory.Schedule(**config["schedule"])
        self.associate = memory.Associate(
            os.path.join(config["storage_root"], "associate"), **config["associate"]
        )
        self.concepts, self.chats = [], config.get("chats", [])

        # prompt
        self.scratch = prompt.Scratch(self.name, config["currently"], config["scratch"])

        # status
        status = {"poignancy": 0}
        self.status = utils.update_dict(status, config.get("status", {}))
        self.plan = config.get("plan", {})

        # 经济与物品系统：基础库存与钱包
        self.inventory: Inventory = Inventory()
        self.wallet: Wallet = Wallet(balance=100.0)

        # record
        self.last_record = utils.get_timer().daily_duration()

        # action and events
        if "action" in config:
            self.action = memory.Action.from_dict(config["action"])
            tiles = self.maze.get_address_tiles(self.get_event().address)
            config["coord"] = random.choice(list(tiles))
        else:
            tile = self.maze.tile_at(config["coord"])
            address = tile.get_address("game_object", as_list=True)
            self.action = memory.Action(
                memory.Event(self.name, address=address),
                memory.Event(address[-1], address=address),
            )

        # update maze
        self.coord, self.path = None, None
        self.move(config["coord"], config.get("path"))
        if self.coord is None:
            self.coord = config["coord"]

    def abstract(self):
        des = {
            "name": self.name,
            "currently": self.scratch.currently,
            "tile": self.maze.tile_at(self.coord).abstract(),
            "status": self.status,
            "concepts": {c.node_id: c.abstract() for c in self.concepts},
            "chats": self.chats,
            "action": self.action.abstract(),
            "associate": self.associate.abstract(),
        }
        if self.schedule.scheduled():
            des["schedule"] = self.schedule.abstract()
        if self.llm_available():
            des["llm"] = self._llm.get_summary()
        # if self.plan.get("path"):
        #     des["path"] = "-".join(
        #         ["{},{}".format(c[0], c[1]) for c in self.plan["path"]]
        #     )
        return des

    def __str__(self):
        return utils.dump_dict(self.abstract())

    def reset(self):
        if not self._llm:
            self._llm = create_llm_model(self.think_config["llm"])
        if not self._image_model:
            self._image_model = create_image_model({"provider": "hybrid"})

    def completion(self, func_hint, *args, **kwargs):
        assert hasattr(
            self.scratch, "prompt_" + func_hint
        ), "Can not find func prompt_{} from scratch".format(func_hint)
        func = getattr(self.scratch, "prompt_" + func_hint)
        prompt = func(*args, **kwargs)
        title, msg = "{}.{}".format(self.name, func_hint), {}
        if self.llm_available():
            self.logger.info("{} -> {}".format(self.name, func_hint))
            output = self._llm.completion(**prompt, caller=func_hint)
            responses = self._llm.meta_responses
            msg = {"<PROMPT>": "\n" + prompt["prompt"] + "\n"}
            msg.update(
                {
                    "<RESPONSE[{}/{}]>".format(idx+1, len(responses)): "\n" + r + "\n"
                    for idx, r in enumerate(responses)
                }
            )
        else:
            output = prompt.get("failsafe")
        msg["<OUTPUT>"] = "\n" + str(output) + "\n"
        self.logger.debug(utils.block_msg(title, msg))
        return output

    def think(self, status, agents):
        events = self.move(status["coord"], status.get("path"))
        plan, _ = self.make_schedule()

        # 获取天气数据和影响
        weather_data = self.get_weather_data()
        weather_effects = self.get_weather_effects()

        if (plan["describe"] == "sleeping" or "睡" in plan["describe"]) and self.is_awake():
            self.logger.info("{} is going to sleep...".format(self.name))
            address = self.spatial.find_address("睡觉", as_list=True)
            tiles = self.maze.get_address_tiles(address)
            coord = random.choice(list(tiles))
            events = self.move(coord)
            self.action = memory.Action(
                memory.Event(self.name, "正在", "睡觉", address=address, emoji="😴"),
                memory.Event(
                    address[-1],
                    "被占用",
                    self.name,
                    address=address,
                    emoji="🛌",
                ),
                duration=plan["duration"],
                start=utils.get_timer().daily_time(plan["start"]),
            )
        if self.is_awake():
            self.percept()
            # 在制定计划时考虑天气因素
            self.make_plan(agents, weather_data=weather_data, weather_effects=weather_effects)
            self.reflect()
        else:
            if self.action.finished():
                self.action = self._determine_action(weather_data=weather_data, weather_effects=weather_effects)

        emojis = {}
        if self.action:
            emojis[self.name] = {"emoji": self.get_event().emoji, "coord": self.coord}
        for eve, coord in events.items():
            if eve.subject in agents:
                continue
            emojis[":".join(eve.address)] = {"emoji": eve.emoji, "coord": coord}
        self.plan = {
            "name": self.name,
            "path": self.find_path(agents),
            "emojis": emojis,
        }
        return self.plan

    def move(self, coord, path=None):
        events = {}

        def _update_tile(coord):
            tile = self.maze.tile_at(coord)
            if not self.action:
                return {}
            if not tile.update_events(self.get_event()):
                tile.add_event(self.get_event())
            obj_event = self.get_event(False)
            if obj_event:
                self.maze.update_obj(coord, obj_event)
            return {e: coord for e in tile.get_events()}

        if self.coord and self.coord != coord:
            tile = self.get_tile()
            tile.remove_events(subject=self.name)
            if tile.has_address("game_object"):
                addr = tile.get_address("game_object")
                self.maze.update_obj(
                    self.coord, memory.Event(addr[-1], address=addr)
                )
            events.update({e: self.coord for e in tile.get_events()})
        if not path:
            events.update(_update_tile(coord))
        self.coord = coord
        self.path = path or []

        return events

    def make_schedule(self):
        if not self.schedule.scheduled():
            self.logger.info("{} is making schedule...".format(self.name))
            
            # 获取天气数据以影响日程安排
            weather_data = self.get_weather_data()
            weather_effects = self.get_weather_effects()
            
            # update currently
            if self.associate.index.nodes_num > 0:
                self.associate.cleanup_index()
                focus = [
                    f"{self.name} 在 {utils.get_timer().daily_format_cn()} 的计划。",
                    f"在 {self.name} 的生活中，重要的近期事件。",
                ]
                retrieved = self.associate.retrieve_focus(focus)
                self.logger.info(
                    "{} retrieved {} concepts".format(self.name, len(retrieved))
                )
                if retrieved:
                    plan = self.completion("retrieve_plan", retrieved)
                    thought = self.completion("retrieve_thought", retrieved)
                    self.scratch.currently = self.completion(
                        "retrieve_currently", plan, thought
                    )
            # make init schedule
            self.schedule.create = utils.get_timer().get_date()
            wake_up = self.completion("wake_up")
            
            # 根据是否有天气数据选择不同的prompt
            if weather_data and weather_effects:
                init_schedule = self.completion("schedule_init_weather", wake_up, weather_data, weather_effects)
            else:
                init_schedule = self.completion("schedule_init", wake_up)
            # make daily schedule
            hours = [f"{i}:00" for i in range(24)]
            # seed = [(h, "sleeping") for h in hours[:wake_up]]
            seed = [(h, "睡觉") for h in hours[:wake_up]]
            seed += [(h, "") for h in hours[wake_up:]]
            schedule = {}
            for _ in range(self.schedule.max_try):
                schedule = {h: s for h, s in seed[:wake_up]}
                schedule.update(
                    self.completion("schedule_daily", wake_up, init_schedule)
                )
                if len(set(schedule.values())) >= self.schedule.diversity:
                    break

            def _to_duration(date_str):
                return utils.daily_duration(utils.to_date(date_str, "%H:%M"))

            schedule = {_to_duration(k): v for k, v in schedule.items()}
            starts = list(sorted(schedule.keys()))
            for idx, start in enumerate(starts):
                end = starts[idx + 1] if idx + 1 < len(starts) else 24 * 60
                self.schedule.add_plan(schedule[start], end - start)
            schedule_time = utils.get_timer().time_format_cn(self.schedule.create)
            thought = "这是 {} 在 {} 的计划：{}".format(
                self.name, schedule_time, "；".join(init_schedule)
            )
            event = memory.Event(
                self.name,
                "计划",
                schedule_time,
                describe=thought,
                address=self.get_tile().get_address(),
            )
            self._add_concept(
                "thought",
                event,
                expire=self.schedule.create + datetime.timedelta(days=30),
            )
        # decompose current plan
        plan, _ = self.schedule.current_plan()
        if self.schedule.decompose(plan):
            decompose_schedule = self.completion(
                "schedule_decompose", plan, self.schedule
            )
            decompose, start = [], plan["start"]
            for describe, duration in decompose_schedule:
                decompose.append(
                    {
                        "idx": len(decompose),
                        "describe": describe,
                        "start": start,
                        "duration": duration,
                    }
                )
                start += duration
            plan["decompose"] = decompose
        return self.schedule.current_plan()

    def revise_schedule(self, event, start, duration):
        self.action = memory.Action(event, start=start, duration=duration)
        plan, _ = self.schedule.current_plan()
        if len(plan["decompose"]) > 0:
            plan["decompose"] = self.completion(
                "schedule_revise", self.action, self.schedule
            )

    def percept(self):
        scope = self.maze.get_scope(self.coord, self.percept_config)
        # add spatial memory
        for tile in scope:
            if tile.has_address("game_object"):
                self.spatial.add_leaf(tile.address)
        events, arena = {}, self.get_tile().get_address("arena")
        # gather events in scope
        for tile in scope:
            if not tile.events or tile.get_address("arena") != arena:
                continue
            dist = math.dist(tile.coord, self.coord)
            for event in tile.get_events():
                if dist < events.get(event, float("inf")):
                    events[event] = dist
        events = list(sorted(events.keys(), key=lambda k: events[k]))
        # get concepts
        self.concepts, valid_num = [], 0
        for idx, event in enumerate(events[: self.percept_config["att_bandwidth"]]):
            recent_nodes = (
                self.associate.retrieve_events() + self.associate.retrieve_chats()
            )
            recent_nodes = set(n.describe for n in recent_nodes)
            if event.get_describe() not in recent_nodes:
                if event.object == "idle" or event.object == "空闲":
                    node = Concept.from_event(
                        "idle_" + str(idx), "event", event, poignancy=1
                    )
                else:
                    valid_num += 1
                    node_type = "chat" if event.fit(self.name, "对话") else "event"
                    node = self._add_concept(node_type, event)
                    self.status["poignancy"] += node.poignancy
                self.concepts.append(node)
        self.concepts = [c for c in self.concepts if c.event.subject != self.name]
        self.logger.info(
            "{} percept {}/{} concepts".format(self.name, valid_num, len(self.concepts))
        )

    def make_plan(self, agents, weather_data=None, weather_effects=None):
        # 考虑天气对反应的影响
        if self._reaction(agents, weather_effects=weather_effects):
            return
        if self.path:
            return
        if self.action.finished():
            self.action = self._determine_action(weather_data=weather_data, weather_effects=weather_effects)

    # create action && object events
    def make_event(self, subject, describe, address):
        # emoji = self.completion("describe_emoji", describe)
        # return self.completion(
        #     "describe_event", subject, subject + describe, address, emoji
        # )

        e_describe = describe.replace("(", "").replace(")", "").replace("<", "").replace(">", "")
        if e_describe.startswith(subject + "此时"):
            e_describe = e_describe[len(subject + "此时"):]
        if e_describe.startswith(subject):
            e_describe = e_describe[len(subject):]
        event = memory.Event(
            subject, "此时", e_describe, describe=describe, address=address
        )
        return event

    def reflect(self):
        def _add_thought(thought, evidence=None):
            # event = self.completion(
            #     "describe_event",
            #     self.name,
            #     thought,
            #     address=self.get_tile().get_address(),
            # )
            event = self.make_event(self.name, thought, self.get_tile().get_address())
            return self._add_concept("thought", event, filling=evidence)

        if self.status["poignancy"] < self.think_config["poignancy_max"]:
            return
        nodes = self.associate.retrieve_events() + self.associate.retrieve_thoughts()
        if not nodes:
            return
        self.logger.info(
            "{} reflect(P{}/{}) with {} concepts...".format(
                self.name,
                self.status["poignancy"],
                self.think_config["poignancy_max"],
                len(nodes),
            )
        )
        nodes = sorted(nodes, key=lambda n: n.access, reverse=True)[
            : self.associate.max_importance
        ]
        # summary thought
        focus = self.completion("reflect_focus", nodes, 3)
        retrieved = self.associate.retrieve_focus(focus, reduce_all=False)
        for r_nodes in retrieved.values():
            thoughts = self.completion("reflect_insights", r_nodes, 5)
            for thought, evidence in thoughts:
                _add_thought(thought, evidence)
        # summary chats
        if self.chats:
            recorded, evidence = set(), []
            for name, _ in self.chats:
                if name == self.name or name in recorded:
                    continue
                res = self.associate.retrieve_chats(name)
                if res and len(res) > 0:
                    node = res[-1]
                    evidence.append(node.node_id)
            thought = self.completion("reflect_chat_planing", self.chats)
            _add_thought(f"对于 {self.name} 的计划：{thought}", evidence)
            thought = self.completion("reflect_chat_memory", self.chats)
            _add_thought(f"{self.name} {thought}", evidence)
        self.status["poignancy"] = 0
        self.chats = []

    def find_path(self, agents):
        address = self.get_event().address
        if self.path:
            return self.path
        if address == self.get_tile().get_address():
            return []
        if address[0] == "<waiting>":
            return []
        if address[0] == "<persona>":
            target_tiles = self.maze.get_around(agents[address[1]].coord)
        else:
            target_tiles = self.maze.get_address_tiles(address)
        if tuple(self.coord) in target_tiles:
            return []

        # filter tile with self event
        def _ignore_target(t_coord):
            if list(t_coord) == list(self.coord):
                return True
            events = self.maze.tile_at(t_coord).get_events()
            if any(e.subject in agents for e in events):
                return True
            return False

        target_tiles = [t for t in target_tiles if not _ignore_target(t)]
        if not target_tiles:
            return []
        if len(target_tiles) >= 4:
            target_tiles = random.sample(target_tiles, 4)
        pathes = {t: self.maze.find_path(self.coord, t) for t in target_tiles}
        target = min(pathes, key=lambda p: len(pathes[p]))
        return pathes[target][1:]

    def _determine_action(self, weather_data=None, weather_effects=None):
        self.logger.info("{} is determining action...".format(self.name))
        plan, de_plan = self.schedule.current_plan()
        describes = [plan["describe"], de_plan["describe"]]
        
        # 根据天气调整行动描述
        if weather_data and weather_effects:
            describes = self._adjust_action_for_weather(describes, weather_data, weather_effects)
        
        address = self.spatial.find_address(describes[0], as_list=True)
        if not address:
            tile = self.get_tile()
            kwargs = {
                "describes": describes,
                "spatial": self.spatial,
                "address": tile.get_address("world", as_list=True),
            }
            kwargs["address"].append(
                self.completion("determine_sector", **kwargs, tile=tile)
            )
            arenas = self.spatial.get_leaves(kwargs["address"])
            if len(arenas) == 1:
                kwargs["address"].append(arenas[0])
            else:
                kwargs["address"].append(self.completion("determine_arena", **kwargs))
            objs = self.spatial.get_leaves(kwargs["address"])
            if len(objs) == 1:
                kwargs["address"].append(objs[0])
            elif len(objs) > 1:
                kwargs["address"].append(self.completion("determine_object", **kwargs))
            address = kwargs["address"]

        event = self.make_event(self.name, describes[-1], address)
        obj_describe = self.completion("describe_object", address[-1], describes[-1])
        obj_event = self.make_event(address[-1], obj_describe, address)

        event.emoji = f"{de_plan['describe']}"

        return memory.Action(
            event,
            obj_event,
            duration=de_plan["duration"],
            start=utils.get_timer().daily_time(de_plan["start"]),
        )

    def _reaction(self, agents=None, ignore_words=None, weather_effects=None):
        focus = None
        ignore_words = ignore_words or ["空闲"]
        
        # 根据天气调整反应倾向
        if weather_effects:
            social_modifier = weather_effects.get("social_activity_modifier", 1.0)
            if social_modifier < 0.8:
                # 天气不好时，减少社交反应
                if random.random() > social_modifier:
                    return False

        def _focus(concept):
            return concept.event.subject in agents

        def _ignore(concept):
            return any(i in concept.describe for i in ignore_words)

        if agents:
            priority = [i for i in self.concepts if _focus(i)]
            if priority:
                focus = random.choice(priority)
        if not focus:
            priority = [i for i in self.concepts if not _ignore(i)]
            if priority:
                focus = random.choice(priority)
        if not focus or focus.event.subject not in agents:
            return
        other, focus = agents[focus.event.subject], self.associate.get_relation(focus)

        if self._chat_with(other, focus):
            return True
        if self._wait_other(other, focus):
            return True
        return False

    def _skip_react(self, other):
        def _skip(event):
            if not event.address or "sleeping" in event.get_describe(False) or "睡觉" in event.get_describe(False):
                return True
            if event.predicate == "待开始":
                return True
            return False

        if utils.get_timer().daily_duration(mode="hour") >= 23:
            return True
        if _skip(self.get_event()) or _skip(other.get_event()):
            return True
        return False

    def _chat_with(self, other, focus):
        if len(self.schedule.daily_schedule) < 1 or len(other.schedule.daily_schedule) < 1:
            # initializing
            return False
        if self._skip_react(other):
            return False
        if other.path:
            return False
        if self.get_event().fit(predicate="对话") or other.get_event().fit(predicate="对话"):
            return False

        chats = self.associate.retrieve_chats(other.name)
        if chats:
            delta = utils.get_timer().get_delta(chats[0].create)
            self.logger.info(
                "retrieved chat between {} and {}({} min):\n{}".format(
                    self.name, other.name, delta, chats[0]
                )
            )
            if delta < 60:
                return False

        if not self.completion("decide_chat", self, other, focus, chats):
            return False

        self.logger.info("{} decides chat with {}".format(self.name, other.name))
        start, chats = utils.get_timer().get_date(), []
        relations = [
            self.completion("summarize_relation", self, other.name),
            other.completion("summarize_relation", other, self.name),
        ]

        for i in range(self.chat_iter):
            text = self.completion(
                "generate_chat", self, other, relations[0], chats
            )

            if i > 0:
                # 对于发起对话的Agent，从第2轮对话开始，检查是否出现“复读”现象
                end = self.completion(
                    "generate_chat_check_repeat", self, chats, text
                )
                if end:
                    break

                # 对于发起对话的Agent，从第2轮对话开始，检查话题是否结束
                chats.append((self.name, text))
                end = self.completion(
                    "decide_chat_terminate", self, other, chats
                )
                if end:
                    break
            else :
                chats.append((self.name, text))

            text = other.completion(
                "generate_chat", other, self, relations[1], chats
            )
            if i > 0:
                # 对于响应对话的Agent，从第2轮开始，检查是否出现“复读”现象
                end = self.completion(
                    "generate_chat_check_repeat", other, chats, text
                )
                if end:
                    break

            chats.append((other.name, text))

            # 对于响应对话的Agent，从第1轮开始，检查话题是否结束
            end = other.completion(
                "decide_chat_terminate", other, self, chats
            )
            if end:
                break

        key = utils.get_timer().get_date("%Y%m%d-%H:%M")
        if key not in self.conversation.keys():
            self.conversation[key] = []
        self.conversation[key].append({f"{self.name} -> {other.name} @ {'，'.join(self.get_event().address)}": chats})

        self.logger.info(
            "{} and {} has chats\n  {}".format(
                self.name,
                other.name,
                "\n  ".join(["{}: {}".format(n, c) for n, c in chats]),
            )
        )
        chat_summary = self.completion("summarize_chats", chats)
        duration = int(sum([len(c[1]) for c in chats]) / 240)
        self.schedule_chat(
            chats, chat_summary, start, duration, other
        )
        other.schedule_chat(chats, chat_summary, start, duration, self)
        return True

    def _wait_other(self, other, focus):
        if self._skip_react(other):
            return False
        if not self.path:
            return False
        if self.get_event().address != other.get_tile().get_address():
            return False
        if not self.completion("decide_wait", self, other, focus):
            return False
        self.logger.info("{} decides wait to {}".format(self.name, other.name))
        start = utils.get_timer().get_date()
        # duration = other.action.end - start
        t = other.action.end - start
        duration = int(t.total_seconds() / 60)
        event = memory.Event(
            self.name,
            "waiting to start",
            self.get_event().get_describe(False),
            # address=["<waiting>"] + self.get_event().address,
            address=self.get_event().address,
            emoji=f"⌛",
        )
        self.revise_schedule(event, start, duration)

    def schedule_chat(self, chats, chats_summary, start, duration, other, address=None):
        self.chats.extend(chats)
        event = memory.Event(
            self.name,
            "对话",
            other.name,
            describe=chats_summary,
            address=address or self.get_tile().get_address(),
            emoji=f"💬",
        )
        self.revise_schedule(event, start, duration)

    def _add_concept(
        self,
        e_type,
        event,
        create=None,
        expire=None,
        filling=None,
    ):
        if event.fit(None, "is", "idle"):
            poignancy = 1
        elif event.fit(None, "此时", "空闲"):
            poignancy = 1
        elif e_type == "chat":
            poignancy = self.completion("poignancy_chat", event)
        else:
            poignancy = self.completion("poignancy_event", event)
        self.logger.debug("{} add associate {}".format(self.name, event))
        return self.associate.add_node(
            e_type,
            event,
            poignancy,
            create=create,
            expire=expire,
            filling=filling,
        )

    def get_tile(self):
        return self.maze.tile_at(self.coord)

    def get_event(self, as_act=True):
        return self.action.event if as_act else self.action.obj_event

    def is_awake(self):
        if not self.action:
            return True
        if self.get_event().fit(self.name, "is", "sleeping"):
            return False
        if self.get_event().fit(self.name, "正在", "睡觉"):
            return False
        return True

    def get_weather_data(self):
        """获取当前天气数据"""
        if self.game and hasattr(self.game, 'environment_manager'):
            return self.game.environment_manager.get_environment_data()
        return None

    def get_weather_effects(self):
        """获取天气对Agent行为的影响"""
        weather_data = self.get_weather_data()
        if not weather_data:
            return {}
        
        weather_info = weather_data.get("weather", {})
        return weather_info.get("effects", {})

    def _adjust_action_for_weather(self, describes, weather_data, weather_effects):
        """根据天气调整行动描述"""
        if not weather_data or not weather_effects:
            return describes
        
        weather_type = weather_data.get("weather", {}).get("type", "sunny")
        social_modifier = weather_effects.get("social_activity_modifier", 1.0)
        movement_modifier = weather_effects.get("movement_speed_modifier", 1.0)
        mood_modifier = weather_effects.get("mood_modifier", 0.0)
        
        adjusted_describes = describes.copy()
        
        # 根据天气类型调整行动
        if weather_type in ["rainy", "stormy"]:
            # 雨天或暴风雨天气，倾向于室内活动
            for i, desc in enumerate(adjusted_describes):
                if "户外" in desc or "外面" in desc or "散步" in desc:
                    if weather_type == "stormy":
                        adjusted_describes[i] = desc.replace("户外", "室内").replace("外面", "家里").replace("散步", "在家休息")
                    else:
                        adjusted_describes[i] = desc.replace("散步", "在室内活动")
        
        elif weather_type == "snowy":
            # 雪天，调整户外活动
            for i, desc in enumerate(adjusted_describes):
                if "散步" in desc:
                    adjusted_describes[i] = desc.replace("散步", "欣赏雪景")
        
        elif weather_type == "foggy":
            # 雾天，减少户外活动
            for i, desc in enumerate(adjusted_describes):
                if "户外" in desc:
                    adjusted_describes[i] = desc.replace("户外", "室内")
        
        # 根据社交活动修正因子调整
        if social_modifier < 0.8:
            for i, desc in enumerate(adjusted_describes):
                if "聚会" in desc or "社交" in desc:
                    adjusted_describes[i] = desc.replace("聚会", "独处").replace("社交", "个人活动")
        
        return adjusted_describes

    def _adjust_schedule_for_weather(self, schedule, weather_data, weather_effects):
        """根据天气调整日程安排"""
        if not weather_data or not weather_effects:
            return schedule
        
        weather_type = weather_data.get("weather", {}).get("type", "sunny")
        social_modifier = weather_effects.get("social_activity_modifier", 1.0)
        movement_modifier = weather_effects.get("movement_speed_modifier", 1.0)
        mood_modifier = weather_effects.get("mood_modifier", 0.0)
        
        adjusted_schedule = []
        
        for activity in schedule:
            adjusted_activity = activity
            
            # 根据天气类型调整活动
            if weather_type in ["rainy", "stormy"]:
                # 雨天或暴风雨，将户外活动改为室内活动
                if "散步" in activity:
                    adjusted_activity = activity.replace("散步", "在家阅读")
                elif "户外" in activity:
                    adjusted_activity = activity.replace("户外", "室内")
                elif "公园" in activity:
                    adjusted_activity = activity.replace("公园", "家里")
                elif "运动" in activity and "室内" not in activity:
                    adjusted_activity = activity.replace("运动", "室内运动")
            
            elif weather_type == "snowy":
                # 雪天，调整户外活动
                if "散步" in activity:
                    adjusted_activity = activity.replace("散步", "欣赏雪景")
                elif "运动" in activity and "室内" not in activity:
                    adjusted_activity = activity.replace("运动", "室内运动")
            
            elif weather_type == "foggy":
                # 雾天，减少户外活动
                if "户外" in activity:
                    adjusted_activity = activity.replace("户外", "室内")
                elif "开车" in activity:
                    adjusted_activity = activity.replace("开车", "在家")
            
            # 根据社交活动修正因子调整
            if social_modifier < 0.8:
                if "聚会" in activity:
                    adjusted_activity = activity.replace("聚会", "独处时光")
                elif "拜访" in activity:
                    adjusted_activity = activity.replace("拜访", "在家休息")
                elif "社交" in activity:
                    adjusted_activity = activity.replace("社交", "个人活动")
            
            # 根据心情修正因子调整
            if mood_modifier < -0.2:
                # 心情不好时，倾向于安静的活动
                if "派对" in activity:
                    adjusted_activity = activity.replace("派对", "安静地休息")
                elif "热闹" in activity:
                    adjusted_activity = activity.replace("热闹", "安静")
            
            adjusted_schedule.append(adjusted_activity)
        
        return adjusted_schedule

    def llm_available(self):
        if not self._llm:
            return False
        return self._llm.is_available()

    def image_model_available(self):
        if not self._image_model:
            return False
        return self._image_model.is_available()

    def generate_image(self, prompt, **kwargs):
        """生成图片"""
        if not self.image_model_available():
            self.logger.warning(f"{self.name} 图片生成模型不可用")
            return None
        
        try:
            self.logger.info(f"{self.name} 正在生成图片: {prompt}")
            result = self._image_model.generate_image(prompt, **kwargs)
            self.logger.info(f"{self.name} 图片生成成功: {result.get('url', 'N/A')}")
            return result
        except Exception as e:
            self.logger.error(f"{self.name} 图片生成失败: {e}")
            return None

    def describe_and_generate_image(self, scene_description=None):
        """根据当前场景描述生成图片"""
        if not self.image_model_available():
            return None
            
        if not scene_description:
            # 生成当前场景的描述
            current_event = self.get_event()
            location = "，".join(current_event.address)
            activity = self.scratch.currently
            scene_description = f"{self.name}在{location}{activity}"
        
        # 使用LLM优化图片描述
        if self.llm_available():
            try:
                prompt_data = self.scratch.prompt_generate_image_description(scene_description)
                response = self._llm_model.completion(prompt_data["prompt"])
                optimized_description = prompt_data["callback"](response)
                scene_description = optimized_description
            except Exception as e:
                self.logger.warning(f"{self.name} 优化图片描述失败: {e}")
        
        return self.generate_image(scene_description)

    def to_dict(self, with_action=True):
        info = {
            "status": self.status,
            "schedule": self.schedule.to_dict(),
            "associate": self.associate.to_dict(),
            "chats": self.chats,
            "currently": self.scratch.currently,
            "wallet": {"currency": self.wallet.currency.value, "balance": self.wallet.balance},
            "inventory": {
                "materials": {rt.value: amt for rt, amt in self.inventory.materials.items()},
                "items": {it.value: cnt for it, cnt in self.inventory.items.items()},
            },
        }
        if with_action:
            info.update({"action": self.action.to_dict()})
        return info
    
    # ==================== AI建造和经济决策功能 ====================
    
    def consider_building(self, terrain_engine, building_decision_engine, agent_coord=None):
        """
        考虑是否需要建造
        
        Args:
            terrain_engine: 地形引擎
            building_decision_engine: 建造决策引擎
            agent_coord: Agent当前坐标（可选）
        
        Returns:
            建造决策或None
        """
        if not hasattr(self, '_last_building_check'):
            self._last_building_check = 0
        
        current_time = utils.get_timer().daily_duration()
        
        # 每小时最多考虑一次建造
        if current_time - self._last_building_check < 60:
            return None
        
        self._last_building_check = current_time
        
        # 转换库存为ResourceType格式
        agent_resources = {}
        for resource_type, amount in self.inventory.materials.items():
            agent_resources[resource_type] = amount
        
        # 分析建造意图
        decision = building_decision_engine.analyze_agent_building_intention(
            agent_id=self.name,
            agent_resources=agent_resources,
            agent_money=self.wallet.balance,
            agent_coord=agent_coord
        )
        
        return decision
    
    def execute_building_decision(self, decision, terrain_engine, building_decision_engine):
        """
        执行建造决策
        
        Args:
            decision: 建造决策
            terrain_engine: 地形引擎
            building_decision_engine: 建造决策引擎
        
        Returns:
            执行结果
        """
        # 转换库存为ResourceType格式
        agent_resources = {}
        for resource_type, amount in self.inventory.materials.items():
            agent_resources[resource_type] = amount
        
        # 执行建造
        result = building_decision_engine.execute_building_decision(
            agent_id=self.name,
            decision=decision,
            consume_agent_resources=True,  # 从Agent资源扣除
            agent_resources=agent_resources
        )
        
        # 如果成功，更新Agent的库存
        if result.get("status") == "success":
            cost = decision.get("cost", {})
            for resource_type, amount in cost.items():
                if resource_type in self.inventory.materials:
                    self.inventory.materials[resource_type] -= amount
            
            self.logger.info(
                f"{self.name} 建造了 {decision['building_type'].value} "
                f"在位置 {decision['location']}，原因：{decision['reason']}"
            )
            
            # 添加到记忆
            event = memory.Event(
                self.name,
                "建造了",
                decision['building_type'].value,
                describe=f"{self.name} 建造了 {decision['building_type'].value}：{decision['reason']}",
                address=self.get_tile().get_address()
            )
            self._add_concept("event", event)
        
        return result
    
    def consider_economic_action(self, economy_engine, economy_behavior_engine, other_agents):
        """
        考虑经济行为
        
        Args:
            economy_engine: 经济引擎
            economy_behavior_engine: 经济行为引擎
            other_agents: 其他Agent列表
        
        Returns:
            经济行动或None
        """
        if not hasattr(self, '_last_economy_check'):
            self._last_economy_check = 0
        
        current_time = utils.get_timer().daily_duration()
        
        # 每30分钟最多考虑一次经济行为
        if current_time - self._last_economy_check < 30:
            return None
        
        self._last_economy_check = current_time
        
        # 分析经济机会
        opportunity = economy_behavior_engine.analyze_economic_opportunity(
            agent_id=self.name,
            inventory=self.inventory,
            wallet=self.wallet,
            other_agents=other_agents
        )
        
        return opportunity
    
    def execute_economic_action(self, action, economy_behavior_engine):
        """
        执行经济行动
        
        Args:
            action: 经济行动
            economy_behavior_engine: 经济行为引擎
        
        Returns:
            执行结果
        """
        result = economy_behavior_engine.execute_economic_action(
            agent_id=self.name,
            action=action
        )
        
        if result.get("status") == "success":
            action_type = action.get("behavior_type")
            reason = action.get("reason", "")
            
            self.logger.info(
                f"{self.name} 执行了经济行为 {action_type}：{reason}"
            )
            
            # 添加到记忆
            event = memory.Event(
                self.name,
                "进行了",
                action_type,
                describe=f"{self.name} {reason}",
                address=self.get_tile().get_address()
            )
            self._add_concept("event", event)
        
        return result
    
    def gather_resources_from_location(self, terrain_engine):
        """
        从当前位置采集资源
        
        Args:
            terrain_engine: 地形引擎
        
        Returns:
            采集到的资源
        """
        # 获取当前位置的地形瓦片
        tile_x = self.coord[0] // 32  # 假设每个瓦片32像素
        tile_y = self.coord[1] // 32
        
        tile = terrain_engine.get_tile(tile_x, tile_y)
        if not tile:
            return {}
        
        gathered = {}
        
        # 根据地形类型采集资源
        for resource_type, amount in tile.resources.items():
            if amount > 0:
                # 采集一小部分资源（1-5%）
                gather_amount = amount * random.uniform(0.01, 0.05)
                gathered[resource_type] = gather_amount
                
                # 添加到Agent的库存
                self.inventory.add_material(resource_type, gather_amount)
                
                # 从瓦片扣除
                tile.resources[resource_type] = max(0, amount - gather_amount)
        
        if gathered:
            self.logger.info(
                f"{self.name} 采集了资源：" + 
                ", ".join(f"{rt.value}: {amt:.1f}" for rt, amt in gathered.items())
            )
        
        return gathered
