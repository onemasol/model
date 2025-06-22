from typing import Dict, Optional
import json
from datetime import datetime, timedelta
import re

def calc(state: Dict) -> Dict:
    """
    calendar_agent에서 받은 정보를 바탕으로 Google Calendar API 호출을 위한 payload를 생성합니다.
    
    state에서 사용하는 정보:
    - calendar_type: "event" 또는 "task"
    - calendar_operation: "create", "read", "update", "delete"
    - extracted_info: {"title": "...", "dateTime": "...", "date": "..."}
    - next_node: "CalC" 또는 "CalRUD"
    """
    
    try:
        # calendar_agent에서 분류한 정보 가져오기
        calendar_type = state.get("calendar_type", "event")
        calendar_operation = state.get("calendar_operation", "read")
        extracted_info = state.get("extracted_info", {})
        next_node = state.get("next_node", "CalRUD")
        
        print(f"=== CalC Payload 생성 ===")
        print(f"타입: {calendar_type}")
        print(f"작업: {calendar_operation}")
        print(f"추출된 정보: {extracted_info}")
        print(f"다음 노드: {next_node}")
        
        # Google Calendar API 페이로드 생성
        payload = create_google_calendar_payload(calendar_type, calendar_operation, extracted_info)
        state["calendar_payload"] = payload
        state["crud_result"] = f"Google Calendar {calendar_operation} payload가 생성되었습니다: {json.dumps(payload, ensure_ascii=False, indent=2)}"
        
        # 로그 기록
        state.setdefault("agent_messages", []).append({
            "agent": "calc",
            "payload": payload,
            "operation": calendar_operation,
            "type": calendar_type
        })
        
    except Exception as e:
        error_msg = f"CalC 오류: {str(e)}"
        state["crud_result"] = error_msg
        state.setdefault("agent_messages", []).append({
            "agent": "calc",
            "error": str(e)
        })
    
    return state

def create_google_calendar_payload(calendar_type: str, operation: str, extracted_info: Dict) -> Dict:
    """
    Google Calendar API 호출을 위한 payload를 생성합니다.
    
    Args:
        calendar_type: "event" 또는 "task"
        operation: "create", "read", "update", "delete"
        extracted_info: calendar_agent에서 추출한 정보
        
    Returns:
        Google Calendar API 형식의 페이로드
    """
    
    title = extracted_info.get("title", "")
    date_time = extracted_info.get("dateTime", "")
    date = extracted_info.get("date", "")
    
    # 기본 페이로드 구조
    payload = {
        "summary": title,  # 이벤트 제목
        "description": "",  # 이벤트 설명 (선택사항)
        "location": "",     # 위치 (선택사항)
        "start": {},
        "end": {},
        "reminders": {
            "useDefault": True
        }
    }
    
    # 시작/종료 시간 설정
    if date_time:
        # 시간이 있는 경우 (특정 시간 일정)
        start_time = date_time
        end_time = calculate_end_time(date_time)  # 기본 1시간 후
        
        payload["start"] = {
            "dateTime": start_time,
            "timeZone": "Asia/Seoul"
        }
        payload["end"] = {
            "dateTime": end_time,
            "timeZone": "Asia/Seoul"
        }
    elif date:
        # 시간이 없는 경우 (종일 일정)
        payload["start"] = {
            "date": date,
            "timeZone": "Asia/Seoul"
        }
        payload["end"] = {
            "date": date,
            "timeZone": "Asia/Seoul"
        }
    else:
        # 날짜/시간 정보가 없는 경우 오늘로 설정
        today = datetime.now().strftime("%Y-%m-%d")
        payload["start"] = {
            "date": today,
            "timeZone": "Asia/Seoul"
        }
        payload["end"] = {
            "date": today,
            "timeZone": "Asia/Seoul"
        }
    
    # 작업 유형에 따른 추가 설정
    if operation == "create":
        # 생성 작업의 경우 기본 설정 유지
        pass
    elif operation == "update":
        # 업데이트 작업의 경우 etag나 id가 필요할 수 있음
        payload["update_required"] = True
    elif operation == "delete":
        # 삭제 작업의 경우 id가 필요
        payload["delete_required"] = True
    elif operation == "read":
        # 조회 작업의 경우 필터 조건
        payload["query_params"] = {
            "timeMin": payload["start"].get("dateTime") or payload["start"].get("date"),
            "timeMax": payload["end"].get("dateTime") or payload["end"].get("date"),
            "singleEvents": True,
            "orderBy": "startTime"
        }
    
    return payload

