import uuid
import re

def make_agent_logs_payload(state: dict) -> dict:
    user_message = state["messages"][-1] if state.get("messages") else ""
    agent_response = state.get("final_answer") or state.get("final_output") or ""
    
    # session_id는 state에서 가져오거나 기본값 사용
    session_id = state.get("session_id", "3fa85f64-5717-4562-b3fc-2c963f66afa6")
    
    # 기본 payload 구성 (필수 필드만)
    payload = {
        "session_id": session_id,
        "user_message": user_message,
        "agent_response": agent_response
    }
    
    # crud_result에서 ID 추출
    crud_result = state.get("crud_result", "")
    
    # 이벤트 ID 추출 (예: "이벤트 생성 완료: da2e0f41-aef8-4495-ab8f-a6dd325995cd")
    event_match = re.search(r'이벤트 생성 완료: ([a-f0-9-]{36})', crud_result)
    if event_match:
        payload["event_id"] = event_match.group(1)
    
    # 태스크 ID 추출 (예: "할일 생성 완료: da2e0f41-aef8-4495-ab8f-a6dd325995cd")
    task_match = re.search(r'할일 생성 완료: ([a-f0-9-]{36})', crud_result)
    if task_match:
        payload["task_id"] = task_match.group(1)
    
    return payload
