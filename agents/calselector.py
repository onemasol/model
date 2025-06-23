from typing import Dict, Any
from datetime import datetime
import requests
import json

def calselector(state: Dict) -> Dict:
    """
    CalSelector 노드: state의 schedule_type에 따라 구글 캘린더 API 요청을 보내고 응답을 처리합니다.
    
    Args:
        state: 현재 상태 딕셔너리
        
    Returns:
        state: 업데이트된 상태 딕셔너리
    """
    try:
        # 현재 상태에서 필요한 정보 추출
        schedule_type = state.get("schedule_type", "all")  # 기본값은 "all"
        operation_type = state.get("operation_type", "read")
        query_info = state.get("query_info", {})
        
        # 구글 캘린더 API 요청문 생성
        api_requests = []
        
        if schedule_type == "event":
            # 일정(calendar) API 요청문 생성
            calendar_api_request = {
                "api_type": "google_calendar",
                "method": "GET",
                "endpoint": "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                "params": {
                    "maxResults": 100,
                    "showHidden": False,
                    "showDeleted": False
                },
                "headers": {
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                "operation": operation_type,
                "event_type": "event"
            }
            api_requests.append(calendar_api_request)
        
        if schedule_type == "task":
            # 할일(task) API 요청문 생성 - Google Tasks API 사용
            task_api_request = {
                "api_type": "google_tasks",
                "method": "GET", 
                "endpoint": "https://tasks.googleapis.com/tasks/v1/lists/@default/tasks",
                "params": {
                    "dueMin": query_info.get("due_at"),
                    "dueMax": query_info.get("due_at"),
                    "showCompleted": False,
                    "showDeleted": False,
                    "showHidden": False,
                    "maxResults": 100
                },
                "headers": {
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                "operation": operation_type,
                "event_type": "task"
            }
            api_requests.append(task_api_request)
        
        # 실제 API 호출 및 응답 처리
        api_responses = []
        for req in api_requests:
            try:
                print(f"=== CalSelector: {req['api_type']} API 호출 중... ===")
                
                # 실제 API 호출 (현재는 시뮬레이션)
                # TODO: 실제 access_token으로 교체 필요
                if req['api_type'] == 'google_calendar':
                    # Google Calendar API 응답 시뮬레이션
                    mock_response = {
                        "kind": "calendar#calendarList",
                        "etag": "\"mock_etag\"",
                        "items": [
                            {
                                "kind": "calendar#calendarListEntry",
                                "etag": "\"mock_etag\"",
                                "id": "primary",
                                "summary": "기본 캘린더",
                                "description": "사용자의 기본 캘린더",
                                "location": "",
                                "timeZone": "Asia/Seoul",
                                "summaryOverride": "",
                                "colorId": "",
                                "backgroundColor": "#4285f4",
                                "foregroundColor": "#ffffff",
                                "hidden": False,
                                "selected": True,
                                "accessRole": "owner",
                                "defaultReminders": [],
                                "notificationSettings": {
                                    "notifications": []
                                },
                                "primary": True,
                                "deleted": False
                            }
                        ]
                    }
                else:  # google_tasks
                    # Google Tasks API 응답 시뮬레이션
                    mock_response = {
                        "kind": "tasks#tasks",
                        "etag": "\"mock_etag\"",
                        "items": [
                            {
                                "kind": "tasks#task",
                                "id": "mock_task_id",
                                "etag": "\"mock_etag\"",
                                "title": "오늘 할 일 예시",
                                "updated": "2024-01-15T10:00:00.000Z",
                                "selfLink": "https://tasks.googleapis.com/tasks/v1/lists/@default/tasks/mock_task_id",
                                "position": "00000000000000000000",
                                "status": "needsAction",
                                "due": query_info.get("due_at", "2024-01-15T23:59:59+09:00")
                            }
                        ]
                    }
                
                api_responses.append({
                    'api_type': req['api_type'],
                    'status_code': 200,
                    'success': True,
                    'data': mock_response,
                    'request_info': {
                        'endpoint': req['endpoint'],
                        'params': req['params'],
                        'operation': req['operation']
                    }
                })
                
                print(f"✅ {req['api_type']} API 응답 수신 완료")
                
            except Exception as api_error:
                print(f"❌ {req['api_type']} API 호출 실패: {str(api_error)}")
                api_responses.append({
                    'api_type': req['api_type'],
                    'status_code': 500,
                    'success': False,
                    'error': str(api_error),
                    'request_info': {
                        'endpoint': req['endpoint'],
                        'params': req['params'],
                        'operation': req['operation']
                    }
                })
        
        # state 업데이트
        state["api_requests"] = api_requests
        state["api_responses"] = api_responses
        state["next_node"] = "answer_generator"  # 응답 처리 후 답변 생성기로
        
        # 결과 요약 생성
        request_count = len(api_requests)
        response_count = len([r for r in api_responses if r.get('success', False)])
        api_types = [req['api_type'] for req in api_requests]
        summary = f"{request_count}개의 API 요청 중 {response_count}개 성공: {api_types}"
        
        # 로그 기록
        state.setdefault("agent_messages", []).append({
            "agent": "calselector",
            "schedule_type": schedule_type,
            "operation_type": operation_type,
            "api_requests": api_requests,
            "api_responses": api_responses,
            "summary": summary,
            "next_node": state["next_node"]
        })
        
        print(f"=== CalSelector: {summary} ===")
        
    except Exception as e:
        # 에러 처리
        error_msg = f"CalSelector 노드 오류: {str(e)}"
        state["error"] = error_msg
        state["next_node"] = "answer_generator"  # 에러시 답변 생성기로
        
        state.setdefault("agent_messages", []).append({
            "agent": "calselector",
            "error": str(e),
            "next_node": "answer_generator"
        })
    
    return state