def calculate_end_time(start_time: str, duration_hours: int = 1) -> str:
    """
    시작 시간으로부터 종료 시간을 계산합니다.
    
    Args:
        start_time: RFC3339 형식의 시작 시간
        duration_hours: 지속 시간 (시간 단위, 기본값: 1시간)
        
    Returns:
        RFC3339 형식의 종료 시간
    """
    try:
        # RFC3339 형식 파싱 (예: "2024-01-16T14:00:00+09:00")
        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = dt + timedelta(hours=duration_hours)
        return end_dt.isoformat()
    except:
        # 파싱 실패시 기본값 반환
        return start_time

def parse_date_time(date_str: str, time_str: str) -> tuple[Optional[str], Optional[str]]:
    """
    한국어 날짜/시간 문자열을 파싱합니다.
    """
    parsed_date = None
    parsed_time = None
    
    # 날짜 파싱
    if date_str:
        parsed_date = parse_korean_date(date_str)
    
    # 시간 파싱
    if time_str:
        parsed_time = parse_korean_time(time_str)
    
    return parsed_date, parsed_time

def parse_korean_date(date_str: str) -> Optional[str]:
    """
    한국어 날짜 표현을 ISO 형식으로 변환합니다.
    """
    today = datetime.now()
    
    # "내일", "모레" 등 상대적 표현 처리
    if "내일" in date_str:
        target_date = today + timedelta(days=1)
    elif "모레" in date_str:
        target_date = today + timedelta(days=2)
    elif "어제" in date_str:
        target_date = today - timedelta(days=1)
    elif "오늘" in date_str:
        target_date = today
    elif "이번 주" in date_str:
        # 이번 주 월요일
        days_since_monday = today.weekday()
        target_date = today - timedelta(days=days_since_monday)
    elif "다음 주" in date_str:
        # 다음 주 월요일
        days_since_monday = today.weekday()
        target_date = today - timedelta(days=days_since_monday) + timedelta(days=7)
    else:
        # 구체적인 날짜가 있는 경우 (예: "12월 25일")
        try:
            # 월/일 패턴 찾기
            month_day_pattern = r'(\d+)월\s*(\d+)일'
            match = re.search(month_day_pattern, date_str)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                year = today.year
                
                # 과거 월인 경우 다음 해로 설정
                if month < today.month:
                    year += 1
                
                target_date = datetime(year, month, day)
            else:
                return None
        except:
            return None
    
    return target_date.strftime("%Y-%m-%d")

def parse_korean_time(time_str: str) -> Optional[str]:
    """
    한국어 시간 표현을 24시간 형식으로 변환합니다.
    """
    if not time_str or time_str in ["", "전체", "null"]:
        return None
    
    # "오전", "오후" 처리
    is_pm = "오후" in time_str or "PM" in time_str.upper()
    is_am = "오전" in time_str or "AM" in time_str.upper()
    
    # 시간 추출
    time_pattern = r'(\d+)시'
    match = re.search(time_pattern, time_str)
    
    if match:
        hour = int(match.group(1))
        
        # 오후인 경우 12를 더함 (12시는 제외)
        if is_pm and hour != 12:
            hour += 12
        # 오전 12시는 0시로 변환
        elif is_am and hour == 12:
            hour = 0
        
        return f"{hour:02d}:00"
    
    return None
