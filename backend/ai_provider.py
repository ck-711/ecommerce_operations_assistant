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

class OpenAIProvider:
    name='openai'
    def __init__(self):
        from openai import OpenAI
        key=os.getenv('OPENAI_API_KEY')
        if not key: raise RuntimeError('OPENAI_API_KEY is required when AI_PROVIDER=openai')
        kwargs={'api_key':key};
        if os.getenv('OPENAI_BASE_URL'): kwargs['base_url']=os.environ['OPENAI_BASE_URL']
        self.client=OpenAI(**kwargs)
        self.model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
    def _json(self, instruction: str) -> dict:
        response=self.client.chat.completions.create(model=self.model,temperature=0.2,response_format={'type':'json_object'},messages=[{'role':'system','content':'你是电商运营助手，只输出合法 JSON。'},{'role':'user','content':instruction}])
        import json
        return json.loads(response.choices[0].message.content)
    def diagnose_product(self, product_name, category): return self._json(f'为商品{product_name}（类目：{category}）输出 positioning 和 recommendations 两个字段。')
    def generate_creative_plan(self, product_name, plan_type): return self._json(f'为商品{product_name}生成{plan_type}方案，输出 title 和 items 数组。')
    def generate_ad_recommendation(self, product_name, metrics): return self._json(f'为商品{product_name}生成投放建议，输出 summary 和 objective。数据：{metrics}')
    def generate_review(self, product_name, metrics): return self._json(f'为商品{product_name}生成复盘，输出 summary 和 next_actions 数组。数据：{metrics}')

def get_ai_provider() -> AIProvider:
    provider=os.getenv('AI_PROVIDER','openai')
    if provider == 'demo': return DemoAIProvider()
    if provider == 'openai': return OpenAIProvider()
    raise RuntimeError('AI_PROVIDER is not configured. Set AI_PROVIDER=demo only for local tests or install a real provider adapter.')
