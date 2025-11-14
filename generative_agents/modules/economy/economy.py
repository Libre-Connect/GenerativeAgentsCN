"""
经济与物品系统
提供：货币钱包、物品与材料库存、合成配方、交易引擎与事件记录
"""

from __future__ import annotations

import datetime
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from modules.terrain.terrain_development import ResourceType


class CurrencyType(Enum):
    COIN = "coin"


class ItemType(Enum):
    FOOD_PACK = "food_pack"       # 食物包（由 FOOD 打包）
    TOOL_AXE = "tool_axe"         # 斧头（WOOD + METAL）
    TOOL_PICKAXE = "tool_pickaxe" # 镐（WOOD + METAL）
    TOOL_HAMMER = "tool_hammer"   # 锤子（WOOD + METAL）
    MATERIAL_BRICK = "material_brick" # 砖（STONE 加工）


@dataclass
class Wallet:
    currency: CurrencyType = CurrencyType.COIN
    balance: float = 0.0

    def deposit(self, amount: float) -> None:
        self.balance = max(0.0, self.balance + max(0.0, float(amount)))

    def withdraw(self, amount: float) -> bool:
        amount = max(0.0, float(amount))
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False


@dataclass
class Inventory:
    materials: Dict[ResourceType, float] = field(default_factory=dict)
    items: Dict[ItemType, int] = field(default_factory=dict)

    def add_material(self, resource: ResourceType, amount: float) -> None:
        self.materials[resource] = self.materials.get(resource, 0.0) + max(0.0, float(amount))

    def remove_materials(self, reqs: Dict[ResourceType, float]) -> bool:
        # 检查
        for r, a in reqs.items():
            if self.materials.get(r, 0.0) < a:
                return False
        # 扣除
        for r, a in reqs.items():
            self.materials[r] = max(0.0, self.materials.get(r, 0.0) - a)
        return True

    def add_item(self, item: ItemType, count: int = 1) -> None:
        self.items[item] = self.items.get(item, 0) + max(0, int(count))

    def remove_item(self, item: ItemType, count: int = 1) -> bool:
        count = max(0, int(count))
        if self.items.get(item, 0) >= count:
            self.items[item] = self.items.get(item, 0) - count
            if self.items[item] <= 0:
                self.items.pop(item, None)
            return True
        return False


@dataclass
class CraftingRecipe:
    id: str
    inputs: Dict[ResourceType, float]
    output_item: ItemType
    output_count: int = 1
    station: Optional[str] = None  # 需要的设施，例如工坊


DEFAULT_RECIPES: Dict[str, CraftingRecipe] = {
    "food_pack": CraftingRecipe(
        id="food_pack",
        inputs={ResourceType.FOOD: 5.0},
        output_item=ItemType.FOOD_PACK,
        output_count=1,
        station=None,
    ),
    "brick": CraftingRecipe(
        id="brick",
        inputs={ResourceType.STONE: 10.0},
        output_item=ItemType.MATERIAL_BRICK,
        output_count=4,
        station="workshop",
    ),
    "tool_axe": CraftingRecipe(
        id="tool_axe",
        inputs={ResourceType.WOOD: 4.0, ResourceType.METAL: 6.0},
        output_item=ItemType.TOOL_AXE,
        output_count=1,
        station="workshop",
    ),
    "tool_pickaxe": CraftingRecipe(
        id="tool_pickaxe",
        inputs={ResourceType.WOOD: 4.0, ResourceType.METAL: 8.0},
        output_item=ItemType.TOOL_PICKAXE,
        output_count=1,
        station="workshop",
    ),
}


