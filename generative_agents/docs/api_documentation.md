# AI社会模拟系统 API 文档

## 目录
1. [概述](#概述)
2. [认证和授权](#认证和授权)
3. [社会关系API](#社会关系api)
4. [恋爱系统API](#恋爱系统api)
5. [地形开发API](#地形开发api)
6. [决策系统API](#决策系统api)
7. [多AI交互API](#多ai交互api)
8. [机器学习API](#机器学习api)
9. [系统管理API](#系统管理api)
10. [错误处理](#错误处理)
11. [示例代码](#示例代码)

## 概述

AI社会模拟系统提供RESTful API接口，支持对社会关系、地形开发、AI决策等核心功能的完整操作。所有API返回JSON格式数据，支持标准HTTP状态码。

### 基础信息
- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **字符编码**: UTF-8
- **API版本**: v1.0

### 通用响应格式
```json
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "timestamp": "2024-12-19T10:30:00Z",
    "request_id": "req_123456789"
}
```

### 错误响应格式
```json
{
    "success": false,
    "error": {
        "code": "INVALID_PARAMETER",
        "message": "参数无效",
        "details": "agent_id不能为空"
    },
    "timestamp": "2024-12-19T10:30:00Z",
    "request_id": "req_123456789"
}
```

## 认证和授权

### API密钥认证
```http
Authorization: Bearer YOUR_API_KEY
```

### 获取API密钥
```http
POST /api/v1/auth/token
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**响应示例:**
```json
{
    "success": true,
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }
}
```

## 社会关系API

### 1. 添加关系

**接口地址:** `POST /api/v1/relationships`

**请求参数:**
```json
{
    "agent_a": "agent_001",
    "agent_b": "agent_002",
    "relationship_type": "FRIEND",
    "initial_intimacy": 30.0,
    "initial_trust": 25.0
}
```

**响应示例:**
```json
{
    "success": true,
    "data": {
        "relationship_id": "rel_123456",
        "agent_a": "agent_001",
        "agent_b": "agent_002",
        "relationship_type": "FRIEND",
        "intimacy": 30.0,
        "trust": 25.0,
        "compatibility": 65.0,
        "created_at": "2024-12-19T10:30:00Z"
    }
}
```

### 2. 获取关系信息

**接口地址:** `GET /api/v1/relationships/{agent_id}`

**路径参数:**
- `agent_id`: AI代理ID

**查询参数:**
- `relationship_type`: 关系类型过滤 (可选)
- `min_intimacy`: 最小亲密度过滤 (可选)
- `limit`: 返回数量限制 (默认20)
- `offset`: 偏移量 (默认0)

**响应示例:**
```json
{
    "success": true,
    "data": {
        "agent_id": "agent_001",
        "relationships": [
            {
                "relationship_id": "rel_123456",
                "other_agent": "agent_002",
                "relationship_type": "FRIEND",
                "intimacy": 75.5,
                "trust": 68.2,
                "compatibility": 82.1,
                "interaction_count": 45,
                "last_interaction": "2024-12-19T09:15:00Z"
            }
        ],
        "total_count": 1,
        "page_info": {
            "limit": 20,
            "offset": 0,
            "has_more": false
        }
    }
}
```

### 3. 更新关系

**接口地址:** `PUT /api/v1/relationships/{relationship_id}`

**请求参数:**
```json
{
    "intimacy_change": 5.0,
    "trust_change": 3.0,
    "interaction_type": "POSITIVE_CHAT",
    "event_description": "愉快的聊天"
}
```

### 4. 删除关系

**接口地址:** `DELETE /api/v1/relationships/{relationship_id}`

### 5. 获取社交网络

**接口地址:** `GET /api/v1/social/network/{agent_id}`

**查询参数:**
- `depth`: 网络深度 (默认2)
- `min_intimacy`: 最小亲密度阈值 (默认10)

**响应示例:**
```json
{
    "success": true,
    "data": {
        "center_agent": "agent_001",
        "network": {
            "nodes": [
                {
                    "agent_id": "agent_001",
                    "name": "Alice",
                    "level": 0
                },
                {
                    "agent_id": "agent_002", 
                    "name": "Bob",
                    "level": 1
                }
            ],
            "edges": [
                {
                    "from": "agent_001",
                    "to": "agent_002",
                    "relationship_type": "FRIEND",
                    "intimacy": 75.5,
                    "weight": 0.755
                }
            ]
        },
        "statistics": {
            "total_connections": 5,
            "average_intimacy": 62.3,
            "network_density": 0.4
        }
    }
}
```

### 6. 获取关系推荐

**接口地址:** `GET /api/v1/social/recommendations/{agent_id}`

**查询参数:**
- `recommendation_type`: 推荐类型 (FRIEND/ROMANTIC)
- `limit`: 推荐数量 (默认5)

## 恋爱系统API

### 1. 检查恋爱潜力

**接口地址:** `GET /api/v1/romance/potential`

**查询参数:**
- `agent_a`: 第一个AI代理ID
- `agent_b`: 第二个AI代理ID

**响应示例:**
```json
{
    "success": true,
    "data": {
        "agent_a": "agent_001",
        "agent_b": "agent_002",
        "compatibility_score": 78.5,
        "romance_potential": "HIGH",
        "factors": {
            "personality_match": 82.0,
            "interest_overlap": 75.0,
            "value_alignment": 79.0
        },
        "recommendation": "建议尝试发展恋爱关系"
    }
}
```

### 2. 发起恋爱关系

**接口地址:** `POST /api/v1/romance/initiate`

**请求参数:**
```json
{
    "initiator": "agent_001",
    "target": "agent_002",
    "approach_type": "CASUAL_CONVERSATION"
}
```

### 3. 规划约会

**接口地址:** `POST /api/v1/romance/date/plan`

**请求参数:**
```json
{
    "agent_a": "agent_001",
    "agent_b": "agent_002",
    "date_type": "ROMANTIC_DATE",
    "preferred_time": "evening",
    "budget": 100,
    "special_preferences": ["outdoor", "quiet"]
}
```

**响应示例:**
```json
{
    "success": true,
    "data": {
        "date_id": "date_789012",
        "date_plan": {
            "activity": "浪漫晚餐",
            "location": "湖边餐厅",
            "time": "19:00-21:30",
            "estimated_cost": 85,
            "success_probability": 0.82
        },
        "preparation_tasks": [
            "预订餐厅",
            "准备合适的服装",
            "选择话题"
        ]
    }
}
```

### 4. 执行约会

**接口地址:** `POST /api/v1/romance/date/execute`

**请求参数:**
```json
{
    "date_id": "date_789012",
    "execution_quality": 0.85,
    "special_events": ["surprise_gift", "romantic_moment"]
}
```

### 5. 尝试表白

**接口地址:** `POST /api/v1/romance/confess`

**请求参数:**
```json
{
    "confessor": "agent_001",
    "target": "agent_002",
    "confession_style": "ROMANTIC",
    "setting": "private_dinner"
}
```

### 6. 求婚

**接口地址:** `POST /api/v1/romance/propose`

**请求参数:**
```json
{
    "proposer": "agent_001",
    "target": "agent_002",
    "proposal_style": "TRADITIONAL",
    "location": "sunset_beach",
    "ring_value": 500
}
```

### 7. 举办婚礼

**接口地址:** `POST /api/v1/romance/wedding`

**请求参数:**
```json
{
    "bride": "agent_001",
    "groom": "agent_002",
    "wedding_style": "OUTDOOR",
    "guest_list": ["agent_003", "agent_004", "agent_005"],
    "budget": 2000,
    "special_features": ["live_music", "flower_arch"]
}
```

## 地形开发API

### 1. 获取地形信息

**接口地址:** `GET /api/v1/terrain/tile/{x}/{y}`

**路径参数:**
- `x`: X坐标
- `y`: Y坐标

**响应示例:**
```json
{
    "success": true,
    "data": {
        "coord": [10, 15],
        "terrain_type": "GRASSLAND",
        "elevation": 25,
        "resources": {
            "WATER": 80,
            "FOOD": 60,
            "WOOD": 20
        },
        "buildable": true,
        "building": null,
        "accessibility": 0.85,
        "environmental_factors": {
            "fertility": 0.75,
            "climate": 0.80,
            "safety": 0.90
        }
    }
}
```

### 2. 分析地形区域

**接口地址:** `GET /api/v1/terrain/analyze`

**查询参数:**
- `x_min`, `y_min`: 区域左下角坐标
- `x_max`, `y_max`: 区域右上角坐标
- `analysis_type`: 分析类型 (RESOURCES/BUILDABILITY/ACCESSIBILITY)

**响应示例:**
```json
{
    "success": true,
    "data": {
        "region": {
            "bounds": [[0, 0], [20, 20]],
            "total_tiles": 400
        },
        "terrain_distribution": {
            "GRASSLAND": 45.2,
            "FOREST": 30.1,
            "MOUNTAIN": 15.7,
            "WATER": 9.0
        },
        "resource_summary": {
            "total_water": 15420,
            "total_wood": 8930,
            "total_stone": 5670,
            "total_metal": 2340
        },
        "development_potential": {
            "buildable_tiles": 298,
            "optimal_locations": [
                {"coord": [10, 12], "score": 0.92},
                {"coord": [8, 15], "score": 0.89}
            ]
        }
    }
}
```

### 3. 规划建筑

**接口地址:** `POST /api/v1/buildings/plan`

**请求参数:**
```json
{
    "building_type": "HOUSE",
    "preferred_location": [10, 15],
    "owner_id": "agent_001",
    "size": "MEDIUM",
    "special_requirements": ["near_water", "good_view"]
}
```

**响应示例:**
```json
{
    "success": true,
    "data": {
        "plan_id": "plan_345678",
        "building_type": "HOUSE",
        "recommended_location": [10, 15],
        "alternative_locations": [
            {"coord": [9, 16], "score": 0.88},
            {"coord": [11, 14], "score": 0.85}
        ],
        "resource_requirements": {
            "WOOD": 50,
            "STONE": 30,
            "TOOLS": 10
        },
        "estimated_cost": 90,
        "construction_time": 5,
        "success_probability": 0.92
    }
}
```

### 4. 建造建筑

**接口地址:** `POST /api/v1/buildings/construct`

**请求参数:**
```json
{
    "plan_id": "plan_345678",
    "confirm_location": [10, 15],
    "construction_quality": 0.85,
    "rush_construction": false
}
```

### 5. 获取建筑列表

**接口地址:** `GET /api/v1/buildings`

**查询参数:**
- `owner_id`: 所有者ID过滤 (可选)
- `building_type`: 建筑类型过滤 (可选)
- `region`: 区域过滤 (格式: "x1,y1,x2,y2")
- `status`: 状态过滤 (PLANNING/CONSTRUCTION/COMPLETED)

### 6. 升级建筑

**接口地址:** `PUT /api/v1/buildings/{building_id}/upgrade`

**请求参数:**
```json
{
    "upgrade_type": "EXPAND_CAPACITY",
    "investment_level": "HIGH"
}
```

### 7. 创建开发项目

**接口地址:** `POST /api/v1/projects`

**请求参数:**
```json
{
    "project_name": "新区开发",
    "project_type": "SETTLEMENT_DEVELOPMENT",
    "target_region": [[0, 0], [10, 10]],
    "manager_id": "agent_001",
    "priority": "HIGH",
    "phases": [
        {
            "phase_name": "基础设施",
            "buildings": ["HOUSE", "FARM", "WORKSHOP"],
            "duration": 10
        }
    ]
}
```

### 8. 执行项目阶段

**接口地址:** `POST /api/v1/projects/{project_id}/execute`

**请求参数:**
```json
{
    "phase_index": 0,
    "resource_allocation": {
        "WOOD": 200,
        "STONE": 150,
        "TOOLS": 50
    },
    "worker_assignments": ["agent_002", "agent_003"]
}
```

## 决策系统API

### 1. 获取决策选项

**接口地址:** `GET /api/v1/decisions/options/{agent_id}`

**查询参数:**
- `context`: 决策上下文 (SOCIAL/SURVIVAL/DEVELOPMENT)
- `urgency`: 紧急程度 (LOW/MEDIUM/HIGH)

**响应示例:**
```json
{
    "success": true,
    "data": {
        "agent_id": "agent_001",
        "current_state": {
            "location": [10, 15],
            "resources": {"FOOD": 20, "WATER": 30},
            "satisfaction": 0.75,
            "active_goals": 3
        },
        "available_options": [
            {
                "option_id": "opt_001",
                "action_type": "SOCIAL_INTERACTION",
                "description": "与朋友聊天",
                "expected_outcome": {
                    "satisfaction_change": 0.1,
                    "relationship_impact": "POSITIVE"
                },
                "cost": {"TIME": 2},
                "success_probability": 0.85,
                "priority_score": 0.72
            },
            {
                "option_id": "opt_002", 
                "action_type": "RESOURCE_GATHERING",
                "description": "收集食物",
                "expected_outcome": {
                    "resource_gain": {"FOOD": 15},
                    "satisfaction_change": 0.05
                },
                "cost": {"TIME": 3, "ENERGY": 10},
                "success_probability": 0.90,
                "priority_score": 0.68
            }
        ],
        "recommendation": "opt_001"
    }
}
```

### 2. 做出决策

**接口地址:** `POST /api/v1/decisions/make`

**请求参数:**
```json
{
    "agent_id": "agent_001",
    "selected_option": "opt_001",
    "execution_parameters": {
        "target_agent": "agent_002",
        "interaction_style": "FRIENDLY",
        "duration": 2
    }
}
```

### 3. 设置目标

**接口地址:** `POST /api/v1/goals`

**请求参数:**
```json
{
    "agent_id": "agent_001",
    "goal_type": "SOCIAL",
    "description": "建立5个新朋友",
    "priority": "MEDIUM",
    "deadline": "2024-12-31T23:59:59Z",
    "success_criteria": {
        "friend_count": 5,
        "min_intimacy": 50.0
    }
}
```

### 4. 获取目标列表

**接口地址:** `GET /api/v1/goals/{agent_id}`

**查询参数:**
- `status`: 状态过滤 (ACTIVE/COMPLETED/FAILED)
- `goal_type`: 目标类型过滤
- `priority`: 优先级过滤

### 5. 更新目标进度

**接口地址:** `PUT /api/v1/goals/{goal_id}/progress`

**请求参数:**
```json
{
    "progress_update": {
        "friend_count": 3,
        "current_intimacy": 45.0
    },
    "status": "IN_PROGRESS",
    "notes": "已建立3个朋友关系，继续努力"
}
```

## 多AI交互API

### 1. 发送消息

**接口地址:** `POST /api/v1/interactions/message`

**请求参数:**
```json
{
    "sender_id": "agent_001",
    "receiver_id": "agent_002",
    "message_type": "CHAT",
    "content": "你好，今天天气真不错！",
    "context": {
        "location": [10, 15],
        "mood": "HAPPY",
        "topic": "WEATHER"
    }
}
```

### 2. 广播消息

**接口地址:** `POST /api/v1/interactions/broadcast`

**请求参数:**
```json
{
    "sender_id": "agent_001",
    "message_type": "ANNOUNCEMENT",
    "content": "我正在组织一个建设项目，欢迎大家参与！",
    "target_criteria": {
        "location_radius": 50,
        "relationship_types": ["FRIEND", "NEIGHBOR"],
        "min_skill_level": 3
    }
}
```

### 3. 创建协作项目

**接口地址:** `POST /api/v1/collaborations`

**请求参数:**
```json
{
    "project_name": "社区花园建设",
    "collaboration_type": "CONSTRUCTION",
    "initiator_id": "agent_001",
    "description": "在社区中心建设一个美丽的花园",
    "required_skills": ["GARDENING", "CONSTRUCTION"],
    "max_participants": 5,
    "duration": 7,
    "resource_pool": {
        "TOOLS": 20,
        "SEEDS": 50,
        "WATER": 100
    }
}
```

### 4. 加入协作项目

**接口地址:** `POST /api/v1/collaborations/{project_id}/join`

**请求参数:**
```json
{
    "agent_id": "agent_002",
    "contribution": {
        "skills": ["GARDENING"],
        "resources": {"TOOLS": 5, "WATER": 20},
        "time_commitment": 0.8
    },
    "motivation": "我喜欢园艺，希望为社区做贡献"
}
```

### 5. 获取交互历史

**接口地址:** `GET /api/v1/interactions/history/{agent_id}`

**查询参数:**
- `other_agent`: 对方代理ID (可选)
- `interaction_type`: 交互类型过滤
- `start_date`: 开始日期
- `end_date`: 结束日期
- `limit`: 返回数量限制

## 机器学习API

### 1. 预测AI行为

**接口地址:** `POST /api/v1/ml/predict/behavior`

**请求参数:**
```json
{
    "agent_id": "agent_001",
    "prediction_context": {
        "current_state": {
            "location": [10, 15],
            "resources": {"FOOD": 20, "WATER": 30},
            "satisfaction": 0.75
        },
        "available_actions": ["CHAT", "BUILD", "EXPLORE"],
        "time_horizon": 5
    }
}
```

**响应示例:**
```json
{
    "success": true,
    "data": {
        "agent_id": "agent_001",
        "predictions": [
            {
                "action": "CHAT",
                "probability": 0.65,
                "confidence": 0.82,
                "expected_outcome": {
                    "satisfaction_change": 0.1,
                    "social_impact": "POSITIVE"
                }
            },
            {
                "action": "BUILD",
                "probability": 0.25,
                "confidence": 0.75,
                "expected_outcome": {
                    "resource_change": {"WOOD": -20, "TOOLS": -5},
                    "long_term_benefit": 0.3
                }
            }
        ],
        "model_version": "v1.2.3",
        "prediction_timestamp": "2024-12-19T10:30:00Z"
    }
}
```

### 2. 获取关系推荐

**接口地址:** `POST /api/v1/ml/recommend/relationships`

**请求参数:**
```json
{
    "agent_id": "agent_001",
    "recommendation_type": "FRIENDSHIP",
    "candidate_agents": ["agent_002", "agent_003", "agent_004"],
    "context_factors": {
        "location_preference": "NEARBY",
        "personality_match": true,
        "skill_complementarity": true
    }
}
```

### 3. 优化建设布局

**接口地址:** `POST /api/v1/ml/optimize/development`

**请求参数:**
```json
{
    "optimization_type": "BUILDING_PLACEMENT",
    "region": [[0, 0], [20, 20]],
    "buildings": [
        {"type": "HOUSE", "count": 5},
        {"type": "FARM", "count": 2},
        {"type": "WORKSHOP", "count": 1}
    ],
    "constraints": {
        "min_distance_between_buildings": 2,
        "resource_accessibility": true,
        "environmental_impact": "MINIMAL"
    }
}
```

### 4. 更新学习模型

**接口地址:** `POST /api/v1/ml/model/update`

**请求参数:**
```json
{
    "model_type": "BEHAVIOR_PREDICTION",
    "training_data": {
        "new_interactions": 150,
        "feedback_samples": 45,
        "outcome_data": 120
    },
    "update_strategy": "INCREMENTAL"
}
```

## 系统管理API

### 1. 获取系统状态

**接口地址:** `GET /api/v1/system/status`

**响应示例:**
```json
{
    "success": true,
    "data": {
        "system_health": "HEALTHY",
        "uptime": "72h 15m 30s",
        "active_agents": 25,
        "active_relationships": 156,
        "ongoing_projects": 8,
        "resource_usage": {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 23.1
        },
        "performance_metrics": {
            "avg_response_time": 120,
            "requests_per_minute": 45,
            "error_rate": 0.02
        }
    }
}
```

### 2. 获取统计信息

**接口地址:** `GET /api/v1/system/statistics`

**查询参数:**
- `time_range`: 时间范围 (1h/24h/7d/30d)
- `metrics`: 指标类型 (relationships/buildings/interactions)

### 3. 导出数据

**接口地址:** `GET /api/v1/system/export`

**查询参数:**
- `data_type`: 数据类型 (relationships/terrain/agents/all)
- `format`: 导出格式 (json/csv/xml)
- `date_range`: 日期范围

### 4. 导入数据

**接口地址:** `POST /api/v1/system/import`

**请求参数:**
```json
{
    "data_type": "relationships",
    "format": "json",
    "data": "...",
    "merge_strategy": "UPDATE_EXISTING"
}
```

## 错误处理

### 错误代码列表

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| INVALID_PARAMETER | 400 | 请求参数无效 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

### 错误处理示例

```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/api/v1/relationships",
        headers={"Authorization": "Bearer YOUR_TOKEN"},
        json={
            "agent_a": "agent_001",
            "agent_b": "agent_002",
            "relationship_type": "FRIEND"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("关系创建成功:", data["data"])
    else:
        error = response.json()["error"]
        print(f"错误: {error['code']} - {error['message']}")
        
except requests.exceptions.RequestException as e:
    print(f"网络错误: {e}")
```

## 示例代码

### Python SDK示例

```python
from ai_social_sim import SocialSimulationClient

# 初始化客户端
client = SocialSimulationClient(
    base_url="http://localhost:8000/api/v1",
    api_key="your_api_key"
)

# 创建AI代理
agent1 = client.agents.create(
    name="Alice",
    personality={"openness": 0.8, "extraversion": 0.7}
)

agent2 = client.agents.create(
    name="Bob", 
    personality={"openness": 0.6, "extraversion": 0.5}
)

# 建立关系
relationship = client.relationships.add(
    agent_a=agent1.id,
    agent_b=agent2.id,
    relationship_type="FRIEND"
)

# 检查恋爱潜力
romance_potential = client.romance.check_potential(
    agent_a=agent1.id,
    agent_b=agent2.id
)

if romance_potential.score > 70:
    # 发起恋爱关系
    romance = client.romance.initiate(
        initiator=agent1.id,
        target=agent2.id
    )
    
    # 规划约会
    date_plan = client.romance.plan_date(
        agent_a=agent1.id,
        agent_b=agent2.id,
        date_type="ROMANTIC_DATE"
    )
    
    # 执行约会
    date_result = client.romance.execute_date(
        date_id=date_plan.date_id,
        execution_quality=0.85
    )

# 地形开发
terrain_analysis = client.terrain.analyze_region(
    x_min=0, y_min=0, x_max=20, y_max=20
)

# 规划建筑
building_plan = client.buildings.plan(
    building_type="HOUSE",
    preferred_location=[10, 15],
    owner_id=agent1.id
)

# 建造建筑
building = client.buildings.construct(
    plan_id=building_plan.plan_id,
    confirm_location=[10, 15]
)

# AI决策
decision_options = client.decisions.get_options(agent1.id)
best_option = max(decision_options, key=lambda x: x.priority_score)

decision_result = client.decisions.make(
    agent_id=agent1.id,
    selected_option=best_option.option_id
)

print(f"AI {agent1.name} 决定: {decision_result.action_description}")
```

### JavaScript SDK示例

```javascript
import { SocialSimulationClient } from 'ai-social-sim-js';

// 初始化客户端
const client = new SocialSimulationClient({
    baseURL: 'http://localhost:8000/api/v1',
    apiKey: 'your_api_key'
});

// 异步操作示例
async function simulateInteraction() {
    try {
        // 获取AI代理列表
        const agents = await client.agents.list();
        
        // 选择两个代理
        const agent1 = agents[0];
        const agent2 = agents[1];
        
        // 发送消息
        const message = await client.interactions.sendMessage({
            senderId: agent1.id,
            receiverId: agent2.id,
            messageType: 'CHAT',
            content: '你好，今天过得怎么样？'
        });
        
        // 获取AI行为预测
        const prediction = await client.ml.predictBehavior({
            agentId: agent2.id,
            predictionContext: {
                currentState: agent2.currentState,
                availableActions: ['CHAT', 'BUILD', 'EXPLORE']
            }
        });
        
        console.log('预测结果:', prediction.predictions);
        
        // 根据预测结果做出决策
        const decision = await client.decisions.make({
            agentId: agent2.id,
            selectedOption: prediction.predictions[0].action
        });
        
        console.log('AI决策:', decision);
        
    } catch (error) {
        console.error('操作失败:', error.message);
    }
}

// 运行模拟
simulateInteraction();
```

### cURL示例

```bash
# 获取API令牌
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 创建关系
curl -X POST http://localhost:8000/api/v1/relationships \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_a": "agent_001",
    "agent_b": "agent_002", 
    "relationship_type": "FRIEND",
    "initial_intimacy": 30.0
  }'

# 获取社交网络
curl -X GET "http://localhost:8000/api/v1/social/network/agent_001?depth=2" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 规划建筑
curl -X POST http://localhost:8000/api/v1/buildings/plan \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "building_type": "HOUSE",
    "preferred_location": [10, 15],
    "owner_id": "agent_001"
  }'

# 获取系统状态
curl -X GET http://localhost:8000/api/v1/system/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 版本更新

### v1.0 (当前版本)
- 基础社会关系管理
- 恋爱系统完整流程
- 地形开发和建筑系统
- AI决策和目标管理
- 多AI交互协作
- 机器学习算法集成

### 计划中的功能 (v1.1)
- 经济系统API
- 政治和治理API
- 文化和教育API
- 高级分析和报告API
- 实时事件流API
- WebSocket支持

---

*API文档版本: v1.0*  
*最后更新: 2024年12月*  
*技术支持: api-support@ai-social-sim.com*