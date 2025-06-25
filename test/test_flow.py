# Import global session and access token variables from api2
import sys
import os
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.getset import (
    get_current_session_id,
    get_current_access_token,
    get_current_user_input,
    get_current_ocr_result,
)

from routers.task_router import task_router
from agents.calendar_agent import calendar_agent
from agents.answer_planner import answer_planner
from agents.answer_generator import answer_generator
from agents.calselector import calselector
from models.agent_state import AgentState


def merge_input(user_query: str, ocr_result: str) -> str:
    """
    Merge user query and OCR result into a single line.
    Replace any line breaks or carriage returns in the inputs with spaces.
    """
    # Combine the inputs with a space separator
    merged = f"{ocr_result} {user_query}"
    # Replace any newline or carriage return with a space and collapse multiple spaces
    sanitized = merged.replace("\n", " ").replace("\r", " ")
    # Collapse any sequence of whitespace into a single space
    input = " ".join(sanitized.split())
    return input

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

    start = True
    
    while start:
        # Fetch latest user input and OCR result from global getters
        user_input = merge_input(get_current_user_input(), get_current_ocr_result())
        
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
            "final_output": None,
            "next_node": None,
            "agent_messages": [],
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
            
            # Step 3-1: query_refiner 실행 (라우팅이 query_refiner인 경우)
            refiner_result = None  # 변수 초기화
            if current_state.get('next_node') == 'query_refiner':
                print("\n🔍 Step 3-1: Query Refiner 실행")
                step_start_time = time.time()
                from routers.query_refiner import query_refiner
                refiner_result = query_refiner(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = refiner_result.copy()
                
                print(f"✅ Query Refiner 결과:")
                print(f"   - 다음 노드: {refiner_result.get('next_node', 'N/A')}")
                print(f"   - 정제된 쿼리: {refiner_result.get('refined_query', 'N/A')}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # query_refiner가 rag_retriever로 라우팅하는지 확인
                if refiner_result.get('next_node') == 'rag_retriever':
                    print("✅ Query Refiner: rag_retriever로 올바르게 라우팅됨")
                else:
                    print(f"⚠️  Query Refiner: 예상과 다름. 다음 노드: {refiner_result.get('next_node')}")
            else:
                print("\n🔍 Step 3-1: Query Refiner 건너뜀 (다른 플로우)")
            
            # Step 3-2: rag_retriever 실행 (라우팅이 rag_retriever인 경우)
            rag_result = None  # 변수 초기화
            if current_state.get('next_node') == 'rag_retriever':
                print("\n📚 Step 3-2: RAG Retriever 실행")
                step_start_time = time.time()
                from agents.rag_retriever import rag_retriever
                rag_result = rag_retriever(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = rag_result.copy()
                
                print(f"✅ RAG Retriever 결과:")
                print(f"   - 다음 노드: {rag_result.get('next_node', 'N/A')}")
                print(f"   - RAG 결과: {rag_result.get('rag_result', 'N/A')[:100]}...")
                print(f"   - 문서 개수: {rag_result.get('rag_docs', 'N/A')[:100]}...")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # rag_retriever가 rag_quality_critic로 라우팅하는지 확인
                if rag_result.get('next_node') == 'rag_quality_critic':
                    print("✅ RAG Retriever: rag_quality_critic로 올바르게 라우팅됨")
                else:
                    print(f"⚠️  RAG Retriever: 예상과 다름. 다음 노드: {rag_result.get('next_node')}")
            else:
                print("\n📚 Step 3-2: RAG Retriever 건너뜀 (다른 플로우)")
            
            # Step 3-3: rag_quality_critic 실행 (라우팅이 rag_quality_critic인 경우)
            rag_critic_result = None  # 변수 초기화
            if current_state.get('next_node') == 'rag_quality_critic':
                print("\n🔍 Step 3-3: RAG Quality Critic 실행")
                step_start_time = time.time()
                from routers.rag_quality_critic import rag_quality_critic
                rag_critic_result = rag_quality_critic(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = rag_critic_result.copy()
                
                print(f"✅ RAG Quality Critic 결과:")
                print(f"   - 다음 노드: {rag_critic_result.get('next_node', 'N/A')}")
                print(f"   - 품질 점수: {rag_critic_result.get('quality_score', 'N/A')}")
                print(f"   - 품질 평가: {rag_critic_result.get('quality_assessment', 'N/A')}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # rag_quality_critic의 라우팅 결정 확인
                next_node = rag_critic_result.get('next_node')
                if next_node == 'websearch_agent':
                    print("✅ RAG Quality Critic: websearch_agent로 라우팅 (웹 검색 필요)")
                elif next_node == 'calendar_needed':
                    print("✅ RAG Quality Critic: calendar_needed로 라우팅 (일정 처리 판단)")
                elif next_node == 'rag_retriever':
                    print("✅ RAG Quality Critic: rag_retriever로 라우팅 (RAG 재검색)")
                else:
                    print(f"⚠️  RAG Quality Critic: 예상과 다름. 다음 노드: {next_node}")
            else:
                print("\n🔍 Step 3-3: RAG Quality Critic 건너뜀 (다른 플로우)")
            
            # Step 3-4: calendar_needed 실행 (라우팅이 calendar_needed인 경우)
            calendar_needed_result = None  # 변수 초기화
            if current_state.get('next_node') == 'calendar_needed':
                print("\n📅 Step 3-4: Calendar Needed 실행")
                step_start_time = time.time()
                from routers.calendar_needed import calendar_needed
                calendar_needed_result = calendar_needed(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = calendar_needed_result.copy()
                
                print(f"✅ Calendar Needed 결과:")
                print(f"   - 다음 노드: {calendar_needed_result.get('next_node', 'N/A')}")
                print(f"   - 판단 결과: {calendar_needed_result.get('router_messages', [{}])[-1].get('decision', 'N/A')}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # calendar_needed의 라우팅 결정 확인
                next_node = calendar_needed_result.get('next_node')
                if next_node == 'calendar_agent':
                    print("✅ Calendar Needed: calendar_agent로 라우팅 (일정 처리 필요)")
                elif next_node == 'answer_planner':
                    print("✅ Calendar Needed: answer_planner로 라우팅 (단순 정보 응답)")
                else:
                    print(f"⚠️  Calendar Needed: 예상과 다름. 다음 노드: {next_node}")
            else:
                print("\n📅 Step 3-4: Calendar Needed 건너뜀 (다른 플로우)")
            
            # Step 3-5: websearch_agent 실행 (라우팅이 websearch_agent인 경우)
            websearch_agent_result = None  # 변수 초기화
            if current_state.get('next_node') == 'websearch_agent':
                print("\n🔍 Step 3-6: Websearch Agent 실행")
                step_start_time = time.time()
                from agents.websearch_agent import websearch_agent
                websearch_agent_result = websearch_agent(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = websearch_agent_result.copy()
                
                print(f"✅ Websearch Agent 결과:")
                print(f"   - 다음 노드: {websearch_agent_result.get('next_node', 'N/A')}")
                print(f"   - 검색 결과: {websearch_agent_result.get('search_result', 'N/A')[:100]}...")
                print(f"   - 검색된 URL 수: {len(websearch_agent_result.get('search_urls', []))}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # websearch_agent가 websearch_critic으로 라우팅하는지 확인
                if websearch_agent_result.get('next_node') == 'websearch_critic':
                    print("✅ Websearch Agent: websearch_critic으로 올바르게 라우팅됨")
                else:
                    print(f"⚠️  Websearch Agent: 예상과 다름. 다음 노드: {websearch_agent_result.get('next_node')}")
            else:
                print("\n🔍 Step 3-6: Websearch Agent 건너뜀 (다른 플로우)")
            
            # 디버깅: 현재 상태의 next_node 확인
            print(f"\n🔍 디버깅: 현재 next_node = {current_state.get('next_node', 'N/A')}")
            
            # Step 3-7: websearch_critic 실행 (라우팅이 websearch_critic인 경우)
            websearch_critic_result = None  # 변수 초기화
            if current_state.get('next_node') == 'websearch_critic':
                print("\n🌐 Step 3-7: Websearch Critic 실행")
                step_start_time = time.time()
                from routers.websearch_critic import websearch_critic
                websearch_critic_result = websearch_critic(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                current_state = websearch_critic_result.copy()
                
                print(f"✅ Websearch Critic 결과:")
                print(f"   - 다음 노드: {websearch_critic_result.get('next_node', 'N/A')}")
                print(f"   - 웹 검색 필요성: {websearch_critic_result.get('websearch_needed', 'N/A')}")
                print(f"   - 검색 쿼리: {websearch_critic_result.get('search_query', 'N/A')}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # websearch_critic의 라우팅 결정 확인
                next_node = websearch_critic_result.get('next_node')
                if next_node == 'websearch_agent':
                    print("✅ Websearch Critic: websearch_agent로 라우팅 (웹 검색 실행)")
                elif next_node == 'calendar_needed':
                    print("✅ Websearch Critic: calendar_needed로 라우팅 (일정 처리 판단)")
                elif next_node == 'answer_generator':
                    print("✅ Websearch Critic: answer_generator로 라우팅 (웹 검색 불필요)")
                else:
                    print(f"⚠️  Websearch Critic: 예상과 다름. 다음 노드: {next_node}")
            else:
                print(f"\n🌐 Step 3-7: Websearch Critic 건너뜀 (다른 플로우) - 현재 next_node: {current_state.get('next_node', 'N/A')}")
            
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
            
            final_output = answer_result.get('final_output')
            print(f"   → 최종 답변: {final_output}")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
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
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            print(f"\n⏱️  총 실행 시간: {total_duration:.2f}초")
            
            # API 요청 여부 표시
            if crud_result:
                print(f"🎯 API 요청: ✅ 발생 (결과: {crud_result})")
            else:
                print(f"🎯 API 요청: ❌ 발생하지 않음")
            
            if final_output:
                print("\n✅ 전체 플로우 성공!")
            else:
                print("\n❌ 최종 답변 생성 실패")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            start = False

if __name__ == "__main__":
    print("🎉 Flow 테스트를 시작합니다! 🎉")

    test_interactive_calendar_flow()