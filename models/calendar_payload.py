from typing import TypedDict, Optional, Literal, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# ============================================================================
# Google Calendar API 페이로드 스키마 정의
# ============================================================================

class CalendarEventStart(TypedDict, total=False):
    """이벤트 시작 시간 스키마"""
    dateTime: str  # RFC3339 형식 (예: "2024-01-16T14:00:00+09:00")
    date: str      # YYYY-MM-DD 형식 (종일 일정용)
    timeZone: str  # IANA 시간대 (예: "Asia/Seoul")

class CalendarEventEnd(TypedDict, total=False):
    """이벤트 종료 시간 스키마"""
    dateTime: str  # RFC3339 형식
    date: str      # YYYY-MM-DD 형식
    timeZone: str  # IANA 시간대

class CalendarReminders(TypedDict, total=False):
    """알림 설정 스키마"""
    useDefault: bool
    overrides: list[Dict[str, Any]]

class GoogleCalendarEventPayload(TypedDict, total=False):
    """Google Calendar 이벤트 생성/수정용 페이로드"""
    summary: str                    # 이벤트 제목 (필수)
    description: str                # 이벤트 설명
    location: str                   # 위치
    start: CalendarEventStart       # 시작 시간 (필수)
    end: CalendarEventEnd           # 종료 시간 (필수)
    reminders: CalendarReminders    # 알림 설정
    colorId: str                    # 색상 ID
    transparency: Literal["opaque", "transparent"]  # 시간 차단 여부
    visibility: Literal["default", "public", "private", "confidential"]  # 공개 설정
    attendees: list[Dict[str, Any]] # 참석자 목록
    conferenceData: Dict[str, Any]  # 회의 데이터 (Google Meet 등)

# ============================================================================
# C (Create) - 생성 작업 페이로드
# ============================================================================

class C_Event_Payload(TypedDict):
    """일정 생성용 페이로드 (Event)"""
    operation: Literal["create"]
    type: Literal["event"]
    event_data: GoogleCalendarEventPayload
    user_query: str

class C_Task_Payload(TypedDict):
    """할일 생성용 페이로드 (Task)"""
    operation: Literal["create"]
    type: Literal["task"]
    task_data: Dict[str, Any]  # Google Tasks API 형식
    user_query: str

# ============================================================================
# R (Read) - 조회 작업 페이로드
# ============================================================================

class R_Event_Payload(TypedDict):
    """일정 조회용 페이로드 (Event)"""
    operation: Literal["read"]
    type: Literal["event"]
    query_params: Dict[str, Any]
    user_query: str

class R_Task_Payload(TypedDict):
    """할일 조회용 페이로드 (Task)"""
    operation: Literal["read"]
    type: Literal["task"]
    query_params: Dict[str, Any]
    user_query: str

# ============================================================================
# U (Update) - 수정 작업 페이로드
# ============================================================================

class U_Event_Payload(TypedDict):
    """일정 수정용 페이로드 (Event)"""
    operation: Literal["update"]
    type: Literal["event"]
    event_id: str
    event_data: GoogleCalendarEventPayload
    user_query: str

class U_Task_Payload(TypedDict):
    """할일 수정용 페이로드 (Task)"""
    operation: Literal["update"]
    type: Literal["task"]
    task_id: str
    task_data: Dict[str, Any]
    user_query: str

# ============================================================================
# D (Delete) - 삭제 작업 페이로드
# ============================================================================

class D_Event_Payload(TypedDict):
    """일정 삭제용 페이로드 (Event)"""
    operation: Literal["delete"]
    type: Literal["event"]
    event_id: str
    user_query: str

class D_Task_Payload(TypedDict):
    """할일 삭제용 페이로드 (Task)"""
    operation: Literal["delete"]
    type: Literal["task"]
    task_id: str
    user_query: str

# ============================================================================
# 통합 페이로드 타입
# ============================================================================

CalendarPayload = (
    C_Event_Payload | C_Task_Payload |
    R_Event_Payload | R_Task_Payload |
    U_Event_Payload | U_Task_Payload |
    D_Event_Payload | D_Task_Payload
)

# ============================================================================
# 페이로드 팩토리 함수들
# ============================================================================