class EconomyEngine:
    """经济引擎：价格、交易、合成与事件"""
    def __init__(self):
        self.agent_inventories: Dict[str, Inventory] = {}
        self.agent_wallets: Dict[str, Wallet] = {}
        self.recipes: Dict[str, CraftingRecipe] = dict(DEFAULT_RECIPES)
        self.base_prices: Dict[str, float] = {
            # 资源基础价格（按单位）
            f"res:{ResourceType.WOOD.value}": 1.0,
            f"res:{ResourceType.STONE.value}": 1.2,
            f"res:{ResourceType.METAL.value}": 2.0,
            f"res:{ResourceType.WATER.value}": 0.5,
            f"res:{ResourceType.FOOD.value}": 1.5,
            f"res:{ResourceType.ENERGY.value}": 2.5,
            # 物品基础价格
            f"item:{ItemType.FOOD_PACK.value}": 9.0,
            f"item:{ItemType.MATERIAL_BRICK.value}": 6.0,
            f"item:{ItemType.TOOL_AXE.value}": 24.0,
            f"item:{ItemType.TOOL_PICKAXE.value}": 28.0,
        }
        self.dynamic_prices: Dict[str, float] = dict(self.base_prices)
        self.events: List[Dict[str, Any]] = []

    def register_agent(self, agent_id: str, starting_balance: float = 100.0) -> None:
        if agent_id not in self.agent_inventories:
            self.agent_inventories[agent_id] = Inventory()
        if agent_id not in self.agent_wallets:
            self.agent_wallets[agent_id] = Wallet(balance=starting_balance)

    def get_price(self, key: str) -> float:
        return float(self.dynamic_prices.get(key, self.base_prices.get(key, 1.0)))

    def update_prices(self, terrain_engine) -> None:
        """根据全球资源稀缺度动态调整价格"""
        scarcity: Dict[ResourceType, float] = {}
        total = 0.0
        for rt in ResourceType:
            amount = float(terrain_engine.global_resources.get(rt, 0.0))
            scarcity[rt] = max(0.1, 1_000.0 / (amount + 1.0))  # 简化：资源越少，稀缺系数越高
            total += amount
        # 更新资源价格
        for rt, s in scarcity.items():
            key = f"res:{rt.value}"
            base = self.base_prices.get(key, 1.0)
            self.dynamic_prices[key] = round(base * (0.6 + min(2.0, s)), 2)
        # 更新物品价格（按其所需材料的加权）
        for item_key, base in self.base_prices.items():
            if not item_key.startswith("item:"):
                continue
            item_name = item_key.split(":", 1)[1]
            # 找配方
            recipe = next((r for r in self.recipes.values() if r.output_item.value == item_name), None)
            if recipe:
                price = 0.0
                for rt, amt in recipe.inputs.items():
                    price += self.get_price(f"res:{rt.value}") * amt
                self.dynamic_prices[item_key] = round(max(base, price * 0.3), 2)

    def craft(self, agent_id: str, recipe_id: str) -> Dict[str, Any]:
        inv = self.agent_inventories.get(agent_id)
        if not inv:
            return {"status": "error", "message": "agent not registered"}
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return {"status": "error", "message": "recipe not found"}
        if not inv.remove_materials(recipe.inputs):
            return {"status": "error", "message": "insufficient materials"}
        inv.add_item(recipe.output_item, recipe.output_count)
        evt = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "type": "craft",
            "agent": agent_id,
            "recipe": recipe_id,
            "output": {"item": recipe.output_item.value, "count": recipe.output_count},
        }
        self._record_event(evt)
        return {"status": "success", "event": evt}

    def propose_trade(self,
                      sender: str,
                      receiver: str,
                      offer_resources: Optional[Dict[str, float]] = None,
                      request_resources: Optional[Dict[str, float]] = None,
                      offer_items: Optional[Dict[str, int]] = None,
                      request_items: Optional[Dict[str, int]] = None,
                      offer_money: float = 0.0,
                      request_money: float = 0.0) -> Dict[str, Any]:
        # 注册检查
        for aid in (sender, receiver):
            self.register_agent(aid)

        s_inv = self.agent_inventories[sender]
        r_inv = self.agent_inventories[receiver]
        s_wal = self.agent_wallets[sender]
        r_wal = self.agent_wallets[receiver]

        # 校验资金
        if offer_money > s_wal.balance:
            return {"status": "error", "message": "sender insufficient funds"}
        if request_money > r_wal.balance:
            return {"status": "error", "message": "receiver insufficient funds"}

        # 校验资源与物品
        def parse_res_map(raw: Optional[Dict[str, float]]) -> Dict[ResourceType, float]:
            res: Dict[ResourceType, float] = {}
            if raw:
                for k, v in raw.items():
                    try:
                        res[ResourceType(k)] = float(v)
                    except Exception:
                        pass
            return res

        def parse_item_map(raw: Optional[Dict[str, int]]) -> Dict[ItemType, int]:
            res: Dict[ItemType, int] = {}
            if raw:
                for k, v in raw.items():
                    try:
                        res[ItemType(k)] = int(v)
                    except Exception:
                        pass
            return res

        s_res = parse_res_map(offer_resources)
        r_res = parse_res_map(request_resources)
        s_items = parse_item_map(offer_items)
        r_items = parse_item_map(request_items)

        # 检查发出方拥有量
        for rt, a in s_res.items():
            if s_inv.materials.get(rt, 0.0) < a:
                return {"status": "error", "message": "sender lacks materials"}
        for it, c in s_items.items():
            if s_inv.items.get(it, 0) < c:
                return {"status": "error", "message": "sender lacks items"}
        for rt, a in r_res.items():
            if r_inv.materials.get(rt, 0.0) < a:
                return {"status": "error", "message": "receiver lacks materials"}
        for it, c in r_items.items():
            if r_inv.items.get(it, 0) < c:
                return {"status": "error", "message": "receiver lacks items"}

        # 执行转移
        for rt, a in s_res.items():
            s_inv.materials[rt] = s_inv.materials.get(rt, 0.0) - a
            r_inv.materials[rt] = r_inv.materials.get(rt, 0.0) + a
        for it, c in s_items.items():
            s_inv.items[it] = s_inv.items.get(it, 0) - c
            r_inv.items[it] = r_inv.items.get(it, 0) + c
        for rt, a in r_res.items():
            r_inv.materials[rt] = r_inv.materials.get(rt, 0.0) - a
            s_inv.materials[rt] = s_inv.materials.get(rt, 0.0) + a
        for it, c in r_items.items():
            r_inv.items[it] = r_inv.items.get(it, 0) - c
            s_inv.items[it] = s_inv.items.get(it, 0) + c

        # 资金流动
        if offer_money > 0:
            if not s_wal.withdraw(offer_money):
                return {"status": "error", "message": "sender withdraw failed"}
            r_wal.deposit(offer_money)
        if request_money > 0:
            if not r_wal.withdraw(request_money):
                return {"status": "error", "message": "receiver withdraw failed"}
            s_wal.deposit(request_money)

        evt = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "type": "trade",
            "sender": sender,
            "receiver": receiver,
            "offer_resources": {k.value: v for k, v in s_res.items()} or None,
            "request_resources": {k.value: v for k, v in r_res.items()} or None,
            "offer_items": {k.value: v for k, v in s_items.items()} or None,
            "request_items": {k.value: v for k, v in r_items.items()} or None,
            "offer_money": round(float(offer_money), 2),
            "request_money": round(float(request_money), 2),
        }
        self._record_event(evt)
        return {"status": "success", "event": evt}

    def auto_step(self, agent_ids: List[str], terrain_engine) -> Optional[Dict[str, Any]]:
        """简易自动交易/合成：随机配对，基于稀缺度进行交易或合成"""
        if not agent_ids:
            return None
        # 更新价格
        self.update_prices(terrain_engine)
        # 随机选择动作：70% 交易，30% 合成
        if random.random() < 0.3:
            # 随机选择一个代理合成食物包或砖
            aid = random.choice(agent_ids)
            recipe_id = random.choice(["food_pack", "brick"]) if random.random() < 0.6 else random.choice(list(self.recipes.keys()))
            return self.craft(aid, recipe_id)
        else:
            # 随机配对交易：偏向 FOOD/STONE/METAL
            a1, a2 = random.sample(agent_ids, k=2) if len(agent_ids) >= 2 else (agent_ids[0], agent_ids[0])
            scarce = sorted([(rt, terrain_engine.global_resources.get(rt, 0.0)) for rt in [ResourceType.FOOD, ResourceType.STONE, ResourceType.METAL]], key=lambda x: x[1])
            target_rt = scarce[0][0]
            # 报价：用钱购买 10 单位稀缺资源
            price = self.get_price(f"res:{target_rt.value}")
            offer_money = round(price * 10.0 * (0.8 + random.random()*0.4), 2)
            return self.propose_trade(
                sender=a1,
                receiver=a2,
                offer_resources=None,
                request_resources={target_rt.value: 10.0},
                offer_items=None,
                request_items=None,
                offer_money=offer_money,
                request_money=0.0,
            )

    def get_state(self) -> Dict[str, Any]:
        return {
            "prices": dict(self.dynamic_prices),
            "agents": {
                aid: {
                    "balance": wal.balance,
                    "materials": {rt.value: amt for rt, amt in inv.materials.items()},
                    "items": {it.value: cnt for it, cnt in inv.items.items()},
                }
                for aid, (inv, wal) in ((aid, (self.agent_inventories.get(aid, Inventory()), self.agent_wallets.get(aid, Wallet())) ) for aid in self.agent_inventories.keys())
            }
        }

    def get_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.events[-limit:] if self.events else []

    def _record_event(self, evt: Dict[str, Any]) -> None:
        self.events.append(evt)
        if len(self.events) > 400:
            self.events = self.events[-250:]