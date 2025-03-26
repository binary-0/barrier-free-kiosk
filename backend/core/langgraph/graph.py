from typing import Dict, Any
from langgraph.graph import Graph, START, END
from .state import WorkflowState
from .nodes.stt_node import process_audio
from .nodes.llm_node import analyze_order

def create_order_analysis_workflow() -> Graph:
    workflow = Graph()
    
    workflow.add_node("process_audio", process_audio)
    workflow.add_node("analyze_order", analyze_order)
    
    workflow.add_edge(START, "process_audio")
    workflow.add_edge("process_audio", "analyze_order")
    workflow.add_edge("analyze_order", END)
    
    return workflow.compile() 