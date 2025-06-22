from typing import Dict, Any, List
import os
import json
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.3,
)

def clean_json_response(content: str) -> str:
    """JSON 응답을 정리하여 파싱 가능한 형태로 만듭니다."""
    content = content.strip()
    
    # JSON 코드 블록 마커 제거
    if content.startswith('```json'):
        content = content[7:]
    elif content.startswith('```'):
        content = content[3:]
    
    if content.endswith('```'):
        content = content[:-3]
    
    content = content.strip()
    
    # 중괄호가 포함된 부분만 추출
    brace_match = re.search(r'\{.*\}', content, re.DOTALL)
    if brace_match:
        content = brace_match.group()
    
    return content

def parse_selection_response(content: str) -> Dict:
    """선택 응답을 안전하게 파싱하여 딕셔너리로 변환합니다."""
    try:
        # JSON으로 파싱 시도
        cleaned_content = clean_json_response(content)
        return json.loads(cleaned_content)
    except json.JSONDecodeError:
        # 파싱 실패시 기본값 반환
        return {
            "selected_calendar_id": "primary",
            "selected_task_list_id": "@default",
            "reason": "파싱 실패로 기본값 사용"
        }

def get_calendar_list_api() -> List[Dict[str, Any]]:
    """Google Calendar API를 호출하여 캘린더 목록을 가져옵니다."""
    try:
        access_token = os.getenv("GOOGLE_ACCESS_TOKEN")
        if not access_token:
            print("경고: GOOGLE_ACCESS_TOKEN이 설정되지 않았습니다. 모의 데이터를 사용합니다.")
            return mock_calendar_list_api()
        
        url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        calendars = data.get("items", [])
        print(f"Google Calendar API 호출 성공: {len(calendars)}개 캘린더 조회")
        
        return calendars
        
    except Exception as e:
        print(f"Google Calendar API 호출 실패: {str(e)}. 모의 데이터를 사용합니다.")
        return mock_calendar_list_api()

def get_task_list_api() -> List[Dict[str, Any]]:
    """Google Tasks API를 호출하여 태스크 리스트를 가져옵니다."""
    try:
        access_token = os.getenv("GOOGLE_ACCESS_TOKEN")
        if not access_token:
            print("경고: GOOGLE_ACCESS_TOKEN이 설정되지 않았습니다. 모의 데이터를 사용합니다.")
            return mock_task_list_api()
        
        url = "https://tasks.googleapis.com/tasks/v1/users/@me/lists"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        task_lists = data.get("items", [])
        print(f"Google Tasks API 호출 성공: {len(task_lists)}개 태스크 리스트 조회")
        
        return task_lists
        
    except Exception as e:
        print(f"Google Tasks API 호출 실패: {str(e)}. 모의 데이터를 사용합니다.")
        return mock_task_list_api()

def mock_calendar_list_api() -> List[Dict[str, Any]]:
    """캘린더 목록 API 모의 응답 (API 호출 실패시 사용)"""
    return [
        {
            "id": "primary",
            "summary": "내 캘린더",
            "primary": True,
            "accessRole": "owner"
        },
        {
            "id": "work@company.com",
            "summary": "업무 캘린더",
            "primary": False,
            "accessRole": "writer"
        },
        {
            "id": "family@example.com",
            "summary": "가족 캘린더",
            "primary": False,
            "accessRole": "reader"
        }
    ]

def mock_task_list_api() -> List[Dict[str, Any]]:
    """태스크 리스트 API 모의 응답 (API 호출 실패시 사용)"""
    return [
        {
            "id": "@default",
            "title": "내 할일",
            "kind": "tasks#taskList"
        },
        {
            "id": "work_tasks",
            "title": "업무 할일",
            "kind": "tasks#taskList"
        },
        {
            "id": "personal_tasks",
            "title": "개인 할일",
            "kind": "tasks#taskList"
        }
    ]

