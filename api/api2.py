

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

# Import your existing execution function (adjust import path as necessary)
from agents.executor import execute_model

app = FastAPI()

# Global variables for session and access token
_current_session_id: Optional[str] = None
_current_access_token: Optional[str] = None

class InitRequest(BaseModel):
    user_input: str
    access_token: str

class MessageRequest(BaseModel):
    user_input: str
    session_id: str
    access_token: Optional[str] = None

class AgentResponse(BaseModel):
    session_id: str
    response: str

@app.post("/v1/chat/init", response_model=AgentResponse)
def start_session(req: InitRequest):
    global _current_session_id, _current_access_token
    # Store incoming access token and generate new session ID
    _current_access_token = req.access_token
    session_id = str(uuid.uuid4())
    _current_session_id = session_id
    # Call your model execution function
    response_text = execute_model(req.user_input, session_id)
    return AgentResponse(session_id=session_id, response=response_text)

@app.post("/v1/chat/message", response_model=AgentResponse)
def session_messages(req: MessageRequest):
    # Validate session ID
    if _current_session_id != req.session_id:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    # If access_token provided, validate it
    if req.access_token and req.access_token != _current_access_token:
        raise HTTPException(status_code=401, detail="Invalid access_token")
    # Call your model execution function with existing session
    response_text = execute_model(req.user_input, req.session_id)
    return AgentResponse(session_id=req.session_id, response=response_text)