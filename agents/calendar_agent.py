# agent/calendar_agent

from typing import Dict, List, Optional, Any
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone
import pytz

load_dotenv()

model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.3,
)

class CalendarAgent:
    def __init__(self):
        self.seoul_tz = pytz.timezone('Asia/Seoul')
        # 실제 구현에서는 여기서 Google API 클라이언트를 초기화합니다
        # self.calendar_service = build('calendar', 'v3', credentials=credentials)
        # self.tasks_service = build('tasks', 'v1', credentials=credentials)
        
    def _get_calendar_id(self) -> str:
        """
        기본 캘린더 ID를 가져옵니다.
        실제 구현에서는 calendarList.list API를 호출합니다.
        현재는 기본값으로 'primary'를 반환합니다.
        """
        return "primary"
    
    def _get_tasklist_id(self) -> str:
        """
        기본 작업 목록 ID를 가져옵니다.
        실제 구현에서는 tasklists.list API를 호출합니다.
        현재는 기본값으로 '@default'를 반환합니다.
        """
        return "@default"
    
    def _parse_datetime(self, date_str: str) -> str:
        """
        날짜 문자열을 파싱하고 서울 시간대의 ISO 형식으로 변환합니다.
        """
        try:
            # 다양한 날짜 형식을 파싱해봅니다
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                # 한국 날짜 형식으로 가정 (YYYY-MM-DD HH:MM)
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            
            # 서울 시간대로 변환
            if dt.tzinfo is None:
                dt = self.seoul_tz.localize(dt)
            else:
                dt = dt.astimezone(self.seoul_tz)
            
            return dt.isoformat()
        except Exception as e:
            raise ValueError(f"잘못된 날짜 형식입니다: {date_str}. 오류: {e}")

def calendar_agent(state: Dict) -> Dict:
    """
    Google Calendar 및 Tasks API 작업을 처리하는 캘린더 에이전트입니다.
    백엔드 팀을 위해 실제 API request body를 생성합니다.
    """
    user_query = state["messages"][-1]
    schedule_type = state.get("schedule_type", "event")
    
    # 캘린더 에이전트 초기화
    cal_agent = CalendarAgent()
    
    # 사용자 의도를 파싱하고 매개변수를 추출합니다
    intent_result = _parse_calendar_intent(user_query, schedule_type)
    
    if not intent_result:
        state["crud_result"] = "일정 관련 요청을 이해할 수 없습니다. 더 구체적으로 말씀해 주세요."
        return state
    
    operation = intent_result["operation"]
    params = intent_result["params"]
    
    try:
        if schedule_type == "event":
            result, api_request = _handle_calendar_event(operation, params, cal_agent)
        elif schedule_type == "task":
            result, api_request = _handle_task(operation, params, cal_agent)
        else:
            result = "일정 타입(event/task)이 명확하지 않습니다."
            api_request = None
            
        state["crud_result"] = result
        if api_request:
            state["api_request"] = api_request
        
    except Exception as e:
        state["crud_result"] = f"일정 처리 중 오류가 발생했습니다: {str(e)}"
    
    # 에이전트 메시지에 추가
    state.setdefault("agent_messages", []).append({
        "agent": "calendar_agent",
        "input_snapshot": {
            "user_query": user_query,
            "schedule_type": schedule_type,
            "operation": operation,
            "params": params
        },
        "output": state["crud_result"],
        "api_request": state.get("api_request")
    })
    
    return state

def _parse_calendar_intent(user_query: str, schedule_type: str) -> Optional[Dict]:
    """
    LLM을 사용하여 사용자 의도를 파싱하고 작업 매개변수를 추출합니다.
    """
    prompt = f"""
    사용자의 일정 관련 요청을 분석하여 작업 유형과 필요한 매개변수를 추출하세요.
    
    일정 타입: {schedule_type}
    사용자 요청: "{user_query}"
    
    가능한 작업:
    - CREATE: 새 일정 생성
    - READ: 기존 일정 조회
    - UPDATE: 기존 일정 수정
    - DELETE: 기존 일정 삭제
    
    응답은 다음 JSON 형식으로 제공하세요:
    {{
        "operation": "CREATE|READ|UPDATE|DELETE",
        "params": {{
            "summary": "일정 제목",
            "location": "장소 (선택사항)",
            "description": "설명 (선택사항)",
            "start_time": "시작 시간 (YYYY-MM-DD HH:MM 형식)",
            "end_time": "종료 시간 (YYYY-MM-DD HH:MM 형식)",
            "search_criteria": "검색 조건 (READ/UPDATE/DELETE용)"
        }}
    }}
    
    분석 결과만 JSON으로 출력하세요.
    """
    
    try:
        response = model.invoke(prompt)
        result = json.loads(response.content.strip())
        return result
    except Exception as e:
        print(f"의도 파싱 오류: {e}")
        return None

