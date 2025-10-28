#!/usr/bin/env python3
"""
AI接口使用示例
展示如何使用修改后的AI接口功能
"""

import sys
import os
sys.path.append('generative_agents')

from modules.model.llm_model import create_llm_model
from modules.model.image_model import create_image_model

def example_llm_usage():
    """LLM使用示例"""
    print("=== LLM使用示例 ===")
    
    # 使用混合LLM模型（优先级：openai-large → gemini → openai → deepseek，失败时降级到GLM）
    config = {
        "provider": "hybrid",
        "model": "openai-large",
        "base_url": "https://text.pollinations.ai",
        "api_key": ""
    }
    
    llm_model = create_llm_model(config)
    
    # 测试对话
    questions = [
        "你好，请简单介绍一下自己",
        "请用一句话描述人工智能的未来",
        "如果你是一个游戏角色，你会是什么样的？"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n问题 {i}: {question}")
        try:
            response = llm_model.completion(question)
            print(f"回答: {response[:100]}...")
        except Exception as e:
            print(f"回答失败: {e}")

def example_image_generation():
    """图片生成使用示例"""
    print("\n=== 图片生成使用示例 ===")
    
    # 使用混合图片模型（优先Pollinations，失败时降级到GLM）
    config = {"provider": "hybrid"}
    image_model = create_image_model(config)
    
    # 测试图片生成
    prompts = [
        "一个美丽的日落风景",
        "一只可爱的小猫在花园里玩耍",
        "未来城市的科幻场景"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n图片 {i}: {prompt}")
        try:
            result = image_model.generate_image(prompt)
            if result.get('success'):
                print(f"✓ 生成成功")
                print(f"  提供商: {result.get('provider')}")
                print(f"  URL: {result.get('url')}")
            else:
                print(f"✗ 生成失败: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"✗ 生成异常: {e}")

def example_agent_integration():
    """Agent集成示例（模拟）"""
    print("\n=== Agent集成示例 ===")
    
    print("在实际的Agent中，你可以这样使用：")
    print("""
# 在agent.py中
class Agent:
    def __init__(self, config, maze, conversation, logger):
        # ... 其他初始化代码 ...
        
        # LLM模型会自动使用混合模式
        self._llm_model = create_llm_model(config.get("agent", {}).get("llm", {}))
        
        # 图片模型也会自动使用混合模式
        self._image_model = create_image_model(config.get("agent", {}).get("image", {}))
    
    def generate_scene_image(self, scene_description):
        '''根据场景描述生成图片'''
        if self.image_model_available():
            # 使用LLM优化描述
            optimized_prompt = self.describe_and_generate_image(scene_description)
            return optimized_prompt
        return None
    
    def chat_with_image(self, other_agent, topic):
        '''带图片的对话'''
        # 正常对话
        chat_response = self.chat_with(other_agent, topic)
        
        # 如果对话涉及场景，生成相关图片
        if "场景" in topic or "环境" in topic:
            scene_image = self.generate_scene_image(f"{self.name}和{other_agent.name}在讨论{topic}")
            return {
                "chat": chat_response,
                "image": scene_image
            }
        return {"chat": chat_response}
""")

def main():
    """主函数"""
    print("AI接口使用示例")
    print("=" * 50)
    
    # 设置环境变量（如果需要）
    # os.environ["ZHIPUAI_API_KEY"] = "your_api_key_here"
    
    example_llm_usage()
    example_image_generation()
    example_agent_integration()
    
    print("\n" + "=" * 50)
    print("示例完成！")
    print("\n主要特性：")
    print("✓ LLM优先级：openai-large → gemini → openai → deepseek")
    print("✓ Pollinations失败时自动降级到GLM服务")
    print("✓ 图片生成：Pollinations优先，GLM备用")
    print("✓ Agent集成：支持场景图片生成和LLM优化描述")

if __name__ == "__main__":
    main()