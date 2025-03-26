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

class WorkflowState(TypedDict):
    audio_path: str
    text: str
    analysis: Optional[OrderAnalysis]
    response: Optional[ResponseInfo]
    session_id: str
    conversation_history: List[Dict[str, str]]
    pending_clarifications: List[str]
    current_order: Optional[Dict[str, Any]] 