def _handle_calendar_event(operation: str, params: Dict, cal_agent: CalendarAgent) -> tuple[str, Dict]:
    """
    캘린더 이벤트 작업을 처리하고 백엔드를 위한 API request body를 생성합니다.
    """
    calendar_id = cal_agent._get_calendar_id()
    
    if operation == "CREATE":
        return _create_calendar_event(params, calendar_id)
    elif operation == "READ":
        return _read_calendar_event(params, calendar_id)
    elif operation == "UPDATE":
        return _update_calendar_event(params, calendar_id)
    elif operation == "DELETE":
        return _delete_calendar_event(params, calendar_id)
    else:
        return "지원하지 않는 작업입니다.", {}

def _create_calendar_event(params: Dict, calendar_id: str) -> tuple[str, Dict]:
    """
    새 캘린더 이벤트를 생성하고 백엔드를 위한 API request body를 생성합니다.
    """
    try:
        # Google Calendar API 형식에 맞게 이벤트 데이터를 준비합니다
        event_data = {
            "summary": params.get("summary", "새 일정"),
            "location": params.get("location", ""),
            "description": params.get("description", ""),
            "start": {
                "dateTime": params.get("start_time"),
                "timeZone": "Asia/Seoul"
            },
            "end": {
                "dateTime": params.get("end_time"),
                "timeZone": "Asia/Seoul"
            }
        }
        
        # 백엔드 팀을 위한 API request body 생성
        api_request = {
            "api_type": "google_calendar",
            "operation": "events.insert",
            "calendar_id": calendar_id,
            "request_body": event_data,
            "http_method": "POST",
            "endpoint": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        }
        
        result = f"일정이 성공적으로 생성되었습니다.\n제목: {event_data['summary']}\n시간: {params.get('start_time')} ~ {params.get('end_time')}\n장소: {event_data['location']}"
        
        return result, api_request
        
    except Exception as e:
        return f"일정 생성 중 오류가 발생했습니다: {str(e)}", {}

def _read_calendar_event(params: Dict, calendar_id: str) -> tuple[str, Dict]:
    """
    검색 조건에 따라 캘린더 이벤트를 조회하고 백엔드를 위한 API request body를 생성합니다.
    """
    try:
        search_criteria = params.get("search_criteria", "")
        
        # 백엔드 팀을 위한 API request body 생성
        api_request = {
            "api_type": "google_calendar",
            "operation": "events.list",
            "calendar_id": calendar_id,
            "query_params": {
                "q": search_criteria,
                "singleEvents": True,
                "orderBy": "startTime"
            },
            "http_method": "GET",
            "endpoint": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        }
        
        result = f"'{search_criteria}' 관련 일정을 검색했습니다."
        
        return result, api_request
        
    except Exception as e:
        return f"일정 조회 중 오류가 발생했습니다: {str(e)}", {}

