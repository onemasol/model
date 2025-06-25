# agents/answer_generator.py

from typing import Dict, Optional
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
import torch
import httpx
import json
from datetime import datetime, timedelta
from api.make_agents_log_payload import make_agent_logs_payload
from api.send_agents_log import send_log_to_backend

# NVIDIA GPU 최적화 설정
def setup_optimal_device():
    """NVIDIA GPU 환경에 최적화된 device 설정"""
    if torch.cuda.is_available():
        # CUDA 환경 변수 설정
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # 첫 번째 GPU 사용
        os.environ['CUDA_LAUNCH_BLOCKING'] = '1'  # 디버깅을 위한 동기 실행
        
        # GPU 메모리 최적화 설정
        torch.backends.cudnn.benchmark = True  # cuDNN 최적화
        torch.backends.cudnn.deterministic = False  # 성능 향상을 위해 비결정적
        
        device = torch.device("cuda:0")
        
        # GPU 메모리 캐시 정리
        torch.cuda.empty_cache()
        
        print(f"🚀 GPU 사용: {torch.cuda.get_device_name(0)}")
        print(f"📊 GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
        
    else:
        device = torch.device("cpu")
        print("⚠️  GPU 사용 불가능: CPU 사용")
    
    return device

device = setup_optimal_device()
load_dotenv()

model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.5,
)

