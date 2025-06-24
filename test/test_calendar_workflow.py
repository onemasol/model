import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import calendar_agent
from agents.calselector import calselector 

def test_calendar_workflow():
    """calendar_agent에서 calselector로 이어지는 워크플로우를 테스트합니다."""
    
    # 테스트 케이스들 - CRUD 모든 케이스 포함
    test_cases = [
        # CREATE 케이스들
        {
            "description": "CREATE - 특정 시간 일정 생성 (내일 오후 2시 미팅)",
            "input": "내일 오후 2시에 팀 미팅 추가해줘",
            "expected_type": "event",
            "expected_operation": "create",
            "expected_node": "answer_planner",
            "crud_type": "CREATE"
        },
        {
            "description": "CREATE - 종일 할일 생성 (오늘 장보기)",
            "input": "오늘 장보기 할일 추가해줘",
            "expected_type": "task",
            "expected_operation": "create",
            "expected_node": "answer_planner",
            "crud_type": "CREATE"
        },
        {
            "description": "CREATE - 복잡한 일정 생성 (다음주 월요일 오전 10시 회의)",
            "input": "다음주 월요일 오전 10시에 프로젝트 회의 추가해줘",
            "expected_type": "event",
            "expected_operation": "create",
            "expected_node": "answer_planner",
            "crud_type": "CREATE"
        },
        {
            "description": "CREATE - 마감일 있는 할일 (내일까지 보고서 작성)",
            "input": "내일까지 보고서 작성할일 추가해줘",
            "expected_type": "task",
            "expected_operation": "create",
            "expected_node": "answer_planner",
            "crud_type": "CREATE"
        },
        
        # READ 케이스들
        {
            "description": "READ - 일정 조회 (이번 주 일정)",
            "input": "이번 주 일정 보여줘",
            "expected_type": "event",
            "expected_operation": "read",
            "expected_node": "calselector",
            "crud_type": "READ"
        },
        {
            "description": "READ - 할일 조회 (오늘 할 일)",
            "input": "오늘 할 일 보여줘",
            "expected_type": "task",
            "expected_operation": "read",
            "expected_node": "calselector",
            "crud_type": "READ"
        },
        {
            "description": "READ - 특정 날짜 일정 (내일 일정)",
            "input": "내일 일정 보여줘",
            "expected_type": "event",
            "expected_operation": "read",
            "expected_node": "calselector",
            "crud_type": "READ"
        },
        {
            "description": "READ - 전체 일정 조회 (모든 일정)",
            "input": "모든 일정 보여줘",
            "expected_type": "event",
            "expected_operation": "read",
            "expected_node": "calselector",
            "crud_type": "READ"
        },
        
        # UPDATE 케이스들
        {
            "description": "UPDATE - 일정 시간 수정 (내일 미팅 시간 변경)",
            "input": "내일 오후 3시로 미팅 시간 변경해줘",
            "expected_type": "event",
            "expected_operation": "update",
            "expected_node": "calselector",
            "crud_type": "UPDATE"
        },
        {
            "description": "UPDATE - 할일 제목 수정 (장보기 제목 변경)",
            "input": "장보기 제목을 '식료품 구매'로 변경해줘",
            "expected_type": "task",
            "expected_operation": "update",
            "expected_node": "calselector",
            "crud_type": "UPDATE"
        },
        {
            "description": "UPDATE - 일정 장소 수정 (미팅 장소 변경)",
            "input": "내일 미팅 장소를 '회의실 B'로 변경해줘",
            "expected_type": "event",
            "expected_operation": "update",
            "expected_node": "calselector",
            "crud_type": "UPDATE"
        },
        
        # DELETE 케이스들
        {
            "description": "DELETE - 일정 삭제 (내일 미팅 취소)",
            "input": "내일 미팅 취소해줘",
            "expected_type": "event",
            "expected_operation": "delete",
            "expected_node": "calselector",
            "crud_type": "DELETE"
        },
        {
            "description": "DELETE - 할일 삭제 (장보기 할일 삭제)",
            "input": "장보기 할일 삭제해줘",
            "expected_type": "task",
            "expected_operation": "delete",
            "expected_node": "calselector",
            "crud_type": "DELETE"
        },
        {
            "description": "DELETE - 특정 일정 삭제 (팀 미팅 삭제)",
            "input": "팀 미팅 삭제해줘",
            "expected_type": "event",
            "expected_operation": "delete",
            "expected_node": "calselector",
            "crud_type": "DELETE"
        }
    ]
    
    print("=" * 80)
    print("📅 Calendar Agent → calselector Workflow 테스트 (CRUD 전체)")
    print("=" * 80)
    
    # CRUD별 통계
    crud_stats = {"CREATE": 0, "READ": 0, "UPDATE": 0, "DELETE": 0}
    crud_success = {"CREATE": 0, "READ": 0, "UPDATE": 0, "DELETE": 0}
    
    for i, test_case in enumerate(test_cases, 1):
        crud_type = test_case['crud_type']
        crud_stats[crud_type] += 1
        
        print(f"\n🧪 테스트 {i}: {test_case['description']}")
        print(f"📋 CRUD 타입: {crud_type}")
        print("-" * 60)
        print(f"입력: {test_case['input']}")
        
        # 초기 상태 설정
        initial_state = {
            "messages": [test_case["input"]],
            "agent_messages": [],
            "router_messages": [],
            "user_id": "542c2e7e-256a-4e15-abdb-f38310e94007"  # 실제 사용자 ID 추가
        }
        
        try:
            # Step 1: calendar_agent 실행
            print("\n📋 Step 1: Calendar Agent 실행")
            calendar_result = calendar_agent(initial_state.copy())
            
            print(f"✅ 분류 결과:")
            print(f"   - 타입: {calendar_result.get('calendar_type', 'N/A')}")
            print(f"   - 작업: {calendar_result.get('calendar_operation', 'N/A')}")
            print(f"   - 다음 노드: {calendar_result.get('next_node', 'N/A')}")
            
            # 예상 결과와 비교
            actual_type = calendar_result.get('calendar_type', '')
            actual_operation = calendar_result.get('calendar_operation', '')
            actual_node = calendar_result.get('next_node', '')
            
            type_match = actual_type == test_case['expected_type']
            operation_match = actual_operation == test_case['expected_operation']
            node_match = actual_node == test_case['expected_node']
            
            if type_match and operation_match and node_match:
                print("✅ Calendar Agent 결과: 모든 예상과 일치!")
                crud_success[crud_type] += 1
            else:
                print("❌ Calendar Agent 결과: 예상과 다름")
                if not type_match:
                    print(f"   - 타입: 예상 {test_case['expected_type']}, 실제 {actual_type}")
                if not operation_match:
                    print(f"   - 작업: 예상 {test_case['expected_operation']}, 실제 {actual_operation}")
                if not node_match:
                    print(f"   - 노드: 예상 {test_case['expected_node']}, 실제 {actual_node}")

            # Step 2: 작업에 따른 처리
            next_node_result = {}
            if actual_operation == "create":
                print("\n🔧 Step 2: CREATE - Calendar Agent에서 페이로드 생성")
                next_node_result = calendar_result
                
                print(f"✅ 페이로드 생성 결과:")
                payload = next_node_result.get('event_payload', {})
                print(f"   - 제목: {payload.get('title', 'N/A')}")
                print(f"   - 시작 시간: {payload.get('start_at', 'N/A')}")
                print(f"   - 종료 시간: {payload.get('end_at', 'N/A')}")
                print(f"   - 마감 시간: {payload.get('due_at', 'N/A')}")
                print(f"   - 이벤트 타입: {payload.get('event_type', 'N/A')}")
                
                # 페이로드 유효성 검사
                event_type = payload.get('event_type', 'event')
                title = payload.get('title')
                start_at = payload.get('start_at')
                end_at = payload.get('end_at')
                due_at = payload.get('due_at')
                
                if event_type == "task":
                    if title and due_at and (start_at is None or start_at == "null") and (end_at is None or end_at == "null"):
                        print("✅ 페이로드: 유효한 Task 구조")
                    else:
                        print("❌ 페이로드: Task 구조에 문제가 있음")
                else:
                    if title and start_at and end_at and (due_at is None or due_at == "null"):
                        print("✅ 페이로드: 유효한 Event 구조")
                    else:
                        print("❌ 페이로드: Event 구조에 문제가 있음")
            
            elif actual_node == "calselector":
                print(f"\n🔧 Step 2: {crud_type} - calselector 실행")
                next_node_result = calselector(calendar_result.copy())
                
                print(f"✅ calselector 결과:")
                print(f"   - 다음 노드: {next_node_result.get('next_node', 'N/A')}")
                print(f"   - API 요청 수: {len(next_node_result.get('api_requests', []))}")
                
                # API 요청 상세 정보 출력
                api_requests = next_node_result.get('api_requests', [])
                for i, req in enumerate(api_requests, 1):
                    print(f"\n📡 API 요청 {i} 상세 정보:")
                    print(f"   - API 타입: {req.get('api_type', 'N/A')}")
                    print(f"   - HTTP 메소드: {req.get('method', 'N/A')}")
                    print(f"   - 엔드포인트: {req.get('endpoint', 'N/A')}")
                    print(f"   - 작업 유형: {req.get('operation', 'N/A')}")
                    print(f"   - 이벤트 타입: {req.get('event_type', 'N/A')}")
                    
                    # 파라미터 상세 출력
                    params = req.get('params', {})
                    if params:
                        print(f"   - 쿼리 파라미터:")
                        for key, value in params.items():
                            print(f"     • {key}: {value}")
                    else:
                        print(f"   - 쿼리 파라미터: 없음")
                    
                    # 헤더 정보 출력 (토큰 숨김)
                    headers = req.get('headers', {})
                    if headers:
                        print(f"   - 요청 헤더:")
                        for key, value in headers.items():
                            if key == 'Authorization':
                                print(f"     • {key}: Bearer [토큰 숨김]")
                            else:
                                print(f"     • {key}: {value}")
                    else:
                        print(f"   - 요청 헤더: 없음")

                # API 응답 및 선택된 항목들 출력
                api_responses = next_node_result.get('api_responses', [])
                if api_responses and api_responses[0].get('success', False):
                    response_data = api_responses[0].get('data', {})
                    
                    print(f"\n📊 API 응답 결과:")
                    print(f"   - 총 항목 수: {response_data.get('total_count', 0)}개")
                    print(f"   - 이벤트 수: {response_data.get('event_count', 0)}개")
                    print(f"   - 태스크 수: {response_data.get('task_count', 0)}개")
                    
                    # 이벤트 목록 출력
                    events = response_data.get('events', [])
                    if events:
                        print(f"\n📅 조회된 이벤트 목록:")
                        for i, event in enumerate(events, 1):
                            print(f"   {i}. {event.get('title', 'N/A')}")
                            print(f"      - 시간: {event.get('start_at', 'N/A')} ~ {event.get('end_at', 'N/A')}")
                            print(f"      - 장소: {event.get('location', 'N/A')}")
                            print(f"      - ID: {event.get('id', 'N/A')}")
                            print(f"      - 캘린더: {event.get('calendar_id', 'N/A')}")
                    
                    # 태스크 목록 출력
                    tasks = response_data.get('tasks', [])
                    if tasks:
                        print(f"\n📝 조회된 태스크 목록:")
                        for i, task in enumerate(tasks, 1):
                            print(f"   {i}. {task.get('title', 'N/A')}")
                            print(f"      - 상태: {task.get('status', 'N/A')}")
                            print(f"      - 생성일: {task.get('created_at', 'N/A')}")
                            print(f"      - 수정일: {task.get('updated_at', 'N/A')}")
                            print(f"      - ID: {task.get('task_id', 'N/A')}")
                    
                    # RUD 후보 ID 목록 출력
                    rud_candidate_ids = next_node_result.get('rud_candidate_ids', [])
                    if rud_candidate_ids:
                        print(f"\n🎯 RUD 후보 ID 목록 (Top {len(rud_candidate_ids)}):")
                        for i, candidate_id in enumerate(rud_candidate_ids, 1):
                            # 해당 ID가 어떤 항목인지 찾기
                            found_item = None
                            item_type = ""
                            
                            # 이벤트에서 찾기
                            for event in events:
                                if event.get('id') == candidate_id:
                                    found_item = event
                                    item_type = "이벤트"
                                    break
                            
                            # 태스크에서 찾기
                            if not found_item:
                                for task in tasks:
                                    if task.get('task_id') == candidate_id:
                                        found_item = task
                                        item_type = "태스크"
                                        break
                            
                            if found_item:
                                print(f"   {i}. [{item_type}] {found_item.get('title', 'N/A')} (ID: {candidate_id})")
                                if item_type == "이벤트":
                                    print(f"      - 시간: {found_item.get('start_at', 'N/A')} ~ {found_item.get('end_at', 'N/A')}")
                                    print(f"      - 장소: {found_item.get('location', 'N/A')}")
                                else:
                                    print(f"      - 상태: {found_item.get('status', 'N/A')}")
                                    print(f"      - 생성일: {found_item.get('created_at', 'N/A')}")
                            else:
                                print(f"   {i}. [알 수 없음] ID: {candidate_id}")
                    
                    # 작업 유형에 따른 선택된 항목 분석
                    operation_type = next_node_result.get('operation_type', 'read')
                    print(f"\n🔍 {operation_type.upper()} 작업 분석:")
                    
                    if operation_type == "read":
                        print(f"   - 조회 작업: 총 {len(events) + len(tasks)}개 항목 조회 완료")
                        if events:
                            print(f"   - 이벤트 조회: {len(events)}개")
                        if tasks:
                            print(f"   - 태스크 조회: {len(tasks)}개")
                    
                    elif operation_type == "update":
                        print(f"   - 수정 작업: {len(rud_candidate_ids)}개 후보 항목 중 선택 필요")
                        if rud_candidate_ids:
                            print(f"   - 수정 대상 후보: {rud_candidate_ids[0] if rud_candidate_ids else 'N/A'}")
                    
                    elif operation_type == "delete":
                        print(f"   - 삭제 작업: {len(rud_candidate_ids)}개 후보 항목 중 선택 필요")
                        if rud_candidate_ids:
                            print(f"   - 삭제 대상 후보: {rud_candidate_ids[0] if rud_candidate_ids else 'N/A'}")
                else:
                    print(f"\n❌ API 응답 실패 또는 데이터 없음")
                    if api_responses:
                        error_response = api_responses[0]
                        print(f"   - 상태 코드: {error_response.get('status_code', 'N/A')}")
                        print(f"   - 에러 메시지: {error_response.get('error', 'N/A')}")

                # calselector 유효성 검사
                if next_node_result.get('next_node') == "answer_generator":
                    print("✅ 라우팅: answer_generator로 올바르게 전달됨")
                else:
                    print(f"❌ 라우팅: 잘못된 노드로 전달됨 ({next_node_result.get('next_node')})")
                
                # API 요청 유효성 검사
                if api_requests:
                    print("✅ API 요청: 정상적으로 생성됨")
                    for req in api_requests:
                        if req.get('api_type') == 'calendar_unified':
                            print(f"✅ API 타입: {req.get('api_type')} - 유효함")
                        else:
                            print(f"❌ API 타입: {req.get('api_type')} - 유효하지 않음")
                else:
                    print("❌ API 요청: 생성되지 않음")
            
            else:
                print(f"\n🤷‍♀️ Step 2: 알 수 없는 다음 노드 ({actual_node})")
                next_node_result = calendar_result

            # 전체 워크플로우 결과
            print(f"\n📊 전체 워크플로우 결과:")
            print(f"   - 최종 상태: {next_node_result.get('crud_result', 'N/A')}")
            print(f"   - 에이전트 메시지 수: {len(next_node_result.get('agent_messages', []))}")
            
            # 에이전트 메시지 로그
            print(f"\n📝 에이전트 메시지:")
            for msg in next_node_result.get('agent_messages', []):
                agent_name = msg.get('agent', 'unknown').replace('_agent', ' Agent')
                summary = msg.get('summary', 'N/A')
                print(f"   - {agent_name.capitalize()}: {summary}")
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)

    # CRUD별 통계 출력
    print("\n" + "=" * 80)
    print("📊 CRUD 테스트 통계")
    print("=" * 80)
    
    for crud_type in ["CREATE", "READ", "UPDATE", "DELETE"]:
        total = crud_stats[crud_type]
        success = crud_success[crud_type]
        success_rate = (success / total * 100) if total > 0 else 0
        print(f"{crud_type}: {success}/{total} 성공 ({success_rate:.1f}%)")
    
    total_tests = sum(crud_stats.values())
    total_success = sum(crud_success.values())
    overall_success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    print(f"\n전체: {total_success}/{total_tests} 성공 ({overall_success_rate:.1f}%)")