@dataclass
class CalendarPayloadFactory:
    """페이로드 생성을 위한 팩토리 클래스"""
    
    @staticmethod
    def create_C_Event_payload(
        title: str,
        start_time: str,
        end_time: Optional[str] = None,
        description: str = "",
        location: str = "",
        timezone: str = "Asia/Seoul",
        user_query: str = ""
    ) -> C_Event_Payload:
        """일정 생성용 페이로드 생성 (Event)"""
        
        # 종료 시간이 없으면 시작 시간 + 1시간으로 설정
        if not end_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(hours=1)
                end_time = end_dt.isoformat()
            except:
                end_time = start_time
        
        event_data: GoogleCalendarEventPayload = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_time,
                "timeZone": timezone
            },
            "end": {
                "dateTime": end_time,
                "timeZone": timezone
            },
            "reminders": {
                "useDefault": True
            }
        }
        
        return {
            "operation": "create",
            "type": "event",
            "event_data": event_data,
            "user_query": user_query
        }
    
    @staticmethod
    def create_C_Task_payload(
        title: str,
        due_date: Optional[str] = None,
        description: str = "",
        user_query: str = ""
    ) -> C_Task_Payload:
        """할일 생성용 페이로드 생성 (Task)"""
        
        task_data = {
            "title": title,
            "notes": description
        }
        
        if due_date:
            task_data["due"] = due_date
        
        return {
            "operation": "create",
            "type": "task",
            "task_data": task_data,
            "user_query": user_query
        }
    
    @staticmethod
    def create_R_Event_payload(
        time_min: str,
        time_max: str,
        max_results: int = 10,
        user_query: str = ""
    ) -> R_Event_Payload:
        """일정 조회용 페이로드 생성 (Event)"""
        
        query_params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        return {
            "operation": "read",
            "type": "event",
            "query_params": query_params,
            "user_query": user_query
        }
    
    @staticmethod
    def create_R_Task_payload(
        max_results: int = 10,
        user_query: str = ""
    ) -> R_Task_Payload:
        """할일 조회용 페이로드 생성 (Task)"""
        
        query_params = {
            "maxResults": max_results,
            "showCompleted": False
        }
        
        return {
            "operation": "read",
            "type": "task",
            "query_params": query_params,
            "user_query": user_query
        }
    
    @staticmethod
    def create_U_Event_payload(
        event_id: str,
        title: str,
        start_time: str,
        end_time: Optional[str] = None,
        description: str = "",
        location: str = "",
        timezone: str = "Asia/Seoul",
        user_query: str = ""
    ) -> U_Event_Payload:
        """일정 수정용 페이로드 생성 (Event)"""
        
        if not end_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(hours=1)
                end_time = end_dt.isoformat()
            except:
                end_time = start_time
        
        event_data: GoogleCalendarEventPayload = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_time,
                "timeZone": timezone
            },
            "end": {
                "dateTime": end_time,
                "timeZone": timezone
            },
            "reminders": {
                "useDefault": True
            }
        }
        
        return {
            "operation": "update",
            "type": "event",
            "event_id": event_id,
            "event_data": event_data,
            "user_query": user_query
        }
    
    @staticmethod
    def create_D_Event_payload(
        event_id: str,
        user_query: str = ""
    ) -> D_Event_Payload:
        """일정 삭제용 페이로드 생성 (Event)"""
        
        return {
            "operation": "delete",
            "type": "event",
            "event_id": event_id,
            "user_query": user_query
        }

# ============================================================================
# 페이로드 검증 함수들
# ============================================================================

def validate_calendar_payload(payload: Dict[str, Any]) -> bool:
    """페이로드 유효성 검증"""
    try:
        operation = payload.get("operation")
        calendar_type = payload.get("type")
        
        if not operation or not calendar_type:
            return False
        
        # 작업별 검증
        if operation == "create":
            if calendar_type == "event":
                event_data = payload.get("event_data", {})
                return "summary" in event_data and "start" in event_data and "end" in event_data
            elif calendar_type == "task":
                task_data = payload.get("task_data", {})
                return "title" in task_data
        
        elif operation == "read":
            return "query_params" in payload
        
        elif operation == "update":
            if calendar_type == "event":
                return "event_id" in payload and "event_data" in payload
            elif calendar_type == "task":
                return "task_id" in payload and "task_data" in payload
        
        elif operation == "delete":
            if calendar_type == "event":
                return "event_id" in payload
            elif calendar_type == "task":
                return "task_id" in payload
        
        return False
        
    except Exception:
        return False

def get_payload_template(operation: str, calendar_type: str) -> Dict[str, Any]:
    """작업별 페이로드 템플릿 반환"""
    
    templates: Dict[str, Dict[str, Any]] = {
        "C_Event": {
            "operation": "create",
            "type": "event",
            "event_data": {
                "summary": "",
                "description": "",
                "location": "",
                "start": {"dateTime": "", "timeZone": "Asia/Seoul"},
                "end": {"dateTime": "", "timeZone": "Asia/Seoul"},
                "reminders": {"useDefault": True}
            },
            "user_query": ""
        },
        "C_Task": {
            "operation": "create",
            "type": "task",
            "task_data": {
                "title": "",
                "notes": "",
                "due": ""
            },
            "user_query": ""
        },
        "R_Event": {
            "operation": "read",
            "type": "event",
            "query_params": {
                "timeMin": "",
                "timeMax": "",
                "maxResults": 10,
                "singleEvents": True,
                "orderBy": "startTime"
            },
            "user_query": ""
        },
        "R_Task": {
            "operation": "read",
            "type": "task",
            "query_params": {
                "maxResults": 10,
                "showCompleted": False
            },
            "user_query": ""
        },
        "U_Event": {
            "operation": "update",
            "type": "event",
            "event_id": "",
            "event_data": {
                "summary": "",
                "description": "",
                "location": "",
                "start": {"dateTime": "", "timeZone": "Asia/Seoul"},
                "end": {"dateTime": "", "timeZone": "Asia/Seoul"},
                "reminders": {"useDefault": True}
            },
            "user_query": ""
        },
        "D_Event": {
            "operation": "delete",
            "type": "event",
            "event_id": "",
            "user_query": ""
        }
    }
    
    template_key = f"{operation}_{calendar_type.capitalize()}"
    return templates.get(template_key, {}) 