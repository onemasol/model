import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import calendar_agent
from agents.calselector import calselector 

def test_calendar_workflow():
    """calendar_agent에서 calselector로 이어지는 워크플로우를 테스트합니다."""
    
    # 테스트 케이스들
    test_cases = [
        {
            "description": "특정 시간 일정 생성 (내일 오후 2시 미팅)",
            "input": "내일 오후 2시에 팀 미팅 추가해줘",
            "expected_type": "event",
            "expected_operation": "create",
            "expected_node": "answer_planner"
        },
        {
            "description": "종일 할일 생성 (오늘 장보기)",
            "input": "오늘 장보기 할일 추가해줘",
            "expected_type": "task",
            "expected_operation": "create",
            "expected_node": "answer_planner"
        },
        {
            "description": "일정 조회 (이번 주 일정)",
            "input": "이번 주 일정 보여줘",
            "expected_type": "event",
            "expected_operation": "read",
            "expected_node": "calselector"
        },
        {
            "description": "할일 조회 (오늘 할 일)",
            "input": "오늘 할 일 보여줘",
            "expected_type": "task",
            "expected_operation": "read",
            "expected_node": "calselector"
        },
        {
            "description": "일정 수정 (내일 미팅 시간 변경)",
            "input": "내일 오후 3시로 미팅 시간 변경해줘",
            "expected_type": "event",
            "expected_operation": "update",
            "expected_node": "calselector"
        },
        {
            "description": "일정 삭제 (내일 미팅 취소)",
            "input": "내일 미팅 취소해줘",
            "expected_type": "event",
            "expected_operation": "delete",
            "expected_node": "calselector"
        },
        {
            "description": "복잡한 일정 생성 (다음주 월요일 오전 10시 회의)",
            "input": "다음주 월요일 오전 10시에 프로젝트 회의 추가해줘",
            "expected_type": "event",
            "expected_operation": "create",
            "expected_node": "answer_planner"
        }
    ]
    
    print("=" * 80)
    print("📅 Calendar Agent → calselector Workflow 테스트")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 테스트 {i}: {test_case['description']}")
        print("-" * 60)
        print(f"입력: {test_case['input']}")
        
        # 초기 상태 설정
        initial_state = {
            "messages": [test_case["input"]],
            "agent_messages": [],
            "router_messages": []
        }
        
        try:
            # Step 1: calendar_agent 실행
            print("\n📋 Step 1: Calendar Agent 실행")
            calendar_result = calendar_agent(initial_state.copy())
            
            print(f"✅ 분류 결과:")
            print(f"   - 타입: {calendar_result.get('calendar_type', 'N/A')}")
            print(f"   - 작업: {calendar_result.get('calendar_operation', 'N/A')}")
            print(f"   - 다음 노드: {calendar_result.get('next_node', 'N/A')}")
            print(f"   - 추출된 정보: {json.dumps(calendar_result.get('extracted_info', {}), ensure_ascii=False, indent=2)}")
            
            print(f"\n📊 Calendar Agent State:")
            print(f"   - title: {calendar_result.get('title', 'N/A')}")
            print(f"   - start_at: {calendar_result.get('start_at', 'N/A')}")
            print(f"   - end_at: {calendar_result.get('end_at', 'N/A')}")
            print(f"   - due_at: {calendar_result.get('due_at', 'N/A')}")
            print(f"   - timezone: {calendar_result.get('timezone', 'N/A')}")
            print(f"   - event_type: {calendar_result.get('event_type', 'N/A')}")
            
            # 예상 결과와 비교
            actual_type = calendar_result.get('calendar_type', '')
            actual_operation = calendar_result.get('calendar_operation', '')
            actual_node = calendar_result.get('next_node', '')
            
            type_match = actual_type == test_case['expected_type']
            operation_match = actual_operation == test_case['expected_operation']
            node_match = actual_node == test_case['expected_node']
            
            if type_match and operation_match and node_match:
                print("✅ Calendar Agent 결과: 모든 예상과 일치!")
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
                print("\n🔧 Step 2: Calendar Agent에서 페이로드 생성 완료")
                next_node_result = calendar_result
                
                print(f"✅ 페이로드 생성 결과:")
                payload = next_node_result.get('event_payload', {})
                print(f"   - 제목: {payload.get('title', 'N/A')}")
                print(f"   - 시작 시간: {payload.get('start_at', 'N/A')}")
                print(f"   - 종료 시간: {payload.get('end_at', 'N/A')}")
                print(f"   - 마감 시간: {payload.get('due_at', 'N/A')}")
                print(f"   - 이벤트 타입: {payload.get('event_type', 'N/A')}")
                
                print(f"\n📊 Final State (Create):")
                print(f"   - title: {next_node_result.get('title', 'N/A')}")
                print(f"   - start_at: {next_node_result.get('start_at', 'N/A')}")
                print(f"   - end_at: {next_node_result.get('end_at', 'N/A')}")
                print(f"   - due_at: {next_node_result.get('due_at', 'N/A')}")
                print(f"   - timezone: {next_node_result.get('timezone', 'N/A')}")
                print(f"   - event_type: {next_node_result.get('event_type', 'N/A')}")
                print(f"   - event_payload: {json.dumps(next_node_result.get('event_payload', {}), ensure_ascii=False, indent=2)}")
                
                # 페이로드 유효성 검사 (event_type에 따라 다름)
                event_type = payload.get('event_type', 'event')
                title = payload.get('title')
                start_at = payload.get('start_at')
                end_at = payload.get('end_at')
                due_at = payload.get('due_at')
                
                if event_type == "task":
                    # task는 title과 due_at만 있으면 됨 (start_at, end_at은 null이어야 함)
                    if title and due_at and (start_at is None or start_at == "null") and (end_at is None or end_at == "null"):
                        print("✅ 페이로드: 유효한 Task 구조")
                    else:
                        print("❌ 페이로드: Task 구조에 문제가 있음")
                else:
                    # event는 title, start_at, end_at 모두 있어야 함 (due_at은 null이어야 함)
                    if title and start_at and end_at and (due_at is None or due_at == "null"):
                        print("✅ 페이로드: 유효한 Event 구조")
                    else:
                        print("❌ 페이로드: Event 구조에 문제가 있음")
            
            elif actual_node == "calselector":
                print("\n🔧 calselector 실행...")
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
                    
                    # 헤더 정보 출력
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
                    
                    # 전체 요청 구조 출력 (JSON)
                    print(f"   - 전체 요청 구조:")
                    print(json.dumps(req, ensure_ascii=False, indent=4))

                print(f"\n📊 Final State (RUD):")
                print(f"   - title: {next_node_result.get('title', 'N/A')}")
                print(f"   - start_at: {next_node_result.get('start_at', 'N/A')}")
                print(f"   - end_at: {next_node_result.get('end_at', 'N/A')}")
                print(f"   - due_at: {next_node_result.get('due_at', 'N/A')}")
                print(f"   - timezone: {next_node_result.get('timezone', 'N/A')}")
                print(f"   - event_type: {next_node_result.get('event_type', 'N/A')}")
                print(f"   - operation_type: {next_node_result.get('operation_type', 'N/A')}")
                print(f"   - schedule_type: {next_node_result.get('schedule_type', 'N/A')}")
                print(f"   - query_info: {json.dumps(next_node_result.get('query_info', {}), ensure_ascii=False, indent=2)}")

                # calselector 유효성 검사
                if next_node_result.get('next_node') == "calendar_api_utils":
                    print("✅ 라우팅: calendar_api_utils로 올바르게 전달됨")
                else:
                    print("❌ 라우팅: 잘못된 노드로 전달됨")
                
                # API 요청 유효성 검사
                if api_requests:
                    print("✅ API 요청: 정상적으로 생성됨")
                    for req in api_requests:
                        if req.get('api_type') in ['google_calendar', 'google_tasks']:
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
        "router_messages": []
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

if __name__ == "__main__":
    print("🚀 Calendar Workflow 테스트 시작")
    print(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 기본 워크플로우 테스트
    test_calendar_workflow()
    
    # 특정 시나리오 상세 테스트
    test_specific_scenario()
    
    print("\n✅ 모든 테스트 완료!") 