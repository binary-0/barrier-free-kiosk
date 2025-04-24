from typing import Dict, Any
from langgraph.graph import Graph, START, END
from .state import WorkflowState


from .nodes.stt_node import process_audio
from .nodes.llm_node import analyze_order
from .nodes.rule_based_node import process_dialogue, should_use_llm
from .nodes.intent_classifier_node import classify_intent


def create_order_analysis_workflow() -> Graph:
    workflow = Graph()
    
    workflow.add_node("process_audio", process_audio)       
    workflow.add_node("classify_intent", classify_intent)   
    workflow.add_node("rule_based_dialogue", process_dialogue) 
    workflow.add_node("analyze_order", analyze_order)       
    
    workflow.add_edge(START, "process_audio")
    workflow.add_edge("process_audio", "classify_intent")
    workflow.add_edge("classify_intent", "rule_based_dialogue")  
    
    workflow.add_conditional_edges(
        "rule_based_dialogue",
        should_use_llm,
        {
            "analyze_order": "analyze_order",  
            "END": END  
        }
    )
    workflow.add_edge("analyze_order", END)
    
    return workflow.compile()
