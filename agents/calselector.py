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

class SimilarityCalculator:
    """텍스트, 시간, 최신성 유사도를 계산하는 클래스"""
    
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
    
    @staticmethod
    def calculate_recency_score(created_at: Optional[str]) -> float:
        """항목의 최신성을 기반으로 점수를 계산합니다."""
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


class CandidateSelector:
    """후보 항목 선택을 담당하는 클래스"""
    
    def __init__(self):
        self.similarity_calculator = SimilarityCalculator()
    
    def calculate_similarity_score(self, query_info: Dict[str, Any], item: Dict[str, Any]) -> float:
        """사용자 쿼리와 항목 간의 종합 유사도 점수를 계산합니다."""
        score = 0.0
        
        # 1. 제목 유사도 (가중치: 40%)
        query_title = query_info.get('title', '')
        item_title = item.get('title', '')
        if query_title and item_title:
            title_similarity = self.similarity_calculator.calculate_text_similarity(query_title, item_title)
            score += title_similarity * 0.4
        
        # 2. 시간 유사도 (가중치: 30%)
        query_start = query_info.get('start_at')
        item_start = item.get('start_at')
        if query_start and item_start:
            time_similarity = self.similarity_calculator.calculate_time_similarity(query_start, item_start)
            score += time_similarity * 0.3
        
        # 3. 타입 매칭 (가중치: 20%)
        query_type = query_info.get('event_type', 'event')
        item_type = 'event' if 'start_at' in item and 'end_at' in item else 'task'
        if query_type == item_type:
            score += 0.2
        
        # 4. 최신성 (가중치: 10%)
        recency_score = self.similarity_calculator.calculate_recency_score(item.get('created_at'))
        score += recency_score * 0.1
        
        return score
    
    def select_top_candidates(self, items: List[Dict[str, Any]], query_info: Dict[str, Any]) -> List[str]:
        """유사도 점수를 기반으로 Top-1 후보를 선택합니다."""
        if not items:
            return []
        
        # 각 항목에 대해 유사도 점수 계산
        scored_items = []
        for item in items:
            # 이벤트인지 할일인지 확인하여 올바른 ID 필드 사용
            if item.get('event_type') == 'task' or 'task_id' in item:
                item_id = item.get('task_id')
            else:
                item_id = item.get('id')
            
            if item_id:
                similarity_score = self.calculate_similarity_score(query_info, item)
                scored_items.append({
                    'id': item_id,
                    'item': item,
                    'score': similarity_score
                })
        
        # 점수 기준으로 정렬 (높은 점수 우선)
        scored_items.sort(key=lambda x: x['score'], reverse=True)
        
        # Top-1 선택
        top_candidate = scored_items[0] if scored_items else None
        
        # 디버깅을 위한 점수 출력
        if top_candidate:
            self._print_candidate_scores([top_candidate])
            return [top_candidate['id']]
        else:
            print(f"\n🔍 유사도 점수 계산 결과: 후보 없음")
            return []
    
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
    
    # def get_user_id(self, state: Dict[str, Any]) -> str:
    #     """사용자 ID를 가져옵니다."""
    #     # 1. state에서 user_id 가져오기
    #     user_id = "4a728952-53a0-4abe-ae8c-0ff440d6585e"
    #     return user_id
    
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
        api_endpoint = f"{self.base_url}/api/v1/calendar/{user_id}/all"
        
        try:
            print(f"🌐 API 엔드포인트: {api_endpoint}")
            
            response = requests.get(
                api_endpoint,
                headers=headers,
                timeout=self.timeout
            )
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                api_data = response.json()
                print(f"✅ API 호출 성공: {len(api_data)}개 항목 수신")
                if api_data and len(api_data) > 0:
                    print(f"📋 첫 번째 항목: {api_data[0].get('title', 'N/A')}")
                return {"success": True, "data": api_data}
            else:
                print(f"❌ API 호출 실패 (상태 코드: {response.status_code})")
                print(f"   응답 내용: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as req_error:
            print(f"⚠️ 네트워크 오류: {str(req_error)}")
            return {"success": False, "error": str(req_error)}
    
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
            operation_type = state.get("operation_type") or state.get("calendar_operation", "read")
            query_info = state.get("query_info", {})
            
            # 디버깅: 상태 정보 출력
            print(f"🔍 CalSelector 디버깅:")
            print(f"   - schedule_type: {schedule_type}")
            print(f"   - operation_type: {operation_type}")
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
        operation_type = state.get("operation_type") or state.get("calendar_operation", "read")
        
        api_request = {
            "api_type": "calendar_unified",
            "method": "GET",
            "endpoint": f"/api/v1/calendar/{user_id}/all",
            "params": {},
            "headers": headers,
            "operation": operation_type,
            "event_type": "all"
        }
        
        print(f"=== CalSelector: 통합 조회 API 호출 중... ===")
        print(f"   - operation_type: {operation_type}")
        api_result = self.api_client.call_api(headers, user_id)
        
        return {
            "request": api_request,
            "result": api_result
        }
    
    def _analyze_response(self, api_result: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """API 응답을 분석하여 이벤트와 태스크로 분류합니다."""
        events = []
        tasks = []
        all_items = []
        
        if api_result["result"]["success"]:
            mock_response = api_result["result"]["data"]
        else:
            mock_response = self.api_client.get_fallback_data()
        
        for item in mock_response:
            if isinstance(item, dict):
                all_items.append(item)
                if "start_at" in item and "end_at" in item:
                    events.append(item)
                elif "task_id" in item and "status" in item:
                    tasks.append(item)
        
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
        
        if all_items and query_info:
            if operation_type == "read":
                # READ 작업: 첫 번째 항목만 선택
                print(f"\n📋 READ 작업: 첫 번째 항목 선택")
                if all_items:
                    # 이벤트인지 할일인지 확인하여 올바른 ID 필드 사용
                    first_item = all_items[0]
                    if first_item.get('event_type') == 'task' or 'task_id' in first_item:
                        item_id = first_item.get('task_id')
                        print(f"   - 할일로 판단: task_id 사용")
                    else:
                        item_id = first_item.get('id')
                        print(f"   - 이벤트로 판단: id 사용")
                    
                    if item_id:
                        selected_item_id = item_id
                        print(f"   - 선택된 항목: {first_item.get('title', 'N/A')}")
                        print(f"   - 선택된 ID: {item_id}")
            else:
                # UPDATE/DELETE 작업: 유사도 기반 선택
                print(f"\n🎯 유사도 기반 후보 선택 중...")
                print(f"   - 쿼리 정보: {json.dumps(query_info, ensure_ascii=False, indent=2)}")
                candidate_ids = self.candidate_selector.select_top_candidates(all_items, query_info)
                selected_item_id = candidate_ids[0] if candidate_ids else None
        else:
            # 쿼리 정보가 없거나 항목이 없는 경우 첫 번째 항목 선택
            print(f"\n⚠️ 쿼리 정보가 없어 첫 번째 항목을 선택합니다.")
            if all_items:
                # 이벤트인지 할일인지 확인하여 올바른 ID 필드 사용
                first_item = all_items[0]
                if first_item.get('event_type') == 'task' or 'task_id' in first_item:
                    item_id = first_item.get('task_id')
                    print(f"   - 할일로 판단: task_id 사용")
                else:
                    item_id = first_item.get('id')
                    print(f"   - 이벤트로 판단: id 사용")
                
                if item_id:
                    selected_item_id = item_id
                    print(f"   - 선택된 항목: {first_item.get('title', 'N/A')}")
                    print(f"   - 선택된 ID: {item_id}")
        
        print(f"🔍 최종 선택된 항목 ID: {selected_item_id}")
        return selected_item_id
    
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
            print(f"\n✅ 선택된 항목 ID: {selected_item_id}")
        else:
            print(f"\n⚠️ 선택할 후보 항목이 없습니다.")
        
        # 응답 데이터를 state에 저장
        if api_responses[0].get('success', False):
            response_data = api_responses[0].get('data', {})
            state["unified_calendar_data"] = response_data
            state["events"] = response_data.get('events', [])
            state["tasks"] = response_data.get('tasks', [])
        
        print(f"✅ 통합 조회 API 응답 수신 완료")
        print(f"📊 총 {len(events) + len(tasks)}개 항목 (이벤트: {len(events)}개, 태스크: {len(tasks)}개)")
        
        return state
    
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
