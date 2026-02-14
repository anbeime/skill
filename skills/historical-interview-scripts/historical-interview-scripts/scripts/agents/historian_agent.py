#!/usr/bin/env python3
"""
历史考据智能体
"""

from typing import Dict, List, Any
from .base_agent import BaseAgent


class HistorianAgent(BaseAgent):
    """历史考据智能体"""
    
    def execute(self, characters: List[str]) -> Dict[str, Dict]:
        """
        分析历史人物
        
        Args:
            characters: 历史人物列表
        
        Returns:
            dict: 人物档案字典
        """
        self.log(f"开始分析{len(characters)}个人物...")
        
        characters_data = {}
        
        for character in characters:
            # 先从记忆库中查找
            cached_data = self.memory.get(f'characters.{character}')
            
            if cached_data:
                self.log(f"  - {character}：使用缓存数据")
                characters_data[character] = cached_data
            else:
                # 调用LLM生成人物档案
                self.log(f"  - {character}：生成新档案...")
                character_data = self._generate_character_profile(character)
                characters_data[character] = character_data
                
                # 存入记忆库
                self.memory.set(f'characters.{character}', character_data)
        
        self.log(f"✓ 完成：分析{len(characters_data)}个人物")
        
        return characters_data
    
    def _generate_character_profile(self, character: str) -> Dict[str, Any]:
        """
        生成人物档案
        
        Args:
            character: 人物姓名
        
        Returns:
            dict: 人物档案
        """
        # 构建提示词
        prompt = f"""
请分析历史人物"{character}"，生成结构化的人物档案，包含以下信息：

1. 核心人设：用3-5个关键词描述人物的核心形象
2. 经典事迹：列出3-5个最具代表性的事迹
3. 性格特点：提炼3-5个核心性格特征
4. 可调侃点：找出3-5个适合现代语境调侃的角度
5. 禁忌边界：明确哪些历史事实可以调侃，哪些必须尊重
6. 经典名言：列出2-3句广为流传的名言

请以JSON格式返回：
{{
    "name": "人物姓名",
    "core_image": ["核心人设关键词"],
    "classical_deeds": ["经典事迹"],
    "personality": ["性格特点"],
    "teasable_points": ["可调侃点"],
    "taboo_boundaries": {
        "must_respect": ["必须尊重的内容"],
        "can_tease": ["可以调侃的内容"],
        "forbidden": ["禁止触碰的内容"]
    },
    "classic_quotes": ["经典名言"]
}}
"""
        
        # 调用LLM
        # response = self._call_llm(prompt)
        
        # 模拟响应（实际使用时替换为真实API调用）
        if character == "李白":
            response = {
                "name": "李白",
                "core_image": ["浪漫主义诗人", "豪放不羁", "嗜酒如命", "漫游天下"],
                "classical_deeds": ["斗酒诗百篇", "漫游天下", "与杜甫友谊"],
                "personality": ["豪放", "随性", "才华横溢", "乐观"],
                "teasable_points": [
                    "诗仙称号是否因喝酒",
                    "月下独酌是酒瘾还是抑郁",
                    "与杜甫的CP关系",
                    "漫游天下是旅游还是逃难"
                ],
                "taboo_boundaries": {
                    "must_respect": ["诗歌成就", "爱国情怀", "艺术才华"],
                    "can_tease": ["饮酒习惯", "漫游天下", "与杜甫的友谊"],
                    "forbidden": ["歪曲历史事实", "恶意贬低", "政治隐喻"]
                },
                "classic_quotes": [
                    "天生我材必有用，千金散尽还复来",
                    "举头望明月，低头思故乡",
                    "长风破浪会有时，直挂云帆济沧海"
                ]
            }
        elif character == "李清照":
            response = {
                "name": "李清照",
                "core_image": ["婉约派词人", "才女气质", "好赌", "好酒"],
                "classical_deeds": ["宋词创作", "金石收藏", "南渡后流亡"],
                "personality": ["优雅", "犀利", "敢爱敢恨", "才情"],
                "teasable_points": [
                    "才女也爱躺平撸串",
                    "好赌是不是职业病",
                    "是不是恋爱脑",
                    "吐槽苏轼太直男"
                ],
                "taboo_boundaries": {
                    "must_respect": ["文学成就", "爱国情怀", "女性地位"],
                    "can_tease": ["好赌", "好酒", "情感经历"],
                    "forbidden": ["歪曲历史事实", "恶意贬低", "性别歧视"]
                },
                "classic_quotes": [
                    "寻寻觅觅，冷冷清清，凄凄惨惨戚戚",
                    "生当作人杰，死亦为鬼雄",
                    "莫道不销魂，帘卷西风，人比黄花瘦"
                ]
            }
        else:
            # 默认响应（用于其他人物）
            response = {
                "name": character,
                "core_image": ["历史人物"],
                "classical_deeds": [],
                "personality": [],
                "teasable_points": [],
                "taboo_boundaries": {
                    "must_respect": [],
                    "can_tease": [],
                    "forbidden": ["歪曲历史事实", "恶意贬低"]
                },
                "classic_quotes": []
            }
        
        return response