def _update_calendar_event(params: Dict, calendar_id: str) -> tuple[str, Dict]:
    """
    기존 캘린더 이벤트를 수정하고 백엔드를 위한 API request body를 생성합니다.
    """
    try:
        search_criteria = params.get("search_criteria", "")
        
        # 수정할 데이터 준비
        update_data = {
            "summary": params.get("summary"),
            "location": params.get("location"),
            "description": params.get("description")
        }
        
        # 백엔드 팀을 위한 API request body 생성
        # 1단계: 이벤트 검색
        search_request = {
            "api_type": "google_calendar",
            "operation": "events.list",
            "calendar_id": calendar_id,
            "query_params": {
                "q": search_criteria
            },
            "http_method": "GET",
            "endpoint": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            "step": "search_event"
        }
        
        # 2단계: 이벤트 수정 (event_id는 백엔드에서 검색 결과에서 추출)
        update_request = {
            "api_type": "google_calendar",
            "operation": "events.patch",
            "calendar_id": calendar_id,
            "event_id": "{{event_id_from_search}}",  # 백엔드에서 검색 결과에서 추출
            "request_body": update_data,
            "http_method": "PATCH",
            "endpoint": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{{event_id_from_search}}",
            "step": "update_event",
            "depends_on": "search_event"
        }
        
        api_request = {
            "multi_step": True,
            "steps": [search_request, update_request]
        }
        
        result = f"'{search_criteria}' 일정이 성공적으로 수정되었습니다."
        
        return result, api_request
        
    except Exception as e:
        return f"일정 수정 중 오류가 발생했습니다: {str(e)}", {}

def _delete_calendar_event(params: Dict, calendar_id: str) -> tuple[str, Dict]:
    """
    캘린더 이벤트를 삭제하고 백엔드를 위한 API request body를 생성합니다.
    """
    try:
        search_criteria = params.get("search_criteria", "")
        
        # 백엔드 팀을 위한 API request body 생성
        # 1단계: 이벤트 검색
        search_request = {
            "api_type": "google_calendar",
            "operation": "events.list",
            "calendar_id": calendar_id,
            "query_params": {
                "q": search_criteria
            },
            "http_method": "GET",
            "endpoint": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            "step": "search_event"
        }
        
        # 2단계: 이벤트 삭제 (event_id는 백엔드에서 검색 결과에서 추출)
        delete_request = {
            "api_type": "google_calendar",
            "operation": "events.delete",
            "calendar_id": calendar_id,
            "event_id": "{{event_id_from_search}}",  # 백엔드에서 검색 결과에서 추출
            "http_method": "DELETE",
            "endpoint": f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{{event_id_from_search}}",
            "step": "delete_event",
            "depends_on": "search_event"
        }
        
        api_request = {
            "multi_step": True,
            "steps": [search_request, delete_request]
        }
        
        result = f"'{search_criteria}' 일정이 성공적으로 삭제되었습니다."
        
        return result, api_request
        
    except Exception as e:
        return f"일정 삭제 중 오류가 발생했습니다: {str(e)}", {}

def _handle_task(operation: str, params: Dict, cal_agent: CalendarAgent) -> tuple[str, Dict]:
    """
    작업 관련 작업을 처리하고 백엔드를 위한 API request body를 생성합니다.
    """
    tasklist_id = cal_agent._get_tasklist_id()
    
    if operation == "CREATE":
        return _create_task(params, tasklist_id)
    elif operation == "READ":
        return _read_task(params, tasklist_id)
    elif operation == "UPDATE":
        return _update_task(params, tasklist_id)
    elif operation == "DELETE":
        return _delete_task(params, tasklist_id)
    else:
        return "지원하지 않는 작업입니다.", {}

def _create_task(params: Dict, tasklist_id: str) -> tuple[str, Dict]:
    """
    새 작업을 생성하고 백엔드를 위한 API request body를 생성합니다.
    """
    try:
        task_data = {
            "title": params.get("summary", "새 할 일"),
            "notes": params.get("description", ""),
            "due": params.get("end_time")  # 작업은 end_time을 마감일로 사용합니다
        }
        
        # 백엔드 팀을 위한 API request body 생성
        api_request = {
            "api_type": "google_tasks",
            "operation": "tasks.insert",
            "tasklist_id": tasklist_id,
            "request_body": task_data,
            "http_method": "POST",
            "endpoint": f"https://www.googleapis.com/tasks/v1/lists/{tasklist_id}/tasks"
        }
        
        result = f"할 일이 성공적으로 생성되었습니다.\n제목: {task_data['title']}\n마감일: {params.get('end_time')}\n메모: {task_data['notes']}"
        
        return result, api_request
        
    except Exception as e:
        return f"할 일 생성 중 오류가 발생했습니다: {str(e)}", {}