def create_api_headers(access_token: Optional[str] = None) -> Dict[str, str]:
    """
    API 요청용 헤더 생성
    
    Args:
        access_token: 인증 토큰 (선택사항)
    
    Returns:
        API 요청 헤더 딕셔너리
    """
    headers = { # 하드코딩함 Access Token
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA4NzU1MzYsInN1YiI6IjRhNzI4OTUyLTUzYTAtNGFiZS1hZThjLTBmZjQ0MGQ2NTg1ZSJ9.n4dtcTdY3w4sWGVEcr1z0fyKFeGZ-w8b6mH8EkKJX2M",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    # 1. 매개변수로 전달된 access_token 사용
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    return headers

async def handle_calendar_api_request(state: Dict) -> Dict:
    """
    calendar_type과 calendar_operation 조합에 따른 12가지 경우의 수 처리
    
    calendar_type: "event" | "task" | "agent_event"
    calendar_operation: "create" | "read" | "update" | "delete"
    
    12가지 조합:
    1. event + create
    2. event + read  
    3. event + update
    4. event + delete
    5. task + create
    6. task + read
    7. task + update
    8. task + delete
    9. agent_event + create
    10. agent_event + read
    11. agent_event + update
    12. agent_event + delete
    """
    calendar_type = state.get("calendar_type")
    calendar_operation = state.get("calendar_operation")
    base_url = "http://52.79.95.55:8000"
    
    if not calendar_type or not calendar_operation:
        print("⚠️  calendar_type 또는 calendar_operation이 설정되지 않았습니다.")
        return state
    
    # 인증 헤더 설정
    access_token = state.get("access_token")
    headers = create_api_headers(access_token)
    
    try:
        if calendar_type == "event":
            if calendar_operation == "create":
                # 1. event + create
                return await handle_event_create(state, base_url, headers)
                
            elif calendar_operation == "read":
                # 2. event + read
                return await handle_event_read(state, base_url, headers)
                
            elif calendar_operation == "update":
                # 3. event + update
                return await handle_event_update(state, base_url, headers)
                
            elif calendar_operation == "delete":
                # 4. event + delete
                return await handle_event_delete(state, base_url, headers)
                
        elif calendar_type == "task":
            if calendar_operation == "create":
                # 5. task + create
                return await handle_task_create(state, base_url, headers)
                
            elif calendar_operation == "read":
                # 6. task + read
                return await handle_task_read(state, base_url, headers)
                
            elif calendar_operation == "update":
                # 7. task + update
                return await handle_task_update(state, base_url, headers)
                
            elif calendar_operation == "delete":
                # 8. task + delete
                return await handle_task_delete(state, base_url, headers)
                
        elif calendar_type == "agent_event":
            if calendar_operation == "create":
                # 9. agent_event + create
                return await handle_agent_event_create(state, base_url, headers)
                
            elif calendar_operation == "read":
                # 10. agent_event + read
                return await handle_agent_event_read(state, base_url, headers)
                
            elif calendar_operation == "update":
                # 11. agent_event + update
                return await handle_agent_event_update(state, base_url, headers)
                
            elif calendar_operation == "delete":
                # 12. agent_event + delete
                return await handle_agent_event_delete(state, base_url, headers)
        
        print(f"❌ 지원하지 않는 조합: {calendar_type} + {calendar_operation}")
        return state
        
    except Exception as e:
        print(f"❌ 캘린더 API 요청 중 오류 발생: {str(e)}")
        return state

async def create_agent_task(
    title: str, 
    description: str, 
    due_at: str,
    used_agents: list,
    access_token: Optional[str] = None
) -> Dict:
    """
    에이전트 태스크를 API를 통해 생성
    
    Args:
        title: 태스크 제목
        description: 태스크 설명
        used_agents: 사용된 에이전트 목록
        access_token: API 인증 토큰 (선택사항)
    
    Returns:
        생성된 태스크 정보
    """
    api_url = "http://52.79.95.55:8000/api/v1/agent/tasks"
    
    payload = {
        "title": title,
        "description": description,
        "due_at": due_at,
        "status": "pending",
        "used_agents": used_agents
    }
    
    # 헤더 생성
    headers = create_api_headers(access_token)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print("⚠️  인증이 필요합니다. access_token을 제공해주세요.")
                return {"error": "Authentication required"}
            else:
                print(f"❌ 태스크 생성 실패: {response.status_code} - {response.text}")
                return {"error": f"Failed to create task: {response.status_code}"}
                
    except Exception as e:
        print(f"❌ API 요청 중 오류 발생: {str(e)}")
        return {"error": f"Request failed: {str(e)}"}

async def create_agent_event(
    title: str, 
    description: str, 
    start_at: str,
    end_at: str,
    location: str,
    created_by_agent: str,
    access_token: Optional[str] = None
) -> Dict:
    """
    에이전트 이벤트를 API를 통해 생성
    
    Args:
        title: 이벤트 제목
        description: 이벤트 설명
        start_at: 시작 시간 (ISO 형식)
        end_at: 종료 시간 (ISO 형식)
        location: 위치
        created_by_agent: 생성한 에이전트 이름
        access_token: API 인증 토큰 (선택사항)
    
    Returns:
        생성된 이벤트 정보
    """
    api_url = "http://52.79.95.55:8000/api/v1/agent/events"
    
    payload = {
        "title": title,
        "description": description,
        "start_at": start_at,
        "end_at": end_at,
        "location": location,
        "created_by_agent": created_by_agent
    }
    
    # 헤더 생성
    headers = create_api_headers(access_token)
    
    # 디버깅 정보 출력
    print(f"🔍 에이전트 이벤트 생성 디버깅:")
    print(f"   - API URL: {api_url}")
    print(f"   - Headers: {headers}")
    print(f"   - Payload: {payload}")
    print(f"   - Access Token: {'있음' if access_token else '없음'}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 에이전트 이벤트 API 요청 전송 중...")
            response = await client.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            print(f"📊 에이전트 이벤트 응답 상태 코드: {response.status_code}")
            print(f"📄 에이전트 이벤트 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 에이전트 이벤트 응답 데이터: {result}")
                return result
            elif response.status_code == 403:
                print("⚠️  인증이 필요합니다. access_token을 제공해주세요.")
                return {"error": "Authentication required"}
            else:
                print(f"❌ 응답 내용: {response.text}")
                print(f"❌ 에이전트 이벤트 생성 실패: {response.status_code} - {response.text}")
                return {"error": f"Failed to create agent event: {response.status_code}"}
                
    except Exception as e:
        print(f"❌ 에이전트 이벤트 API 요청 중 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"Request failed: {str(e)}"}

async def handle_event_create(state: Dict, base_url: str, headers: Dict) -> Dict:
    """이벤트 생성 처리"""
    print("📅 이벤트 생성 요청 처리 중...")
    
    # 디버깅: 상태 정보 출력
    print(f"🔍 디버깅 정보:")
    print(f"   - base_url: {base_url}")
    print(f"   - headers: {headers}")
    print(f"   - state keys: {list(state.keys())}")
    
    # 이벤트 생성용 payload 구성
    event_data = {
        "title": state.get("title", ""),
        "start_at": state.get("start_at"),
        "end_at": state.get("end_at"),
        "timezone": state.get("timezone", "Asia/Seoul"),
        "description": state.get("initial_input", "")
    }
    
    # event_payload가 있으면 사용
    if state.get("event_payload"):
        event_data.update(state["event_payload"])
    
    # 디버깅: 페이로드 정보 출력
    print(f"📋 이벤트 페이로드:")
    print(f"   - title: {event_data.get('title')}")
    print(f"   - start_at: {event_data.get('start_at')}")
    print(f"   - end_at: {event_data.get('end_at')}")
    print(f"   - timezone: {event_data.get('timezone')}")
    print(f"   - description: {event_data.get('description')}")
    
    api_url = f"{base_url}/api/v1/calendar/events"
    print(f"🌐 API URL: {api_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 API 요청 전송 중...")
            response = await client.post(api_url, json=event_data, headers=headers)
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            print(f"📄 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 응답 데이터: {result}")
                state["crud_result"] = f"이벤트 생성 완료: {result.get('id', 'N/A')}"
                print(f"✅ 이벤트 생성 완료: {result.get('id', 'N/A')}")
                
                # API 처리 완료 플래그 설정
                state["_api_processed"] = True
                
                # 이벤트 생성 시에는 추가 생성 없음 (중복 방지)
                print("✅ 이벤트 생성 완료 - 추가 에이전트 이벤트/태스크 생성 없음")
            else:
                print(f"❌ 응답 내용: {response.text}")
                state["crud_result"] = f"이벤트 생성 실패: {response.status_code}"
                print(f"❌ 이벤트 생성 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ API 요청 중 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        state["crud_result"] = f"이벤트 생성 중 오류: {str(e)}"
    
    return state

async def handle_event_read(state: Dict, base_url: str, headers: Dict) -> Dict:
    """이벤트 조회 처리"""
    print("📅 이벤트 조회 요청 처리 중...")
    
    # 조회 조건 구성
    query_params = {}
    if state.get("query_info"):
        query_params.update(state["query_info"])
    
    # 특정 이벤트 조회
    if state.get("selected_item_id"):
        api_url = f"{base_url}/api/v1/calendar/events/{state['selected_item_id']}"
        print(f"🌐 GET 요청 - 특정 이벤트 조회: {api_url}")
    else:
        # 전체 이벤트 조회
        api_url = f"{base_url}/api/v1/calendar/events"
        print(f"🌐 GET 요청 - 전체 이벤트 조회: {api_url}")
    
    print(f"📡 GET 요청 전송 중...")
    print(f"   - Method: GET")
    print(f"   - URL: {api_url}")
    print(f"   - Headers: {headers}")
    print(f"   - Query Params: {query_params}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers, params=query_params)
        
        print(f"📊 GET 응답 상태 코드: {response.status_code}")
        print(f"📄 GET 응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            state["crud_result"] = f"이벤트 조회 완료: {len(result) if isinstance(result, list) else 1}개 항목"
            print(f"✅ 이벤트 조회 완료: {len(result) if isinstance(result, list) else 1}개 항목")
            print(f"📋 응답 데이터: {result}")
        else:
            state["crud_result"] = f"이벤트 조회 실패: {response.status_code}"
            print(f"❌ 이벤트 조회 실패: {response.status_code} - {response.text}")
    
    return state

async def handle_event_update(state: Dict, base_url: str, headers: Dict) -> Dict:
    """이벤트 수정 처리"""
    print("📅 이벤트 수정 요청 처리 중...")
    
    if not state.get("selected_item_id"):
        state["crud_result"] = "수정할 이벤트 ID가 필요합니다."
        print("❌ 수정할 이벤트 ID가 필요합니다.")
        return state
    
    # 수정할 데이터 구성
    update_data = {}
    if state.get("title"):
        update_data["title"] = state["title"]
    if state.get("start_at"):
        update_data["start_at"] = state["start_at"]
    if state.get("end_at"):
        update_data["end_at"] = state["end_at"]
    if state.get("timezone"):
        update_data["timezone"] = state["timezone"]
    
    # event_payload가 있으면 사용
    if state.get("event_payload"):
        update_data.update(state["event_payload"])
    
    api_url = f"{base_url}/api/v1/calendar/events/{state['selected_item_id']}"
    
    async with httpx.AsyncClient() as client:
        response = await client.put(api_url, json=update_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            state["crud_result"] = f"이벤트 수정 완료: {result.get('id', 'N/A')}"
            print(f"✅ 이벤트 수정 완료: {result.get('id', 'N/A')}")
        else:
            state["crud_result"] = f"이벤트 수정 실패: {response.status_code}"
            print(f"❌ 이벤트 수정 실패: {response.status_code} - {response.text}")
    
    return state

async def handle_event_delete(state: Dict, base_url: str, headers: Dict) -> Dict:
    """이벤트 삭제 처리"""
    print("📅 이벤트 삭제 요청 처리 중...")
    
    if not state.get("selected_item_id"):
        state["crud_result"] = "삭제할 이벤트 ID가 필요합니다."
        print("❌ 삭제할 이벤트 ID가 필요합니다.")
        return state
    
    api_url = f"{base_url}/api/v1/calendar/events/{state['selected_item_id']}"
    print(f"🌐 DELETE 요청 - 이벤트 삭제: {api_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 DELETE 요청 전송 중...")
            print(f"   - Method: DELETE")
            print(f"   - URL: {api_url}")
            print(f"   - Headers: {headers}")
            response = await client.delete(api_url, headers=headers)
            
            print(f"📊 DELETE 응답 상태 코드: {response.status_code}")
            print(f"📄 DELETE 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 204:
                # 204 No Content - 성공적으로 삭제됨
                state["crud_result"] = f"이벤트 삭제 완료: {state['selected_item_id']} (204 No Content)"
                print(f"✅ 이벤트 삭제 완료: {state['selected_item_id']} (204 No Content)")
            elif response.status_code == 200:
                # 200 OK - 성공적으로 삭제됨 (기존 호환성)
                state["crud_result"] = f"이벤트 삭제 완료: {state['selected_item_id']}"
                print(f"✅ 이벤트 삭제 완료: {state['selected_item_id']}")
            elif response.status_code == 404:
                error_msg = f"삭제할 이벤트를 찾을 수 없습니다. (ID: {state['selected_item_id']}) - 해당 이벤트가 존재하지 않거나 현재 사용자의 이벤트가 아닙니다."
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
            else:
                error_msg = f"이벤트 삭제 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
                print(f"📄 응답 내용: {response.text}")
    except Exception as e:
        error_msg = f"이벤트 삭제 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

async def handle_task_create(state: Dict, base_url: str, headers: Dict) -> Dict:
    """할일 생성 처리"""
    print("📋 할일 생성 요청 처리 중...")
    
    # 이미 처리된 경우 중복 방지
    if state.get("_api_processed"):
        print("⚠️  이미 API 처리가 완료되었습니다. 중복 요청을 방지합니다.")
        return state
    
    # 사용된 에이전트 정보 구성
    used_agents = []
    if state.get("agent_messages"):
        for msg in state["agent_messages"]:
            used_agents.append({
                "agent_name": msg.get("agent", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "input_summary": str(msg.get("input_snapshot", {}).get("user_query", ""))[:100] + "...",
                "operation": "task_creation"
            })
    else:
        # 기본 에이전트 정보
        used_agents.append({
            "agent_name": "answer_generator",
            "timestamp": datetime.now().isoformat(),
            "input_summary": str(state.get("initial_input", ""))[:100] + "...",
            "operation": "task_creation"
        })
    
    # 할일 생성용 payload 구성
    task_data = {
        "title": state.get("title", ""),
        "description": state.get("initial_input", ""),
        "status": "pending",
        "due_at": state.get("due_at"),
        "used_agents": used_agents
    }
    
    # event_payload가 있으면 사용 (할일도 동일한 필드 사용)
    if state.get("event_payload"):
        task_data.update(state["event_payload"])
    
    # API 엔드포인트 수정 - agent tasks API 사용
    api_url = f"{base_url}/api/v1/agent/tasks"
    print(f"🌐 할일 생성 API URL: {api_url}")
    
    # 디버깅 정보 출력
    print(f"🔍 할일 생성 디버깅:")
    print(f"   - API URL: {api_url}")
    print(f"   - Headers: {headers}")
    print(f"   - Payload: {task_data}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 할일 생성 API 요청 전송 중...")
            response = await client.post(api_url, json=task_data, headers=headers)
            
            print(f"📊 할일 생성 응답 상태 코드: {response.status_code}")
            print(f"📄 할일 생성 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                state["crud_result"] = f"할일 생성 완료: {result.get('task_id', 'N/A')}"
                print(f"✅ 할일 생성 완료: {result.get('task_id', 'N/A')}")
                
                # API 처리 완료 플래그 설정
                state["_api_processed"] = True
                
                # 할일 생성 시에는 추가 생성 없음 (중복 방지)
                print("✅ 할일 생성 완료 - 추가 에이전트 이벤트/태스크 생성 없음")
            else:
                print(f"❌ 응답 내용: {response.text}")
                error_msg = f"할일 생성 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
    except Exception as e:
        error_msg = f"할일 생성 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

async def handle_task_read(state: Dict, base_url: str, headers: Dict) -> Dict:
    """할일 조회 처리"""
    print("📋 할일 조회 요청 처리 중...")
    
    # 디버깅: 상태 정보 출력
    print(f"🔍 할일 조회 디버깅 정보:")
    print(f"   - selected_item_id: {state.get('selected_item_id')}")
    print(f"   - state keys: {list(state.keys())}")
    print(f"   - initial_input: {state.get('initial_input', '')}")
    
    # 특정 할일 조회 (task_id가 필요함)
    if state.get("selected_item_id"):
        api_url = f"{base_url}/api/v1/agent/tasks/{state['selected_item_id']}"
        print(f"🌐 특정 할일 조회 API URL: {api_url}")
        print(f"🔍 조회할 할일 ID: {state['selected_item_id']}")
    else:
        # 전체 할일 조회 (현재는 지원하지 않음 - 특정 task_id 필요)
        error_msg = "할일 조회를 위해서는 task_id가 필요합니다. 구체적인 할일 ID를 지정해주세요."
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        return state
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 GET 요청 전송 중...")
            print(f"   - Method: GET")
            print(f"   - URL: {api_url}")
            print(f"   - Headers: {headers}")
            response = await client.get(api_url, headers=headers)
            
            print(f"📊 GET 응답 상태 코드: {response.status_code}")
            print(f"📄 GET 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 특정 할일 조회 완료")
                print(f"📋 할일 상세 정보:")
                print(f"   - 제목: {result.get('title', 'N/A')}")
                print(f"   - 설명: {result.get('description', 'N/A')}")
                print(f"   - 상태: {result.get('status', 'N/A')}")
                print(f"   - 할일 ID: {result.get('task_id', 'N/A')}")
                print(f"   - 사용자 ID: {result.get('user_id', 'N/A')}")
                print(f"   - 마감일: {result.get('due_at', 'N/A')}")
                print(f"   - 생성 시간: {result.get('created_at', 'N/A')}")
                print(f"   - 수정 시간: {result.get('updated_at', 'N/A')}")
                
                # 사용된 에이전트 정보 출력
                used_agents = result.get('used_agents', [])
                if used_agents:
                    print(f"   - 사용된 에이전트: {len(used_agents)}개")
                    for i, agent in enumerate(used_agents, 1):
                        print(f"     {i}. {agent.get('agent_name', 'N/A')} - {agent.get('operation', 'N/A')}")
                        print(f"        시간: {agent.get('timestamp', 'N/A')}")
                        print(f"        입력 요약: {agent.get('input_summary', 'N/A')}")
                else:
                    print(f"   - 사용된 에이전트: 없음")
                
                # 전체 응답 데이터 출력
                print(f"📋 전체 응답 데이터: {result}")
                
                # 응답 결과를 state에 저장
                state["crud_result"] = f"할일 조회 완료: {result.get('title', 'N/A')} (ID: {result.get('task_id', 'N/A')})"
                state["task_details"] = result  # 전체 응답 데이터 저장
                
            elif response.status_code == 404:
                error_msg = f"할일을 찾을 수 없습니다. (ID: {state.get('selected_item_id', 'N/A')}) - 해당 태스크가 존재하지 않거나 현재 사용자의 태스크가 아닙니다."
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
            else:
                error_msg = f"할일 조회 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
                print(f"📄 응답 내용: {response.text}")
    except Exception as e:
        error_msg = f"할일 조회 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

async def handle_task_update(state: Dict, base_url: str, headers: Dict) -> Dict:
    """할일 수정 처리"""
    print("📋 할일 수정 요청 처리 중...")
    
    if not state.get("selected_item_id"):
        error_msg = "수정할 할일 ID가 필요합니다."
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        return state
    
    # 수정할 데이터 구성
    update_data = {}
    if state.get("title"):
        update_data["title"] = state["title"]
    if state.get("description"):
        update_data["description"] = state["description"]
    if state.get("status"):
        update_data["status"] = state["status"]
    if state.get("due_at"):
        update_data["due_at"] = state["due_at"]
    
    # event_payload가 있으면 사용
    if state.get("event_payload"):
        update_data.update(state["event_payload"])
    
    # API 엔드포인트 수정 - agent tasks API 사용
    api_url = f"{base_url}/api/v1/agent/tasks/{state['selected_item_id']}"
    print(f"🌐 PUT 요청 - 할일 수정: {api_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 PUT 요청 전송 중...")
            print(f"   - Method: PUT")
            print(f"   - URL: {api_url}")
            print(f"   - Headers: {headers}")
            print(f"   - Payload: {update_data}")
            response = await client.put(api_url, json=update_data, headers=headers)
            
            print(f"📊 PUT 응답 상태 코드: {response.status_code}")
            print(f"📄 PUT 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                state["crud_result"] = f"할일 수정 완료: {result.get('task_id', 'N/A')}"
                print(f"✅ 할일 수정 완료: {result.get('task_id', 'N/A')}")
                print(f"📋 수정된 할일 정보:")
                print(f"   - 제목: {result.get('title', 'N/A')}")
                print(f"   - 설명: {result.get('description', 'N/A')}")
                print(f"   - 상태: {result.get('status', 'N/A')}")
                print(f"   - 할일 ID: {result.get('task_id', 'N/A')}")
                print(f"   - 마감일: {result.get('due_at', 'N/A')}")
            elif response.status_code == 404:
                error_msg = f"수정할 할일을 찾을 수 없습니다. (ID: {state['selected_item_id']}) - 해당 태스크가 존재하지 않거나 현재 사용자의 태스크가 아닙니다."
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
            else:
                error_msg = f"할일 수정 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
                print(f"📄 응답 내용: {response.text}")
    except Exception as e:
        error_msg = f"할일 수정 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

async def handle_task_delete(state: Dict, base_url: str, headers: Dict) -> Dict:
    """할일 삭제 처리"""
    print("📋 할일 삭제 요청 처리 중...")
    
    # 디버깅: 상태 정보 출력
    print(f"🔍 할일 삭제 디버깅 정보:")
    print(f"   - selected_item_id: {state.get('selected_item_id')}")
    print(f"   - state keys: {list(state.keys())}")
    print(f"   - initial_input: {state.get('initial_input', '')}")
    
    if not state.get("selected_item_id"):
        error_msg = "삭제할 할일 ID가 필요합니다. 구체적인 할일을 지정해주세요."
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        return state
    
    # API 엔드포인트 수정 - agent tasks API 사용
    api_url = f"{base_url}/api/v1/agent/tasks/{state['selected_item_id']}"
    print(f"🌐 DELETE 요청 - 할일 삭제: {api_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 DELETE 요청 전송 중...")
            print(f"   - Method: DELETE")
            print(f"   - URL: {api_url}")
            print(f"   - Headers: {headers}")
            response = await client.delete(api_url, headers=headers)
            
            print(f"📊 DELETE 응답 상태 코드: {response.status_code}")
            print(f"📄 DELETE 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 204:
                # 204 No Content - 성공적으로 삭제됨
                state["crud_result"] = f"할일 삭제 완료: {state['selected_item_id']} (204 No Content)"
                print(f"✅ 할일 삭제 완료: {state['selected_item_id']} (204 No Content)")
            elif response.status_code == 200:
                # 200 OK - 성공적으로 삭제됨 (기존 호환성)
                state["crud_result"] = f"할일 삭제 완료: {state['selected_item_id']}"
                print(f"✅ 할일 삭제 완료: {state['selected_item_id']}")
            elif response.status_code == 404:
                error_msg = f"삭제할 할일을 찾을 수 없습니다. (ID: {state['selected_item_id']}) - 해당 태스크가 존재하지 않거나 현재 사용자의 태스크가 아닙니다."
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
            else:
                error_msg = f"할일 삭제 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
                print(f"📄 응답 내용: {response.text}")
    except Exception as e:
        error_msg = f"할일 삭제 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

async def create_agent_task_for_calendar_operation(
    state: Dict, 
    operation_type: str, 
    calendar_item_id: str,
    auth_header: Optional[str] = None
) -> None:
    """
    캘린더 작업 후 에이전트 태스크 생성
    
    Args:
        state: 현재 상태
        operation_type: 작업 타입 (예: "이벤트 생성", "할일 생성")
        calendar_item_id: 생성된 캘린더 항목 ID
        auth_header: 인증 헤더
    """
    try:
        # 사용된 에이전트 목록 추출
        used_agents = []
        if state.get("agent_messages"):
            for msg in state["agent_messages"]:
                used_agents.append({
                    "agent_name": msg.get("agent", "unknown"),
                    "timestamp": datetime.now().isoformat(),
                    "input_summary": str(msg.get("input_snapshot", {}).get("user_query", ""))[:100] + "...",
                    "operation": operation_type
                })
        
        # 태스크 제목과 설명 생성
        task_title = f"{operation_type}: {state.get('title', '제목 없음')}"
        task_description = f"""작업 타입: {operation_type}
사용자 질문: {state.get('initial_input', '')}
생성된 항목 ID: {calendar_item_id}
사용된 에이전트: {[agent['agent_name'] for agent in used_agents]}
처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}""".strip()
        
        # access_token 추출 (Bearer 토큰에서)
        access_token = None
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header[7:]  # "Bearer " 제거
        
        # due_at 설정 (기본값: 현재 시간 + 1일)
        due_at = state.get("due_at", (datetime.now() + timedelta(days=1)).isoformat())
        
        # 에이전트 태스크 생성
        task_result = await create_agent_task(
            title=task_title,
            description=task_description,
            due_at=due_at,
            used_agents=used_agents,
            access_token=access_token
        )
        
        if "error" not in task_result:
            state["created_agent_task"] = task_result
            print(f"✅ 에이전트 태스크 생성 완료: {task_result.get('task_id', 'N/A')}")
        else:
            print(f"⚠️  에이전트 태스크 생성 실패: {task_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 에이전트 태스크 생성 중 오류 발생: {str(e)}")

async def create_agent_event_for_calendar_operation(
    state: Dict, 
    calendar_event_id: str,
    auth_header: Optional[str] = None
) -> None:
    """
    캘린더 이벤트 생성 후 에이전트 이벤트 생성
    
    Args:
        state: 현재 상태
        calendar_event_id: 생성된 캘린더 이벤트 ID
        auth_header: 인증 헤더
    """
    try:
        # 사용된 에이전트 이름 추출
        created_by_agent = "answer_generator"
        if state.get("agent_messages"):
            # 가장 최근 에이전트 사용
            latest_agent = state["agent_messages"][-1]
            created_by_agent = latest_agent.get("agent", "answer_generator")
        
        # 에이전트 이벤트 제목과 설명 생성
        event_title = f"{state.get('title', '제목 없음')}"
        event_description = f"""사용자 요청으로 캘린더 이벤트를 생성했습니다.
사용자 질문: {state.get('initial_input', '')}
생성된 이벤트 ID: {calendar_event_id}
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}""".strip()
        
        # 위치 정보 (기본값 또는 event_payload에서 추출)
        location = state.get("location", "위치 미지정")
        if state.get("event_payload") and state["event_payload"].get("location"):
            location = state["event_payload"]["location"]
        
        # 시작/종료 시간
        start_at = state.get("start_at", datetime.now().isoformat())
        end_at = state.get("end_at", datetime.now().isoformat())
        
        # access_token 추출 (Bearer 토큰에서)
        access_token = None
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header[7:]  # "Bearer " 제거
        
        # 에이전트 이벤트 생성
        event_result = await create_agent_event(
            title=event_title,
            description=event_description,
            start_at=start_at,
            end_at=end_at,
            location=location,
            created_by_agent=created_by_agent,
            access_token=access_token
        )
        
        if "error" not in event_result:
            state["created_agent_event"] = event_result
            print(f"✅ 에이전트 이벤트 생성 완료")
        else:
            print(f"⚠️  에이전트 이벤트 생성 실패: {event_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 에이전트 이벤트 생성 중 오류 발생: {str(e)}")

async def handle_agent_event_create(state: Dict, base_url: str, headers: Dict) -> Dict:
    """에이전트 이벤트 생성 처리"""
    print("📅 에이전트 이벤트 생성 요청 처리 중...")
    
    # 사용된 에이전트 정보 구성
    created_by_agent = "answer_generator"
    if state.get("agent_messages"):
        # 가장 최근 에이전트 사용
        latest_agent = state["agent_messages"][-1]
        created_by_agent = latest_agent.get("agent", "answer_generator")
    
    # 에이전트 이벤트 생성용 payload 구성
    event_data = {
        "title": state.get("title", ""),
        "description": state.get("initial_input", ""),
        "start_at": state.get("start_at"),
        "end_at": state.get("end_at"),
        "location": state.get("location", "위치 미지정"),
        "source_type": "user",
        "created_by_agent": created_by_agent,
        "timezone": state.get("timezone", "Asia/Seoul")
    }
    
    # event_payload가 있으면 사용
    if state.get("event_payload"):
        event_data.update(state["event_payload"])
    
    # API 엔드포인트 - agent events API 사용
    api_url = f"{base_url}/api/v1/agent/events"
    print(f"🌐 POST 요청 - 에이전트 이벤트 생성: {api_url}")
    
    # 디버깅 정보 출력
    print(f"🔍 에이전트 이벤트 생성 디버깅:")
    print(f"   - API URL: {api_url}")
    print(f"   - Headers: {headers}")
    print(f"   - Payload: {event_data}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 POST 요청 전송 중...")
            print(f"   - Method: POST")
            print(f"   - URL: {api_url}")
            print(f"   - Headers: {headers}")
            print(f"   - Payload: {event_data}")
            response = await client.post(api_url, json=event_data, headers=headers)
            
            print(f"📊 POST 응답 상태 코드: {response.status_code}")
            print(f"📄 POST 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                state["crud_result"] = f"에이전트 이벤트 생성 완료: {result.get('id', 'N/A')}"
                print(f"✅ 에이전트 이벤트 생성 완료: {result.get('id', 'N/A')}")
                print(f"📋 생성된 에이전트 이벤트 정보:")
                print(f"   - 제목: {result.get('title', 'N/A')}")
                print(f"   - 설명: {result.get('description', 'N/A')}")
                print(f"   - 시작: {result.get('start_at', 'N/A')}")
                print(f"   - 종료: {result.get('end_at', 'N/A')}")
                print(f"   - 위치: {result.get('location', 'N/A')}")
                print(f"   - 이벤트 ID: {result.get('id', 'N/A')}")
            else:
                error_msg = f"에이전트 이벤트 생성 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
                print(f"📄 응답 내용: {response.text}")
    except Exception as e:
        error_msg = f"에이전트 이벤트 생성 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

async def handle_agent_event_read(state: Dict, base_url: str, headers: Dict) -> Dict:
    """에이전트 이벤트 조회 처리"""
    print("📅 에이전트 이벤트 조회 요청 처리 중...")
    
    # 특정 에이전트 이벤트 조회 (event_id가 필요함)
    if state.get("selected_item_id"):
        api_url = f"{base_url}/api/v1/agent/events/{state['selected_item_id']}"
        print(f"🌐 GET 요청 - 특정 에이전트 이벤트 조회: {api_url}")
        print(f"🔍 조회할 에이전트 이벤트 ID: {state['selected_item_id']}")
    else:
        # 전체 에이전트 이벤트 조회 (현재는 지원하지 않음 - 특정 event_id 필요)
        error_msg = "에이전트 이벤트 조회를 위해서는 event_id가 필요합니다. 구체적인 이벤트 ID를 지정해주세요."
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        return state
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 GET 요청 전송 중...")
            print(f"   - Method: GET")
            print(f"   - URL: {api_url}")
            print(f"   - Headers: {headers}")
            response = await client.get(api_url, headers=headers)
            
            print(f"📊 GET 응답 상태 코드: {response.status_code}")
            print(f"📄 GET 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 특정 에이전트 이벤트 조회 완료")
                print(f"📋 에이전트 이벤트 상세 정보:")
                print(f"   - 제목: {result.get('title', 'N/A')}")
                print(f"   - 설명: {result.get('description', 'N/A')}")
                print(f"   - 시작: {result.get('start_at', 'N/A')}")
                print(f"   - 종료: {result.get('end_at', 'N/A')}")
                print(f"   - 위치: {result.get('location', 'N/A')}")
                print(f"   - 이벤트 ID: {result.get('id', 'N/A')}")
                print(f"   - 사용자 ID: {result.get('user_id', 'N/A')}")
                print(f"   - 생성 에이전트: {result.get('created_by_agent', 'N/A')}")
                print(f"   - 소스 타입: {result.get('source_type', 'N/A')}")
                print(f"   - 생성 시간: {result.get('created_at', 'N/A')}")
                print(f"   - 수정 시간: {result.get('updated_at', 'N/A')}")
                
                # 전체 응답 데이터 출력
                print(f"📋 전체 응답 데이터: {result}")
                
                # 응답 결과를 state에 저장
                state["crud_result"] = f"에이전트 이벤트 조회 완료: {result.get('title', 'N/A')} (ID: {result.get('id', 'N/A')})"
                state["agent_event_details"] = result  # 전체 응답 데이터 저장
                
            elif response.status_code == 404:
                error_msg = f"에이전트 이벤트를 찾을 수 없습니다. (ID: {state.get('selected_item_id', 'N/A')}) - 해당 이벤트가 존재하지 않거나 현재 사용자의 이벤트가 아닙니다."
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
            else:
                error_msg = f"에이전트 이벤트 조회 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
                print(f"📄 응답 내용: {response.text}")
    except Exception as e:
        error_msg = f"에이전트 이벤트 조회 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

async def handle_agent_event_update(state: Dict, base_url: str, headers: Dict) -> Dict:
    """에이전트 이벤트 수정 처리"""
    print("📅 에이전트 이벤트 수정 요청 처리 중...")
    
    if not state.get("selected_item_id"):
        error_msg = "수정할 에이전트 이벤트 ID가 필요합니다."
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        return state
    
    # 수정할 데이터 구성
    update_data = {}
    if state.get("title"):
        update_data["title"] = state["title"]
    if state.get("description"):
        update_data["description"] = state["description"]
    if state.get("start_at"):
        update_data["start_at"] = state["start_at"]
    if state.get("end_at"):
        update_data["end_at"] = state["end_at"]
    if state.get("location"):
        update_data["location"] = state["location"]
    if state.get("timezone"):
        update_data["timezone"] = state["timezone"]
    
    # event_payload가 있으면 사용
    if state.get("event_payload"):
        update_data.update(state["event_payload"])
    
    # API 엔드포인트 - agent events API 사용
    api_url = f"{base_url}/api/v1/agent/events/{state['selected_item_id']}"
    print(f"🌐 PUT 요청 - 에이전트 이벤트 수정: {api_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 PUT 요청 전송 중...")
            print(f"   - Method: PUT")
            print(f"   - URL: {api_url}")
            print(f"   - Headers: {headers}")
            print(f"   - Payload: {update_data}")
            response = await client.put(api_url, json=update_data, headers=headers)
            
            print(f"📊 PUT 응답 상태 코드: {response.status_code}")
            print(f"📄 PUT 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                state["crud_result"] = f"에이전트 이벤트 수정 완료: {result.get('id', 'N/A')}"
                print(f"✅ 에이전트 이벤트 수정 완료: {result.get('id', 'N/A')}")
                print(f"📋 수정된 에이전트 이벤트 정보:")
                print(f"   - 제목: {result.get('title', 'N/A')}")
                print(f"   - 설명: {result.get('description', 'N/A')}")
                print(f"   - 시작: {result.get('start_at', 'N/A')}")
                print(f"   - 종료: {result.get('end_at', 'N/A')}")
                print(f"   - 위치: {result.get('location', 'N/A')}")
                print(f"   - 이벤트 ID: {result.get('id', 'N/A')}")
            elif response.status_code == 404:
                error_msg = f"수정할 에이전트 이벤트를 찾을 수 없습니다. (ID: {state['selected_item_id']}) - 해당 이벤트가 존재하지 않거나 현재 사용자의 이벤트가 아닙니다."
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
            else:
                error_msg = f"에이전트 이벤트 수정 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
                print(f"📄 응답 내용: {response.text}")
    except Exception as e:
        error_msg = f"에이전트 이벤트 수정 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

async def handle_agent_event_delete(state: Dict, base_url: str, headers: Dict) -> Dict:
    """에이전트 이벤트 삭제 처리"""
    print("📅 에이전트 이벤트 삭제 요청 처리 중...")
    
    if not state.get("selected_item_id"):
        error_msg = "삭제할 에이전트 이벤트 ID가 필요합니다. 구체적인 이벤트를 지정해주세요."
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        return state
    
    # API 엔드포인트 - agent events API 사용
    api_url = f"{base_url}/api/v1/agent/events/{state['selected_item_id']}"
    print(f"🌐 DELETE 요청 - 에이전트 이벤트 삭제: {api_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 DELETE 요청 전송 중...")
            print(f"   - Method: DELETE")
            print(f"   - URL: {api_url}")
            print(f"   - Headers: {headers}")
            response = await client.delete(api_url, headers=headers)
            
            print(f"📊 DELETE 응답 상태 코드: {response.status_code}")
            print(f"📄 DELETE 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                # 200 OK - 성공적으로 삭제됨
                state["crud_result"] = f"에이전트 이벤트 삭제 완료: {state['selected_item_id']}"
                print(f"✅ 에이전트 이벤트 삭제 완료: {state['selected_item_id']}")
            elif response.status_code == 404:
                error_msg = f"삭제할 에이전트 이벤트를 찾을 수 없습니다. (ID: {state['selected_item_id']}) - 해당 이벤트가 존재하지 않거나 현재 사용자의 이벤트가 아닙니다."
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
            else:
                error_msg = f"에이전트 이벤트 삭제 실패: {response.status_code} - {response.text}"
                state["crud_result"] = error_msg
                print(f"❌ {error_msg}")
                print(f"📄 응답 내용: {response.text}")
    except Exception as e:
        error_msg = f"에이전트 이벤트 삭제 중 오류 발생: {str(e)}"
        state["crud_result"] = error_msg
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return state

def answer_generator(state: Dict) -> Dict:
    user_query = state["initial_input"]
    rag_info = state.get("rag_result", "")
    web_info = state.get("search_result", "")
    crud_info = state.get("crud_result", "")
    prev_answer = state.get("final_output", "")  # answer_planner/이전 에이전트 답변

    prompt = f"""
    당신은 '요식업 자영업자'를 도와주는 실무 전문 어시스턴트입니다.  
세무, 위생, 일정, 민원 대응 등 실생활에서 마주치는 행정·정보적 이슈를 **전문적이되 친절한 상담 톤**으로 도와주세요.

[사용자 질문]
\"\"\"{user_query}\"\"\"  

[문서 기반 정보 (RAG)]
\"\"\"{rag_info if rag_info else "관련 문서 검색 정보 없음"}\"\"\"  

[웹 검색 결과]
\"\"\"{web_info if web_info else "관련 웹 검색 결과 없음"}\"\"\"  

[일정 정보 또는 처리 결과]
\"\"\"{crud_info if crud_info else "일정/처리 결과 없음"}\"\"\"  

[이전 생성된 응답 또는 초안 (AnswerPlanner)]
\"\"\"{prev_answer if prev_answer else "이전 답변 없음"}\"\"\"  

---

작성 지침:
- **일정 정보 또는 처리 방법**이 있다면 가장 먼저 안내하세요.
- 모든 정보(RAG/웹/이전 답변 등)를 종합하여, 중복 없이 핵심만 정리해 실무적으로 설명해주세요.
- 필요 시 관련 배경 지식도 간단히 덧붙이되, 복잡한 법령 해석보다는 **실행 중심**으로 답변하세요.
- 답변 톤은 "동네 세무사/상담사/법무사처럼 도메인 지식에 대한 전문성을 바탕으로, 자영업자들이 이해할 수 있게 친절하게" 유지해주세요.
- 마지막엔 **사용자의 후속 질문을 유도**하거나 **관련 이슈에 대한 안내**로 마무리하면 좋습니다.

👉 위 정보를 바탕으로, 사용자의 질문에 대해 실질적으로 도움 되는 요약형 응답을 아래에 작성해주세요. (1회 출력만)

    """

    response = model.invoke(prompt)
    final_response = response.content.strip()

    state["final_output"] = final_response
    state.setdefault("agent_messages", []).append({
        "agent": "answer_generator",
        "input_snapshot": {
            "user_query": user_query,
            "rag_info": rag_info,
            "web_info": web_info,
            "crud_info": crud_info,
            "prev_answer": prev_answer
        },
        "output": final_response
    })

    # 캘린더 API 요청 처리 (calendar_type과 calendar_operation이 설정된 경우)
    print(f"🔍 캘린더 API 요청 디버깅:")
    print(f"   - calendar_type: {state.get('calendar_type')}")
    print(f"   - calendar_operation: {state.get('calendar_operation')}")
    print(f"   - agent_task_type: {state.get('agent_task_type')}")
    print(f"   - agent_task_operation: {state.get('agent_task_operation')}")
    print(f"   - state keys: {list(state.keys())}")
    
    # 두 가지 네이밍 컨벤션 모두 지원
    calendar_type = state.get("calendar_type") or state.get("agent_task_type")
    calendar_operation = state.get("calendar_operation") or state.get("agent_task_operation")
    
    # calselector에서 가져온 데이터 확인
    events = state.get("events", [])
    tasks = state.get("tasks", [])
    selected_item_id = state.get("selected_item_id")
    
    print(f"🔍 CalSelector 데이터 확인:")
    print(f"   - events 개수: {len(events)}")
    print(f"   - tasks 개수: {len(tasks)}")
    print(f"   - selected_item_id: {selected_item_id}")
    
    if calendar_type and calendar_operation:
        print(f"✅ 캘린더 작업 조건 충족 - {calendar_type} + {calendar_operation}")
        
        # calselector에서 이미 데이터를 가져왔으므로, 해당 데이터를 활용
        if calendar_type == "task" and calendar_operation == "read":
            # 할일 조회: selected_item_id가 있으면 실제 API 호출
            if selected_item_id:
                print(f"📋 할일 조회 API 호출 시작... (ID: {selected_item_id})")
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    state = loop.run_until_complete(handle_calendar_api_request(state))
                    
                except Exception as e:
                    print(f"❌ 캘린더 API 요청 처리 중 오류 발생: {str(e)}")
            else:
                # selected_item_id가 없는 경우 CalSelector 데이터 사용
                if tasks:
                    print(f"✅ CalSelector에서 가져온 할일 목록 사용:")
                    for i, task in enumerate(tasks[:5], 1):
                        print(f"   {i}. [{task.get('task_id', 'N/A')}] {task.get('title', 'N/A')}")
                    
                    state["crud_result"] = f"할일 목록 조회 완료: {len(tasks)}개 항목"
                else:
                    state["crud_result"] = "조회할 할일이 없습니다."
                
        elif calendar_type == "task" and calendar_operation == "create":
            # 할일 생성: API 호출 필요
            print(f"📋 할일 생성 API 호출 시작...")
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                state = loop.run_until_complete(handle_calendar_api_request(state))
                
            except Exception as e:
                print(f"❌ 캘린더 API 요청 처리 중 오류 발생: {str(e)}")
                
        elif calendar_type == "task" and calendar_operation == "update":
            # 할일 수정: API 호출 필요
            print(f"📋 할일 수정 API 호출 시작...")
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                state = loop.run_until_complete(handle_calendar_api_request(state))
                
            except Exception as e:
                print(f"❌ 캘린더 API 요청 처리 중 오류 발생: {str(e)}")
                
        elif calendar_type == "task" and calendar_operation == "delete":
            # 할일 삭제: API 호출 필요
            print(f"📋 할일 삭제 API 호출 시작...")
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                state = loop.run_until_complete(handle_calendar_api_request(state))
                
            except Exception as e:
                print(f"❌ 캘린더 API 요청 처리 중 오류 발생: {str(e)}")
                
        elif calendar_type == "agent_event":
            # 에이전트 이벤트 작업: API 호출 필요
            print(f"📋 에이전트 이벤트 {calendar_operation} API 호출 시작...")
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                state = loop.run_until_complete(handle_calendar_api_request(state))
                
            except Exception as e:
                print(f"❌ 캘린더 API 요청 처리 중 오류 발생: {str(e)}")
                
        else:
            # 기타 작업: 캘린더 API 호출하지 않음
            print(f"⚠️ 기타 calendar_type/calendar_operation 조합 - API 호출하지 않음")
            try:
                state["crud_result"] = "지원하지 않는 캘린더 작업이거나 API 호출 조건 불충족"
            except Exception as e:
                print(f"❌ 캘린더 API 요청 처리 중 오류 발생: {str(e)}")
    else:
        print(f"⚠️  캘린더 API 요청 조건 불충족 - calendar_type 또는 calendar_operation이 설정되지 않음")


    # 캘린더 API 요청 처리 (calendar_type과 calendar_operation이 설정된 경우)
    if state.get("calendar_type") and state.get("calendar_operation"):
        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            state = loop.run_until_complete(handle_calendar_api_request(state))
            
        except Exception as e:
            print(f"❌ 캘린더 API 요청 처리 중 오류 발생: {str(e)}")

    # ✅ 로그 전송 추가
    try:
        payload = make_agent_logs_payload(state)
        send_log_to_backend(payload)
        state["log_sent"] = send_log_to_backend(payload)
    except Exception as e:
        state["log_sent"] = False
        print(f"❌ 현운 로그 전송 중 오류 발생: {str(e)}")

    return state
