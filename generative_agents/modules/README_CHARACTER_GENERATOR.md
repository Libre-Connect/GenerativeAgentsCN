# AgentGenerator - 角色生成器

## 快速使用

### 基本用法

```python
from modules.agent_generator import AgentGenerator

# 创建生成器实例
generator = AgentGenerator()

# 1. 查看所有可用角色（63个）
characters = generator.get_available_characters()
print(f"可用角色: {len(characters)} 个")

# 2. 智能选择角色（推荐）
config = {
    "name": "张三",
    "age": 30,
    "occupation": "软件工程师",
    "personality": "友善专业",
    "description": "一位经验丰富的工程师",
    "coord": [50, 50]
}

images = generator.generate_agent_images(config)
# 系统会根据年龄、职业、性格自动选择最合适的角色图片

# 3. 保存角色（只生成texture.png，不生成portrait.png）
folder_path = generator.save_agent_to_folder(config, images)
print(f"角色已保存到: {folder_path}")
```

### 手动指定角色

```python
# 用户选择特定的角色图片
user_input = {
    "selected_character": "suit_02.png"
}

images = generator.generate_agent_images(config, user_input)
folder_path = generator.save_agent_to_folder(config, images)
```

## 生成的文件

```
agents/角色名称/
├── agent.json      # 角色配置
└── texture.png     # 96x128像素，从characters目录复制
```

**注意**: 不再生成 `portrait.png`

## 可用角色类型

- **学生系列**: student_01.png ~ student_09.png
- **职业人士**: suit_01.png ~ suit_05.png, president.png, shop_keeper.png
- **老年人**: oldman_01.png, oldman_02.png, oldwoman_01.png, oldwoman_02.png
- **儿童**: littleboy_01.png, littleboy_02.png, littlegirl_01.png, littlegirl_02.png
- **骑士/战士**: armor.png, 骑士A.png, 骑兵A.png 等
- **示例角色**: sample_character_01.png ~ sample_character_16.png

共63个角色可选！

## 智能匹配规则

系统会根据以下属性自动选择合适的角色：

- **年龄**: <18岁→学生/儿童, 18-50岁→职业人士, >50岁→老年人
- **职业**: 自动匹配相关职业图片
- **性格**: 匹配对应的表情风格
- **名字**: 精确匹配（如"骑士"会选择骑士图片）

## 完整文档

详细文档请查看：
- [使用指南](../../CHARACTER_GENERATOR_GUIDE.md)
- [实现报告](../../CHARACTER_GENERATOR_IMPLEMENTATION.md)
- [测试脚本](../../test_character_generator.py)

