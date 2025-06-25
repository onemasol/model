from pydantic import BaseModel
from typing import Optional, List, Any

class InputRequest(BaseModel):
    user_id: str
    access_token: str
    session_id: str
    user_input: str
    ocr_result: Optional[str] = None

class RelayRequest(BaseModel):
    prompt: str
    access_token: str

class AgentResponse(BaseModel):
    final_answer: str
    agent_messages: List[str]
    router_messages: List[str]
    crud_result: Optional[Any] = None