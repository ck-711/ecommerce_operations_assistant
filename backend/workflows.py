from typing import TypedDict
from langgraph.graph import END, StateGraph
from backend.ai_provider import get_ai_provider

class ProductState(TypedDict, total=False):
    product_name: str
    category: str
    metrics: dict
    plan_type: str
    diagnosis: dict
    creative_plan: dict
    recommendation: dict
    review: dict

def _run(nodes, initial):
    graph=StateGraph(ProductState)
    previous=None
    for name,fn in nodes:
        graph.add_node(name,fn)
        if previous: graph.add_edge(previous,name)
        else: graph.set_entry_point(name)
        previous=name
    graph.add_edge(previous,END)
    return graph.compile().invoke(initial)

def run_diagnosis(product_name: str, category: str) -> dict:
    provider=get_ai_provider()
    def load(state): return {'product_name':product_name,'category':category}
    def analyze(state): return {'diagnosis':provider.diagnose_product(state['product_name'],state['category'])}
    return _run([('load_product',load),('analyze_product',analyze)],{})['diagnosis']

def run_creative_plan(product_name: str, plan_type: str) -> dict:
    provider=get_ai_provider()
    def load(state): return {'product_name':product_name,'plan_type':plan_type}
    def generate(state): return {'creative_plan':provider.generate_creative_plan(state['product_name'],state['plan_type'])}
    return _run([('load_product',load),('generate_plan',generate)],{})['creative_plan']

def run_ad_recommendation(product_name: str, metrics: dict | None = None) -> dict:
    provider=get_ai_provider()
    def load(state): return {'product_name':product_name,'metrics':metrics or {}}
    def generate(state): return {'recommendation':provider.generate_ad_recommendation(state['product_name'],state['metrics'])}
    return _run([('load_product',load),('generate_recommendation',generate)],{})['recommendation']

def run_review(product_name: str, metrics: dict | None = None) -> dict:
    provider=get_ai_provider()
    def load(state): return {'product_name':product_name,'metrics':metrics or {}}
    def generate(state): return {'review':provider.generate_review(state['product_name'],state['metrics'])}
    return _run([('load_product',load),('generate_review',generate)],{})['review']
