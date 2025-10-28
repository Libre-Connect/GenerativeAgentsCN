#!/usr/bin/env python3
"""
测试修改后的agent生成功能
"""

import requests
import json
import os

def test_agent_generation():
    """测试agent生成API"""
    
    # API端点
    url = "http://127.0.0.1:5000/api/generate_agent"
    
    # 测试数据
    test_data = {
        "name": "测试角色",
        "description": "一个用于测试的角色，性格开朗友善",
        "age": 25,
        "occupation": "学生"
    }
    
    print("正在测试agent生成功能...")
    print(f"请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送POST请求
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查返回的数据结构
            if result.get('success'):
                data = result.get('data', {})
                config = data.get('config', {})
                images = data.get('images', {})
                
                print(f"\n生成的角色名称: {config.get('name')}")
                print(f"角色年龄: {config.get('age')}")
                print(f"角色职业: {config.get('occupation')}")
                
                if 'selected_image_path' in images:
                    print(f"✅ 成功选择预设图片: {images['selected_image_path']}")
                    print(f"Web路径: {images.get('selected_image_web_path')}")
                else:
                    print("⚠️  未找到选择的图片路径")
                
                return True
            else:
                print(f"❌ API返回失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"错误内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_agent_saving():
    """测试agent保存到文件夹功能"""
    
    url = "http://127.0.0.1:5000/api/save_agent"
    
    # 首先生成一个agent
    generate_url = "http://127.0.0.1:5000/api/generate_agent"
    test_data = {
        "name": "保存测试角色",
        "description": "用于测试保存功能的角色",
        "age": 30,
        "occupation": "教师"
    }
    
    print("\n正在测试agent保存功能...")
    
    try:
        # 生成agent
        gen_response = requests.post(generate_url, json=test_data, timeout=30)
        if gen_response.status_code != 200:
            print("❌ 生成agent失败")
            return False
            
        gen_result = gen_response.json()
        if not gen_result.get('success'):
            print("❌ 生成agent API返回失败")
            return False
        
        # 保存agent
        save_data = gen_result['data']
        save_response = requests.post(url, json=save_data, timeout=30)
        
        print(f"保存响应状态码: {save_response.status_code}")
        
        if save_response.status_code == 200:
            save_result = save_response.json()
            print("✅ 保存请求成功!")
            print(f"保存结果: {json.dumps(save_result, ensure_ascii=False, indent=2)}")
            
            if save_result.get('success'):
                # 检查文件是否真的被创建
                agent_name = test_data['name'].replace(' ', '_')
                agent_folder = f"/Users/sunyuefeng/GenerativeAgentsCN-1/generative_agents/frontend/static/assets/village/agents/{agent_name}"
                
                files_to_check = [
                    os.path.join(agent_folder, 'agent.json'),
                    os.path.join(agent_folder, 'portrait.png'),
                    os.path.join(agent_folder, 'texture.png')
                ]
                
                print(f"\n检查文件是否创建在: {agent_folder}")
                all_files_exist = True
                for file_path in files_to_check:
                    if os.path.exists(file_path):
                        print(f"✅ {os.path.basename(file_path)} 存在")
                    else:
                        print(f"❌ {os.path.basename(file_path)} 不存在")
                        all_files_exist = False
                
                return all_files_exist
            else:
                print(f"❌ 保存失败: {save_result.get('message')}")
                return False
        else:
            print(f"❌ 保存HTTP错误: {save_response.status_code}")
            print(f"错误内容: {save_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 保存测试错误: {e}")
        return False

if __name__ == "__main__":
    print("开始测试修改后的agent生成功能")
    print("=" * 50)
    
    # 测试生成功能
    generation_success = test_agent_generation()
    
    # 测试保存功能
    saving_success = test_agent_saving()
    
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"Agent生成功能: {'✅ 通过' if generation_success else '❌ 失败'}")
    print(f"Agent保存功能: {'✅ 通过' if saving_success else '❌ 失败'}")
    
    if generation_success and saving_success:
        print("\n🎉 所有测试通过! 修改后的功能工作正常。")
    else:
        print("\n⚠️  部分测试失败，请检查日志。")