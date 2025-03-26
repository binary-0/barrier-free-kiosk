from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class OrderSession(BaseModel):
    session_id: str
    created_at: datetime
    last_updated: datetime
    current_order: Optional[Dict[str, Any]] = None
    pending_clarifications: List[str] = []
    conversation_history: List[Dict[str, str]] = []

class OrderSessionManager:
    def __init__(self):
        self.sessions: Dict[str, OrderSession] = {}
    
    def create_session(self, session_id: str) -> OrderSession:
        now = datetime.now()
        session = OrderSession(
            session_id=session_id,
            created_at=now,
            last_updated=now
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[OrderSession]:
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, order_data: Dict[str, Any]) -> OrderSession:
        if session_id not in self.sessions:
            return self.create_session(session_id)
        
        session = self.sessions[session_id]
        session.last_updated = datetime.now()
        session.current_order = order_data
        return session
    
    def add_conversation(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def clear_pending_clarifications(self, session_id: str):
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session.pending_clarifications = []
    
    def add_pending_clarification(self, session_id: str, clarification: str):
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        if clarification not in session.pending_clarifications:
            session.pending_clarifications.append(clarification)
    
    def remove_pending_clarification(self, session_id: str, clarification: str):
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        if clarification in session.pending_clarifications:
            session.pending_clarifications.remove(clarification)
    
    def resolve_pending_clarification(self, session_id: str):
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        if session.pending_clarifications:
            session.pending_clarifications.pop(0) 