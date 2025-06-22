from typing import Dict, List, Optional, Literal
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from utils.calendar_api_utils import create_api_request_from_payload

load_dotenv()

model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.5,
)

def parse_calendar_intent(user_query: str) -> Dict:
    """사용자 질의에서 캘린더 작업 의도 파악"""
    prompt = f"""
    사용자의 질의를 분석하여 캘린더/할일 관리 작업의 의도를 정확히 파악해주세요.
    
    질의: "{user_query}"
    
    다음 키워드와 문맥을 고려하여 판단해주세요:
    
    **일정 관련:**
    - CREATE_EVENT: "추가해줘", "등록해줘", "만들어줘", "일정 잡아줘", "예약해줘" 등의 표현이 있거나 새로운 일정을 말하는 경우
    - READ_EVENT: "보여줘", "확인해줘", "조회해줘", "일정이 뭐야", "언제야", "전체 일정", "모든 일정", "일정 목록" 등의 표현이 있거나 기존 일정을 묻는 경우
    - UPDATE_EVENT: "수정해줘", "변경해줘", "바꿔줘", "다른 시간으로", "다른 날짜로" 등의 표현이 있는 경우
    - DELETE_EVENT: "삭제해줘", "취소해줘", "지워줘", "없애줘" 등의 표현이 있는 경우
    
    **할일 관련:**
    - CREATE_TASK: "할일 추가", "해야 할 일", "해야 해", "완료해야" 등의 표현이 있거나 새로운 할일을 말하는 경우
    - READ_TASK: "할일 목록", "해야 할 일 뭐야", "할 일 보여줘", "전체 할일", "모든 할일" 등의 표현이 있는 경우
    - UPDATE_TASK: "할일 수정", "할일 변경" 등의 표현이 있는 경우
    - DELETE_TASK: "할일 삭제", "할일 취소" 등의 표현이 있는 경우
    
    정확히 분석하여 다음 JSON 형식으로 응답해주세요:
    {{
        "intent": "CREATE_EVENT",
        "type": "event",
        "operation": "create"
    }}
    
    type은 "event" 또는 "task" 중 하나여야 합니다.
    operation은 "create", "read", "update", "delete" 중 하나여야 합니다.
    """
    
    response = model.invoke(prompt).content.strip()
    try:
        return json.loads(response)
    except:
        # LLM 분류 실패 시 기본값
        return {"intent": "READ_EVENT", "type": "event", "operation": "read"}

def extract_event_data(user_query: str) -> Dict:
    """사용자 질의에서 일정 데이터 추출"""
    prompt = f"""
    사용자의 질의에서 일정 정보를 추출해주세요.
    
    질의: "{user_query}"
    
    다음 정보를 JSON 형태로 추출해주세요:
    - summary: 일정 제목
    - location: 장소 (있는 경우)
    - description: 설명 (있는 경우)
    - start: 시작 시간 (ISO 8601 형식)
    - end: 종료 시간 (ISO 8601 형식)
    
    예시:
    {{
        "summary": "팀 미팅",
        "location": "회의실 A",
        "description": "주간 프로젝트 진행상황 논의",
        "start": {{
            "dateTime": "2024-01-15T10:00:00",
            "timeZone": "Asia/Seoul"
        }},
        "end": {{
            "dateTime": "2024-01-15T11:00:00",
            "timeZone": "Asia/Seoul"
        }}
    }}
    """
    
    response = model.invoke(prompt).content.strip()
    try:
        return json.loads(response)
    except:
        return {"summary": "새 일정", "start": {"dateTime": datetime.now().isoformat()}}

def extract_task_data(user_query: str) -> Dict:
    """사용자 질의에서 할일 데이터 추출"""
    prompt = f"""
    사용자의 질의에서 할일 정보를 추출해주세요.
    
    질의: "{user_query}"
    
    다음 정보를 JSON 형태로 추출해주세요:
    - title: 할일 제목
    - notes: 메모 (있는 경우)
    - due: 마감일 (ISO 8601 형식, 있는 경우)
    
    예시:
    {{
        "title": "보고서 작성",
        "notes": "월간 실적 보고서 작성",
        "due": "2024-01-20T18:00:00.000Z"
    }}
    """
    
    response = model.invoke(prompt).content.strip()
    try:
        return json.loads(response)
    except:
        return {"title": "새 할일"}

def prepare_calendar_payload(intent: Dict, operation: str, type_: str, user_query: str) -> Dict:
    """캘린더 API 호출을 위한 페이로드 준비"""
    payload = {
        "intent": intent.get("intent", ""),
        "operation": operation,
        "type": type_,
        "user_query": user_query
    }
    
    if operation == "create":
        if type_ == "event":
            payload["event_data"] = extract_event_data(user_query)
        elif type_ == "task":
            payload["task_data"] = extract_task_data(user_query)
    
    elif operation == "read":
        if type_ == "event":
            # 일정 조회 조건 설정
            payload["query_params"] = {
                "time_min": datetime.utcnow().isoformat() + 'Z',
                "time_max": (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z',
                "single_events": True,
                "order_by": "startTime"
            }
        elif type_ == "task":
            payload["query_params"] = {}
    
    elif operation in ["update", "delete"]:
        # 수정/삭제를 위해서는 ID가 필요
        payload["error"] = f"{type_} {operation}을 위해서는 ID가 필요합니다."
    
    return payload

def calendar_agent(state: Dict) -> Dict:
    """캘린더 에이전트 메인 함수"""
    user_query = state["messages"][-1]
    schedule_type = state.get("schedule_type", "event")
    
    try:
        # 사용자 의도 파악
        intent = parse_calendar_intent(user_query)
        operation = intent.get("operation", "read")
        type_ = intent.get("type", schedule_type)
        
        # 기본 페이로드 준비
        payload = prepare_calendar_payload(intent, operation, type_, user_query)
        
        # 사용 가능한 캘린더/할일 목록 정보 (실제로는 외부에서 제공받아야 함)
        available_calendars = state.get("available_calendars", [])
        available_task_lists = state.get("available_task_lists", [])
        
        # API 요청 본문 생성
        api_request = create_api_request_from_payload(
            payload, 
            available_calendars, 
            available_task_lists
        )
        
        # 페이로드와 API 요청 본문을 상태에 저장
        state["calendar_payload"] = payload
        state["calendar_api_request"] = api_request
        
        # 작업 요약 생성
        if operation == "create":
            summary = f"{type_} 생성 요청이 준비되었습니다."
        elif operation == "read":
            summary = f"{type_} 조회 요청이 준비되었습니다."
        elif operation == "update":
            summary = f"{type_} 수정 요청이 준비되었습니다."
        elif operation == "delete":
            summary = f"{type_} 삭제 요청이 준비되었습니다."
        else:
            summary = f"{type_} 작업 요청이 준비되었습니다."
        
        state["crud_result"] = summary
        
        # 로그 기록
        state.setdefault("agent_messages", []).append({
            "agent": "calendar_agent",
            "intent": intent,
            "operation": operation,
            "type": type_,
            "payload": payload,
            "api_request": api_request,
            "summary": summary
        })
        
    except Exception as e:
        error_msg = f"캘린더 에이전트 오류: {str(e)}"
        state["crud_result"] = error_msg
        state.setdefault("agent_messages", []).append({
            "agent": "calendar_agent",
            "error": str(e)
        })
    
    return state
