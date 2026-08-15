from typing import TypedDict
from backend.ai_provider import get_ai_provider

class DiagnosisState(TypedDict, total=False):
    product_name: str
    category: str
    positioning: str
    recommendations: str

try:
    from langgraph.graph import END, StateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

def run_diagnosis(product_name: str, category: str) -> dict:
    provider=get_ai_provider()
    if not LANGGRAPH_AVAILABLE:
        return provider.diagnose_product(product_name, category)
    def load(state): return {'product_name': product_name, 'category': category}
    def analyze(state): return provider.diagnose_product(state['product_name'], state['category'])
    graph=StateGraph(DiagnosisState); graph.add_node('load',load); graph.add_node('analyze',analyze); graph.set_entry_point('load'); graph.add_edge('load','analyze'); graph.add_edge('analyze',END)
    return graph.compile().invoke({})
