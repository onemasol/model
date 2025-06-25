from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

def get_calendar_id_from_query(user_query: str, available_calendars: List[Dict[str, Any]]) -> str:
    """사용자 질의와 사용 가능한 캘린더 목록에서 적절한 캘린더 ID 선택"""
    if not available_calendars:
        return 'primary'
    
    # 기본 캘린더가 있으면 우선 사용
    for cal in available_calendars:
        if cal.get('primary', False):
            return cal['id']
    
    # 질의에서 캘린더 이름 매칭
    query_lower = user_query.lower()
    for cal in available_calendars:
        if cal.get('summary', '').lower() in query_lower:
            return cal['id']
    
    # 매칭되는 것이 없으면 첫 번째 캘린더 사용
    return available_calendars[0]['id']

def get_task_list_id_from_query(user_query: str, available_task_lists: List[Dict[str, Any]]) -> str:
    """사용자 질의와 사용 가능한 할일 목록에서 적절한 할일 목록 ID 선택"""
    if not available_task_lists:
        return '@default'
    
    # 기본 할일 목록이 있으면 우선 사용
    for task_list in available_task_lists:
        if task_list.get('title', '').lower() in ['my tasks', '내 할일', '기본']:
            return task_list['id']
    
    # 질의에서 할일 목록 이름 매칭
    query_lower = user_query.lower()
    for task_list in available_task_lists:
        if task_list.get('title', '').lower() in query_lower:
            return task_list['id']
    
    # 매칭되는 것이 없으면 첫 번째 할일 목록 사용
    return available_task_lists[0]['id']

def prepare_calendar_event_request_body(event_data: Dict[str, Any], calendar_id: str = 'primary') -> Dict[str, Any]:
    """Google Calendar API 이벤트 생성/수정 요청 본문 준비"""
    body: Dict[str, Any] = {
        'title': event_data.get('title', '새 일정'),
        'start': event_data.get('start', {
            'dateTime': datetime.now().isoformat(),
            'timeZone': 'Asia/Seoul'
        }),
        'end': event_data.get('end', {
            'dateTime': (datetime.now() + timedelta(hours=1)).isoformat(),
            'timeZone': 'Asia/Seoul'
        })
    }
    
    # 선택적 필드 추가
    if event_data.get('location'):
        body['location'] = event_data['location']
    
    if event_data.get('description'):
        body['description'] = event_data['description']
    
    return {
        'calendarId': calendar_id,
        'body': body
    }

def prepare_calendar_event_list_request_body(
    calendar_id: str = 'primary',
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """Google Calendar API 이벤트 목록 조회 요청 본문 준비"""
    if not time_min:
        time_min = datetime.utcnow().isoformat() + 'Z'
    if not time_max:
        time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
    
    return {
        'calendarId': calendar_id,
        'timeMin': time_min,
        'timeMax': time_max,
        'maxResults': max_results,
        'singleEvents': True,
        'orderBy': 'startTime'
    }

def prepare_calendar_event_get_request_body(calendar_id: str, event_id: str) -> Dict[str, Any]:
    """Google Calendar API 이벤트 조회 요청 본문 준비"""
    return {
        'calendarId': calendar_id,
        'eventId': event_id
    }

def prepare_calendar_event_update_request_body(
    calendar_id: str,
    event_id: str,
    event_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Google Calendar API 이벤트 수정 요청 본문 준비"""
    request_body = prepare_calendar_event_request_body(event_data, calendar_id)
    request_body['eventId'] = event_id
    return request_body

def prepare_calendar_event_delete_request_body(calendar_id: str, event_id: str) -> Dict[str, Any]:
    """Google Calendar API 이벤트 삭제 요청 본문 준비"""
    return {
        'calendarId': calendar_id,
        'eventId': event_id
    }

def prepare_tasks_request_body(task_data: Dict[str, Any], task_list_id: str = '@default') -> Dict[str, Any]:
    """Google Tasks API 할일 생성/수정 요청 본문 준비"""
    body: Dict[str, Any] = {
        'title': task_data.get('title', '새 할일')
    }
    
    # 선택적 필드 추가
    if task_data.get('notes'):
        body['notes'] = task_data['notes']
    
    if task_data.get('due'):
        body['due'] = task_data['due']
    
    return {
        'tasklist': task_list_id,
        'body': body
    }

def prepare_tasks_list_request_body(task_list_id: str = '@default', max_results: int = 100) -> Dict[str, Any]:
    """Google Tasks API 할일 목록 조회 요청 본문 준비"""
    return {
        'tasklist': task_list_id,
        'maxResults': max_results
    }

def prepare_tasks_get_request_body(task_list_id: str, task_id: str) -> Dict[str, Any]:
    """Google Tasks API 할일 조회 요청 본문 준비"""
    return {
        'tasklist': task_list_id,
        'task': task_id
    }

def prepare_tasks_update_request_body(
    task_list_id: str,
    task_id: str,
    task_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Google Tasks API 할일 수정 요청 본문 준비"""
    request_body = prepare_tasks_request_body(task_data, task_list_id)
    request_body['task'] = task_id
    return request_body

def prepare_tasks_delete_request_body(task_list_id: str, task_id: str) -> Dict[str, Any]:
    """Google Tasks API 할일 삭제 요청 본문 준비"""
    return {
        'tasklist': task_list_id,
        'task': task_id
    }

def create_api_request_from_payload(
    payload: Dict[str, Any], 
    available_calendars: Optional[List[Dict[str, Any]]] = None, 
    available_task_lists: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """페이로드로부터 실제 API 요청 본문 생성"""
    intent = payload.get('intent', '')
    operation = payload.get('operation', 'read')
    type_ = payload.get('type', 'event')
    user_query = payload.get('user_query', '')
    
    request_body: Dict[str, Any] = {
        'api_type': 'google_calendar' if type_ == 'event' else 'google_tasks',
        'operation': operation,
        'intent': intent
    }
    
    if type_ == 'event':
        # 캘린더 ID 결정
        calendar_id = get_calendar_id_from_query(user_query, available_calendars or [])
        
        if operation == 'create':
            event_data = payload.get('event_data', {})
            request_body.update(prepare_calendar_event_request_body(event_data, calendar_id))
        
        elif operation == 'read':
            query_params = payload.get('query_params', {})
            request_body.update(prepare_calendar_event_list_request_body(
                calendar_id=calendar_id,
                time_min=query_params.get('time_min'),
                time_max=query_params.get('time_max'),
                max_results=query_params.get('max_results', 10)
            ))
        
        elif operation == 'update':
            # 수정을 위해서는 event_id가 필요
            request_body['error'] = '일정 수정을 위해서는 event_id가 필요합니다.'
        
        elif operation == 'delete':
            # 삭제를 위해서는 event_id가 필요
            request_body['error'] = '일정 삭제를 위해서는 event_id가 필요합니다.'
    
    elif type_ == 'task':
        # 할일 목록 ID 결정
        task_list_id = get_task_list_id_from_query(user_query, available_task_lists or [])
        
        if operation == 'create':
            task_data = payload.get('task_data', {})
            request_body.update(prepare_tasks_request_body(task_data, task_list_id))
        
        elif operation == 'read':
            request_body.update(prepare_tasks_list_request_body(task_list_id))
        
        elif operation == 'update':
            # 수정을 위해서는 task_id가 필요
            request_body['error'] = '할일 수정을 위해서는 task_id가 필요합니다.'
        
        elif operation == 'delete':
            # 삭제를 위해서는 task_id가 필요
            request_body['error'] = '할일 삭제를 위해서는 task_id가 필요합니다.'
    
    return request_body 