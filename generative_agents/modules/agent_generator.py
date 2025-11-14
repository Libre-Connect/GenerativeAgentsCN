import os
import json
import requests
import random
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import urllib.parse


class AgentGenerator:
    """AI角色生成器"""
    
    def __init__(self):
        # API配置
        self.pai_token = os.getenv('PAI_TOKEN', 'r5bQfseAxxaO7YNc')
        self.zhipu_api_key = os.getenv('ZHIPUAI_API_KEY', 'c776b1833ad5e38df90756a57b1bcafc.Da0sFSNyQE2BMJEd')
        
        # API端点
        self.pollinations_text_url = 'https://text.pollinations.ai/openai'
        self.pollinations_image_url = 'https://image.pollinations.ai/prompt'
        
        # 默认坐标范围（基于现有agent配置）
        self.coord_ranges = {
            'x': (10, 90),
            'y': (10, 90)
        }
        
    def generate_agent_config(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据用户输入生成完整的agent配置文件
        
        Args:
            user_input: 用户输入的角色信息
            
        Returns:
            生成的agent配置字典
        """
        # 构建AI提示词
        prompt = self._build_agent_prompt(user_input)
        
        # 调用AI生成配置
        ai_response = self._call_ai_api(prompt)
        
        # 解析AI响应并构建完整配置
        config = self._parse_ai_response(ai_response, user_input)
        
        return config
    
    def get_available_characters(self):
        """获取所有可用的角色图片列表"""
        try:
            characters_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'frontend', 'static', 'assets', 'characters'
            )
            
            if not os.path.exists(characters_dir):
                print(f"警告：角色图片目录不存在: {characters_dir}")
                return []
            
            # 获取所有PNG图片，排除xcf文件
            available_images = []
            for filename in sorted(os.listdir(characters_dir)):
                if filename.lower().endswith('.png') and not filename.startswith('.'):
                    available_images.append(filename)
            
            return available_images
            
        except Exception as e:
            print(f"获取可用角色列表时出错: {e}")
            return []
    
    def generate_agent_images(self, config, user_input=None):
        """处理角色形象选择 - 只生成texture.png"""
        try:
            name = config.get('name', 'Character')
            
            # 获取预设角色图片目录
            characters_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'frontend', 'static', 'assets', 'characters'
            )
            
            # 获取所有可用的角色图片
            available_images = self.get_available_characters()
            
            if not available_images:
                print(f"警告：在 {characters_dir} 中没有找到角色图片")
                return {'texture': None, 'available_characters': []}
            
            print(f"发现 {len(available_images)} 个可用角色图片")
            
            # 选择角色图片
            selected_character = None
            
            if user_input and user_input.get('selected_character'):
                # 用户明确选择了角色
                selected_character = user_input['selected_character']
                
                # 验证选择的角色是否存在
                if selected_character not in available_images:
                    print(f"警告：用户选择的角色 '{selected_character}' 不存在，将随机选择")
                    selected_character = random.choice(available_images)
                else:
                    print(f"✓ 用户为角色 '{name}' 选择了形象: {selected_character}")
            else:
                # 智能选择：根据角色属性推荐合适的图片
                selected_character = self._smart_select_character(config, available_images)
                print(f"✓ 为角色 '{name}' 智能选择了形象: {selected_character}")
            
            # 构建完整路径
            selected_image_path = os.path.join(characters_dir, selected_character)
            
            # 验证文件存在
            if not os.path.exists(selected_image_path):
                print(f"错误：选择的角色图片不存在: {selected_image_path}")
                # 回退到第一个可用图片
                selected_character = available_images[0]
                selected_image_path = os.path.join(characters_dir, selected_character)
            
            # 返回结果
            images = {
                'texture': f'/static/assets/characters/{selected_character}',
                'selected_image_path': selected_image_path,
                'selected_image_name': selected_character,
                'available_characters': available_images  # 返回所有可用角色供前端选择
            }
            
            return images
            
        except Exception as e:
            print(f"选择角色图片时发生错误: {e}")
            return {'texture': None, 'available_characters': []}
    
    def _smart_select_character(self, config, available_images):
        """根据角色属性智能选择合适的角色图片"""
        try:
            age = config.get('age', 25)
            occupation = config.get('occupation', '').lower()
            personality = config.get('personality', '').lower()
            name = config.get('name', '').lower()
            
            # 定义角色图片与属性的匹配规则
            character_rules = {
                # 年龄相关
                'young': ['student_', 'littleboy_', 'littlegirl_', 'sample_character_'],
                'old': ['oldman_', 'oldwoman_', 'father', 'noble'],
                'middle': ['citizen_', 'suit_', 'father'],
                
                # 职业相关
                'student': ['student_'],
                'teacher': ['noble', 'father', 'citizen_'],
                'business': ['suit_', 'president'],
                'doctor': ['suit_', 'citizen_'],
                'artist': ['sample_character_', 'heroine', 'hero_'],
                'merchant': ['shop_keeper', 'citizen_'],
                'warrior': ['armor', 'hero_', 'badboy'],
                'knight': ['armor', '骑士', '骑兵'],
                'farmer': ['citizen_', 'father'],
                'scientist': ['suit_', 'sample_character_'],
                'engineer': ['suit_', 'sample_character_'],
                
                # 性格相关
                'friendly': ['citizen_', 'student_', 'sample_character_'],
                'serious': ['suit_', 'president', 'noble'],
                'energetic': ['student_', 'hero_', 'sample_character_'],
                'calm': ['oldman_', 'noble', 'father'],
                
                # 特殊角色
                'leader': ['president', 'noble', 'suit_'],
                'hero': ['hero_', 'armor', 'heroine']
            }
            
            # 计算每个图片的匹配分数
            scores = {}
            for image in available_images:
                score = 0
                image_lower = image.lower()
                
                # 年龄匹配
                if age < 18:
                    for pattern in character_rules.get('young', []):
                        if pattern in image_lower:
                            score += 3
                elif age > 50:
                    for pattern in character_rules.get('old', []):
                        if pattern in image_lower:
                            score += 3
                else:
                    for pattern in character_rules.get('middle', []):
                        if pattern in image_lower:
                            score += 2
                
                # 职业匹配
                for job_key, patterns in character_rules.items():
                    if job_key in occupation:
                        for pattern in patterns:
                            if pattern in image_lower:
                                score += 5
                
                # 性格匹配
                for trait_key, patterns in character_rules.items():
                    if trait_key in personality:
                        for pattern in patterns:
                            if pattern in image_lower:
                                score += 2
                
                # 名字匹配（精确匹配中文）
                if '骑士' in name or 'knight' in name:
                    if '骑士' in image or 'knight' in image_lower:
                        score += 10
                if '骑兵' in name or 'cavalry' in name:
                    if '骑兵' in image or 'cavalry' in image_lower:
                        score += 10
                
                scores[image] = score
            
            # 如果有高分图片，从高分中随机选择
            max_score = max(scores.values())
            if max_score > 0:
                high_score_images = [img for img, score in scores.items() if score >= max_score * 0.8]
                return random.choice(high_score_images)
            
            # 没有匹配的，随机选择
            return random.choice(available_images)
            
        except Exception as e:
            print(f"智能选择角色时出错: {e}")
            return random.choice(available_images)
    
    def _build_agent_prompt(self, user_input: Dict[str, Any]) -> str:
        """构建AI生成agent配置的提示词"""
        name = user_input.get('name', '')
        description = user_input.get('description', '')
        age = user_input.get('age', '')
        occupation = user_input.get('occupation', '')
        personality = user_input.get('personality', '')
        
        prompt = f"""请根据以下信息生成一个AI角色的详细配置。请以JSON格式返回，包含以下字段：

用户输入信息：
- 姓名：{name}
- 描述：{description}
- 年龄：{age if age else '请推测合适的年龄'}
- 职业：{occupation if occupation else '请根据描述推测职业'}
- 性格：{personality if personality else '请根据描述推测性格特点'}

请生成包含以下字段的JSON配置：
{{
    "name": "角色姓名",
    "age": 年龄数字,
    "occupation": "职业",
    "personality": "性格特点描述",
    "description": "详细的角色描述（100-200字）",
    "lifestyle": "生活方式描述",
    "daily_plan": "日常计划描述",
    "interests": ["兴趣1", "兴趣2", "兴趣3"],
    "skills": ["技能1", "技能2", "技能3"],
    "relationships": "社交关系倾向",
    "goals": "人生目标",
    "background": "背景故事",
    "speech_style": "说话风格",
    "values": "价值观"
}}

请确保生成的内容符合中文语境，角色设定合理且有趣。只返回JSON格式的内容，不要包含其他文字。"""
        
        return prompt
    
    def _build_portrait_prompt(self, name: str, age: int, occupation: str, personality: str, description: str) -> str:
        """构建头像图片生成提示词"""
        prompt = f"Portrait of {name}, {age} years old {occupation}, {personality} personality, "
        prompt += f"professional headshot, clean background, high quality, realistic style, "
        prompt += f"friendly expression, looking at camera"
        
        return prompt
    
    def _build_image_prompt(self, name: str, age: int, occupation: str, personality: str, description: str) -> str:
        """构建全身图片生成提示词"""
        prompt = f"Full body illustration of {name}, {age} years old {occupation}, {personality} personality, "
        prompt += f"standing pose, professional attire, clean background, high quality, "
        prompt += f"cartoon style, friendly appearance"
        
        return prompt
    
    def _call_ai_api(self, prompt: str) -> str:
        """调用AI API生成文本"""
        try:
            # 使用Pollinations API
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.pai_token}'
            }
            
            data = {
                'model': 'openai',
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'system': '你是一个专业的AI角色设计师，擅长创建有趣且合理的虚拟角色。',
                'max_tokens': 2048,
                'stream': False
            }
            
            response = requests.post(self.pollinations_text_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"AI API调用失败: {e}")
            # 返回默认配置
            return self._get_fallback_config()
    
    def _extract_occupation_from_learned(self, learned: str) -> str:
        """从learned字段中提取职业信息"""
        if not learned:
            return "person"
        
        # 常见职业关键词映射
        occupation_keywords = {
            '店主': 'merchant',
            '商店': 'merchant', 
            '药店': 'pharmacist',
            '市场': 'merchant',
            '农民': 'farmer',
            '农场': 'farmer',
            '医生': 'doctor',
            '护士': 'nurse',
            '老师': 'teacher',
            '学生': 'student',
            '警察': 'guard',
            '保安': 'guard',
            '厨师': 'cook',
            '餐厅': 'cook',
            '铁匠': 'blacksmith',
            '工匠': 'craftsman',
            '学者': 'scholar',
            '图书': 'librarian',
            '艺术家': 'artist',
            '音乐': 'musician'
        }
        
        learned_lower = learned.lower()
        for keyword, occupation in occupation_keywords.items():
            if keyword in learned_lower:
                return occupation
        
        return "person"  # 默认职业

    def _build_appearance_description_with_user_input(self, name: str, age: int, occupation: str, personality: str, description: str, user_appearance: str) -> str:
        """构建包含用户输入外貌特征的详细描述"""
        try:
            appearance_parts = []
            
            # 优先使用用户输入的外貌特征
            if user_appearance:
                appearance_parts.append(user_appearance)
            
            # 根据年龄确定外表
            if age < 18:
                appearance_parts.append("young person")
            elif age < 30:
                appearance_parts.append("young adult")
            elif age < 50:
                appearance_parts.append("middle-aged person")
            else:
                appearance_parts.append("elderly person")
            
            # 根据职业添加特征（如果用户没有详细描述）
            if not user_appearance or len(user_appearance.strip()) < 10:
                occupation_features = {
                    'farmer': 'wearing simple clothes, sun-tanned skin',
                    'merchant': 'well-dressed, friendly appearance',
                    'guard': 'strong build, armor or uniform',
                    'scholar': 'glasses, neat appearance, books',
                    'blacksmith': 'muscular build, work clothes',
                    'cook': 'apron, chef hat, friendly smile',
                    'doctor': 'white coat, stethoscope, caring expression',
                    'teacher': 'professional attire, kind expression',
                    'student': 'casual clothes, backpack, youthful',
                    'artist': 'creative style, paint-stained clothes',
                    'musician': 'instrument, artistic appearance'
                }
                
                if occupation.lower() in occupation_features:
                    appearance_parts.append(occupation_features[occupation.lower()])
            
            # 根据性格添加表情特征
            if personality:
                personality_lower = personality.lower()
                if any(word in personality_lower for word in ['friendly', '友好', 'kind', '善良']):
                    appearance_parts.append("warm smile, kind eyes")
                elif any(word in personality_lower for word in ['serious', '严肃', 'stern', '严厉']):
                    appearance_parts.append("serious expression, focused gaze")
                elif any(word in personality_lower for word in ['cheerful', '开朗', 'happy', '快乐']):
                    appearance_parts.append("bright smile, cheerful demeanor")
            
            return ", ".join(appearance_parts)
            
        except Exception as e:
            print(f"Error building appearance description: {e}")
            return f"{name}, person"

    def _build_appearance_description(self, name: str, age: int, occupation: str, personality: str, description: str) -> str:
        """构建详细的角色外表特征描述"""
        try:
            # 基础外表特征
            appearance_parts = []
            
            # 根据年龄确定外表
            if age < 18:
                appearance_parts.append("young person")
            elif age < 30:
                appearance_parts.append("young adult")
            elif age < 50:
                appearance_parts.append("middle-aged person")
            else:
                appearance_parts.append("elderly person")
            
            # 根据职业添加特征
            occupation_features = {
                'farmer': 'wearing simple clothes, sun-tanned skin',
                'merchant': 'well-dressed, friendly appearance',
                'guard': 'strong build, armor or uniform',
                'scholar': 'glasses, neat appearance, books',
                'blacksmith': 'muscular build, work clothes',
                'cook': 'apron, chef hat, friendly smile',
                'doctor': 'white coat, stethoscope, caring expression',
                'teacher': 'professional attire, kind eyes',
                'artist': 'creative clothing, paint stains, expressive',
                'warrior': 'battle-worn, strong physique, scars'
            }
            
            if occupation.lower() in occupation_features:
                appearance_parts.append(occupation_features[occupation.lower()])
            else:
                appearance_parts.append(f"{occupation} attire")
            
            # 根据性格添加表情特征
            personality_features = {
                'friendly': 'warm smile, kind eyes',
                'serious': 'stern expression, focused gaze',
                'cheerful': 'bright smile, happy expression',
                'mysterious': 'hooded, shadowy features',
                'wise': 'thoughtful expression, gentle eyes',
                'brave': 'confident posture, determined look',
                'shy': 'modest appearance, gentle features',
                'energetic': 'dynamic pose, lively expression'
            }
            
            for trait in personality_features:
                if trait in personality.lower():
                    appearance_parts.append(personality_features[trait])
                    break
            else:
                appearance_parts.append('neutral expression')
            
            # 如果有描述，提取关键外表信息
            if description:
                # 简化描述，提取关键词
                desc_lower = description.lower()
                if 'hair' in desc_lower or '头发' in description:
                    if 'black' in desc_lower or '黑' in description:
                        appearance_parts.append('black hair')
                    elif 'brown' in desc_lower or '棕' in description:
                        appearance_parts.append('brown hair')
                    elif 'blonde' in desc_lower or '金' in description:
                        appearance_parts.append('blonde hair')
                
                if 'tall' in desc_lower or '高' in description:
                    appearance_parts.append('tall')
                elif 'short' in desc_lower or '矮' in description:
                    appearance_parts.append('short')
            
            return ', '.join(appearance_parts)
            
        except Exception as e:
            print(f"构建外表描述时出错: {e}")
            return f"{age} years old {occupation}"
    
    def _call_pollinations_image_api(self, prompt: str, model: str = "gptimage", width: int = 512, height: int = 512, image_url: str = None) -> str:
        """
        调用Pollinations图片生成API
        
        Args:
            prompt: 图片生成提示词
            model: 使用的模型 (gptimage 或 kontext)
            width: 图片宽度
            height: 图片高度
            image_url: 参考图片URL（可选）
            
        Returns:
            生成的图片URL
        """
        try:
            import urllib.parse
            import requests
            import time
            
            # 简化提示词，避免过长导致API错误
            if len(prompt) > 200:
                # 截取前200个字符并确保完整性
                prompt = prompt[:200].rsplit(' ', 1)[0] if ' ' in prompt[:200] else prompt[:200]
            
            # URL编码提示词
            encoded_prompt = urllib.parse.quote(prompt)
            
            # 构建完整URL - 使用传入的尺寸参数
            base_params = f"width={width}&height={height}&nologo=true"
            
            # 如果有参考图片，添加image参数
            if image_url:
                base_params += f"&image={urllib.parse.quote(image_url)}"
            
            if model == "gptimage":
                api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{base_params}"
            elif model == "kontext":
                # kontext模型需要使用token验证
                api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=kontext&token={self.pai_token}&{base_params}"
            else:
                # 默认使用基础API
                api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{base_params}"
            
            print(f"正在生成图片: {api_url}")
            
            # 直接返回URL，不进行验证（因为图片生成需要时间）
            return api_url
            
        except Exception as e:
            print(f"调用Pollinations API失败: {e}")
            return None
            raise
    
    def _parse_ai_response(self, ai_response: str, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI响应并构建完整配置"""
        try:
            # 尝试解析JSON
            if '{' in ai_response and '}' in ai_response:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                json_str = ai_response[json_start:json_end]
                ai_config = json.loads(json_str)
            else:
                raise ValueError("无法找到有效的JSON格式")
                
        except Exception as e:
            print(f"解析AI响应失败: {e}")
            # 使用默认配置
            ai_config = self._get_default_ai_config(user_input)
        
        # 生成随机坐标
        coord = self._generate_random_coord()
        
        # 构建完整的agent配置
        config = {
            "name": ai_config.get('name', user_input.get('name', '未知角色')),
            "age": ai_config.get('age', user_input.get('age', 25)),
            "occupation": ai_config.get('occupation', user_input.get('occupation', '普通人')),
            "personality": ai_config.get('personality', user_input.get('personality', '友善')),
            "description": ai_config.get('description', user_input.get('description', '一个有趣的角色')),
            "lifestyle": ai_config.get('lifestyle', '规律的生活方式'),
            "daily_plan": ai_config.get('daily_plan', '早起工作，晚上休息'),
            "interests": ai_config.get('interests', ['阅读', '音乐', '运动']),
            "skills": ai_config.get('skills', ['沟通', '学习', '适应']),
            "relationships": ai_config.get('relationships', '喜欢结交朋友'),
            "goals": ai_config.get('goals', '过上充实的生活'),
            "background": ai_config.get('background', '普通的成长背景'),
            "speech_style": ai_config.get('speech_style', '友善而礼貌'),
            "values": ai_config.get('values', '诚实、善良、努力'),
            "coord": coord,
            "created_at": datetime.now().isoformat()
        }
        
        return config
    
    def _generate_random_coord(self) -> Tuple[int, int]:
        """生成随机坐标"""
        x = random.randint(self.coord_ranges['x'][0], self.coord_ranges['x'][1])
        y = random.randint(self.coord_ranges['y'][0], self.coord_ranges['y'][1])
        return [x, y]
    
    def _get_fallback_config(self) -> str:
        """获取备用配置（当AI API失败时使用）"""
        return json.dumps({
            "name": "默认角色",
            "age": 25,
            "occupation": "普通人",
            "personality": "友善开朗",
            "description": "一个友善的角色，喜欢与人交流",
            "lifestyle": "规律的生活方式",
            "daily_plan": "早起工作，晚上休息",
            "interests": ["阅读", "音乐", "运动"],
            "skills": ["沟通", "学习", "适应"],
            "relationships": "喜欢结交朋友",
            "goals": "过上充实的生活",
            "background": "普通的成长背景",
            "speech_style": "友善而礼貌",
            "values": "诚实、善良、努力"
        })
    
    def _get_default_ai_config(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认AI配置"""
        return {
            "name": user_input.get('name', '默认角色'),
            "age": user_input.get('age', 25),
            "occupation": user_input.get('occupation', '普通人'),
            "personality": user_input.get('personality', '友善开朗'),
            "description": user_input.get('description', '一个友善的角色'),
            "lifestyle": "规律的生活方式",
            "daily_plan": "早起工作，晚上休息",
            "interests": ["阅读", "音乐", "运动"],
            "skills": ["沟通", "学习", "适应"],
            "relationships": "喜欢结交朋友",
            "goals": "过上充实的生活",
            "background": "普通的成长背景",
            "speech_style": "友善而礼貌",
            "values": "诚实、善良、努力"
        }
    
    def save_agent_to_folder(self, config: Dict[str, Any], images: Dict[str, str], base_path: str = None) -> str:
        """
        将生成的角色配置和图片保存到文件夹
        
        Args:
            config: 角色配置字典
            images: 图片URL字典
            base_path: 基础保存路径，默认为agents目录
            
        Returns:
            保存的文件夹路径
        """
        try:
            import time
            
            # 如果没有指定base_path，使用默认的agents目录
            if base_path is None:
                base_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),  # generative_agents目录
                    'frontend', 'static', 'assets', 'village', 'agents'
                )
            
            # 创建角色文件夹
            agent_name = config.get('name', f'agent_{int(time.time())}')
            # 清理文件夹名称，移除特殊字符
            safe_name = "".join(c for c in agent_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_name:
                safe_name = f'agent_{int(time.time())}'
            
            folder_path = os.path.join(base_path, safe_name)
            os.makedirs(folder_path, exist_ok=True)
            
            # 添加创建时间到配置
            config['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            config['folder_name'] = safe_name
            
            # 保存配置文件
            config_path = os.path.join(folder_path, 'agent.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"Configuration saved to: {config_path}")
            
            # 复制并保存图片（只生成texture.png，不生成portrait.png）
            if images.get('selected_image_path'):
                # 从预设角色图片中复制
                try:
                    selected_image_path = images['selected_image_path']
                    
                    # 只复制为texture.png（96x128像素）
                    texture_path = os.path.join(folder_path, 'texture.png')
                    self._copy_and_resize_image(selected_image_path, texture_path, (96, 128))
                    print(f"✓ Texture复制成功: {texture_path}")
                    print(f"  源文件: {images.get('selected_image_name')}")
                    
                except Exception as e:
                    print(f"✗ 复制角色图片失败: {e}")
                    # 创建默认纹理图
                    self._create_default_image(os.path.join(folder_path, 'texture.png'))
            else:
                print("警告：没有选中的角色图片，创建默认texture")
                self._create_default_image(os.path.join(folder_path, 'texture.png'))
            
            print(f"Agent {agent_name} successfully saved to: {folder_path}")
            return folder_path
            
        except Exception as e:
            print(f"Failed to save agent to folder: {e}")
            raise
    
    def _make_safe_filename(self, filename: str) -> str:
        """创建安全的文件名"""
        # 移除或替换不安全的字符
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        safe_name = ''.join(c if c in safe_chars else '_' for c in filename)
        
        # 确保不为空
        if not safe_name:
            safe_name = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return safe_name
    
    def _download_image(self, url: str, save_path: str):
        """下载图片到本地并进行缩放"""
        try:
            import requests
            from PIL import Image
            import io
            
            print(f"正在下载图片: {url}")
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 下载图片到内存
            image_data = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    image_data.write(chunk)
            image_data.seek(0)
            
            # 打开图片并进行缩放
            img = Image.open(image_data)
            
            # 根据文件名判断需要缩放的尺寸
            filename = os.path.basename(save_path)
            if 'portrait' in filename:
                # portrait: 320x320 -> 32x32
                target_size = (32, 32)
                print(f"缩放portrait图片: {img.size} -> {target_size}")
            elif 'texture' in filename:
                # texture: 288x384 -> 96x128
                target_size = (96, 128)
                print(f"缩放texture图片: {img.size} -> {target_size}")
            else:
                # 其他图片保持原尺寸
                target_size = img.size
                print(f"保持原尺寸: {img.size}")
            
            # 使用NEAREST插值保持像素艺术风格
            if target_size != img.size:
                img = img.resize(target_size, Image.NEAREST)
            
            # 保存缩放后的图片
            img.save(save_path)
            print(f"图片下载并缩放成功: {save_path}")
                
        except Exception as e:
            print(f"下载或缩放图片失败: {e}")
            # 如果下载失败，创建一个默认图片
            self._create_default_image(save_path)
    
    def _copy_and_resize_image(self, source_path: str, target_path: str, target_size: tuple):
        """复制并调整图片大小"""
        try:
            from PIL import Image
            import shutil
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 打开源图片
            with Image.open(source_path) as img:
                # 调整大小，使用NEAREST插值保持像素艺术风格
                resized_img = img.resize(target_size, Image.NEAREST)
                
                # 保存调整后的图片
                resized_img.save(target_path)
                print(f"Image copied and resized: {source_path} -> {target_path} ({target_size})")
                
        except Exception as e:
            print(f"Failed to copy and resize image: {e}")
            # 如果复制失败，创建默认图片
            self._create_default_image(target_path)

    def _create_default_image(self, save_path: str):
        """创建默认图片占位符"""
        try:
            from PIL import Image, ImageDraw
            
            # 根据文件名判断图片尺寸
            filename = os.path.basename(save_path)
            if 'portrait' in filename:
                size = (32, 32)
                color = (100, 100, 100)  # 灰色
            elif 'texture' in filename:
                size = (96, 128)
                color = (150, 150, 150)  # 浅灰色
            else:
                size = (64, 64)
                color = (128, 128, 128)  # 中灰色
            
            # 创建纯色图片
            img = Image.new('RGB', size, color)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 保存图片
            img.save(save_path)
            print(f"Created default image: {save_path}")
            
        except Exception as e:
            print(f"Failed to create default image: {e}")
            # 如果PIL不可用，创建一个文本文件作为占位符
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w') as f:
                f.write("# Default image placeholder")