def _read_task(params: Dict, tasklist_id: str) -> tuple[str, Dict]:
    """
    검색 조건에 따라 작업을 조회하고 백엔드를 위한 API request body를 생성합니다.
    """
    try:
        search_criteria = params.get("search_criteria", "")
        
        # 백엔드 팀을 위한 API request body 생성
        api_request = {
            "api_type": "google_tasks",
            "operation": "tasks.list",
            "tasklist_id": tasklist_id,
            "query_params": {
                "q": search_criteria
            },
            "http_method": "GET",
            "endpoint": f"https://www.googleapis.com/tasks/v1/lists/{tasklist_id}/tasks"
        }
        
        result = f"'{search_criteria}' 관련 할 일을 검색했습니다."
        
        return result, api_request
        
    except Exception as e:
        return f"할 일 조회 중 오류가 발생했습니다: {str(e)}", {}

def _update_task(params: Dict, tasklist_id: str) -> tuple[str, Dict]:
    """
    기존 작업을 수정하고 백엔드를 위한 API request body를 생성합니다.
    """
    try:
        search_criteria = params.get("search_criteria", "")
        
        # 수정할 데이터 준비
        update_data = {
            "title": params.get("summary"),
            "notes": params.get("description")
        }
        
        # 백엔드 팀을 위한 API request body 생성
        # 1단계: 작업 검색
        search_request = {
            "api_type": "google_tasks",
            "operation": "tasks.list",
            "tasklist_id": tasklist_id,
            "query_params": {
                "q": search_criteria
            },
            "http_method": "GET",
            "endpoint": f"https://www.googleapis.com/tasks/v1/lists/{tasklist_id}/tasks",
            "step": "search_task"
        }
        
        # 2단계: 작업 수정 (task_id는 백엔드에서 검색 결과에서 추출)
        update_request = {
            "api_type": "google_tasks",
            "operation": "tasks.patch",
            "tasklist_id": tasklist_id,
            "task_id": "{{task_id_from_search}}",  # 백엔드에서 검색 결과에서 추출
            "request_body": update_data,
            "http_method": "PATCH",
            "endpoint": f"https://www.googleapis.com/tasks/v1/lists/{tasklist_id}/tasks/{{task_id_from_search}}",
            "step": "update_task",
            "depends_on": "search_task"
        }
        
        api_request = {
            "multi_step": True,
            "steps": [search_request, update_request]
        }
        
        result = f"'{search_criteria}' 할 일이 성공적으로 수정되었습니다."
        
        return result, api_request
        
    except Exception as e:
        return f"할 일 수정 중 오류가 발생했습니다: {str(e)}", {}

def _delete_task(params: Dict, tasklist_id: str) -> tuple[str, Dict]:
    """
    작업을 삭제하고 백엔드를 위한 API request body를 생성합니다.
    """
    try:
        search_criteria = params.get("search_criteria", "")
        
        # 백엔드 팀을 위한 API request body 생성
        # 1단계: 작업 검색
        search_request = {
            "api_type": "google_tasks",
            "operation": "tasks.list",
            "tasklist_id": tasklist_id,
            "query_params": {
                "q": search_criteria
            },
            "http_method": "GET",
            "endpoint": f"https://www.googleapis.com/tasks/v1/lists/{tasklist_id}/tasks",
            "step": "search_task"
        }
        
        # 2단계: 작업 삭제 (task_id는 백엔드에서 검색 결과에서 추출)
        delete_request = {
            "api_type": "google_tasks",
            "operation": "tasks.delete",
            "tasklist_id": tasklist_id,
            "task_id": "{{task_id_from_search}}",  # 백엔드에서 검색 결과에서 추출
            "http_method": "DELETE",
            "endpoint": f"https://www.googleapis.com/tasks/v1/lists/{tasklist_id}/tasks/{{task_id_from_search}}",
            "step": "delete_task",
            "depends_on": "search_task"
        }
        
        api_request = {
            "multi_step": True,
            "steps": [search_request, delete_request]
        }
        
        result = f"'{search_criteria}' 할 일이 성공적으로 삭제되었습니다."
        
        return result, api_request
        
    except Exception as e:
        return f"할 일 삭제 중 오류가 발생했습니다: {str(e)}", {}