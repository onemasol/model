import sys
import os
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.task_router import task_router
from agents.calendar_agent import calendar_agent
from agents.answer_planner import answer_planner
from agents.answer_generator import answer_generator
from agents.calselector import calselector
from models.agent_state import AgentState

def test_agent_task_flow():
    """Agent Task CRUD 플로우를 테스트합니다."""
    
    print("=" * 80)
    print("🤖 Agent Task CRUD 테스트")
    print("⚠️  실제 API 요청이 발생할 수 있습니다!")
    print("=" * 80)
    
    # Agent Task CRUD 테스트 케이스들
    agent_task_test_cases = [
        {
            "description": "🤖 에이전트 태스크 생성",
            "input": "새로운 프로젝트 태스크를 생성해줘",
            "agent_task_type": "task",
            "agent_task_operation": "create",
            "title": "새로운 프로젝트",
            "description": "새로운 프로젝트를 위한 태스크입니다.",
            "status": "pending",
            "used_agents": [
                {
                    "agent_name": "task_router",
                    "timestamp": "2025-06-25T12:00:00Z",
                    "input_summary": "새로운 프로젝트 태스크 생성 요청",
                    "operation": "태스크 생성"
                }
            ]
        },
        {
            "description": "🔍 에이전트 태스크 조회",
            "input": "태스크 ID 12345의 정보를 조회해줘",
            "agent_task_type": "task",
            "agent_task_operation": "read",
            "selected_item_id": "12345"
        },
        {
            "description": "✏️ 에이전트 태스크 수정",
            "input": "태스크 ID 12345의 상태를 완료로 변경해줘",
            "agent_task_type": "task",
            "agent_task_operation": "update",
            "selected_item_id": "12345",
            "status": "completed"
        },
        {
            "description": "🗑️ 에이전트 태스크 삭제",
            "input": "태스크 ID 12345를 삭제해줘",
            "agent_task_type": "task",
            "agent_task_operation": "delete",
            "selected_item_id": "12345"
        },
        {
            "description": "📋 복잡한 에이전트 태스크 생성",
            "input": "다중 에이전트 협업 태스크를 생성해줘",
            "agent_task_type": "task",
            "agent_task_operation": "create",
            "title": "다중 에이전트 협업 프로젝트",
            "description": "여러 에이전트가 협업하는 복잡한 프로젝트입니다.",
            "status": "in_progress",
            "used_agents": [
                {
                    "agent_name": "task_router",
                    "timestamp": "2025-06-25T12:00:00Z",
                    "input_summary": "다중 에이전트 협업 태스크 생성",
                    "operation": "태스크 생성"
                },
                {
                    "agent_name": "calendar_agent",
                    "timestamp": "2025-06-25T12:01:00Z",
                    "input_summary": "일정 관리 지원",
                    "operation": "일정 관리"
                },
                {
                    "agent_name": "answer_planner",
                    "timestamp": "2025-06-25T12:02:00Z",
                    "input_summary": "답변 계획 수립",
                    "operation": "답변 계획"
                }
            ]
        }
    ]
    
    for i, test_case in enumerate(agent_task_test_cases, 1):
        print(f"\n🧪 Agent Task 테스트 {i}: {test_case['description']}")
        print("-" * 60)
        print(f"입력: {test_case['input']}")
        
        # 초기 상태 설정 (Agent Task CRUD용)
        initial_state = {
            "type": "question",
            "initial_input": test_case["input"],
            "rag_result": "에이전트 태스크 관련 정보",
            "search_result": "에이전트 태스크 검색 결과",
            "crud_result": None,
            "final_answer": None,
            "next_node": None,
            "agent_messages": [
                {
                    "agent": "task_router",
                    "input_snapshot": {"user_query": test_case["input"]},
                    "output": "에이전트 태스크 처리 준비 완료"
                }
            ],
            "router_messages": [],
            "user_id": "542c2e7e-256a-4e15-abdb-f38310e94007",
            
            # Agent Task CRUD 설정
            "agent_task_type": test_case.get("agent_task_type"),
            "agent_task_operation": test_case.get("agent_task_operation"),
            "title": test_case.get("title"),
            "description": test_case.get("description"),
            "status": test_case.get("status"),
            "used_agents": test_case.get("used_agents"),
            "selected_item_id": test_case.get("selected_item_id")
        }
        
        # 전체 시작 시간
        total_start_time = time.time()
        
        try:
            # Agent Task CRUD 직접 테스트 (answer_generator만 실행)
            print("\n🤖 Agent Task CRUD 테스트")
            step_start_time = time.time()
            result = answer_generator(initial_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print(f"✅ Agent Task CRUD 결과:")
            print(f"   - 최종 답변: {result.get('final_answer', 'N/A')}")
            print(f"   - CRUD 결과: {result.get('crud_result', 'N/A')}")
            print(f"   - 에이전트 메시지: {len(result.get('agent_messages', []))}개")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
            # API 요청 결과 확인
            crud_result = result.get('crud_result')
            if crud_result:
                print(f"   🎯 API 요청 결과: {crud_result}")
            else:
                print("   ⚠️  API 요청 결과가 없습니다.")
            
            # 생성된 에이전트 태스크 확인
            if result.get('created_agent_task'):
                print(f"   📋 생성된 에이전트 태스크: {result['created_agent_task']}")
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            
            # 전체 플로우 요약
            print(f"\n📊 Agent Task CRUD 요약:")
            print(f"   - 입력: {test_case['input']}")
            print(f"   - 작업: {test_case.get('agent_task_type')} + {test_case.get('agent_task_operation')}")
            print(f"   - 총 실행 시간: {total_duration:.2f}초")
            
            # API 요청 여부 표시
            if crud_result:
                print(f"   - API 요청: ✅ 발생 (결과: {crud_result})")
            else:
                print(f"   - API 요청: ❌ 발생하지 않음")
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

def test_calendar_flow():
    """task_router → calendar_agent → answer_planner → answer_generator → END 플로우를 테스트합니다."""
    
    print("=" * 80)
    print("📅 Calendar Flow 테스트 (task_router → calendar_agent → answer_planner → answer_generator)")
    print("⚠️  실제 API 요청이 발생할 수 있습니다!")
    print("=" * 80)
    
    # 일정 등록 관련 테스트 케이스들
    test_cases = [
        {
            "description": "🕐 정확한 시간 일정 생성 (분 단위)",
            "input": "다음주 화요일 오후 2시 30분에 치과 예약 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🌙 늦은 밤 일정 생성",
            "input": "오늘 밤 11시 30분에 야간 근무 시작",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "📅 장기 프로젝트 일정",
            "input": "7월 1일부터 7월 15일까지 여름 휴가로 설정해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🔄 반복 일정 생성",
            "input": "매주 월요일 오전 9시에 팀 스크럼 미팅 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🏥 긴급 의료 일정",
            "input": "내일 오전 8시에 응급실 예약 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🎓 학업 관련 할일",
            "input": "다음주 금요일까지 논문 제출 마감일 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "💼 비즈니스 미팅 (시간대 고려)",
            "input": "내일 새벽 3시에 뉴욕 팀과 화상회의 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🎉 특별한 이벤트",
            "input": "12월 25일 크리스마스 파티 오후 6시부터 10시까지 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🏃‍♂️ 운동 일정",
            "input": "매일 아침 6시에 조깅 1시간 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🍽️ 식사 일정",
            "input": "오늘 점심 12시 30분에 고객과 비즈니스 런치 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "✈️ 여행 일정",
            "input": "8월 15일 오전 10시에 인천공항 출발 비행기 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🎭 문화생활",
            "input": "이번주 토요일 오후 2시에 뮤지컬 관람 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🏠 집안일",
            "input": "오늘 저녁 7시에 집 청소 2시간 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "📚 독서 시간",
            "input": "매일 밤 10시에 독서 30분 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "🎵 음악 연습",
            "input": "내일 오후 4시에 피아노 연습 1시간 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        }
    ]
    
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    print("=" * 80)
    print("📅 Calendar Flow 테스트 (task_router → calendar_agent → answer_planner → answer_generator)")
    print("⚠️  실제 API 요청이 발생할 수 있습니다!")
    print("=" * 80)
    
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 테스트 {i}: {test_case['description']}")
        print("-" * 60)
        print(f"입력: {test_case['input']}")
        
        # 초기 상태 설정
        initial_state = {
            "type": "question",
            "initial_input": test_case["input"],
            "rag_result": None,
            "search_result": None,
            "crud_result": None,
            "final_answer": None,
            "next_node": None,
            "agent_messages": [],
            "router_messages": [],
            "user_id": "542c2e7e-256a-4e15-abdb-f38310e94007"  # 실제 사용자 ID 추가
        }
        
        # 전체 시작 시간
        total_start_time = time.time()
        
        try:
            # Step 1: task_router 실행
            print("\n📋 Step 1: Task Router 실행")
            step_start_time = time.time()
            task_result = task_router(initial_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print(f"✅ Task Router 결과:")
            print(f"   - 다음 노드: {task_result.get('next_node', 'N/A')}")
            print(f"   - 라우터 메시지: {len(task_result.get('router_messages', []))}개")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
            # 디버깅: 라우터 메시지 상세 출력
            router_messages = task_result.get('router_messages', [])
            if router_messages:
                print(f"   - 라우터 메시지 상세:")
                for i, msg in enumerate(router_messages, 1):
                    print(f"     {i}. {msg}")
            
            # task_router가 calendar_agent로 라우팅하는지 확인
            if task_result.get('next_node') == 'calendar_agent':
                print("✅ Task Router: calendar_agent로 올바르게 라우팅됨")
            else:
                print(f"⚠️  Task Router: 예상과 다름. 다음 노드: {task_result.get('next_node')}")
                print("   💡 다른 플로우로 진행하겠습니다.")
            
            # Step 2: calendar_agent 실행 (라우팅이 calendar_agent인 경우)
            current_state = task_result.copy()
            calendar_result = None  # 변수 초기화
            if task_result.get('next_node') == 'calendar_agent':
                print("\n📅 Step 2: Calendar Agent 실행")
                step_start_time = time.time()
                calendar_result = calendar_agent(task_result.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = calendar_result.copy()
                
                print(f"✅ Calendar Agent 결과:")
                print(f"   - 타입: {calendar_result.get('calendar_type', 'N/A')}")
                print(f"   - 작업: {calendar_result.get('calendar_operation', 'N/A')}")
                print(f"   - 다음 노드: {calendar_result.get('next_node', 'N/A')}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # 디버깅: calendar_type과 calendar_operation 조합 확인
                calendar_type = calendar_result.get('calendar_type')
                calendar_operation = calendar_result.get('calendar_operation')
                if calendar_type and calendar_operation:
                    print(f"   - 조합: {calendar_type} + {calendar_operation}")
                    if calendar_type == "event" and calendar_operation == "delete":
                        print("   🔍 이벤트 삭제 작업 감지!")
                    elif calendar_type == "task" and calendar_operation == "delete":
                        print("   🔍 할일 삭제 작업 감지!")
                    elif calendar_type == "agent_task" and calendar_operation == "delete":
                        print("   🔍 에이전트 태스크 삭제 작업 감지!")
                
                # 페이로드 정보 출력
                payload = calendar_result.get('event_payload', {})
                if payload:
                    print(f"   - 제목: {payload.get('title', 'N/A')}")
                    print(f"   - 시작 시간: {payload.get('start_at', 'N/A')}")
                    print(f"   - 종료 시간: {payload.get('end_at', 'N/A')}")
                    print(f"   - 마감 시간: {payload.get('due_at', 'N/A')}")
                    print(f"   - 이벤트 타입: {payload.get('event_type', 'N/A')}")
                
                # selected_item_id 확인 (삭제/수정 시 중요)
                selected_item_id = calendar_result.get('selected_item_id')
                if selected_item_id:
                    print(f"   - 선택된 항목 ID: {selected_item_id}")
                
                # calendar_agent가 answer_planner로 라우팅하는지 확인
                if calendar_result.get('next_node') == 'answer_planner':
                    print("✅ Calendar Agent: answer_planner로 올바르게 라우팅됨")
                else:
                    print(f"⚠️  Calendar Agent: 예상과 다름. 다음 노드: {calendar_result.get('next_node')}")
            else:
                print("\n📅 Step 2: Calendar Agent 건너뜀 (다른 플로우)")
            
            # Step 3: calselector 실행 (라우팅이 calselector인 경우)
            selector_result = None  # 변수 초기화
            if current_state.get('next_node') == 'calselector':
                print("\n🎯 Step 3: CalSelector 실행")
                step_start_time = time.time()
                selector_result = calselector(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = selector_result.copy()
                
                print(f"✅ CalSelector 결과:")
                print(f"   - 다음 노드: {selector_result.get('next_node', 'N/A')}")
                print(f"   - 선택된 항목 ID: {selector_result.get('selected_item_id', 'N/A')}")
                print(f"   - API 응답: {len(selector_result.get('api_responses', []))}개")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # API 응답 정보 출력
                api_responses = selector_result.get('api_responses', [])
                if api_responses:
                    for i, response in enumerate(api_responses, 1):
                        print(f"   - API 응답 {i}:")
                        print(f"     - 상태 코드: {response.get('status_code', 'N/A')}")
                        print(f"     - 성공 여부: {response.get('success', 'N/A')}")
                        data = response.get('data', {})
                        print(f"     - 이벤트 수: {data.get('event_count', 0)}개")
                        print(f"     - 태스크 수: {data.get('task_count', 0)}개")
                        print(f"     - 총 항목 수: {data.get('total_count', 0)}개")
                
                # calselector가 answer_generator로 라우팅하는지 확인
                if selector_result.get('next_node') == 'answer_generator':
                    print("✅ CalSelector: answer_generator로 올바르게 라우팅됨")
                else:
                    print(f"⚠️  CalSelector: 예상과 다름. 다음 노드: {selector_result.get('next_node')}")
            else:
                print("\n🎯 Step 3: CalSelector 건너뜀 (다른 플로우)")
            
            # Step 4: answer_planner 실행 (라우팅이 answer_planner인 경우)
            planner_result = None  # 변수 초기화
            if current_state.get('next_node') == 'answer_planner':
                print("\n📝 Step 4: Answer Planner 실행")
                step_start_time = time.time()
                planner_result = answer_planner(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = planner_result.copy()
                
                print(f"✅ Answer Planner 결과:")
                print(f"   - 다음 노드: {planner_result.get('next_node', 'N/A')}")
                print(f"   - 에이전트 메시지: {len(planner_result.get('agent_messages', []))}개")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # 디버깅: 에이전트 메시지 상세 출력
                agent_messages = planner_result.get('agent_messages', [])
                if agent_messages:
                    print(f"   - 에이전트 메시지 상세:")
                    for i, msg in enumerate(agent_messages, 1):
                        agent_name = msg.get('agent', 'unknown')
                        output = msg.get('output', 'N/A')
                        print(f"     {i}. {agent_name}: {output[:100]}...")
                
                # answer_planner가 answer_generator로 라우팅하는지 확인
                if planner_result.get('next_node') == 'answer_generator':
                    print("✅ Answer Planner: answer_generator로 올바르게 라우팅됨")
                else:
                    print(f"⚠️  Answer Planner: 예상과 다름. 다음 노드: {planner_result.get('next_node')}")
            else:
                print("\n📝 Step 4: Answer Planner 건너뜀 (다른 플로우)")
            
            # Step 5: answer_generator 실행 (항상 실행)
            print("\n💬 Step 5: Answer Generator 실행")
            step_start_time = time.time()
            answer_result = answer_generator(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print(f"✅ Answer Generator 결과:")
            print(f"   - 최종 답변: {answer_result.get('final_answer', 'N/A')}")
            print(f"   - 에이전트 메시지: {len(answer_result.get('agent_messages', []))}개")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            # 디버깅: 현재 상태의 중요 필드들 확인
            print(f"   - 현재 상태 디버깅:")
            print(f"     - calendar_type: {current_state.get('calendar_type', 'N/A')}")
            print(f"     - calendar_operation: {current_state.get('calendar_operation', 'N/A')}")
            print(f"     - agent_task_type: {current_state.get('agent_task_type', 'N/A')}")
            print(f"     - agent_task_operation: {current_state.get('agent_task_operation', 'N/A')}")
            print(f"     - selected_item_id: {current_state.get('selected_item_id', 'N/A')}")
            
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            # API 요청 결과 확인
            crud_result = answer_result.get('crud_result')
            if crud_result:
                print(f"   🎯 API 요청 결과: {crud_result}")
            else:
                print("   ⚠️  API 요청 결과가 없습니다.")
            
            # 생성된 에이전트 태스크/이벤트 확인
            if answer_result.get('created_agent_task'):
                print(f"   📋 생성된 에이전트 태스크: {answer_result['created_agent_task']}")
            
            if answer_result.get('created_agent_event'):
                print(f"   📅 생성된 에이전트 이벤트: {answer_result['created_agent_event']}")
            
            # 최종 답변이 생성되었는지 확인
            if answer_result.get('final_answer'):
                print("✅ Answer Generator: 최종 답변 생성 완료")
            else:
                print("❌ Answer Generator: 최종 답변 생성 실패")
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            
            # 전체 플로우 요약
            print(f"\n📊 전체 플로우 요약:")
            print(f"   - 입력: {test_case['input']}")
            
            # 실제 실행된 플로우 표시
            actual_flow = []
            if task_result.get('next_node'):
                actual_flow.append("task_router")
                if task_result.get('next_node') == 'calendar_agent' and calendar_result:
                    actual_flow.append("calendar_agent")
                    if calendar_result.get('next_node') == 'calselector' and selector_result:
                        actual_flow.append("calselector")
                        if selector_result.get('next_node') == 'answer_generator':
                            actual_flow.append("answer_generator")
                        else:
                            actual_flow.append(f"answer_generator(직접)")
                    elif calendar_result.get('next_node') == 'answer_planner' and planner_result:
                        actual_flow.append("answer_planner")
                        if planner_result.get('next_node') == 'answer_generator':
                            actual_flow.append("answer_generator")
                        else:
                            actual_flow.append(f"answer_generator(직접)")
                    else:
                        actual_flow.append(f"answer_generator(직접)")
                else:
                    actual_flow.append(f"answer_generator(직접)")
            else:
                actual_flow.append("answer_generator(직접)")
            
            print(f"   - 실제 플로우: {' → '.join(actual_flow)}")
            print(f"   - 총 실행 시간: {total_duration:.2f}초")
            
            # API 요청 여부 표시
            if crud_result:
                print(f"   - API 요청: ✅ 발생 (결과: {crud_result})")
            else:
                print(f"   - API 요청: ❌ 발생하지 않음")
            
            final_answer = answer_result.get('final_answer', 'N/A')
            if final_answer and final_answer != 'N/A':
                print(f"   - 최종 답변: {final_answer[:100]}...")
            else:
                print(f"   - 최종 답변: {final_answer}")
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

def test_interactive_calendar_flow():
    """사용자 입력을 받아서 calendar flow를 대화형으로 테스트합니다."""
    
    print("\n" + "=" * 80)
    print("🎯 대화형 Calendar Flow 테스트")
    print("⚠️  실제 API 요청이 발생할 수 있습니다!")
    print("=" * 80)
    print("일정 등록 관련 질문을 입력하면 task_router → calendar_agent → answer_planner → answer_generator 플로우를 테스트합니다.")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    
    print("\n💡 재미있는 예시들:")
    print("   🕐 '다음주 화요일 오후 2시 30분에 치과 예약 추가해줘'")
    print("   🌙 '오늘 밤 11시 30분에 야간 근무 시작'")
    print("   📅 '7월 1일부터 7월 15일까지 여름 휴가로 설정해줘'")
    print("   🔄 '매주 월요일 오전 9시에 팀 스크럼 미팅 추가해줘'")
    print("   🏥 '내일 오전 8시에 응급실 예약 추가해줘'")
    print("   🎓 '다음주 금요일까지 논문 제출 마감일 추가해줘'")
    print("   💼 '내일 새벽 3시에 뉴욕 팀과 화상회의 추가해줘'")
    print("   🎉 '12월 25일 크리스마스 파티 오후 6시부터 10시까지 추가해줘'")
    print("   🏃‍♂️ '매일 아침 6시에 조깅 1시간 추가해줘'")
    print("   🍽️ '오늘 점심 12시 30분에 고객과 비즈니스 런치 추가해줘'")
    print("   ✈️ '8월 15일 오전 10시에 인천공항 출발 비행기 추가해줘'")
    print("   🎭 '이번주 토요일 오후 2시에 뮤지컬 관람 추가해줘'")
    print("   🏠 '오늘 저녁 7시에 집 청소 2시간 추가해줘'")
    print("   📚 '매일 밤 10시에 독서 30분 추가해줘'")
    print("   🎵 '내일 오후 4시에 피아노 연습 1시간 추가해줘'")
    
    while True:
        # 사용자 입력 받기
        user_input = input("\n📝 일정 등록 질문을 입력하세요: ").strip()
        
        # 종료 조건 확인
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n테스트를 종료합니다.")
            break
        
        if not user_input:
            print("입력이 비어있습니다. 다시 입력해주세요.")
            continue
        
        print(f"\n🔄 '{user_input}' 처리 중...")
        
        # 초기 상태 설정
        initial_state = {
            "type": "question",
            "initial_input": user_input,
            "rag_result": None,
            "search_result": None,
            "crud_result": None,
            "final_answer": None,
            "next_node": None,
            "agent_messages": [],
            "router_messages": [],
            "user_id": "542c2e7e-256a-4e15-abdb-f38310e94007"  # 실제 사용자 ID 추가
        }
        
        # 전체 시작 시간
        total_start_time = time.time()
        
        try:
            # Step 1: task_router
            print("\n1️⃣ Task Router 실행...")
            step_start_time = time.time()
            task_result = task_router(initial_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            next_node = task_result.get('next_node')
            print(f"   → 다음 노드: {next_node}")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
            if next_node != 'calendar_agent':
                print(f"   ⚠️  calendar_agent로 라우팅되지 않음. 실제: {next_node}")
                print("   💡 다른 플로우로 진행하겠습니다.")
            
            # Step 2: calendar_agent (라우팅이 calendar_agent인 경우)
            current_state = task_result.copy()
            calendar_result = None  # 변수 초기화
            if task_result.get('next_node') == 'calendar_agent':
                print("\n2️⃣ Calendar Agent 실행...")
                step_start_time = time.time()
                calendar_result = calendar_agent(task_result.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = calendar_result.copy()
                
                # 캘린더 결과 출력
                payload = calendar_result.get('event_payload', {})
                if payload:
                    print(f"   → 일정 정보:")
                    print(f"     - 제목: {payload.get('title', 'N/A')}")
                    print(f"     - 시작: {payload.get('start_at', 'N/A')}")
                    print(f"     - 종료: {payload.get('end_at', 'N/A')}")
                    print(f"     - 마감: {payload.get('due_at', 'N/A')}")
                    print(f"     - 타입: {payload.get('event_type', 'N/A')}")
                
                next_node = calendar_result.get('next_node')
                print(f"   → 다음 노드: {next_node}")
                print(f"   → 실행 시간: {step_duration:.2f}초")
                
                if next_node != 'answer_planner':
                    print(f"   ⚠️  answer_planner로 라우팅되지 않음. 실제: {next_node}")
            else:
                print("\n2️⃣ Calendar Agent 건너뜀 (다른 플로우)")
            
            # Step 3: calselector 실행 (라우팅이 calselector인 경우)
            selector_result = None  # 변수 초기화
            if current_state.get('next_node') == 'calselector':
                print("\n🎯 Step 3: CalSelector 실행")
                step_start_time = time.time()
                selector_result = calselector(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = selector_result.copy()
                
                print(f"✅ CalSelector 결과:")
                print(f"   - 다음 노드: {selector_result.get('next_node', 'N/A')}")
                print(f"   - 선택된 항목 ID: {selector_result.get('selected_item_id', 'N/A')}")
                print(f"   - API 응답: {len(selector_result.get('api_responses', []))}개")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # API 응답 정보 출력
                api_responses = selector_result.get('api_responses', [])
                if api_responses:
                    for i, response in enumerate(api_responses, 1):
                        print(f"   - API 응답 {i}:")
                        print(f"     - 상태 코드: {response.get('status_code', 'N/A')}")
                        print(f"     - 성공 여부: {response.get('success', 'N/A')}")
                        data = response.get('data', {})
                        print(f"     - 이벤트 수: {data.get('event_count', 0)}개")
                        print(f"     - 태스크 수: {data.get('task_count', 0)}개")
                        print(f"     - 총 항목 수: {data.get('total_count', 0)}개")
                
                # calselector가 answer_generator로 라우팅하는지 확인
                if selector_result.get('next_node') == 'answer_generator':
                    print("✅ CalSelector: answer_generator로 올바르게 라우팅됨")
                else:
                    print(f"⚠️  CalSelector: 예상과 다름. 다음 노드: {selector_result.get('next_node')}")
            else:
                print("\n🎯 Step 3: CalSelector 건너뜀 (다른 플로우)")
            
            # Step 4: answer_planner 실행 (라우팅이 answer_planner인 경우)
            planner_result = None  # 변수 초기화
            if current_state.get('next_node') == 'answer_planner':
                print("\n📝 Step 4: Answer Planner 실행")
                step_start_time = time.time()
                planner_result = answer_planner(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = planner_result.copy()
                
                print(f"✅ Answer Planner 결과:")
                print(f"   - 다음 노드: {planner_result.get('next_node', 'N/A')}")
                print(f"   - 에이전트 메시지: {len(planner_result.get('agent_messages', []))}개")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # 디버깅: 에이전트 메시지 상세 출력
                agent_messages = planner_result.get('agent_messages', [])
                if agent_messages:
                    print(f"   - 에이전트 메시지 상세:")
                    for i, msg in enumerate(agent_messages, 1):
                        agent_name = msg.get('agent', 'unknown')
                        output = msg.get('output', 'N/A')
                        print(f"     {i}. {agent_name}: {output[:100]}...")
                
                # answer_planner가 answer_generator로 라우팅하는지 확인
                if planner_result.get('next_node') == 'answer_generator':
                    print("✅ Answer Planner: answer_generator로 올바르게 라우팅됨")
                else:
                    print(f"⚠️  Answer Planner: 예상과 다름. 다음 노드: {planner_result.get('next_node')}")
            else:
                print("\n📝 Step 4: Answer Planner 건너뜀 (다른 플로우)")
            
            # Step 5: answer_generator 실행 (항상 실행)
            print("\n💬 Step 5: Answer Generator 실행")
            step_start_time = time.time()
            answer_result = answer_generator(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            final_answer = answer_result.get('final_answer')
            print(f"   → 최종 답변: {final_answer}")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
            # API 요청 결과 확인
            crud_result = answer_result.get('crud_result')
            if crud_result:
                print(f"   🎯 API 요청 결과: {crud_result}")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
            else:
                print("   ⚠️  API 요청 결과가 없습니다.")
>>>>>>> Stashed changes
=======
            else:
                print("   ⚠️  API 요청 결과가 없습니다.")
>>>>>>> Stashed changes
            
            # 생성된 에이전트 태스크/이벤트 확인
            if answer_result.get('created_agent_task'):
                print(f"   📋 생성된 에이전트 태스크: {answer_result['created_agent_task']}")
            
            if answer_result.get('created_agent_event'):
                print(f"   📅 생성된 에이전트 이벤트: {answer_result['created_agent_event']}")
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            print(f"\n⏱️  총 실행 시간: {total_duration:.2f}초")
            
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            # 실제 실행된 플로우 표시
            actual_flow = []
            if task_result.get('next_node'):
                actual_flow.append("task_router")
                if task_result.get('next_node') == 'calendar_agent' and calendar_result:
                    actual_flow.append("calendar_agent")
                    if calendar_result.get('next_node') == 'calselector' and selector_result:
                        actual_flow.append("calselector")
                        if selector_result.get('next_node') == 'answer_generator':
                            actual_flow.append("answer_generator")
                        else:
                            actual_flow.append(f"answer_generator(직접)")
                    elif calendar_result.get('next_node') == 'answer_planner' and planner_result:
                        actual_flow.append("answer_planner")
                        if planner_result.get('next_node') == 'answer_generator':
                            actual_flow.append("answer_generator")
                        else:
                            actual_flow.append(f"answer_generator(직접)")
                    else:
                        actual_flow.append(f"answer_generator(직접)")
                else:
                    actual_flow.append(f"answer_generator(직접)")
            else:
                actual_flow.append("answer_generator(직접)")
            
            print(f"🔄 실제 플로우: {' → '.join(actual_flow)}")
            
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            # API 요청 여부 표시
            if crud_result:
                print(f"🎯 API 요청: ✅ 발생 (결과: {crud_result})")
            else:
                print(f"🎯 API 요청: ❌ 발생하지 않음")
            
            if final_answer:
                print("\n✅ 전체 플로우 성공!")
            else:
                print("\n❌ 최종 답변 생성 실패")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🎉 Calendar Flow 테스트를 시작합니다! 🎉")
    print("📅 다양한 일정 시나리오를 테스트해보세요!")
    print("1. 🚀 자동 테스트 (미리 정의된 케이스들)")
    print("2. 💬 대화형 테스트 (사용자 입력)")
    print("3. 🤖 Agent Task CRUD 테스트")
    
    choice = input("\n선택하세요 (1, 2, 또는 3): ").strip()
    
    if choice == "1":
        print("\n🚀 자동 테스트를 시작합니다!")
        test_calendar_flow()
    elif choice == "2":
        print("\n💬 대화형 테스트를 시작합니다!")
        test_interactive_calendar_flow()
    elif choice == "3":
        print("\n🤖 Agent Task CRUD 테스트를 시작합니다!")
        test_agent_task_flow()
    else:
        print("❌ 잘못된 선택입니다. 자동 테스트를 실행합니다.")
        test_calendar_flow() 