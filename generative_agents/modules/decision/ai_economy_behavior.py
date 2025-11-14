"""
AI经济行为决策模块
让Agent能够智能地进行交易、合成、资源管理等经济活动
"""

import random
import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from modules.economy.economy import (
    EconomyEngine,
    ItemType,
    Inventory,
    Wallet,
    CraftingRecipe
)
from modules.terrain.terrain_development import ResourceType


class EconomicBehaviorType(Enum):
    """经济行为类型"""
    TRADE = "trade"           # 交易
    CRAFT = "craft"           # 合成
    GATHER = "gather"         # 采集资源
    SELL = "sell"             # 出售物品
    BUY = "buy"              # 购买物品
    SAVE = "save"            # 储蓄
    INVEST = "invest"        # 投资


class TradeStrategy(Enum):
    """交易策略"""
    AGGRESSIVE = "aggressive"   # 激进：追求利润最大化
    BALANCED = "balanced"       # 平衡：兼顾利润和关系
    COOPERATIVE = "cooperative" # 合作：优先考虑共同利益
    CONSERVATIVE = "conservative" # 保守：避免风险


class AIEconomyBehaviorEngine:
    """AI经济行为决策引擎"""
    
    def __init__(self, economy_engine: EconomyEngine):
        self.economy_engine = economy_engine
        self.agent_strategies: Dict[str, TradeStrategy] = {}
        self.agent_needs: Dict[str, Dict[ResourceType, float]] = {}
        self.trade_history: List[Dict[str, Any]] = []
    
    def register_agent(
        self, 
        agent_id: str, 
        strategy: TradeStrategy = TradeStrategy.BALANCED,
        initial_needs: Optional[Dict[ResourceType, float]] = None
    ):
        """注册Agent的经济行为策略"""
        self.agent_strategies[agent_id] = strategy
        
        if initial_needs is None:
            # 默认需求
            initial_needs = {
                ResourceType.FOOD: 20.0,
                ResourceType.WOOD: 10.0,
                ResourceType.STONE: 10.0,
            }
        self.agent_needs[agent_id] = initial_needs
        
        # 确保在经济引擎中注册
        self.economy_engine.register_agent(agent_id)
    
    def update_agent_needs(self, agent_id: str, inventory: Inventory):
        """更新Agent的需求（基于当前库存）"""
        needs = {}
        
        # 基本需求阈值
        thresholds = {
            ResourceType.FOOD: 30.0,
            ResourceType.WOOD: 20.0,
            ResourceType.STONE: 20.0,
            ResourceType.METAL: 15.0,
            ResourceType.WATER: 25.0,
            ResourceType.ENERGY: 20.0,
        }
        
        # 计算缺口
        for resource_type, threshold in thresholds.items():
            current_amount = inventory.materials.get(resource_type, 0)
            if current_amount < threshold:
                needs[resource_type] = threshold - current_amount
        
        self.agent_needs[agent_id] = needs
        return needs
    
    def analyze_economic_opportunity(
        self,
        agent_id: str,
        inventory: Inventory,
        wallet: Wallet,
        other_agents: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        分析经济机会
        返回建议的经济行动
        """
        # 更新需求
        self.update_agent_needs(agent_id, inventory)
        
        opportunities = []
        
        # 1. 检查是否需要交易
        trade_opp = self._analyze_trade_opportunity(
            agent_id, inventory, wallet, other_agents
        )
        if trade_opp:
            opportunities.append(trade_opp)
        
        # 2. 检查是否可以合成
        craft_opp = self._analyze_crafting_opportunity(agent_id, inventory)
        if craft_opp:
            opportunities.append(craft_opp)
        
        # 3. 检查是否应该出售多余物品
        sell_opp = self._analyze_selling_opportunity(agent_id, inventory, wallet)
        if sell_opp:
            opportunities.append(sell_opp)
        
        # 根据策略和收益选择最佳机会
        if not opportunities:
            return None
        
        return max(opportunities, key=lambda x: x.get("expected_benefit", 0))
    
    def _analyze_trade_opportunity(
        self,
        agent_id: str,
        inventory: Inventory,
        wallet: Wallet,
        other_agents: List[str]
    ) -> Optional[Dict[str, Any]]:
        """分析交易机会"""
        needs = self.agent_needs.get(agent_id, {})
        if not needs:
            return None
        
        # 找到最需要的资源
        most_needed = max(needs.items(), key=lambda x: x[1])
        needed_resource, needed_amount = most_needed
        
        # 检查是否有多余的资源可以交换
        surplus_resources = {}
        for resource_type, amount in inventory.materials.items():
            if resource_type not in needs:
                if amount > 10:  # 有超过10单位的资源
                    surplus_resources[resource_type] = amount
        
        if not surplus_resources and wallet.balance < 10:
            return None  # 既没有多余资源也没有钱
        
        # 选择交易对象
        if not other_agents:
            return None
        
        trade_partner = random.choice(other_agents)
        
        # 构建交易提议
        offer_resources = {}
        offer_money = 0.0
        
        # 策略决定交易方式
        strategy = self.agent_strategies.get(agent_id, TradeStrategy.BALANCED)
        
        if surplus_resources:
            # 用资源交换
            surplus_type = random.choice(list(surplus_resources.keys()))
            offer_amount = min(surplus_resources[surplus_type] * 0.3, 15)
            offer_resources[surplus_type.value] = offer_amount
        elif wallet.balance >= 10:
            # 用钱购买
            price = self.economy_engine.get_price(f"res:{needed_resource.value}")
            offer_money = price * min(needed_amount, 10)
            
            # 根据策略调整价格
            if strategy == TradeStrategy.AGGRESSIVE:
                offer_money *= 0.8  # 压价
            elif strategy == TradeStrategy.COOPERATIVE:
                offer_money *= 1.1  # 愿意多付
        
        request_amount = min(needed_amount, 10)
        
        return {
            "behavior_type": EconomicBehaviorType.TRADE,
            "action": "trade",
            "partner": trade_partner,
            "offer_resources": offer_resources or None,
            "request_resources": {needed_resource.value: request_amount},
            "offer_money": offer_money,
            "request_money": 0.0,
            "expected_benefit": needed_amount * 0.5,  # 满足需求的价值
            "reason": f"需要 {needed_resource.value} 资源"
        }
    
    def _analyze_crafting_opportunity(
        self,
        agent_id: str,
        inventory: Inventory
    ) -> Optional[Dict[str, Any]]:
        """分析合成机会"""
        # 检查可以合成的配方
        craftable_recipes = []
        
        for recipe_id, recipe in self.economy_engine.recipes.items():
            # 检查是否有足够材料
            can_craft = True
            for resource_type, amount in recipe.inputs.items():
                if inventory.materials.get(resource_type, 0) < amount:
                    can_craft = False
                    break
            
            if can_craft:
                craftable_recipes.append((recipe_id, recipe))
        
        if not craftable_recipes:
            return None
        
        # 选择最有价值的配方
        best_recipe = None
        best_value = 0
        
        for recipe_id, recipe in craftable_recipes:
            # 计算价值：产出价格 - 投入成本
            output_price = self.economy_engine.get_price(
                f"item:{recipe.output_item.value}"
            )
            input_cost = sum(
                self.economy_engine.get_price(f"res:{rt.value}") * amount
                for rt, amount in recipe.inputs.items()
            )
            
            value = (output_price * recipe.output_count) - input_cost
            
            if value > best_value:
                best_value = value
                best_recipe = (recipe_id, recipe)
        
        if not best_recipe:
            return None
        
        recipe_id, recipe = best_recipe
        
        return {
            "behavior_type": EconomicBehaviorType.CRAFT,
            "action": "craft",
            "recipe_id": recipe_id,
            "output_item": recipe.output_item.value,
            "output_count": recipe.output_count,
            "inputs": {rt.value: amount for rt, amount in recipe.inputs.items()},
            "expected_benefit": best_value,
            "reason": f"合成 {recipe.output_item.value} 可获利"
        }
    
    def _analyze_selling_opportunity(
        self,
        agent_id: str,
        inventory: Inventory,
        wallet: Wallet
    ) -> Optional[Dict[str, Any]]:
        """分析出售机会"""
        # 只在资金不足且有多余物品时出售
        if wallet.balance > 50:
            return None
        
        # 找到可以出售的物品
        sellable_items = []
        for item_type, count in inventory.items.items():
            if count > 0:
                price = self.economy_engine.get_price(f"item:{item_type.value}")
                sellable_items.append((item_type, count, price))
        
        if not sellable_items:
            return None
        
        # 选择价格最高的物品
        best_item = max(sellable_items, key=lambda x: x[2])
        item_type, count, price = best_item
        
        return {
            "behavior_type": EconomicBehaviorType.SELL,
            "action": "sell",
            "item_type": item_type.value,
            "count": min(count, 1),  # 一次只卖一个
            "expected_income": price,
            "expected_benefit": price * 0.8,  # 考虑折扣
            "reason": "需要资金"
        }
    
    def execute_economic_action(
        self,
        agent_id: str,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行经济行动"""
        behavior_type = EconomicBehaviorType(action.get("behavior_type"))
        
        if behavior_type == EconomicBehaviorType.TRADE:
            return self._execute_trade(agent_id, action)
        elif behavior_type == EconomicBehaviorType.CRAFT:
            return self._execute_craft(agent_id, action)
        elif behavior_type == EconomicBehaviorType.SELL:
            return self._execute_sell(agent_id, action)
        else:
            return {"status": "error", "message": "未知的行动类型"}
    
    def _execute_trade(self, agent_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """执行交易"""
        result = self.economy_engine.propose_trade(
            sender=agent_id,
            receiver=action["partner"],
            offer_resources=action.get("offer_resources"),
            request_resources=action.get("request_resources"),
            offer_items=action.get("offer_items"),
            request_items=action.get("request_items"),
            offer_money=action.get("offer_money", 0.0),
            request_money=action.get("request_money", 0.0)
        )
        
        # 记录交易历史
        if result.get("status") == "success":
            self.trade_history.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": agent_id,
                "action": "trade",
                "partner": action["partner"],
                "details": action
            })
        
        return result
    
    def _execute_craft(self, agent_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """执行合成"""
        result = self.economy_engine.craft(
            agent_id=agent_id,
            recipe_id=action["recipe_id"]
        )
        
        if result.get("status") == "success":
            self.trade_history.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": agent_id,
                "action": "craft",
                "recipe": action["recipe_id"],
                "output": action["output_item"]
            })
        
        return result
    
    def _execute_sell(self, agent_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """执行出售（简化版，实际应该找买家）"""
        # 这里简化为直接转换为货币
        inventory = self.economy_engine.agent_inventories.get(agent_id)
        wallet = self.economy_engine.agent_wallets.get(agent_id)
        
        if not inventory or not wallet:
            return {"status": "error", "message": "Agent未注册"}
        
        item_type = ItemType(action["item_type"])
        count = action["count"]
        
        if not inventory.remove_item(item_type, count):
            return {"status": "error", "message": "物品不足"}
        
        income = action["expected_income"] * count * 0.8  # 80%的价格
        wallet.deposit(income)
        
        return {
            "status": "success",
            "sold_item": item_type.value,
            "count": count,
            "income": income
        }
    
    def get_economic_advice(
        self,
        agent_id: str,
        inventory: Inventory,
        wallet: Wallet
    ) -> List[Dict[str, Any]]:
        """
        为Agent提供经济建议
        """
        advice = []
        
        # 更新需求
        needs = self.update_agent_needs(agent_id, inventory)
        
        # 资源需求建议
        if needs:
            advice.append({
                "type": "resource_shortage",
                "priority": "high",
                "message": f"资源短缺：需要 {', '.join(rt.value for rt in needs.keys())}",
                "suggested_action": "交易或采集"
            })
        
        # 资金建议
        if wallet.balance < 20:
            advice.append({
                "type": "low_funds",
                "priority": "medium",
                "message": "资金不足，建议出售多余物品或资源",
                "suggested_action": "出售物品"
            })
        
        # 合成建议
        for recipe_id, recipe in self.economy_engine.recipes.items():
            can_craft = all(
                inventory.materials.get(rt, 0) >= amount
                for rt, amount in recipe.inputs.items()
            )
            if can_craft:
                advice.append({
                    "type": "crafting_opportunity",
                    "priority": "low",
                    "message": f"可以合成 {recipe.output_item.value}",
                    "suggested_action": f"合成 {recipe_id}"
                })
        
        return advice
    
    def simulate_market_dynamics(self, agent_ids: List[str]):
        """
        模拟市场动态
        让多个Agent之间产生自然的经济互动
        """
        if len(agent_ids) < 2:
            return
        
        # 随机选择几个Agent进行经济活动
        active_agents = random.sample(
            agent_ids, 
            min(len(agent_ids), random.randint(2, 5))
        )
        
        for agent_id in active_agents:
            inventory = self.economy_engine.agent_inventories.get(agent_id)
            wallet = self.economy_engine.agent_wallets.get(agent_id)
            
            if not inventory or not wallet:
                continue
            
            # 分析机会
            other_agents = [a for a in agent_ids if a != agent_id]
            opportunity = self.analyze_economic_opportunity(
                agent_id, inventory, wallet, other_agents
            )
            
            if opportunity and random.random() < 0.3:  # 30%概率执行
                self.execute_economic_action(agent_id, opportunity)
    
    def get_economy_statistics(self) -> Dict[str, Any]:
        """获取经济统计信息"""
        total_wealth = 0
        total_resources = {rt: 0.0 for rt in ResourceType}
        agent_count = len(self.economy_engine.agent_wallets)
        
        for agent_id, wallet in self.economy_engine.agent_wallets.items():
            total_wealth += wallet.balance
            
            inventory = self.economy_engine.agent_inventories.get(agent_id)
            if inventory:
                for resource_type, amount in inventory.materials.items():
                    total_resources[resource_type] += amount
        
        avg_wealth = total_wealth / max(1, agent_count)
        
        return {
            "total_wealth": total_wealth,
            "average_wealth": avg_wealth,
            "agent_count": agent_count,
            "total_resources": {rt.value: amount for rt, amount in total_resources.items()},
            "trade_count": len(self.trade_history),
            "recent_trades": self.trade_history[-10:] if self.trade_history else []
        }

