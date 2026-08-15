from dataclasses import dataclass
from typing import Protocol

class AIProvider(Protocol):
    def diagnose_product(self, product_name: str, category: str) -> dict: ...
    def generate_review(self, product_name: str, metrics: dict) -> dict: ...

@dataclass
class DemoAIProvider:
    name: str = 'demo'
    def diagnose_product(self, product_name: str, category: str) -> dict:
        return {'positioning': f'{category or "通用"}高性价比运营单品：{product_name}', 'recommendations': '补充竞品对比、强化核心卖点并测试两组主图'}
    def generate_review(self, product_name: str, metrics: dict) -> dict:
        return {'summary': f'{product_name} 本周期复盘已生成', 'next_actions': ['测试新素材', '关注点击到转化漏斗']}

def get_ai_provider() -> AIProvider:
    # Replace this factory with a configured OpenAI/other provider without changing API routes.
    return DemoAIProvider()
