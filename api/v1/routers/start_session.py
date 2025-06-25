from fastapi import APIRouter, Depends, HTTPException
from api.v1.dto import InputRequest, AgentResponse
from api.v1.service import handle_agent_input
from fastapi import Header

GLOBAL_ACCESS_TOKEN: str = ""

router = APIRouter(prefix="/input", tags=["agent"])

def get_token_header(access_token: str = Header(...)):
    global GLOBAL_ACCESS_TOKEN
    GLOBAL_ACCESS_TOKEN = access_token
    if not access_token:
        raise HTTPException(401, "Missing access token")
    return access_token

@router.post("", response_model=AgentResponse, dependencies=[Depends(get_token_header)])
def post_agent_input(request: InputRequest):
    """
    클라이언트가 body 에 InputRequest 를 보내면
    handle_agent_input 을 호출해서 결과를 돌려준다.
    """
    return handle_agent_input(request)