def test_specific_scenario():
    """특정 시나리오를 상세히 테스트합니다."""
    print("\n" + "=" * 80)
    print("🔍 특정 시나리오 상세 테스트")
    print("=" * 80)
    
    # 복잡한 일정 생성 시나리오
    test_input = "내일 오후 3시 30분에 고객 미팅 추가해줘"
    
    print(f"테스트 입력: {test_input}")
    
    initial_state = {
        "messages": [test_input],
        "agent_messages": [],
        "router_messages": [],
        "user_id": "542c2e7e-256a-4e15-abdb-f38310e94007"  # 실제 사용자 ID 추가
    }
    
    try:
        # Calendar Agent 실행
        print("\n📋 Calendar Agent 실행...")
        calendar_result = calendar_agent(initial_state.copy())
        
        print("Calendar Agent 결과:")
        print(json.dumps({
            "calendar_type": calendar_result.get('calendar_type'),
            "calendar_operation": calendar_result.get('calendar_operation'),
            "next_node": calendar_result.get('next_node'),
            "extracted_info": calendar_result.get('extracted_info')
        }, ensure_ascii=False, indent=2))
        
        # 작업에 따라 분기
        operation = calendar_result.get('calendar_operation')
        next_node = calendar_result.get('next_node')
        final_result = {}
        
        if operation == "create":
            print("\n🔧 Calendar Agent에서 페이로드 생성 완료")
            final_result = calendar_result
            print("Calendar Agent 결과 (Event Payload):")
            print(json.dumps(final_result.get('event_payload', {}), ensure_ascii=False, indent=2))

        elif next_node == "calselector":
            print("\n🔧 calselector 실행...")
            final_result = calselector(calendar_result.copy())
            print("calselector 결과 (API Requests):")
            api_requests = final_result.get('api_requests', [])
            for i, req in enumerate(api_requests, 1):
                print(f"\n📡 API 요청 {i}:")
                print(f"   API 타입: {req.get('api_type')}")
                print(f"   엔드포인트: {req.get('endpoint')}")
                print(f"   메소드: {req.get('method')}")
                print(f"   파라미터: {json.dumps(req.get('params', {}), ensure_ascii=False, indent=2)}")
                print(f"   전체 요청:")
                print(json.dumps(req, ensure_ascii=False, indent=2))
                print()
        else:
            final_result = calendar_result

        # 최종 상태 확인
        print(f"\n📊 최종 상태:")
        print(f"CRUD 결과: {final_result.get('crud_result', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def test_custom_case():
    """사용자가 직접 입력한 커스텀 테스트 케이스를 실행합니다."""
    print("\n" + "=" * 80)
    print("🎯 커스텀 테스트 케이스")
    print("=" * 80)
    
    while True:
        print("\n📝 커스텀 테스트 케이스 입력:")
        print("   (종료하려면 'quit' 또는 'exit' 입력)")
        
        # 사용자 입력 받기
        custom_input = input("   입력: ").strip()
        
        if custom_input.lower() in ['quit', 'exit', 'q']:
            print("   👋 커스텀 테스트를 종료합니다.")
            break
        
        if not custom_input:
            print("   ⚠️ 입력이 비어있습니다. 다시 입력해주세요.")
            continue
        
        print(f"\n🧪 커스텀 테스트 실행: {custom_input}")
        print("-" * 60)
        
        # 초기 상태 설정
        initial_state = {
            "messages": [custom_input],
            "agent_messages": [],
            "router_messages": [],
            "user_id": "542c2e7e-256a-4e15-abdb-f38310e94007"  # 실제 사용자 ID 추가
        }
        
        try:
            # Step 1: calendar_agent 실행
            print("\n📋 Step 1: Calendar Agent 실행")
            calendar_result = calendar_agent(initial_state.copy())
            
            print(f"✅ 분류 결과:")
            print(f"   - 타입: {calendar_result.get('calendar_type', 'N/A')}")
            print(f"   - 작업: {calendar_result.get('calendar_operation', 'N/A')}")
            print(f"   - 다음 노드: {calendar_result.get('next_node', 'N/A')}")
            print(f"   - 제목: {calendar_result.get('title', 'N/A')}")
            print(f"   - 시작 시간: {calendar_result.get('start_at', 'N/A')}")
            print(f"   - 종료 시간: {calendar_result.get('end_at', 'N/A')}")
            print(f"   - 마감 시간: {calendar_result.get('due_at', 'N/A')}")
            print(f"   - 시간대: {calendar_result.get('timezone', 'N/A')}")
            
            # Step 2: 작업에 따른 처리
            actual_operation = calendar_result.get('calendar_operation', '')
            actual_node = calendar_result.get('next_node', '')
            next_node_result = {}
            
            if actual_operation == "create":
                print("\n🔧 Step 2: CREATE - Calendar Agent에서 페이로드 생성")
                next_node_result = calendar_result
                
                print(f"✅ 페이로드 생성 결과:")
                payload = next_node_result.get('event_payload', {})
                print(f"   - 제목: {payload.get('title', 'N/A')}")
                print(f"   - 시작 시간: {payload.get('start_at', 'N/A')}")
                print(f"   - 종료 시간: {payload.get('end_at', 'N/A')}")
                print(f"   - 마감 시간: {payload.get('due_at', 'N/A')}")
                print(f"   - 이벤트 타입: {payload.get('event_type', 'N/A')}")
                
                # 페이로드 유효성 검사
                event_type = payload.get('event_type', 'event')
                title = payload.get('title')
                start_at = payload.get('start_at')
                end_at = payload.get('end_at')
                due_at = payload.get('due_at')
                
                if event_type == "task":
                    if title and due_at and (start_at is None or start_at == "null") and (end_at is None or end_at == "null"):
                        print("✅ 페이로드: 유효한 Task 구조")
                    else:
                        print("❌ 페이로드: Task 구조에 문제가 있음")
                else:
                    if title and start_at and end_at and (due_at is None or due_at == "null"):
                        print("✅ 페이로드: 유효한 Event 구조")
                    else:
                        print("❌ 페이로드: Event 구조에 문제가 있음")
            
            elif actual_node == "calselector":
                print(f"\n🔧 Step 2: RUD - calselector 실행")
                next_node_result = calselector(calendar_result.copy())
                
                print(f"✅ calselector 결과:")
                print(f"   - 다음 노드: {next_node_result.get('next_node', 'N/A')}")
                print(f"   - API 요청 수: {len(next_node_result.get('api_requests', []))}")
                
                # API 요청 상세 정보 출력
                api_requests = next_node_result.get('api_requests', [])
                for i, req in enumerate(api_requests, 1):
                    print(f"\n📡 API 요청 {i} 상세 정보:")
                    print(f"   - API 타입: {req.get('api_type', 'N/A')}")
                    print(f"   - HTTP 메소드: {req.get('method', 'N/A')}")
                    print(f"   - 엔드포인트: {req.get('endpoint', 'N/A')}")
                    print(f"   - 작업 유형: {req.get('operation', 'N/A')}")
                    print(f"   - 이벤트 타입: {req.get('event_type', 'N/A')}")

                # API 응답 및 선택된 항목들 출력
                api_responses = next_node_result.get('api_responses', [])
                if api_responses and api_responses[0].get('success', False):
                    response_data = api_responses[0].get('data', {})
                    
                    print(f"\n📊 API 응답 결과:")
                    print(f"   - 총 항목 수: {response_data.get('total_count', 0)}개")
                    print(f"   - 이벤트 수: {response_data.get('event_count', 0)}개")
                    print(f"   - 태스크 수: {response_data.get('task_count', 0)}개")
                    
                    # 이벤트 목록 출력
                    events = response_data.get('events', [])
                    if events:
                        print(f"\n📅 조회된 이벤트 목록:")
                        for i, event in enumerate(events, 1):
                            print(f"   {i}. {event.get('title', 'N/A')}")
                            print(f"      - 시간: {event.get('start_at', 'N/A')} ~ {event.get('end_at', 'N/A')}")
                            print(f"      - 장소: {event.get('location', 'N/A')}")
                            print(f"      - ID: {event.get('id', 'N/A')}")
                            print(f"      - 캘린더: {event.get('calendar_id', 'N/A')}")
                    
                    # 태스크 목록 출력
                    tasks = response_data.get('tasks', [])
                    if tasks:
                        print(f"\n📝 조회된 태스크 목록:")
                        for i, task in enumerate(tasks, 1):
                            print(f"   {i}. {task.get('title', 'N/A')}")
                            print(f"      - 상태: {task.get('status', 'N/A')}")
                            print(f"      - 생성일: {task.get('created_at', 'N/A')}")
                            print(f"      - 수정일: {task.get('updated_at', 'N/A')}")
                            print(f"      - ID: {task.get('task_id', 'N/A')}")
                    
                    # RUD 후보 ID 목록 출력
                    rud_candidate_ids = next_node_result.get('rud_candidate_ids', [])
                    if rud_candidate_ids:
                        print(f"\n🎯 RUD 후보 ID 목록 (Top {len(rud_candidate_ids)}):")
                        for i, candidate_id in enumerate(rud_candidate_ids, 1):
                            # 해당 ID가 어떤 항목인지 찾기
                            found_item = None
                            item_type = ""
                            
                            # 이벤트에서 찾기
                            for event in events:
                                if event.get('id') == candidate_id:
                                    found_item = event
                                    item_type = "이벤트"
                                    break
                            
                            # 태스크에서 찾기
                            if not found_item:
                                for task in tasks:
                                    if task.get('task_id') == candidate_id:
                                        found_item = task
                                        item_type = "태스크"
                                        break
                            
                            if found_item:
                                print(f"   {i}. [{item_type}] {found_item.get('title', 'N/A')} (ID: {candidate_id})")
                                if item_type == "이벤트":
                                    print(f"      - 시간: {found_item.get('start_at', 'N/A')} ~ {found_item.get('end_at', 'N/A')}")
                                    print(f"      - 장소: {found_item.get('location', 'N/A')}")
                                else:
                                    print(f"      - 상태: {found_item.get('status', 'N/A')}")
                                    print(f"      - 생성일: {found_item.get('created_at', 'N/A')}")
                            else:
                                print(f"   {i}. [알 수 없음] ID: {candidate_id}")
                    
                    # 작업 유형에 따른 선택된 항목 분석
                    operation_type = next_node_result.get('operation_type', 'read')
                    print(f"\n🔍 {operation_type.upper()} 작업 분석:")
                    
                    if operation_type == "read":
                        print(f"   - 조회 작업: 총 {len(events) + len(tasks)}개 항목 조회 완료")
                        if events:
                            print(f"   - 이벤트 조회: {len(events)}개")
                        if tasks:
                            print(f"   - 태스크 조회: {len(tasks)}개")
                    
                    elif operation_type == "update":
                        print(f"   - 수정 작업: {len(rud_candidate_ids)}개 후보 항목 중 선택 필요")
                        if rud_candidate_ids:
                            print(f"   - 수정 대상 후보: {rud_candidate_ids[0] if rud_candidate_ids else 'N/A'}")
                    
                    elif operation_type == "delete":
                        print(f"   - 삭제 작업: {len(rud_candidate_ids)}개 후보 항목 중 선택 필요")
                        if rud_candidate_ids:
                            print(f"   - 삭제 대상 후보: {rud_candidate_ids[0] if rud_candidate_ids else 'N/A'}")
                else:
                    print(f"\n❌ API 응답 실패 또는 데이터 없음")
                    if api_responses:
                        error_response = api_responses[0]
                        print(f"   - 상태 코드: {error_response.get('status_code', 'N/A')}")
                        print(f"   - 에러 메시지: {error_response.get('error', 'N/A')}")

                # calselector 유효성 검사
                if next_node_result.get('next_node') == "answer_generator":
                    print("✅ 라우팅: answer_generator로 올바르게 전달됨")
                else:
                    print(f"❌ 라우팅: 잘못된 노드로 전달됨 ({next_node_result.get('next_node')})")
                
                # API 요청 유효성 검사
                if api_requests:
                    print("✅ API 요청: 정상적으로 생성됨")
                    for req in api_requests:
                        if req.get('api_type') == 'calendar_unified':
                            print(f"✅ API 타입: {req.get('api_type')} - 유효함")
                        else:
                            print(f"❌ API 타입: {req.get('api_type')} - 유효하지 않음")
                else:
                    print("❌ API 요청: 생성되지 않음")
            
            else:
                print(f"\n🤷‍♀️ Step 2: 알 수 없는 다음 노드 ({actual_node})")
                next_node_result = calendar_result

            # 전체 워크플로우 결과
            print(f"\n📊 전체 워크플로우 결과:")
            print(f"   - 최종 상태: {next_node_result.get('crud_result', 'N/A')}")
            print(f"   - 에이전트 메시지 수: {len(next_node_result.get('agent_messages', []))}")
            
            # 에이전트 메시지 로그
            print(f"\n📝 에이전트 메시지:")
            for msg in next_node_result.get('agent_messages', []):
                agent_name = msg.get('agent', 'unknown').replace('_agent', ' Agent')
                summary = msg.get('summary', 'N/A')
                print(f"   - {agent_name.capitalize()}: {summary}")
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)
        
        # 계속할지 묻기
        continue_test = input("\n   계속 테스트하시겠습니까? (y/n): ").strip().lower()
        if continue_test not in ['y', 'yes', '예']:
            print("   👋 커스텀 테스트를 종료합니다.")
            break

