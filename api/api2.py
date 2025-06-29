from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import subprocess
import uuid
import os
from test.test_flow import test_interactive_calendar_flow
from api.flow_runner import run_flow_interactive
from datetime import datetime

# Import your existing execution function (adjust import path as necessary)
from api.getset import (
     set_current_session_id, get_current_session_id,
     set_current_access_token, get_current_access_token,
     set_current_user_input, set_current_ocr_result
)

# Path to the run.sh script
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'run.sh')


app = FastAPI()

# # Global variables for session and access token
# _current_session_id: Optional[str] = None
# _current_access_token: Optional[str] = None
# _current_user_input: Optional[str] = None
# _current_ocr_result: Optional[str] = None

class InitRequest(BaseModel):
    user_id: Optional[str] = None
    access_token: str
    session_id: Optional[str] = None  # will be generated by server
    user_input: str
    ocr_result: Optional[str] = None

class MessageRequest(BaseModel):
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    session_id: str
    user_input: str
    ocr_result: Optional[str] = None

class AgentResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str
    

@app.post("/v1/chat/init", response_model=AgentResponse)
def start_session(req: InitRequest):
    timestamp = datetime.utcnow().isoformat()

    # Store incoming access token and generate new session ID
    session_id = str(uuid.uuid4())
    set_current_access_token(req.access_token)
    set_current_session_id(session_id)
    set_current_user_input(req.user_input)
    set_current_ocr_result(req.ocr_result)
    # Call your model execution function
    try:
        response_text = test_interactive_calendar_flow()
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    return AgentResponse(session_id=session_id, response=response_text, timestamp=timestamp)

@app.post("/v1/chat/message", response_model=AgentResponse)
def session_messages(req: MessageRequest):
    timestamp = datetime.utcnow().isoformat()

    # Validate session ID
    if get_current_session_id() != req.session_id:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    # If access_token provided, validate it
    if req.access_token and req.access_token != get_current_access_token():
        raise HTTPException(status_code=401, detail="Invalid access_token")
    set_current_user_input(req.user_input)
    set_current_ocr_result(req.ocr_result)
    # # Call your model execution function with existing session
    try:
        response_text = test_interactive_calendar_flow()
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    return AgentResponse(session_id=req.session_id, response=response_text, timestamp=timestamp)