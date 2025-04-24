from typing import Dict, Any, TypedDict, List, Optional
from dataclasses import dataclass

class OrderItem(TypedDict):
    name: str
    quantity: int
    options: List[str]
    price: int

class OrderAnalysis(TypedDict):
    items: List[OrderItem]
    total_price: int
    special_requests: str

class ResponseInfo(TypedDict):
    message: str
    needs_clarification: bool
    clarification_items: List[str]

class RuleBasedResult(TypedDict):
    success: bool

class WorkflowState(TypedDict):
    audio_path: str
    text: str
    analysis: Optional[OrderAnalysis]
    response: Optional[ResponseInfo]
    session_id: str
    conversation_history: List[Dict[str, str]]
    pending_clarifications: List[str]
    current_order: Optional[Dict[str, Any]]
    rule_based_result: Optional[RuleBasedResult]
    intent_classification: Optional[Dict[str, Any]]
    pending_clarifications_resolved: Optional[bool] 