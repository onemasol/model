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
from models.agent_state import AgentState

def test_calendar_flow():
    """task_router → calendar_agent → answer_planner → answer_generator → END 플로우를 테스트합니다."""
    
    # 일정 등록 관련 테스트 케이스들
    test_cases = [
        {
            "description": "특정 시간 일정 생성",
            "input": "내일 오후 2시에 팀 미팅 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "종일 할일 생성",
            "input": "오늘 장보기 할일 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "복잡한 일정 생성",
            "input": "다음주 월요일 오전 10시에 프로젝트 회의 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "시간 범위 일정 생성",
            "input": "내일 오후 3시부터 5시까지 고객 미팅 추가해줘",
            "expected_flow": ["task_router", "calendar_agent", "answer_planner", "answer_generator"]
        }
    ]
    
    print("=" * 80)
    print("📅 Calendar Flow 테스트 (task_router → calendar_agent → answer_planner → answer_generator)")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 테스트 {i}: {test_case['description']}")
        print("-" * 60)
        print(f"입력: {test_case['input']}")
        
        # 초기 상태 설정
        initial_state = {
            "type": "question",
            "messages": [test_case["input"]],
            "rag_result": None,
            "search_result": None,
            "crud_result": None,
            "final_answer": None,
            "next_node": None,
            "agent_messages": [],
            "router_messages": []
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
            
            # task_router가 calendar_agent로 라우팅하는지 확인
            if task_result.get('next_node') == 'calendar_agent':
                print("✅ Task Router: calendar_agent로 올바르게 라우팅됨")
            else:
                print(f"❌ Task Router: 예상과 다름. 다음 노드: {task_result.get('next_node')}")
                continue
            
            # Step 2: calendar_agent 실행
            print("\n📅 Step 2: Calendar Agent 실행")
            step_start_time = time.time()
            calendar_result = calendar_agent(task_result.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print(f"✅ Calendar Agent 결과:")
            print(f"   - 타입: {calendar_result.get('calendar_type', 'N/A')}")
            print(f"   - 작업: {calendar_result.get('calendar_operation', 'N/A')}")
            print(f"   - 다음 노드: {calendar_result.get('next_node', 'N/A')}")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
            # 페이로드 정보 출력
            payload = calendar_result.get('event_payload', {})
            if payload:
                print(f"   - 제목: {payload.get('title', 'N/A')}")
                print(f"   - 시작 시간: {payload.get('start_at', 'N/A')}")
                print(f"   - 종료 시간: {payload.get('end_at', 'N/A')}")
                print(f"   - 마감 시간: {payload.get('due_at', 'N/A')}")
                print(f"   - 이벤트 타입: {payload.get('event_type', 'N/A')}")
            
            # calendar_agent가 answer_planner로 라우팅하는지 확인
            if calendar_result.get('next_node') == 'answer_planner':
                print("✅ Calendar Agent: answer_planner로 올바르게 라우팅됨")
            else:
                print(f"❌ Calendar Agent: 예상과 다름. 다음 노드: {calendar_result.get('next_node')}")
                continue
            
            # Step 3: answer_planner 실행
            print("\n📝 Step 3: Answer Planner 실행")
            step_start_time = time.time()
            planner_result = answer_planner(calendar_result.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print(f"✅ Answer Planner 결과:")
            print(f"   - 다음 노드: {planner_result.get('next_node', 'N/A')}")
            print(f"   - 에이전트 메시지: {len(planner_result.get('agent_messages', []))}개")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
            # answer_planner가 answer_generator로 라우팅하는지 확인
            if planner_result.get('next_node') == 'answer_generator':
                print("✅ Answer Planner: answer_generator로 올바르게 라우팅됨")
            else:
                print(f"❌ Answer Planner: 예상과 다름. 다음 노드: {planner_result.get('next_node')}")
                continue
            
            # Step 4: answer_generator 실행
            print("\n💬 Step 4: Answer Generator 실행")
            step_start_time = time.time()
            answer_result = answer_generator(planner_result.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print(f"✅ Answer Generator 결과:")
            print(f"   - 최종 답변: {answer_result.get('final_answer', 'N/A')}")
            print(f"   - 에이전트 메시지: {len(answer_result.get('agent_messages', []))}개")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
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
            print(f"   - Task Router → Calendar Agent → Answer Planner → Answer Generator: ✅ 성공")
            print(f"   - 총 실행 시간: {total_duration:.2f}초")
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
    print("=" * 80)
    print("일정 등록 관련 질문을 입력하면 task_router → calendar_agent → answer_planner → answer_generator 플로우를 테스트합니다.")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    
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
            "messages": [user_input],
            "rag_result": None,
            "search_result": None,
            "crud_result": None,
            "final_answer": None,
            "next_node": None,
            "agent_messages": [],
            "router_messages": []
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
                print(f"   ❌ calendar_agent로 라우팅되지 않음. 실제: {next_node}")
                print("   💡 일정 등록 관련 질문을 입력해보세요. (예: '내일 오후 2시 미팅 추가해줘')")
                continue
            
            # Step 2: calendar_agent
            print("\n2️⃣ Calendar Agent 실행...")
            step_start_time = time.time()
            calendar_result = calendar_agent(task_result.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
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
                print(f"   ❌ answer_planner로 라우팅되지 않음. 실제: {next_node}")
                continue
            
            # Step 3: answer_planner
            print("\n3️⃣ Answer Planner 실행...")
            step_start_time = time.time()
            planner_result = answer_planner(calendar_result.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            next_node = planner_result.get('next_node')
            print(f"   → 다음 노드: {next_node}")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
            if next_node != 'answer_generator':
                print(f"   ❌ answer_generator로 라우팅되지 않음. 실제: {next_node}")
                continue
            
            # Step 4: answer_generator
            print("\n4️⃣ Answer Generator 실행...")
            step_start_time = time.time()
            answer_result = answer_generator(planner_result.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            final_answer = answer_result.get('final_answer')
            print(f"   → 최종 답변: {final_answer}")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            print(f"\n⏱️  총 실행 시간: {total_duration:.2f}초")
            
            if final_answer:
                print("\n✅ 전체 플로우 성공!")
            else:
                print("\n❌ 최종 답변 생성 실패")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("Calendar Flow 테스트를 시작합니다.")
    print("1. 자동 테스트 (미리 정의된 케이스들)")
    print("2. 대화형 테스트 (사용자 입력)")
    
    choice = input("\n선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        test_calendar_flow()
    elif choice == "2":
        test_interactive_calendar_flow()
    else:
        print("잘못된 선택입니다. 자동 테스트를 실행합니다.")
        test_calendar_flow() 