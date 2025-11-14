#!/usr/bin/env python3
"""
角色生成器测试脚本
演示如何使用改进后的角色生成器从characters目录选择角色作为texture.png
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generative_agents'))

from modules.agent_generator import AgentGenerator


def test_list_available_characters():
    """测试1: 列出所有可用的角色图片"""
    print("=" * 60)
    print("测试1: 列出所有可用角色")
    print("=" * 60)
    
    generator = AgentGenerator()
    characters = generator.get_available_characters()
    
    if characters:
        print(f"✓ 发现 {len(characters)} 个可用角色图片:\n")
        
        # 按类型分组显示
        categories = {
            '学生': [],
            '职业人士': [],
            '老年人': [],
            '儿童': [],
            '骑士/战士': [],
            '示例角色': [],
            '其他': []
        }
        
        for char in characters:
            char_lower = char.lower()
            if 'student' in char_lower or '学生' in char:
                categories['学生'].append(char)
            elif 'suit' in char_lower or 'president' in char_lower or 'shop' in char_lower:
                categories['职业人士'].append(char)
            elif 'old' in char_lower or 'father' in char_lower:
                categories['老年人'].append(char)
            elif 'little' in char_lower or 'boy' in char_lower or 'girl' in char_lower:
                categories['儿童'].append(char)
            elif '骑' in char or 'armor' in char_lower or 'knight' in char_lower:
                categories['骑士/战士'].append(char)
            elif 'sample' in char_lower:
                categories['示例角色'].append(char)
            else:
                categories['其他'].append(char)
        
        for category, chars in categories.items():
            if chars:
                print(f"  【{category}】 ({len(chars)}个)")
                for char in chars[:5]:  # 每类只显示前5个
                    print(f"    - {char}")
                if len(chars) > 5:
                    print(f"    ... 还有 {len(chars) - 5} 个")
                print()
    else:
        print("✗ 没有找到可用角色")
    
    print()
    return characters


def test_smart_selection():
    """测试2: 智能选择功能"""
    print("=" * 60)
    print("测试2: 智能角色选择")
    print("=" * 60)
    
    generator = AgentGenerator()
    
    test_cases = [
        {
            "name": "张教授",
            "age": 55,
            "occupation": "大学教师",
            "personality": "严肃认真",
            "description": "一位资深的大学教授"
        },
        {
            "name": "小明",
            "age": 16,
            "occupation": "学生",
            "personality": "活泼开朗",
            "description": "一位高中学生"
        },
        {
            "name": "李经理",
            "age": 35,
            "occupation": "企业管理",
            "personality": "专业严谨",
            "description": "一位成功的企业经理"
        },
        {
            "name": "圣骑士亚瑟",
            "age": 28,
            "occupation": "骑士",
            "personality": "勇敢正义",
            "description": "一位英勇的圣骑士"
        }
    ]
    
    for i, config in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {config['name']}")
        print(f"  年龄: {config['age']}, 职业: {config['occupation']}")
        
        images = generator.generate_agent_images(config)
        
        if images.get('selected_image_name'):
            print(f"  ✓ 智能选择结果: {images['selected_image_name']}")
        else:
            print(f"  ✗ 选择失败")
    
    print()


def test_manual_selection():
    """测试3: 手动指定角色"""
    print("=" * 60)
    print("测试3: 手动指定角色")
    print("=" * 60)
    
    generator = AgentGenerator()
    
    # 用户手动选择角色
    config = {
        "name": "李店主",
        "age": 45,
        "occupation": "商店老板",
        "personality": "和蔼可亲"
    }
    
    user_input = {
        "selected_character": "shop_keeper.png"
    }
    
    print(f"\n角色: {config['name']}")
    print(f"用户指定角色图片: {user_input['selected_character']}")
    
    images = generator.generate_agent_images(config, user_input)
    
    if images.get('selected_image_name'):
        print(f"✓ 成功使用指定角色: {images['selected_image_name']}")
    else:
        print(f"✗ 选择失败")
    
    print()


def test_create_complete_agent():
    """测试4: 创建完整的角色（包括保存到文件夹）"""
    print("=" * 60)
    print("测试4: 创建完整角色")
    print("=" * 60)
    
    generator = AgentGenerator()
    
    # 角色配置
    config = {
        "name": "测试角色",
        "age": 30,
        "occupation": "软件工程师",
        "personality": "友善专业",
        "description": "一位经验丰富的软件工程师",
        "lifestyle": "早睡早起，注重健康",
        "daily_plan": "上午编程，下午开会，晚上学习",
        "interests": ["编程", "阅读", "运动"],
        "skills": ["Python", "JavaScript", "AI"],
        "relationships": "喜欢与同事合作",
        "goals": "成为技术专家",
        "background": "计算机科学毕业",
        "speech_style": "专业且友善",
        "values": "创新、学习、分享",
        "coord": [50, 50]
    }
    
    # 用户选择角色图片（或留空让系统智能选择）
    user_input = {
        # "selected_character": "suit_02.png"  # 可以指定，也可以注释掉让系统智能选择
    }
    
    print(f"\n正在创建角色: {config['name']}")
    
    # 生成角色图片选择
    images = generator.generate_agent_images(config, user_input)
    
    if images.get('selected_image_name'):
        print(f"✓ 选择角色图片: {images['selected_image_name']}")
        
        # 保存到文件夹
        try:
            # 指定保存路径（测试用）
            base_path = os.path.join(
                os.path.dirname(__file__),
                'generative_agents', 'frontend', 'static', 
                'assets', 'village', 'agents'
            )
            
            folder_path = generator.save_agent_to_folder(config, images, base_path)
            print(f"✓ 角色已保存到: {folder_path}")
            
            # 检查生成的文件
            expected_files = ['agent.json', 'texture.png']
            print("\n生成的文件:")
            for filename in expected_files:
                filepath = os.path.join(folder_path, filename)
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    print(f"  ✓ {filename} ({size} bytes)")
                else:
                    print(f"  ✗ {filename} (不存在)")
            
            # 验证没有生成portrait.png
            portrait_path = os.path.join(folder_path, 'portrait.png')
            if not os.path.exists(portrait_path):
                print(f"  ✓ portrait.png (正确地未生成)")
            else:
                print(f"  ⚠️  portrait.png (不应该生成但存在)")
            
        except Exception as e:
            print(f"✗ 保存失败: {e}")
    else:
        print(f"✗ 图片选择失败")
    
    print()


def interactive_character_selection():
    """交互式角色选择"""
    print("=" * 60)
    print("交互式角色创建")
    print("=" * 60)
    
    generator = AgentGenerator()
    characters = generator.get_available_characters()
    
    if not characters:
        print("没有可用的角色图片")
        return
    
    print(f"\n发现 {len(characters)} 个可用角色图片")
    print("\n请输入角色信息:")
    
    try:
        name = input("  角色名称: ").strip() or "默认角色"
        age = int(input("  年龄: ").strip() or "30")
        occupation = input("  职业: ").strip() or "普通人"
        personality = input("  性格: ").strip() or "友善"
        
        config = {
            "name": name,
            "age": age,
            "occupation": occupation,
            "personality": personality,
            "description": f"一位{age}岁的{occupation}",
            "coord": [50, 50]
        }
        
        print("\n是否要手动选择角色图片？")
        print("  1. 手动选择")
        print("  2. 智能选择（推荐）")
        
        choice = input("\n请选择 (1/2): ").strip()
        
        user_input = {}
        
        if choice == "1":
            # 显示可用角色
            print("\n可用角色图片:")
            for i, char in enumerate(characters, 1):
                print(f"  {i}. {char}")
                if i % 10 == 0 and i < len(characters):
                    more = input("\n按Enter继续，输入数字选择角色: ").strip()
                    if more:
                        try:
                            idx = int(more) - 1
                            if 0 <= idx < len(characters):
                                user_input["selected_character"] = characters[idx]
                                break
                        except:
                            pass
            
            if not user_input.get("selected_character"):
                char_num = input(f"\n请输入角色编号 (1-{len(characters)}): ").strip()
                try:
                    idx = int(char_num) - 1
                    if 0 <= idx < len(characters):
                        user_input["selected_character"] = characters[idx]
                except:
                    print("无效的选择，将使用智能选择")
        
        # 生成角色
        images = generator.generate_agent_images(config, user_input)
        
        if images.get('selected_image_name'):
            print(f"\n✓ 选择的角色图片: {images['selected_image_name']}")
            
            save = input("\n是否保存角色到文件夹？ (y/n): ").strip().lower()
            
            if save == 'y':
                base_path = os.path.join(
                    os.path.dirname(__file__),
                    'generative_agents', 'frontend', 'static',
                    'assets', 'village', 'agents'
                )
                
                folder_path = generator.save_agent_to_folder(config, images, base_path)
                print(f"\n✓ 角色已保存到: {folder_path}")
        else:
            print("\n✗ 角色选择失败")
    
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n错误: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("角色生成器测试")
    print("=" * 60 + "\n")
    
    # 运行所有测试
    characters = test_list_available_characters()
    
    if not characters:
        print("错误：没有找到可用的角色图片，请检查characters目录")
        return 1
    
    test_smart_selection()
    test_manual_selection()
    test_create_complete_agent()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    # 询问是否进入交互模式（仅在交互式环境中）
    import sys
    if sys.stdin.isatty():
        print("\n是否要进入交互式角色创建？ (y/n): ", end='')
        try:
            choice = input().strip().lower()
            if choice == 'y':
                interactive_character_selection()
        except (KeyboardInterrupt, EOFError):
            print("\n\n程序已退出")
    else:
        print("\n提示: 在交互式终端中运行可以使用交互式角色创建功能")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

