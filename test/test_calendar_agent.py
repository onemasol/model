import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import calendar_agent, CalendarAgent
from models.agent_state import AgentState

def print_separator(title=""):
    """구분선을 출력합니다."""
    print("\n" + "="*60)
    if title:
        print(f" {title} ")
        print("="*60)
    else:
        print("="*60)

def print_json_pretty(data, title=""):
    """JSON 데이터를 예쁘게 출력합니다."""
    if title:
        print(f"\n📋 {title}:")
    try:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(data)

def test_calendar_agent():
    """Calendar Agent 테스트 함수"""
    print_separator("📅 Calendar Agent 테스트 시작")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print("\n테스트 가능한 예시:")
    print("1. 일정 생성: '내일 오후 2시에 회의 일정 만들어줘'")
    print("2. 일정 조회: '이번 주 회의 일정 보여줘'")
    print("3. 일정 수정: '내일 회의 시간을 3시로 바꿔줘'")
    print("4. 일정 삭제: '내일 회의 일정 삭제해줘'")
    print("5. 할 일 생성: '내일까지 보고서 작성하기'")
    print("6. 할 일 조회: '이번 주 할 일 목록 보여줘'")
    
    while True:
        # 사용자 입력 받기
        user_input = input("\n🎯 테스트할 일정 관련 요청을 입력하세요: ").strip()
        
        # 종료 명령 확인
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n✅ 테스트를 종료합니다.")
            break
        
        # 일정 타입 선택
        print("\n📝 일정 타입을 선택하세요:")
        print("1. event (특정 시간에 진행되는 일정)")
        print("2. task (완료해야 할 작업)")
        
        schedule_type_choice = input("선택 (1 또는 2, 기본값: 1): ").strip()
        schedule_type = "task" if schedule_type_choice == "2" else "event"
        
        print_separator(f"🔍 테스트 실행 - {schedule_type.upper()}")
        
        # 테스트 상태 초기화
        test_state = AgentState(
            type="schedule",
            schedule_type=schedule_type,
            messages=[user_input],
            initial_input=user_input,
            final_output=None,
            rag_result=None,
            search_result=None,
            crud_result=None,
            next_node=None,
            agent_messages=[],
            router_messages=[]
        )
        
        try:
            # Calendar Agent 실행
            print(f"🚀 Calendar Agent 실행 중...")
            print(f"📝 입력: {user_input}")
            print(f"📅 일정 타입: {schedule_type}")
            
            result = calendar_agent(test_state)
            
            # 결과 출력
            print_separator("📊 실행 결과")
            
            # 기본 결과
            print(f"✅ 처리 결과: {result['crud_result']}")
            
            # API Request 정보 출력
            if 'api_request' in result and result['api_request']:
                print_separator("🔧 백엔드용 API Request Body")
                
                api_request = result['api_request']
                
                if api_request.get('multi_step'):
                    print("🔄 다단계 API 호출이 필요합니다:")
                    for i, step in enumerate(api_request['steps'], 1):
                        print(f"\n📋 단계 {i}: {step['operation']}")
                        print(f"   🔗 엔드포인트: {step['endpoint']}")
                        print(f"   📡 HTTP 메서드: {step['http_method']}")
                        print(f"   🏷️  API 타입: {step['api_type']}")
                        
                        if 'query_params' in step:
                            print_json_pretty(step['query_params'], "🔍 쿼리 파라미터")
                        
                        if 'request_body' in step:
                            print_json_pretty(step['request_body'], "📦 Request Body")
                        
                        if 'step' in step:
                            print(f"   🎯 단계: {step['step']}")
                        if 'depends_on' in step:
                            print(f"   ⚡ 의존성: {step['depends_on']}")
                else:
                    print(f"📡 API 타입: {api_request['api_type']}")
                    print(f"🔧 작업: {api_request['operation']}")
                    print(f"🔗 엔드포인트: {api_request['endpoint']}")
                    print(f"📡 HTTP 메서드: {api_request['http_method']}")
                    
                    if 'calendar_id' in api_request:
                        print(f"📅 캘린더 ID: {api_request['calendar_id']}")
                    if 'tasklist_id' in api_request:
                        print(f"📋 작업 목록 ID: {api_request['tasklist_id']}")
                    
                    if 'request_body' in api_request:
                        print_json_pretty(api_request['request_body'], "📦 Request Body")
                    
                    if 'query_params' in api_request:
                        print_json_pretty(api_request['query_params'], "🔍 쿼리 파라미터")
            else:
                print("⚠️  API Request Body가 생성되지 않았습니다.")
            
            # 에이전트 메시지 출력
            if result.get('agent_messages'):
                print_separator("🤖 에이전트 처리 기록")
                for i, msg in enumerate(result['agent_messages'], 1):
                    print(f"\n📝 메시지 {i}:")
                    print(f"   🤖 에이전트: {msg['agent']}")
                    print(f"   📥 입력 스냅샷:")
                    for key, value in msg['input_snapshot'].items():
                        print(f"      - {key}: {value}")
                    print(f"   📤 출력: {msg['output']}")
                    
                    if 'api_request' in msg and msg['api_request']:
                        print(f"   🔧 API Request: 생성됨")
            
            # 상태 정보 출력
            print_separator("📈 상태 정보")
            print(f"📝 최초 입력: {result['initial_input']}")
            print(f"📅 일정 타입: {result.get('schedule_type', '해당 없음')}")
            print(f"🏷️  입력 유형: {result['type']}")
            print(f"💬 대화 기록: {result['messages']}")
            
        except Exception as e:
            print_separator("❌ 오류 발생")
            print(f"오류 내용: {str(e)}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")

