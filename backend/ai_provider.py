from dataclasses import dataclass
import os
from typing import Protocol

class AIProvider(Protocol):
    def diagnose_product(self, product_name: str, category: str) -> dict: ...
    def generate_review(self, product_name: str, metrics: dict) -> dict: ...
    def generate_creative_plan(self, product_name: str, plan_type: str) -> dict: ...
    def generate_ad_recommendation(self, product_name: str, metrics: dict) -> dict: ...

@dataclass
class DemoAIProvider:
    name: str = 'demo'
    def diagnose_product(self, product_name: str, category: str) -> dict:
        return {'positioning': f'{category or "通用"}高性价比运营单品：{product_name}', 'recommendations': '补充竞品对比、强化核心卖点并测试两组主图'}
    def generate_review(self, product_name: str, metrics: dict) -> dict:
        return {'summary': f'{product_name} 本周期复盘已生成', 'next_actions': ['测试新素材', '关注点击到转化漏斗']}
    def generate_creative_plan(self, product_name: str, plan_type: str) -> dict:
        return {'title': f'{product_name} {plan_type} 方案', 'items': [{'title':'核心卖点对比','copy':'突出轻量、便携和转化价值'}]}
    def generate_ad_recommendation(self, product_name: str, metrics: dict) -> dict:
        return {'summary': f'{product_name} 先小预算测试高意向人群，再根据转化扩量', 'objective':'提升转化'}

def get_ai_provider() -> AIProvider:
    provider=os.getenv('AI_PROVIDER','openai')
    if provider == 'demo': return DemoAIProvider()
    raise RuntimeError('AI_PROVIDER is not configured. Set AI_PROVIDER=demo only for local tests or install a real provider adapter.')
