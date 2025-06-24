from typing import Dict, Any, List, Union, Optional
from datetime import datetime, timedelta
import json
import os
import re
from difflib import SequenceMatcher
import sys
import requests  # HTTP 요청을 위한 라이브러리 추가

# Google OAuth 유틸리티 import
try:
    from utils.google_auth import get_access_token, refresh_access_token, is_token_valid, exchange_id_token_for_access_token
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    print("⚠️ Google OAuth 유틸리티를 사용할 수 없습니다. 시뮬레이션 모드로 실행됩니다.")

# dotenv import (선택적)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 파일 로드 완료")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다. 환경변수 로딩을 건너뜁니다.")
except Exception as e:
    print(f"⚠️ .env 파일 로드 실패: {e}")

from utils.calendar_api_utils import (
    prepare_calendar_event_request_body,
    prepare_calendar_event_list_request_body,
    prepare_calendar_event_get_request_body
)
from utils.token_refresh import refresh_calendar_token

def get_fallback_data() -> List[Dict[str, Any]]:
    """API 호출 실패시 빈 배열을 반환합니다."""
    return []

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    두 텍스트 간의 유사도를 계산합니다.
    
    Args:
        text1: 첫 번째 텍스트
        text2: 두 번째 텍스트
        
    Returns:
        float: 0.0 ~ 1.0 사이의 유사도 점수
    """
    if not text1 or not text2:
        return 0.0
    
    # 소문자 변환 및 공백 제거
    text1_clean = text1.lower().strip()
    text2_clean = text2.lower().strip()
    
    # SequenceMatcher를 사용한 유사도 계산
    similarity = SequenceMatcher(None, text1_clean, text2_clean).ratio()
    
    # 키워드 매칭 보너스
    words1 = set(text1_clean.split())
    words2 = set(text2_clean.split())
    
    if words1 and words2:
        common_words = words1.intersection(words2)
        keyword_bonus = len(common_words) / max(len(words1), len(words2))
        similarity = max(similarity, keyword_bonus)
    
    return similarity

def calculate_time_similarity(query_time: str, item_time: str) -> float:
    """
    두 시간 간의 유사도를 계산합니다.
    
    Args:
        query_time: 쿼리에서 추출된 시간
        item_time: 항목의 시간
        
    Returns:
        float: 0.0 ~ 1.0 사이의 유사도 점수
    """
    try:
        # ISO 형식 시간을 datetime 객체로 변환
        query_dt = datetime.fromisoformat(query_time.replace('Z', '+00:00'))
        item_dt = datetime.fromisoformat(item_time.replace('Z', '+00:00'))
        
        # 시간 차이 계산 (분 단위)
        time_diff = abs((query_dt - item_dt).total_seconds() / 60)
        
        # 시간 차이에 따른 유사도 점수 계산
        if time_diff <= 60:  # 1시간 이내
            return 1.0
        elif time_diff <= 1440:  # 24시간 이내
            return 0.8
        elif time_diff <= 10080:  # 1주일 이내
            return 0.6
        elif time_diff <= 43200:  # 1개월 이내
            return 0.4
        else:
            return 0.2
            
    except (ValueError, TypeError):
        return 0.0

def calculate_recency_score(created_at: Optional[str]) -> float:
    """
    항목의 최신성을 기반으로 점수를 계산합니다.
    
    Args:
        created_at: 생성 시간
        
    Returns:
        float: 0.0 ~ 1.0 사이의 최신성 점수
    """
    try:
        if not created_at:
            return 0.5  # 기본값
        
        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now()
        
        # 생성된 지 얼마나 되었는지 계산 (일 단위)
        days_old = (now - created_dt).days
        
        if days_old <= 1:  # 1일 이내
            return 1.0
        elif days_old <= 7:  # 1주일 이내
            return 0.8
        elif days_old <= 30:  # 1개월 이내
            return 0.6
        elif days_old <= 90:  # 3개월 이내
            return 0.4
        else:
            return 0.2
            
    except (ValueError, TypeError):
        return 0.5

def calculate_similarity_score(query_info: Dict[str, Any], item: Dict[str, Any]) -> float:
    """
    사용자 쿼리와 항목 간의 종합 유사도 점수를 계산합니다.
    
    Args:
        query_info: 사용자 쿼리 정보
        item: 캘린더 항목
        
    Returns:
        float: 0.0 ~ 1.0 사이의 종합 유사도 점수
    """
    score = 0.0
    
    # 1. 제목 유사도 (가중치: 40%)
    query_title = query_info.get('title', '')
    item_title = item.get('title', '')
    if query_title and item_title:
        title_similarity = calculate_text_similarity(query_title, item_title)
        score += title_similarity * 0.4
    
    # 2. 시간 유사도 (가중치: 30%)
    query_start = query_info.get('start_at')
    item_start = item.get('start_at')
    if query_start and item_start:
        time_similarity = calculate_time_similarity(query_start, item_start)
        score += time_similarity * 0.3
    
    # 3. 타입 매칭 (가중치: 20%)
    query_type = query_info.get('event_type', 'event')
    item_type = 'event' if 'start_at' in item and 'end_at' in item else 'task'
    if query_type == item_type:
        score += 0.2
    
    # 4. 최신성 (가중치: 10%)
    recency_score = calculate_recency_score(item.get('created_at'))
    score += recency_score * 0.1
    
    return score

def select_top_candidates(items: List[Dict[str, Any]], query_info: Dict[str, Any], top_k: int = 3) -> List[str]:
    """
    유사도 점수를 기반으로 Top-K 후보를 선택합니다.
    
    Args:
        items: 모든 항목 리스트
        query_info: 사용자 쿼리 정보
        top_k: 선택할 후보 수
        
    Returns:
        List[str]: 선택된 후보 ID 리스트
    """
    if not items:
        return []
    
    # 각 항목에 대해 유사도 점수 계산
    scored_items = []
    for item in items:
        item_id = item.get('id') or item.get('task_id')
        if item_id:
            similarity_score = calculate_similarity_score(query_info, item)
            scored_items.append({
                'id': item_id,
                'item': item,
                'score': similarity_score
            })
    
    # 점수 기준으로 정렬 (높은 점수 우선)
    scored_items.sort(key=lambda x: x['score'], reverse=True)
    
    # Top-K 선택
    top_candidates = scored_items[:top_k]
    
    # 디버깅을 위한 점수 출력
    print(f"\n🔍 유사도 점수 계산 결과:")
    for i, candidate in enumerate(top_candidates, 1):
        item = candidate['item']
        title = item.get('title', 'N/A')
        score = candidate['score']
        item_type = '이벤트' if 'start_at' in item else '태스크'
        print(f"   {i}. [{item_type}] {title} (점수: {score:.3f})")
    
    return [candidate['id'] for candidate in top_candidates]

def calselector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    CalSelector 노드: 통합 조회 API를 호출하여 Events와 Tasks를 조회하고 응답을 분석합니다.
    
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
        
        # Access token 가져오기
        access_token = None
        
        # 1. state에서 직접 access_token 가져오기
        access_token = state.get("access_token")
        
        # 2. 환경변수에서 access_token 가져오기
        if not access_token:
            access_token = os.getenv("CALENDAR_API_TOKEN")
            if access_token:
                print(f"✅ 환경변수에서 토큰 로드: {access_token[:10]}...")
            else:
                print("⚠️ 환경변수 CALENDAR_API_TOKEN을 찾을 수 없습니다.")
        
        # 3. access_token이 없어도 API 호출 시도 (인증 없이도 작동할 수 있음)
        if access_token:
            print(f"✅ Access token 사용: {access_token[:20]}...")
        else:
            print("⚠️ Access token 없음 - 인증 없이 API 호출 시도")
        
        # 통합 조회 API 요청 생성
        api_request: Dict[str, Any] = {
            "api_type": "calendar_unified",
            "method": "GET",
            "endpoint": "/api/v1/calendar/all",
            "params": {},
            "headers": {
                "Content-Type": "application/json"
            },
            "operation": operation_type,
            "event_type": "all"
        }
        
        # access_token이 있으면 Authorization 헤더 추가
        if access_token:
            api_request["headers"]["Authorization"] = f"Bearer {access_token}"
        
        # 실제 API 호출 및 응답 처리
        api_responses: List[Dict[str, Any]] = []
        rud_candidate_ids: List[str] = []  # RUD를 위한 유사도 기준 Top3 ID 리스트
        
        try:
            print(f"=== CalSelector: 통합 조회 API 호출 중... ===")
            
            # 실제 API 호출
            # 환경 변수에서 API 설정 가져오기
            api_endpoint = os.getenv("CALENDAR_API_ENDPOINT", "http://52.79.95.55:8000/api/v1/calendar/all")
            
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # access_token이 있으면 Authorization 헤더 추가
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            
            print(f"🌐 API 엔드포인트: {api_endpoint}")
            
            try:
                # 실제 HTTP GET 요청 보내기
                response = requests.get(
                    api_endpoint,
                    headers=headers,
                    timeout=10  # 10초 타임아웃
                )
                print(f"📊 응답 상태 코드: {response.status_code}")
                retried = False
                # 401/403이면 토큰 갱신 후 한 번만 재시도
                if response.status_code in (401, 403):
                    print("🔄 토큰 만료 감지, refresh_token으로 갱신 시도...")
                    new_token = refresh_calendar_token()
                    if new_token:
                        print(f"✅ 새 토큰 발급, 재시도 진행")
                        headers["Authorization"] = f"Bearer {new_token}"
                        response = requests.get(
                            api_endpoint,
                            headers=headers,
                            timeout=10
                        )
                        print(f"📊 재시도 응답 상태 코드: {response.status_code}")
                        retried = True
                        # 환경변수에도 갱신
                        os.environ["CALENDAR_API_TOKEN"] = new_token
                        access_token = new_token
                # 이후 기존 분기 유지
                if response.status_code == 200:
                    api_data = response.json()
                    mock_response = api_data
                    print(f"✅ API 호출 성공: {len(mock_response)}개 항목 수신")
                    if mock_response and len(mock_response) > 0:
                        print(f"📋 첫 번째 항목: {mock_response[0].get('title', 'N/A')}")
                    else:
                        print("⚠️ API 응답이 비어있음 - 빈 데이터 사용")
                        mock_response = get_fallback_data()
                elif response.status_code == 403:
                    print("❌ 인증 실패 (403 Forbidden) - 빈 데이터 사용")
                    print(f"   응답 내용: {response.text}")
                    mock_response = get_fallback_data()
                elif response.status_code == 401:
                    print("❌ 인증 실패 (401 Unauthorized) - 빈 데이터 사용")
                    print(f"   응답 내용: {response.text}")
                    mock_response = get_fallback_data()
                elif response.status_code == 404:
                    print("❌ API 엔드포인트를 찾을 수 없음 (404 Not Found) - 빈 데이터 사용")
                    print(f"   응답 내용: {response.text}")
                    mock_response = get_fallback_data()
                else:
                    print(f"⚠️ API 호출 실패 (상태 코드: {response.status_code}), 빈 데이터 사용")
                    print(f"   응답 내용: {response.text}")
                    mock_response = get_fallback_data()
            except requests.exceptions.RequestException as req_error:
                print(f"⚠️ 네트워크 오류: {str(req_error)}, 빈 데이터 사용")
                mock_response = get_fallback_data()
            
            # 응답 분석 및 분류
            events: List[Dict[str, Any]] = []
            tasks: List[Dict[str, Any]] = []
            all_items: List[Dict[str, Any]] = []  # 모든 항목을 하나의 리스트로
            
            for item in mock_response:
                if isinstance(item, dict):
                    all_items.append(item)  # 모든 항목을 추가
                    if "start_at" in item and "end_at" in item:
                        # Event인 경우
                        events.append(item)
                    elif "task_id" in item and "status" in item:
                        # Task인 경우
                        tasks.append(item)
            
            # 유사도 기반 Top3 후보 선택
            if all_items and query_info:
                operation_type = state.get('operation_type', 'read')
                
                if operation_type == "read":
                    # READ 작업: 모든 항목을 후보로 설정
                    print(f"\n📋 READ 작업: 모든 항목을 후보로 설정")
                    for item in all_items:
                        item_id = item.get('id') or item.get('task_id')
                        if item_id:
                            rud_candidate_ids.append(item_id)
                    print(f"   - 총 {len(rud_candidate_ids)}개 항목을 후보로 설정")
                else:
                    # UPDATE/DELETE 작업: 유사도 기반 선택
                    print(f"\n🎯 유사도 기반 후보 선택 중...")
                    print(f"   - 쿼리 정보: {json.dumps(query_info, ensure_ascii=False, indent=2)}")
                    rud_candidate_ids = select_top_candidates(all_items, query_info, top_k=3)
            else:
                # 쿼리 정보가 없거나 항목이 없는 경우 기본 선택
                print(f"\n⚠️ 쿼리 정보가 없어 기본 선택을 사용합니다.")
                for item in all_items:
                    item_id = item.get('id') or item.get('task_id')
                    if item_id:
                        rud_candidate_ids.append(item_id)
                rud_candidate_ids = rud_candidate_ids[:3]
            
            api_responses.append({
                'api_type': 'calendar_unified',
                'status_code': 200,
                'success': True,
                'data': {
                    'events': events,
                    'tasks': tasks,
                    'total_count': len(mock_response),
                    'event_count': len(events),
                    'task_count': len(tasks)
                },
                'request_info': {
                    'endpoint': api_request['endpoint'],
                    'params': api_request['params'],
                    'operation': api_request['operation']
                }
            })
            
            print(f"✅ 통합 조회 API 응답 수신 완료")
            print(f"📊 총 {len(mock_response)}개 항목 (이벤트: {len(events)}개, 태스크: {len(tasks)}개)")
            
        except Exception as api_error:
            print(f"❌ 통합 조회 API 호출 실패: {str(api_error)}")
            api_responses.append({
                'api_type': 'calendar_unified',
                'status_code': 500,
                'success': False,
                'error': str(api_error),
                'request_info': {
                    'endpoint': api_request['endpoint'],
                    'params': api_request['params'],
                    'operation': api_request['operation']
                }
            })
        
        # state 업데이트
        state["api_requests"] = [api_request]
        state["api_responses"] = api_responses
        state["rud_candidate_ids"] = rud_candidate_ids  # RUD를 위한 유사도 기준 Top3 ID 리스트
        
        # 선택된 항목 정보 저장
        if rud_candidate_ids:
            # Top1 후보를 선택된 항목으로 설정
            selected_id = rud_candidate_ids[0]
            state["selected_item_id"] = selected_id
            print(f"\n✅ 선택된 항목 ID: {selected_id}")
        else:
            print(f"\n⚠️ 선택할 후보 항목이 없습니다.")
        
        state["next_node"] = "answer_generator"  # 응답 처리 후 답변 생성기로
        
        # 응답 데이터를 state에 저장
        if api_responses and isinstance(api_responses[0], dict) and api_responses[0].get('success', False):
            response_data = api_responses[0].get('data', {})
            if isinstance(response_data, dict):
                state["unified_calendar_data"] = response_data
                state["events"] = response_data.get('events', [])
                state["tasks"] = response_data.get('tasks', [])
        
        # 결과 요약 생성
        request_count = len([api_request])
        response_count = len([r for r in api_responses if isinstance(r, dict) and r.get('success', False)])
        summary = f"통합 조회 API 요청 {request_count}개 중 {response_count}개 성공"
        
        if response_count > 0 and isinstance(api_responses[0], dict):
            response_data = api_responses[0].get('data', {})
            if isinstance(response_data, dict):
                summary += f" (총 {response_data.get('total_count', 0)}개 항목)"
        
        # 로그 기록
        state.setdefault("agent_messages", []).append({
            "agent": "calselector",
            "schedule_type": schedule_type,
            "operation_type": operation_type,
            "api_requests": [api_request],
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