def test_calendar_agent_class():
    """CalendarAgent 클래스 테스트"""
    print_separator("🧪 CalendarAgent 클래스 테스트")
    
    try:
        cal_agent = CalendarAgent()
        print("✅ CalendarAgent 인스턴스 생성 성공")
        
        # 캘린더 ID 테스트
        calendar_id = cal_agent._get_calendar_id()
        print(f"📅 캘린더 ID: {calendar_id}")
        
        # 작업 목록 ID 테스트
        tasklist_id = cal_agent._get_tasklist_id()
        print(f"📋 작업 목록 ID: {tasklist_id}")
        
        # 날짜 파싱 테스트
        test_dates = [
            "2025-06-13 14:00",
            "2025-06-13T14:00:00+09:00",
            "2025-06-13T14:00:00Z"
        ]
        
        print("\n📅 날짜 파싱 테스트:")
        for date_str in test_dates:
            try:
                parsed = cal_agent._parse_datetime(date_str)
                print(f"   ✅ {date_str} → {parsed}")
            except Exception as e:
                print(f"   ❌ {date_str} → 오류: {e}")
                
    except Exception as e:
        print(f"❌ CalendarAgent 클래스 테스트 실패: {e}")

def run_specific_tests():
    """특정 테스트 케이스 실행"""
    print_separator("🧪 특정 테스트 케이스 실행")
    
    test_cases = [
        {
            "input": "내일 오후 2시에 회의 일정 만들어줘",
            "schedule_type": "event",
            "description": "일정 생성 테스트"
        },
        {
            "input": "이번 주 회의 일정 보여줘",
            "schedule_type": "event", 
            "description": "일정 조회 테스트"
        },
        {
            "input": "내일 회의 시간을 3시로 바꿔줘",
            "schedule_type": "event",
            "description": "일정 수정 테스트"
        },
        {
            "input": "내일까지 보고서 작성하기",
            "schedule_type": "task",
            "description": "할 일 생성 테스트"
        },
        {
            "input": "이번 주 할 일 목록 보여줘",
            "schedule_type": "task",
            "description": "할 일 조회 테스트"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 테스트 케이스 {i}: {test_case['description']}")
        print(f"📝 입력: {test_case['input']}")
        print(f"📅 타입: {test_case['schedule_type']}")
        
        test_state = AgentState(
            type="schedule",
            schedule_type=test_case['schedule_type'],
            messages=[test_case['input']],
            initial_input=test_case['input'],
            final_output=None,
            rag_result=None,
            search_result=None,
            crud_result=None,
            next_node=None,
            agent_messages=[],
            router_messages=[]
        )
        
        try:
            result = calendar_agent(test_state)
            print(f"✅ 결과: {result['crud_result']}")
            
            if 'api_request' in result and result['api_request']:
                api_request = result['api_request']
                if api_request.get('multi_step'):
                    print(f"🔄 다단계 API 호출 ({len(api_request['steps'])} 단계)")
                else:
                    print(f"📡 단일 API 호출: {api_request['operation']}")
            else:
                print("⚠️  API Request 없음")
                
        except Exception as e:
            print(f"❌ 오류: {e}")

if __name__ == "__main__":
    print("🎯 Calendar Agent 테스트 프로그램")
    print("\n테스트 옵션:")
    print("1. 대화형 테스트 (사용자 입력)")
    print("2. 클래스 테스트")
    print("3. 특정 테스트 케이스 실행")
    print("4. 모든 테스트 실행")
    
    choice = input("\n선택하세요 (1-4, 기본값: 1): ").strip()
    
    if choice == "2":
        test_calendar_agent_class()
    elif choice == "3":
        run_specific_tests()
    elif choice == "4":
        test_calendar_agent_class()
        run_specific_tests()
        test_calendar_agent()
    else:
        test_calendar_agent() 