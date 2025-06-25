"""
CalSelector Agent

캘린더 API를 호출하여 이벤트와 태스크를 조회하고, 
사용자 쿼리와의 유사도를 기반으로 후보 항목을 선택하는 에이전트입니다.
"""

from typing import Dict, Any, List, Union, Optional
from datetime import datetime, timedelta
import json
import os
import re
from difflib import SequenceMatcher
import sys
import requests
from api.getset import get_current_session_id, get_current_access_token, get_current_user_input, get_current_ocr_result

# Google OAuth 유틸리티 import (프론트에서 건네받아야 함)
try:
    from utils.google_auth import (
        get_access_token, 
        refresh_access_token, 
        is_token_valid, 
        exchange_id_token_for_access_token
    )
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    print("⚠️ Google OAuth 유틸리티를 사용할 수 없습니다. 시뮬레이션 모드로 실행됩니다.")

# # dotenv import (선택적)
# try:
#     from dotenv import load_dotenv
#     load_dotenv()
#     print("✅ .env 파일 로드 완료")
# except ImportError:
#     print("⚠️ python-dotenv가 설치되지 않았습니다. 환경변수 로딩을 건너뜁니다.")
# except Exception as e:
#     print(f"⚠️ .env 파일 로드 실패: {e}")

# # 캘린더 API 유틸리티 import
# try:
#     from utils.calendar_api_utils import (
#         prepare_calendar_event_request_body,
#         prepare_calendar_event_list_request_body,
#         prepare_calendar_event_get_request_body
#     )
# except ImportError as e:
#     print(f"⚠️ 캘린더 API 유틸리티를 불러올 수 없습니다: {e}")

class CandidateSelector:
    """후보 항목 선택을 담당하는 클래스"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도를 계산합니다."""
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
    
    @staticmethod
    def calculate_time_similarity(query_time: str, item_time: str) -> float:
        """두 시간 간의 유사도를 계산합니다."""
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
    
    def calculate_similarity_score(self, query_info: Dict[str, Any], item: Dict[str, Any]) -> float:
        """사용자 쿼리와 항목 간의 종합 유사도 점수를 계산합니다."""
        score = 0.0
        
        # 1. 제목 유사도 (가중치: 60%)
        query_title = query_info.get('title', '')
        item_title = item.get('title', '')
        if query_title and item_title:
            title_similarity = self.calculate_text_similarity(query_title, item_title)
            score += title_similarity * 0.6
        
        # 2. 시간 유사도 (가중치: 40%)
        query_start = query_info.get('start_at')
        item_start = item.get('start_at')
        if query_start and item_start:
            time_similarity = self.calculate_time_similarity(query_start, item_start)
            score += time_similarity * 0.4
        
        return score
    
    def select_top_candidates(self, items: List[Dict[str, Any]], query_info: Dict[str, Any]) -> List[str]:
        """유사도 점수를 기반으로 Top-1 후보를 선택합니다."""
        if not items:
            return []
        
        # 각 항목에 대해 유사도 점수 계산
        scored_items: List[Dict[str, Any]] = []
        for item in items:
            # 항목 타입에 따라 올바른 ID 필드 선택
            item_id = self._get_appropriate_id_for_item(item)
            
            if item_id:
                similarity_score = self.calculate_similarity_score(query_info, item)
                scored_items.append({
                    'id': item_id,
                    'item': item,
                    'score': similarity_score
                })
        
        # 점수 기준으로 정렬 (높은 점수 우선)
        scored_items.sort(key=lambda x: float(x['score']), reverse=True)
        
        # Top-1 선택
        top_candidate = scored_items[0] if scored_items else None
        
        # 디버깅을 위한 점수 출력
        if top_candidate:
            self._print_candidate_scores([top_candidate])
            return [str(top_candidate['id'])]
        else:
            print(f"\n🔍 유사도 점수 계산 결과: 후보 없음")
            return []
    
    def _get_appropriate_id_for_item(self, item: Dict[str, Any]) -> Optional[str]:
        """항목 타입에 따라 적절한 ID 필드를 반환합니다.
        
        Returns:
            - event 항목: 'id' 필드 사용
            - task 항목: 'task_id' 필드 사용
        """
        # 이벤트인지 태스크인지 판단
        is_event = 'start_at' in item and 'end_at' in item
        is_task = 'task_id' in item or item.get('event_type') == 'task'
        
        if is_task:
            # task 항목: task_id 필드 사용
            task_id = item.get('task_id')
            if task_id:
                print(f"   - task 항목: task_id 필드 사용 - {task_id}")
                return task_id
            else:
                print(f"   - ⚠️ task 항목이지만 task_id 필드가 없음")
                return None
        elif is_event:
            # event 항목: id 필드 사용
            event_id = item.get('id')
            if event_id:
                print(f"   - event 항목: id 필드 사용 - {event_id}")
                return event_id
            else:
                print(f"   - ⚠️ event 항목이지만 id 필드가 없음")
                return None
        else:
            # 타입을 판단할 수 없는 경우
            print(f"   - ⚠️ 항목 타입을 판단할 수 없음")
            print(f"   - item keys: {list(item.keys())}")
            return None
    
    def _print_candidate_scores(self, candidates: List[Dict[str, Any]]) -> None:
        """후보 점수를 출력합니다."""
        print(f"\n🔍 유사도 점수 계산 결과:")
        for i, candidate in enumerate(candidates, 1):
            item = candidate['item']
            title = item.get('title', 'N/A')
            score = candidate['score']
            item_type = '이벤트' if 'start_at' in item else '태스크'
            print(f"   {i}. [{item_type}] {title} (점수: {score:.3f})")


