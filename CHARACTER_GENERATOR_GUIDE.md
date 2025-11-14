# 角色生成器使用指南

## 概述

改进后的角色生成器能够从 `generative_agents/frontend/static/assets/characters` 目录中智能选择或手动指定角色图片，并生成标准的角色文件结构。

## 主要改进

### ✅ 新功能

1. **智能选择** - 根据角色属性（年龄、职业、性格）自动选择最合适的角色图片
2. **手动指定** - 支持用户指定特定的角色图片
3. **列出可用角色** - 可以查看所有64个可用的角色图片
4. **只生成texture.png** - 不再生成portrait.png，符合要求

### 📁 生成的文件结构

```
generative_agents/frontend/static/assets/village/agents/角色名称/
├── agent.json      # 角色配置文件
└── texture.png     # 角色纹理图片 (96x128像素)
```

**注意**：不再生成 `portrait.png` 文件！

## 使用方法

### 方法1: 智能选择（推荐）

系统会根据角色属性自动选择最合适的图片：

```python
from modules.agent_generator import AgentGenerator

generator = AgentGenerator()

# 配置角色信息
config = {
    "name": "张教授",
    "age": 55,
    "occupation": "大学教师",
    "personality": "严肃认真",
    "description": "一位资深的大学教授"
}

# 生成角色图片（智能选择）
images = generator.generate_agent_images(config)

# 保存角色
folder_path = generator.save_agent_to_folder(config, images)
```

### 方法2: 手动指定角色图片

```python
from modules.agent_generator import AgentGenerator

generator = AgentGenerator()

config = {
    "name": "李店主",
    "age": 45,
    "occupation": "商店老板"
}

# 用户输入（手动指定角色）
user_input = {
    "selected_character": "shop_keeper.png"  # 从characters目录中选择
}

# 生成角色图片（使用指定的图片）
images = generator.generate_agent_images(config, user_input)

# 保存角色
folder_path = generator.save_agent_to_folder(config, images)
```

### 方法3: 查看所有可用角色

```python
from modules.agent_generator import AgentGenerator

generator = AgentGenerator()

# 获取所有可用角色图片列表
characters = generator.get_available_characters()

print(f"发现 {len(characters)} 个可用角色:")
for char in characters:
    print(f"  - {char}")
```

## 智能选择规则

系统会根据以下属性自动匹配最合适的角色图片：

### 年龄匹配

| 年龄范围 | 推荐角色 |
|---------|---------|
| < 18岁 | student_, littleboy_, littlegirl_, sample_character_ |
| 18-50岁 | citizen_, suit_, father |
| > 50岁 | oldman_, oldwoman_, father, noble |

### 职业匹配

| 职业 | 推荐角色 |
|------|---------|
| 学生 | student_ |
| 教师 | noble, father, citizen_ |
| 商人 | suit_, president |
| 医生 | suit_, citizen_ |
| 艺术家 | sample_character_, heroine, hero_ |
| 商店老板 | shop_keeper, citizen_ |
| 战士 | armor, hero_, badboy |
| 骑士 | armor, 骑士, 骑兵 |
| 农民 | citizen_, father |
| 科学家/工程师 | suit_, sample_character_ |

### 性格匹配

| 性格 | 推荐角色 |
|------|---------|
| 友善 | citizen_, student_, sample_character_ |
| 严肃 | suit_, president, noble |
| 活泼 | student_, hero_, sample_character_ |
| 沉着 | oldman_, noble, father |

## 可用的角色图片（64个）

### 学生系列 (9个)
- student_01.png ~ student_09.png

### 职业人士 (5个)
- suit_01.png ~ suit_05.png
- president.png

### 老年人 (4个)
- oldman_01.png, oldman_02.png
- oldwoman_01.png, oldwoman_02.png

### 儿童 (4个)
- littleboy_01.png, littleboy_02.png
- littlegirl_01.png, littlegirl_02.png

### 英雄/战士 (3个)
- hero_01.png, heroine.png
- armor.png, badboy.png

### 示例角色 (16个)
- sample_character_01.png ~ sample_character_16.png

### 骑士/骑兵 (7个)
- 骑士A.png, 骑士2_.png
- 骑兵A.png, 骑兵B.png, 轻骑兵2_.png
- 游牧骑兵.png, 游牧骑兵1.png

### 其他角色 (16个)
- brother.png, father.png, father_friend.png, father_friend_wife.png, father_staff.png
- citizen_01.png, citizen_02.png, citizen_03.png
- chickenboy.png, noble.png, shop_keeper.png
- 牛仔1.png, 白马.png

## 测试脚本

运行测试脚本查看所有功能：

```bash
python test_character_generator.py
```