def select_calendar_list(
    user_query: str,
    available_calendars: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """LLM을 사용하여 적절한 캘린더를 선택합니다."""
    
    calendars_info = []
    for cal in available_calendars:
        calendars_info.append(f"- ID: {cal['id']}, 이름: {cal.get('summary', 'N/A')}, 기본: {cal.get('primary', False)}")
    
    prompt = f"""
    사용자 질의와 사용 가능한 캘린더 목록을 분석하여 가장 적절한 캘린더를 선택해주세요.
    
    [사용자 질의]
    "{user_query}"
    
    [사용 가능한 캘린더]
    {chr(10).join(calendars_info)}
    
    **선택 기준:**
    1. 사용자 질의와 가장 관련성이 높은 캘린더 선택
    2. 기본 캘린더가 있으면 우선 고려
    3. 질의에서 언급된 키워드와 매칭되는 캘린더 선택
    
    다음 JSON 형식으로만 응답해주세요:
    {{
        "selected_calendar_id": "선택된 캘린더 ID",
        "reason": "선택 이유"
    }}
    """
    
    try:
        response = model.invoke(prompt)
        return parse_selection_response(response.content)
    except Exception as e:
        # 에러시 기본값 반환
        return {
            "selected_calendar_id": "primary",
            "reason": f"선택 실패: {str(e)}"
        }

def select_task_list(
    user_query: str,
    available_task_lists: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """LLM을 사용하여 적절한 태스크 리스트를 선택합니다."""
    
    task_lists_info = []
    for task_list in available_task_lists:
        task_lists_info.append(f"- ID: {task_list['id']}, 이름: {task_list.get('title', 'N/A')}")
    
    prompt = f"""
    사용자 질의와 사용 가능한 태스크 리스트를 분석하여 가장 적절한 태스크 리스트를 선택해주세요.
    
    [사용자 질의]
    "{user_query}"
    
    [사용 가능한 태스크 리스트]
    {chr(10).join(task_lists_info)}
    
    **선택 기준:**
    1. 사용자 질의와 가장 관련성이 높은 태스크 리스트 선택
    2. 기본 태스크 리스트가 있으면 우선 고려
    3. 질의에서 언급된 키워드와 매칭되는 태스크 리스트 선택
    
    다음 JSON 형식으로만 응답해주세요:
    {{
        "selected_task_list_id": "선택된 태스크 리스트 ID",
        "reason": "선택 이유"
    }}
    """
    
    try:
        response = model.invoke(prompt)
        return parse_selection_response(response.content)
    except Exception as e:
        # 에러시 기본값 반환
        return {
            "selected_task_list_id": "@default",
            "reason": f"선택 실패: {str(e)}"
        }

def calrud(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    캘린더/태스크 리스트를 조회하고 적절한 리스트를 선택합니다.

    Args:
        state: 현재 상태 딕셔너리

    Returns:
        state: 업데이트된 상태 딕셔너리
    """
    try:
        # calendar_agent에서 분류한 정보 가져오기
        operation = state.get("calendar_operation", "read")
        event_type = state.get("event_type", "event")
        user_query = state.get("messages", [""])[-1] if state.get("messages") else ""
        
        print("=== CalRUD 노드 실행: 캘린더/태스크 리스트 조회 및 선택 ===")
        print(f"작업: {operation}, 타입: {event_type}")

        if operation not in ["read", "update", "delete"]:
            raise ValueError(f"CalRUD 노드는 'read', 'update', 'delete' 작업만 처리합니다. 현재 작업: {operation}")

        # 1단계: 캘린더/태스크 리스트 API 호출
        if event_type == "event":
            # Google Calendar API 호출
            available_calendars = get_calendar_list_api()
            print(f"캘린더 목록 조회 완료: {len(available_calendars)}개")
            
            # 2단계: 적절한 캘린더 선택
            calendar_selection = select_calendar_list(user_query, available_calendars)
            selected_calendar_id = calendar_selection["selected_calendar_id"]
            print(f"선택된 캘린더: {selected_calendar_id} (이유: {calendar_selection['reason']})")
            
            # 결과 저장
            state.update({
                "selected_calendar_id": selected_calendar_id,
                "available_calendars": available_calendars,
                "selection_reason": calendar_selection["reason"],
                "api_type": "google_calendar"
            })
            
        else:  # task
            # Google Tasks API 호출
            available_task_lists = get_task_list_api()
            print(f"태스크 리스트 조회 완료: {len(available_task_lists)}개")
            
            # 2단계: 적절한 태스크 리스트 선택
            task_list_selection = select_task_list(user_query, available_task_lists)
            selected_task_list_id = task_list_selection["selected_task_list_id"]
            print(f"선택된 태스크 리스트: {selected_task_list_id} (이유: {task_list_selection['reason']})")
            
            # 결과 저장
            state.update({
                "selected_task_list_id": selected_task_list_id,
                "available_task_lists": available_task_lists,
                "selection_reason": task_list_selection["reason"],
                "api_type": "google_tasks"
            })

        # 상태 업데이트
        state["crud_result"] = f"{event_type} {operation} 작업을 위한 캘린더/태스크 리스트 선택 완료"
        state["next_node"] = "answer_planner"

        # 로그 기록
        state.setdefault("agent_messages", []).append({
            "agent": "calrud",
            "summary": state["crud_result"],
            "selection_reason": state["selection_reason"],
            "next_node": state["next_node"]
        })

    except Exception as e:
        error_msg = f"CalRUD 오류: {str(e)}"
        state["crud_result"] = error_msg
        state["next_node"] = "answer_generator"
        state.setdefault("agent_messages", []).append({
            "agent": "calrud",
            "error": str(e)
        })

    return state