class CalendarAPIClient:
    """캘린더 API 호출을 담당하는 클래스"""
    
    def __init__(self):
        self.base_url = "http://52.79.95.55:8000"
        self.timeout = 10
    
    def get_access_token(self, state: Dict[str, Any]) -> Optional[str]:
        """액세스 토큰을 가져옵니다."""
        access_token = get_current_access_token()
        return access_token
    
    def get_user_id(self, state: Dict[str, Any]) -> str:
        """사용자 ID를 가져옵니다."""
        # 1. state에서 user_id 가져오기
        user_id = "4a728952-53a0-4abe-ae8c-0ff440d6585e"
        return user_id
    
    def create_headers(self, access_token: Optional[str]) -> Dict[str, str]:
        """API 요청 헤더를 생성합니다."""
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
            print(f"✅ Access token 사용: {access_token[:20]}...")
        else:
            print("⚠️ Access token 없음 - 인증 없이 API 호출 시도")
        
        return headers
    
    def call_api(self, headers: Dict[str, str], user_id: str) -> Dict[str, Any]:
        """캘린더 API를 호출합니다."""
        api_endpoint = f"{self.base_url}/api/v1/calendar/all"
        
        try:
            print(f"🌐 API 호출 테스트 시작...")
            print(f"   - URL: {api_endpoint}")
            print(f"   - Headers: {headers}")
            print(f"   - User ID: {user_id}")
            
            response = requests.get(
                api_endpoint,
                headers=headers,
                timeout=self.timeout
            )
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            print(f"📋 응답 헤더: {dict(response.headers)}")
            print(f"📄 응답 내용: {response.text}")
            
            if response.status_code == 200:
                api_data = response.json()
                print(f"✅ API 호출 성공: {len(api_data)}개 항목 수신")
                if api_data and len(api_data) > 0:
                    print(f"📋 첫 번째 항목: {api_data[0]}")
                return {"success": True, "data": api_data}
            else:
                print(f"❌ API 호출 실패 (상태 코드: {response.status_code})")
                print(f"   응답 내용: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.RequestException as req_error:
            print(f"⚠️ 네트워크 오류: {str(req_error)}")
            return {"success": False, "error": str(req_error)}
        except Exception as e:
            print(f"⚠️ 예상치 못한 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_fallback_data(self) -> List[Dict[str, Any]]:
        """API 호출 실패시 빈 배열을 반환합니다."""
        return []


class CalSelector:
    """CalSelector 메인 클래스"""
    
    def __init__(self):
        self.api_client = CalendarAPIClient()
        self.candidate_selector = CandidateSelector()
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """CalSelector 노드의 메인 처리 로직"""
        try:
            # 상태 정보 추출
            schedule_type = state.get("schedule_type", "all")
            
            # agent_task_type과 agent_task_operation이 있으면 그것을 우선 사용
            if state.get("agent_task_type") and state.get("agent_task_operation"):
                operation_type = f"{state['agent_task_type']}_{state['agent_task_operation']}"
                print(f"🔍 agent_task 설정 사용: {operation_type}")
            else:
                operation_type = state.get("operation_type") or state.get("calendar_operation", "read")
                print(f"🔍 기존 operation_type 사용: {operation_type}")
            
            query_info = state.get("query_info", {})
            
            # 디버깅: 상태 정보 출력
            print(f"🔍 CalSelector 디버깅:")
            print(f"   - schedule_type: {schedule_type}")
            print(f"   - operation_type: {operation_type}")
            print(f"   - agent_task_type: {state.get('agent_task_type')}")
            print(f"   - agent_task_operation: {state.get('agent_task_operation')}")
            print(f"   - query_info: {query_info}")
            print(f"   - state keys: {list(state.keys())}")
            
            # API 호출
            api_result = self._call_calendar_api(state)
            
            # 응답 분석
            events, tasks, all_items = self._analyze_response(api_result)
            
            # 후보 선택
            selected_item_id = self._select_candidates(all_items, query_info, operation_type)
            
            # 상태 업데이트
            updated_state = self._update_state(state, api_result, events, tasks, selected_item_id)
            
            # 로그 기록
            self._log_activity(updated_state, schedule_type, operation_type, api_result)
            
            return updated_state
            
        except Exception as e:
            return self._handle_error(state, e)
    
    def _call_calendar_api(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """캘린더 API를 호출합니다."""
        access_token = self.api_client.get_access_token(state)
        user_id = self.api_client.get_user_id(state)
        headers = self.api_client.create_headers(access_token)
        
        # operation_type을 올바르게 가져오기
        if state.get("agent_task_type") and state.get("agent_task_operation"):
            operation_type = f"{state['agent_task_type']}_{state['agent_task_operation']}"
        else:
            operation_type = state.get("operation_type") or state.get("calendar_operation", "read")
        
        api_request = {
            "api_type": "calendar_unified",
            "method": "GET",
            "endpoint": f"/api/v1/calendar/all",
            "params": {},
            "headers": headers,
            "operation": operation_type,
            "event_type": "all"
        }
        
        print(f"=== CalSelector: 통합 조회 API 호출 중... ===")
        print(f"   - operation_type: {operation_type}")
        print(f"   - access_token: {access_token[:20] if access_token else 'None'}...")
        print(f"   - user_id: {user_id}")
        print(f"   - headers: {headers}")
        
        api_result = self.api_client.call_api(headers, user_id)
        
        print(f"=== CalSelector: API 호출 결과 ===")
        print(f"   - success: {api_result.get('success', False)}")
        print(f"   - error: {api_result.get('error', 'None')}")
        if api_result.get('success') and api_result.get('data'):
            print(f"   - data count: {len(api_result['data'])}")
        
        return {
            "request": api_request,
            "result": api_result
        }
    
    def _analyze_response(self, api_result: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """API 응답을 분석하여 이벤트와 태스크로 분류합니다."""
        events = []
        tasks = []
        all_items = []
        
        print(f"=== CalSelector: API 응답 분석 중... ===")
        print(f"   - api_result keys: {list(api_result.keys())}")
        print(f"   - result success: {api_result['result'].get('success', False)}")
        
        if api_result["result"]["success"]:
            mock_response = api_result["result"]["data"]
            print(f"   - 실제 API 데이터 사용: {len(mock_response)}개 항목")
        else:
            mock_response = self.api_client.get_fallback_data()
            print(f"   - 폴백 데이터 사용: {len(mock_response)}개 항목")
        
        for i, item in enumerate(mock_response):
            if isinstance(item, dict):
                all_items.append(item)
                print(f"   - 항목 {i+1}: {item.get('title', 'N/A')} (type: {'이벤트' if 'start_at' in item else '태스크'})")
                if "start_at" in item and "end_at" in item:
                    events.append(item)
                elif "task_id" in item and "status" in item:
                    tasks.append(item)
        
        print(f"   - 최종 분류: 이벤트 {len(events)}개, 태스크 {len(tasks)}개, 전체 {len(all_items)}개")
        
        return events, tasks, all_items
    
    def _select_candidates(self, all_items: List[Dict[str, Any]], query_info: Dict[str, Any], operation_type: str) -> Optional[str]:
        """작업 유형에 따라 후보를 선택합니다."""
        selected_item_id = None
        
        print(f"\n🔍 _select_candidates 디버깅:")
        print(f"   - all_items 개수: {len(all_items)}")
        print(f"   - query_info: {query_info}")
        print(f"   - operation_type: {operation_type}")
        
        if all_items:
            print(f"   - 첫 번째 항목: {all_items[0]}")
            # 첫 번째 항목의 ID 필드들 확인
            first_item = all_items[0]
            print(f"   - 첫 번째 항목 ID 필드들:")
            print(f"     • id: {first_item.get('id', 'N/A')}")
            print(f"     • task_id: {first_item.get('task_id', 'N/A')}")
            print(f"     • event_type: {first_item.get('event_type', 'N/A')}")
            print(f"     • title: {first_item.get('title', 'N/A')}")
            
            # 모든 항목의 ID 필드 확인
            print(f"   - 모든 항목의 ID 필드 확인:")
            for i, item in enumerate(all_items[:5]):  # 처음 5개만 확인
                print(f"     {i+1}. id: {item.get('id', 'N/A')}, task_id: {item.get('task_id', 'N/A')}, title: {item.get('title', 'N/A')}")
        
        # 작업 타입과 항목 타입에 따라 적절한 항목들 필터링
        filtered_items = []
        if operation_type.startswith("task"):
            # 할일 작업: task_id가 있는 항목들만 선택
            filtered_items = [item for item in all_items if item.get('task_id')]
            print(f"   - 할일 작업: {len(filtered_items)}개 항목 필터링됨 (task_id 있음)")
        else:
            # 이벤트 작업: id가 있는 항목들만 선택
            filtered_items = [item for item in all_items if item.get('id')]
            print(f"   - 이벤트 작업: {len(filtered_items)}개 항목 필터링됨 (id 있음)")
        
        # 필터링된 항목이 없으면 전체 항목 사용
        if not filtered_items:
            print(f"   - ⚠️ 필터링된 항목이 없어 전체 항목 사용")
            filtered_items = all_items
        
        # 항목이 있으면 무조건 하나는 선택
        if filtered_items:
            if query_info and operation_type in ["update", "delete"]:
                # UPDATE/DELETE 작업: 유사도 기반 선택
                print(f"\n🎯 유사도 기반 후보 선택 중...")
                print(f"   - 쿼리 정보: {json.dumps(query_info, ensure_ascii=False, indent=2)}")
                candidate_ids = self.candidate_selector.select_top_candidates(filtered_items, query_info)
                selected_item_id = candidate_ids[0] if candidate_ids else None
                
                # 유사도 기반 선택이 실패하면 첫 번째 항목 선택
                if not selected_item_id:
                    print(f"\n⚠️ 유사도 기반 선택 실패, 첫 번째 항목을 선택합니다.")
                    selected_item_id = self._select_appropriate_id(filtered_items[0], operation_type)
            else:
                # READ 작업 또는 쿼리 정보가 없는 경우: 첫 번째 항목 선택
                print(f"\n📋 첫 번째 항목 선택")
                selected_item_id = self._select_appropriate_id(filtered_items[0], operation_type)
        else:
            print(f"\n⚠️ 선택할 항목이 없습니다.")
        
        print(f"🔍 최종 선택된 항목 ID: {selected_item_id}")
        return selected_item_id
    
    def _select_appropriate_id(self, item: Dict[str, Any], operation_type: str) -> Optional[str]:
        """작업 타입에 따라 적절한 ID를 선택합니다.
        
        Returns:
            - event 항목: 'id' 필드 사용
            - task 항목: 'task_id' 필드 사용
        """
        # 항목 타입에 따라 적절한 ID 선택
        is_event = 'start_at' in item and 'end_at' in item
        is_task = 'task_id' in item or item.get('event_type') == 'task'
        
        if is_task:
            # task 항목: task_id 필드 우선
            if item.get('task_id'):
                item_id = item.get('task_id')
                print(f"   - task 항목: task_id 필드 사용 - {item_id}")
                return item_id
            elif item.get('id'):
                item_id = item.get('id')
                print(f"   - task 항목: id 필드 사용 (fallback) - {item_id}")
                return item_id
        elif is_event:
            # event 항목: id 필드 우선
            if item.get('id'):
                item_id = item.get('id')
                print(f"   - event 항목: id 필드 사용 - {item_id}")
                return item_id
            elif item.get('task_id'):
                item_id = item.get('task_id')
                print(f"   - event 항목: task_id 필드 사용 (fallback) - {item_id}")
                return item_id
        
        print(f"   - ⚠️ ID 필드를 찾을 수 없음")
        print(f"   - item keys: {list(item.keys())}")
        return None
    
    def _update_state(self, state: Dict[str, Any], api_result: Dict[str, Any], 
                     events: List[Dict[str, Any]], tasks: List[Dict[str, Any]], 
                     selected_item_id: Optional[str]) -> Dict[str, Any]:
        """상태를 업데이트합니다."""
        # API 응답 구성
        api_responses = [{
            'api_type': 'calendar_unified',
            'status_code': 200 if api_result["result"]["success"] else 500,
            'success': api_result["result"]["success"],
            'data': {
                'events': events,
                'tasks': tasks,
                'total_count': len(events) + len(tasks),
                'event_count': len(events),
                'task_count': len(tasks)
            },
            'request_info': {
                'endpoint': api_result["request"]['endpoint'],
                'params': api_result["request"]['params'],
                'operation': api_result["request"]['operation']
            }
        }]
        
        if not api_result["result"]["success"]:
            api_responses[0]['error'] = api_result["result"]["error"]
        
        # 상태 업데이트
        state["api_requests"] = [api_result["request"]]
        state["api_responses"] = api_responses
        state["selected_item_id"] = selected_item_id
        state["next_node"] = "answer_generator"
        
        # 선택된 항목 정보 출력
        if selected_item_id:
            selected_item = self._find_item_by_id(selected_item_id, events, tasks)
            if selected_item:
                item_type = "event" if 'start_at' in selected_item else "task"
                title = selected_item.get('title', 'N/A')
                print(f"\n✅ 선택된 항목:")
                print(f"   - ID: {selected_item_id}")
                print(f"   - 유형: {item_type}")
                print(f"   - 타이틀: {title}")
            else:
                print(f"\n✅ 선택된 항목 ID: {selected_item_id}")
        else:
            print(f"\n⚠️ 선택할 후보 항목이 없습니다.")
        
        # 응답 데이터를 state에 저장
        if api_responses[0].get('success', False):
            response_data = api_responses[0].get('data', {})
            state["unified_calendar_data"] = response_data
            state["events"] = response_data.get('events', [])
            state["tasks"] = response_data.get('tasks', [])
        
        print(f"\n🔍 CalSelector 데이터 확인:")
        print(f"   - events 개수: {len(events)}")
        print(f"   - tasks 개수: {len(tasks)}")
        print(f"   - selected_item_id: {selected_item_id}")
        
        # 이벤트와 태스크 목록 간단히 표시 (처음 5개씩)
        if events:
            print(f"\n📅 Events 목록 (처음 5개):")
            for i, event in enumerate(events[:5], 1):
                event_id = event.get('id', 'N/A')
                title = event.get('title', 'N/A')
                print(f"   {i}. [{event_id}] {title}")
            if len(events) > 5:
                print(f"   ... 외 {len(events) - 5}개 더")
        
        if tasks:
            print(f"\n📝 Tasks 목록 (처음 5개):")
            for i, task in enumerate(tasks[:5], 1):
                task_id = task.get('task_id', 'N/A')
                title = task.get('title', 'N/A')
                print(f"   {i}. [{task_id}] {title}")
            if len(tasks) > 5:
                print(f"   ... 외 {len(tasks) - 5}개 더")
        
        print(f"\n✅ 통합 조회 API 응답 수신 완료")
        print(f"📊 총 {len(events) + len(tasks)}개 항목 (이벤트: {len(events)}개, 태스크: {len(tasks)}개)")
        
        return state
    
    def _find_item_by_id(self, item_id: str, events: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """ID로 항목을 찾습니다."""
        # events에서 찾기
        for event in events:
            if event.get('id') == item_id:
                return event
        
        # tasks에서 찾기
        for task in tasks:
            if task.get('task_id') == item_id:
                return task
        
        return None
    
    def _log_activity(self, state: Dict[str, Any], schedule_type: str, operation_type: str, api_result: Dict[str, Any]) -> None:
        """활동을 로그에 기록합니다."""
        request_count = 1
        response_count = 1 if api_result["result"]["success"] else 0
        summary = f"통합 조회 API 요청 {request_count}개 중 {response_count}개 성공"
        
        if response_count > 0:
            events = state.get("events", [])
            tasks = state.get("tasks", [])
            summary += f" (총 {len(events) + len(tasks)}개 항목)"
        
        state.setdefault("agent_messages", []).append({
            "agent": "calselector",
            "schedule_type": schedule_type,
            "operation_type": operation_type,
            "api_requests": [api_result["request"]],
            "api_responses": state["api_responses"],
            "summary": summary,
            "next_node": state["next_node"]
        })
        
        print(f"=== CalSelector: {summary} ===")
    
    def _handle_error(self, state: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """에러를 처리합니다."""
        error_msg = f"CalSelector 노드 오류: {str(error)}"
        state["error"] = error_msg
        state["next_node"] = "answer_generator"
        
        state.setdefault("agent_messages", []).append({
            "agent": "calselector",
            "error": str(error),
            "next_node": "answer_generator"
        })
        
        return state


# 기존 함수 호환성을 위한 래퍼
def calselector(state: Dict[str, Any]) -> Dict[str, Any]:
    """CalSelector 노드: 통합 조회 API를 호출하여 Events와 Tasks를 조회하고 응답을 분석합니다."""
    selector = CalSelector()
    return selector.process(state)
