"""generative_agents.model.image_model"""

import requests
import os
import json
from urllib.parse import urlencode


class ImageModel:
    """图片生成模型基类"""
    
    def __init__(self, config):
        self._config = config
        self._enabled = True
        self.setup(config)
    
    def setup(self, config):
        """子类需要实现的设置方法"""
        raise NotImplementedError("setup is not support for " + str(self.__class__))
    
    def generate_image(self, prompt, **kwargs):
        """生成图片"""
        raise NotImplementedError("generate_image is not support for " + str(self.__class__))
    
    def is_available(self):
        return self._enabled


class PollinationsImageModel(ImageModel):
    """Pollinations图片生成模型"""
    
    def setup(self, config):
        self._pai_token = os.getenv('PAI_TOKEN', 'r5bQfseAxxaO7YNc')
    
    def generate_image(self, prompt, width=1024, height=1024, model='flux', **kwargs):
        """使用Pollinations生成图片"""
        try:
            params = {
                'token': self._pai_token,
                'model': model,
                'width': str(width),
                'height': str(height),
                'nologo': 'true'
            }
            
            # 添加其他可选参数
            if 'enhance' in kwargs:
                params['enhance'] = 'true' if kwargs['enhance'] else 'false'
            if 'seed' in kwargs:
                params['seed'] = str(kwargs['seed'])
            
            url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?{urlencode(params)}"
            
            response = requests.get(url, timeout=60)
            
            if response.ok:
                print(f"Pollinations 图片生成成功: {url}")
                return {
                    'success': True,
                    'url': response.url,
                    'provider': 'pollinations'
                }
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Pollinations 图片生成失败: {e}")
            raise e


class GLMImageModel(ImageModel):
    """GLM图片生成模型"""
    
    def setup(self, config):
        self._zhipu_api_key = os.getenv('ZHIPUAI_API_KEY', 'c776b1833ad5e38df90756a57b1bcafc.Da0sFSNyQE2BMJEd')
    
    def generate_image(self, prompt, size='1024x1024', model='cogview-3-flash', **kwargs):
        """使用GLM生成图片"""
        try:
            body = {
                'model': model,
                'prompt': prompt,
                'size': size
            }
            
            # 添加其他可选参数
            if 'quality' in kwargs:
                body['quality'] = kwargs['quality']
            
            response = requests.post(
                url='https://open.bigmodel.cn/api/paas/v4/images/generations',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self._zhipu_api_key}'
                },
                json=body,
                timeout=60
            )
            
            if response.ok:
                result = response.json()
                if result and 'data' in result and len(result['data']) > 0:
                    image_url = result['data'][0]['url']
                    print(f"GLM 图片生成成功")
                    return {
                        'success': True,
                        'url': image_url,
                        'provider': 'glm'
                    }
                else:
                    raise Exception("GLM 返回数据格式错误")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"GLM 图片生成失败: {e}")
            raise e


class HybridImageModel(ImageModel):
    """混合图片生成模型，优先使用Pollinations，失败时降级到GLM"""
    
    def setup(self, config):
        self._pollinations = PollinationsImageModel(config)
        self._glm = GLMImageModel(config)
    
    def generate_image(self, prompt, **kwargs):
        """生成图片，优先使用Pollinations，失败时降级到GLM"""
        
        # 首先尝试Pollinations
        try:
            return self._pollinations.generate_image(prompt, **kwargs)
        except Exception as e:
            print(f"Pollinations 图片生成失败，降级到 GLM: {e}")
            
            # 降级到GLM
            try:
                # 转换参数格式
                glm_kwargs = {}
                if 'width' in kwargs and 'height' in kwargs:
                    glm_kwargs['size'] = f"{kwargs['width']}x{kwargs['height']}"
                if 'quality' in kwargs:
                    glm_kwargs['quality'] = kwargs['quality']
                
                result = self._glm.generate_image(prompt, **glm_kwargs)
                print("GLM 图片生成成功响应")
                return result
            except Exception as glm_error:
                print(f"GLM 图片生成也失败: {glm_error}")
                raise Exception("所有图片生成服务都失败了")


def create_image_model(config=None):
    """创建图片生成模型"""
    if config is None:
        config = {}
    
    provider = config.get('provider', 'hybrid')
    
    if provider == 'pollinations':
        return PollinationsImageModel(config)
    elif provider == 'glm':
        return GLMImageModel(config)
    elif provider == 'hybrid':
        return HybridImageModel(config)
    else:
        raise NotImplementedError(f"图片生成提供商 {provider} 不支持")