def test_api_connection():
    """실제 API 연결을 테스트합니다."""
    print("\n" + "=" * 80)
    print("🔗 API 연결 테스트")
    print("=" * 80)
    
    import requests
    
    # 테스트용 상태
    test_state = {
        "user_id": "542c2e7e-256a-4e15-abdb-f38310e94007"
    }
    
    try:
        # 직접 API 호출 테스트
        api_url = f"http://52.79.95.55:8000/api/v1/calendar/{test_state['user_id']}/all"
        print(f"🌐 API URL: {api_url}")
        
        response = requests.get(api_url, timeout=10)
        print(f"📊 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 연결 성공!")
            print(f"📋 총 {len(data)}개 일정 조회됨")
            
            if data:
                print(f"📅 첫 번째 일정: {data[0].get('title', 'N/A')}")
                print(f"   - 시작: {data[0].get('start_at', 'N/A')}")
                print(f"   - 종료: {data[0].get('end_at', 'N/A')}")
                print(f"   - ID: {data[0].get('id', 'N/A')}")
        else:
            print(f"❌ API 연결 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"❌ API 테스트 중 오류: {str(e)}")

if __name__ == "__main__":
    # API 연결 테스트 먼저 실행
    test_api_connection()
    
    # 전체 워크플로우 테스트
    test_calendar_workflow()
    
    # 특정 시나리오 테스트
    test_specific_scenario()
    
    # 커스텀 케이스 테스트
    test_custom_case() 