测试脚本包含：
1. ✅ 列出所有可用角色
2. ✅ 测试智能选择功能
3. ✅ 测试手动指定功能
4. ✅ 创建完整角色（保存到文件夹）
5. ✅ 交互式角色创建

## API参考

### AgentGenerator类

#### get_available_characters()
获取所有可用的角色图片列表。

**返回**: `List[str]` - 角色图片文件名列表

**示例**:
```python
characters = generator.get_available_characters()
# ['armor.png', 'badboy.png', 'citizen_01.png', ...]
```

#### generate_agent_images(config, user_input=None)
生成或选择角色图片。

**参数**:
- `config` (dict): 角色配置信息
  - `name` (str): 角色名称
  - `age` (int): 年龄
  - `occupation` (str): 职业
  - `personality` (str): 性格
- `user_input` (dict, optional): 用户输入
  - `selected_character` (str): 指定的角色图片文件名

**返回**: `dict`
```python
{
    'texture': '/static/assets/characters/xxx.png',
    'selected_image_path': '完整的文件路径',
    'selected_image_name': 'xxx.png',
    'available_characters': ['所有可用角色列表']
}
```

#### save_agent_to_folder(config, images, base_path=None)
保存角色到文件夹。

**参数**:
- `config` (dict): 角色配置
- `images` (dict): 图片信息（由generate_agent_images返回）
- `base_path` (str, optional): 保存路径，默认为agents目录

**返回**: `str` - 保存的文件夹路径

## 常见问题

### Q: 为什么不生成portrait.png？

A: 根据要求，新的角色生成器只生成 `texture.png`，不生成 `portrait.png`。这是为了简化文件结构，只保留必要的纹理文件。

### Q: 如何添加新的角色图片？

A: 只需将PNG图片文件放入 `generative_agents/frontend/static/assets/characters/` 目录即可，系统会自动识别。

### Q: 智能选择不准确怎么办？

A: 可以使用手动指定方式，在user_input中指定 `selected_character`。

### Q: texture.png的尺寸是多少？

A: 生成的 texture.png 固定为 96x128 像素。

### Q: 可以修改智能选择规则吗？

A: 可以，编辑 `agent_generator.py` 中的 `_smart_select_character` 方法，修改 `character_rules` 字典。

## 集成示例

### 在Web界面中使用

```python
# web_server.py 或其他后端代码

from modules.agent_generator import AgentGenerator

@app.route('/api/generate_agent', methods=['POST'])
def generate_agent():
    data = request.json
    
    generator = AgentGenerator()
    
    # 如果用户选择了角色图片
    user_input = {}
    if 'selected_character' in data:
        user_input['selected_character'] = data['selected_character']
    
    # 生成配置
    config = generator.generate_agent_config(data)
    
    # 选择角色图片
    images = generator.generate_agent_images(config, user_input)
    
    # 保存角色
    folder_path = generator.save_agent_to_folder(config, images)
    
    return jsonify({
        'success': True,
        'agent_name': config['name'],
        'folder_path': folder_path,
        'selected_character': images.get('selected_image_name')
    })

@app.route('/api/available_characters', methods=['GET'])
def get_available_characters():
    """返回所有可用的角色图片供前端选择"""
    generator = AgentGenerator()
    characters = generator.get_available_characters()
    
    return jsonify({
        'characters': characters,
        'count': len(characters)
    })
```

### 前端选择器示例

```javascript
// 获取可用角色列表
fetch('/api/available_characters')
    .then(res => res.json())
    .then(data => {
        const characters = data.characters;
        
        // 显示角色选择器
        const selector = document.getElementById('character-selector');
        characters.forEach(char => {
            const option = document.createElement('option');
            option.value = char;
            option.text = char;
            selector.appendChild(option);
        });
    });

// 创建角色时发送选择的角色
function createAgent() {
    const data = {
        name: document.getElementById('name').value,
        age: parseInt(document.getElementById('age').value),
        occupation: document.getElementById('occupation').value,
        personality: document.getElementById('personality').value,
        selected_character: document.getElementById('character-selector').value
    };
    
    fetch('/api/generate_agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        console.log('角色创建成功:', result);
    });
}
```

## 总结

改进后的角色生成器提供了：

✅ **64个预设角色** 可供选择  
✅ **智能匹配** 根据属性自动选择  
✅ **手动指定** 完全控制  
✅ **简化结构** 只生成texture.png  
✅ **完整API** 易于集成  

开始使用：

```bash
# 运行测试
python test_character_generator.py

# 查看所有可用角色
python -c "from modules.agent_generator import AgentGenerator; g=AgentGenerator(); print('\n'.join(g.get_available_characters()))"
```

🎉 现在可以轻松创建具有合适外观的角色了！

