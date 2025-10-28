"""generative_agents.model.llm_model"""

import time
import re
import requests
import json
import os
from urllib.parse import urlencode


class LLMModel:
    def __init__(self, config):
        self._api_key = config["api_key"]
        self._base_url = config["base_url"]
        self._model = config["model"]
        self._meta_responses = []
        self._summary = {"total": [0, 0, 0]}

        self._handle = self.setup(config)
        self._enabled = True

    def setup(self, config):
        raise NotImplementedError(
            "setup is not support for " + str(self.__class__)
        )

    def completion(
        self,
        prompt,
        retry=10,
        callback=None,
        failsafe=None,
        caller="llm_normal",
        **kwargs
    ):
        response, self._meta_responses = None, []
        self._summary.setdefault(caller, [0, 0, 0])
        for _ in range(retry):
            try:
                meta_response = self._completion(prompt, **kwargs).strip()
                self._meta_responses.append(meta_response)
                self._summary["total"][0] += 1
                self._summary[caller][0] += 1
                if callback:
                    response = callback(meta_response)
                else:
                    response = meta_response
            except Exception as e:
                print(f"LLMModel.completion() caused an error: {e}")
                time.sleep(5)
                response = None
                continue
            if response is not None:
                break
        pos = 2 if response is None else 1
        self._summary["total"][pos] += 1
        self._summary[caller][pos] += 1
        return response or failsafe

    def _completion(self, prompt, **kwargs):
        raise NotImplementedError(
            "_completion is not support for " + str(self.__class__)
        )

    def is_available(self):
        return self._enabled  # and self._summary["total"][2] <= 10

    def get_summary(self):
        des = {}
        for k, v in self._summary.items():
            des[k] = "S:{},F:{}/R:{}".format(v[1], v[2], v[0])
        return {"model": self._model, "summary": des}

    def disable(self):
        self._enabled = False

    @property
    def meta_responses(self):
        return self._meta_responses


class PollinationsLLMModel(LLMModel):
    def setup(self, config):
        self._pai_token = os.getenv('PAI_TOKEN', 'r5bQfseAxxaO7YNc')
        return None

    def _completion(self, prompt, temperature=0.5):
        # 按优先级尝试不同模型：openai-large → gemini → openai → deepseek
        models = ['openai-large', 'gemini', 'openai', 'deepseek']
        
        for model in models:
            try:
                messages = [{"role": "user", "content": prompt}]
                
                body = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 8192,
                    "temperature": temperature,
                    "stream": False,
                    "token": self._pai_token
                }
                
                response = requests.post(
                    url='https://text.pollinations.ai/openai',
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self._pai_token}'
                    },
                    json=body,
                    timeout=30
                )
                
                if response.ok:
                    result = response.json()
                    if result and 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        print(f"Pollinations {model} 成功响应")
                        return content
                else:
                    print(f"Pollinations {model} 失败: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"Pollinations {model} 异常: {e}")
                continue
        
        # 所有Pollinations模型都失败，抛出异常让上层处理
        raise Exception("所有Pollinations模型都失败")


class GLMLLMModel(LLMModel):
    def setup(self, config):
        self._zhipu_api_key = os.getenv('ZHIPUAI_API_KEY', 'c776b1833ad5e38df90756a57b1bcafc.Da0sFSNyQE2BMJEd')
        return None

    def _completion(self, prompt, temperature=0.5):
        messages = [{"role": "user", "content": prompt}]
        
        body = {
            "model": "glm-4-flash-250414",
            "messages": messages,
            "max_tokens": 8192,
            "temperature": temperature,
            "stream": False
        }
        
        response = requests.post(
            url='https://open.bigmodel.cn/api/paas/v4/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self._zhipu_api_key}'
            },
            json=body,
            timeout=30
        )
        
        if response.ok:
            result = response.json()
            if result and 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
        
        raise Exception(f"GLM API 失败: HTTP {response.status_code}")


class HybridLLMModel(LLMModel):
    """混合LLM模型，优先使用Pollinations，失败时降级到GLM"""
    
    def setup(self, config):
        self._pollinations = PollinationsLLMModel(config)
        self._glm = GLMLLMModel(config)
        return None
    
    def _completion(self, prompt, temperature=0.5):
        # 首先尝试Pollinations（按优先级：openai-large → gemini → openai → deepseek）
        try:
            return self._pollinations._completion(prompt, temperature)
        except Exception as e:
            print(f"Pollinations 服务失败，降级到 GLM: {e}")
            
            # 降级到GLM
            try:
                result = self._glm._completion(prompt, temperature)
                print("GLM 服务成功响应")
                return result
            except Exception as glm_error:
                print(f"GLM 服务也失败: {glm_error}")
                raise Exception("所有AI服务都失败了")


def create_llm_model(llm_config):
    """Create llm model"""

    if llm_config["provider"] == "pollinations":
        return PollinationsLLMModel(llm_config)
    elif llm_config["provider"] == "glm":
        return GLMLLMModel(llm_config)
    elif llm_config["provider"] == "hybrid":
        return HybridLLMModel(llm_config)
    else:
        raise NotImplementedError(
            "llm provider {} is not supported. Only 'pollinations', 'glm', and 'hybrid' are supported.".format(llm_config["provider"])
        )
    return None


def parse_llm_output(response, patterns, mode="match_last", ignore_empty=False):
    if isinstance(patterns, str):
        patterns = [patterns]
    rets = []
    for line in response.split("\n"):
        line = line.replace("**", "").strip()
        for pattern in patterns:
            if pattern:
                matchs = re.findall(pattern, line)
            else:
                matchs = [line]
            if len(matchs) >= 1:
                rets.append(matchs[0])
                break
    if not ignore_empty:
        assert rets, "Failed to match llm output"
    if mode == "match_first":
        return rets[0]
    if mode == "match_last":
        return rets[-1]
    if mode == "match_all":
        return rets
    return None
