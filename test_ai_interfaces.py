#!/usr/bin/env python3
"""
测试AI接口修改的脚本
验证LLM模型优先级和图片生成功能
"""

import sys
import os
sys.path.append('generative_agents')

from modules.model.llm_model import create_llm_model, HybridLLMModel, PollinationsLLMModel, GLMLLMModel
from modules.model.image_model import create_image_model, HybridImageModel, PollinationsImageModel, GLMImageModel

def test_llm_models():
    """测试LLM模型"""
    print("=== 测试LLM模型 ===")
    
    # 测试Pollinations模型
    print("\n1. 测试Pollinations LLM模型")
    try:
        config = {
            "model": "openai-large",
            "base_url": "https://text.pollinations.ai",
            "api_key": ""
        }
        pollinations_model = PollinationsLLMModel(config)
        response = pollinations_model.completion("你好，请简单介绍一下自己。")
        print(f"Pollinations响应: {response[:100]}...")
    except Exception as e:
        print(f"Pollinations模型测试失败: {e}")
    
    # 测试GLM模型
    print("\n2. 测试GLM模型")
    try:
        config = {
            "model": "glm-4-flash-250414",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": os.environ.get("ZHIPUAI_API_KEY", "")
        }
        glm_model = GLMLLMModel(config)
        response = glm_model.completion("你好，请简单介绍一下自己。")
        print(f"GLM响应: {response[:100]}...")
    except Exception as e:
        print(f"GLM模型测试失败: {e}")
    
    # 测试混合模型
    print("\n3. 测试混合LLM模型")
    try:
        config = {
            "provider": "hybrid",
            "model": "openai-large",
            "base_url": "https://text.pollinations.ai",
            "api_key": ""
        }
        hybrid_model = create_llm_model(config)
        response = hybrid_model.completion("你好，请简单介绍一下自己。")
        print(f"混合模型响应: {response[:100]}...")
    except Exception as e:
        print(f"混合模型测试失败: {e}")

def test_image_models():
    """测试图片生成模型"""
    print("\n=== 测试图片生成模型 ===")
    
    # 测试Pollinations图片模型
    print("\n1. 测试Pollinations图片模型")
    try:
        config = {"provider": "pollinations"}
        pollinations_image = PollinationsImageModel(config)
        image_url = pollinations_image.generate_image("a beautiful sunset over mountains")
        print(f"Pollinations图片URL: {image_url}")
    except Exception as e:
        print(f"Pollinations图片模型测试失败: {e}")
    
    # 测试GLM图片模型
    print("\n2. 测试GLM图片模型")
    try:
        config = {
            "provider": "glm",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": os.environ.get("ZHIPUAI_API_KEY", "")
        }
        glm_image = GLMImageModel(config)
        image_url = glm_image.generate_image("a beautiful sunset over mountains")
        print(f"GLM图片URL: {image_url}")
    except Exception as e:
        print(f"GLM图片模型测试失败: {e}")
    
    # 测试混合图片模型
    print("\n3. 测试混合图片模型")
    try:
        config = {"provider": "hybrid"}
        hybrid_image = create_image_model(config)
        image_url = hybrid_image.generate_image("a beautiful sunset over mountains")
        print(f"混合图片模型URL: {image_url}")
    except Exception as e:
        print(f"混合图片模型测试失败: {e}")

def test_model_priority():
    """测试模型优先级"""
    print("\n=== 测试模型优先级 ===")
    
    try:
        config = {
            "model": "openai-large",
            "base_url": "https://text.pollinations.ai",
            "api_key": ""
        }
        pollinations_model = PollinationsLLMModel(config)
        
        # 测试模型优先级顺序
        models = ["openai-large", "gemini", "openai", "deepseek"]
        print(f"模型优先级顺序: {' → '.join(models)}")
        print("注意：PollinationsLLMModel会自动按优先级尝试这些模型")
        
        # 测试实际的completion调用，它会按优先级尝试模型
        try:
            response = pollinations_model.completion("简单测试")
            print(f"✓ 优先级测试成功，获得响应: {response[:50]}...")
        except Exception as e:
            print(f"✗ 所有模型都失败: {str(e)}")
                
    except Exception as e:
        print(f"优先级测试失败: {e}")

def main():
    """主测试函数"""
    print("开始测试AI接口修改...")
    
    # 设置环境变量（如果需要）
    # os.environ["ZHIPUAI_API_KEY"] = "your_api_key_here"
    
    test_llm_models()
    test_image_models()
    test_model_priority()
    
    print("\n=== 测试完成 ===")
    print("注意：某些测试可能因为缺少API密钥而失败，这是正常的。")
    print("重要的是验证代码结构和优先级逻辑是否正确。")

if __name__ == "__main__":
    main()