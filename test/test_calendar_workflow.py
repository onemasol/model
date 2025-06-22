import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import calendar_agent
from agents.calc import calc

def test_calendar_workflow():
    """calendar_agent에서 calc로 이어지는 워크플로우를 테스트합니다."""
    
    # 테스트 케이스들
    test_cases = [
        {
            "description": "특정 시간 일정 생성 (내일 오후 2시 미팅)",
            "input": "내일 오후 2시에 팀 미팅 추가해줘",
            "expected_type": "event",
            "expected_operation": "create",
            "expected_node": "CalC"
        },
        {
            "description": "종일 할일 생성 (오늘 장보기)",
            "input": "오늘 장보기 할일 추가해줘",
            "expected_type": "task",
            "expected_operation": "create",
            "expected_node": "CalC"
        },
        {
            "description": "일정 조회 (이번 주 일정)",
            "input": "이번 주 일정 보여줘",
            "expected_type": "event",
            "expected_operation": "read",
            "expected_node": "CalRUD"
        },
        {
            "description": "할일 조회 (오늘 할 일)",
            "input": "오늘 할 일 보여줘",
            "expected_type": "task",
            "expected_operation": "read",
            "expected_node": "CalRUD"
        },
        {
            "description": "일정 수정 (내일 미팅 시간 변경)",
            "input": "내일 오후 3시로 미팅 시간 변경해줘",
            "expected_type": "event",
            "expected_operation": "update",
            "expected_node": "CalRUD"
        },
        {
            "description": "일정 삭제 (내일 미팅 취소)",
            "input": "내일 미팅 취소해줘",
            "expected_type": "event",
            "expected_operation": "delete",
            "expected_node": "CalRUD"
        },
        {
            "description": "복잡한 일정 생성 (다음주 월요일 오전 10시 회의)",
            "input": "다음주 월요일 오전 10시에 프로젝트 회의 추가해줘",
            "expected_type": "event",
            "expected_operation": "create",
            "expected_node": "CalC"
        }
    ]
    
    print("=" * 80)
    print("📅 Calendar Agent → Calc Workflow 테스트")
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
            
            # Step 2: calc 실행
            print("\n🔧 Step 2: Calc 실행")
            calc_result = calc(calendar_result.copy())
            
            print(f"✅ 페이로드 생성 결과:")
            payload = calc_result.get('calendar_payload', {})
            print(f"   - 요약: {payload.get('summary', 'N/A')}")
            print(f"   - 시작: {json.dumps(payload.get('start', {}), ensure_ascii=False)}")
            print(f"   - 종료: {json.dumps(payload.get('end', {}), ensure_ascii=False)}")
            
            # 페이로드 유효성 검사
            if payload.get('summary') and (payload.get('start') or payload.get('end')):
                print("✅ 페이로드: 유효한 구조")
            else:
                print("❌ 페이로드: 구조에 문제가 있음")
            
            # 전체 워크플로우 결과
            print(f"\n📊 전체 워크플로우 결과:")
            print(f"   - 최종 상태: {calc_result.get('crud_result', 'N/A')}")
            print(f"   - 에이전트 메시지 수: {len(calc_result.get('agent_messages', []))}")
            
            # 에이전트 메시지 로그
            print(f"\n📝 에이전트 메시지:")
            for msg in calc_result.get('agent_messages', []):
                agent_name = msg.get('agent', 'unknown')
                if agent_name == 'calendar_agent':
                    print(f"   - Calendar Agent: {msg.get('summary', 'N/A')}")
                elif agent_name == 'calc':
                    print(f"   - Calc: 페이로드 생성 완료")
            
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
        
        # Calc 실행
        print("\n🔧 Calc 실행...")
        calc_result = calc(calendar_result.copy())
        
        print("Calc 결과:")
        print(json.dumps(calc_result.get('calendar_payload', {}), ensure_ascii=False, indent=2))
        
        # 최종 상태 확인
        print(f"\n📊 최종 상태:")
        print(f"CRUD 결과: {calc_result.get('crud_result', 'N/A')}")
        
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