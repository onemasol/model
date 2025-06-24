import sys
import os
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.task_router import task_router
from routers.query_refiner import query_refiner
from agents.rag_retriever import rag_retriever
from routers.rag_quality_critic import rag_quality_critic
from agents.websearch_agent import websearch_agent
from routers.websearch_critic import websearch_critic
from routers.calendar_needed import calendar_needed
from agents.calendar_agent import calendar_agent
from agents.answer_planner import answer_planner
from agents.answer_generator import answer_generator
from models.agent_state import AgentState

def test_comprehensive_rag_flow():
    """RAG와 웹서치를 포함한 전체 플로우를 테스트합니다."""
    
    # 종합적인 테스트 케이스들
    test_cases = [
        {
            "description": "RAG 성공 후 답변 생성 (기본 세무 정보)",
            "input": "부가세 신고 기간이 언제인가요?",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "calendar_needed", "answer_planner", "answer_generator"]
        },
        {
            "description": "RAG 실패 후 웹서치 (최신 정보 필요)",
            "input": "2024년 12월 기준으로 요식업 위생 관리 기준이 어떻게 변경되었나요?",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "websearch_agent", "websearch_critic"]
        },
        {
            "description": "RAG 재검색 필요 (모호한 질문)",
            "input": "음식점에서 발생할 수 있는 모든 위생 관련 문제와 해결방법을 알려주세요",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "rag_retriever"]
        },
        {
            "description": "웹서치 후 캘린더 작업 (구체적인 일정)",
            "input": "내일 오후 3시에 세무사 상담 약속 잡아주고, 상담 전에 준비해야 할 서류도 알려줘",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "websearch_agent", "websearch_critic", "calendar_needed", "calendar_agent", "answer_planner", "answer_generator"]
        },
        {
            "description": "극단적 웹서치 케이스 (완전히 새로운 정보)",
            "input": "2024년 12월에 새로 발표된 요식업 관련 법규 변경사항과 2025년 1월부터 적용되는 새로운 위생 기준을 알려주세요",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "websearch_agent", "websearch_critic"]
        },
        {
            "description": "실시간 정보 필요 (웹서치 필수)",
            "input": "지금 현재 서울시에서 진행 중인 요식업 지원 정책과 신청 방법을 알려주세요",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "websearch_agent", "websearch_critic"]
        }
    ]
    
    print("=" * 80)
    print("🔍 종합 RAG Flow 테스트 (RAG + 웹서치 + 캘린더 + 답변생성)")
    print("=" * 80)
    
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
            "router_messages": []
        }
        
        # 전체 시작 시간
        total_start_time = time.time()
        current_state = initial_state.copy()
        
        try:
            # Step 1: task_router 실행
            print("\n📋 Step 1: Task Router 실행")
            step_start_time = time.time()
            current_state = task_router(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print(f"✅ Task Router 결과:")
            print(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
            if current_state.get('next_node') != 'query_refiner':
                print(f"❌ Task Router: query_refiner로 라우팅되지 않음. 실제: {current_state.get('next_node')}")
                continue
            
            # Step 2: query_refiner 실행
            print("\n🔧 Step 2: Query Refiner 실행")
            step_start_time = time.time()
            current_state = query_refiner(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print(f"✅ Query Refiner 결과:")
            print(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
            if current_state.get('next_node') != 'rag_retriever':
                print(f"❌ Query Refiner: rag_retriever로 라우팅되지 않음. 실제: {current_state.get('next_node')}")
                continue
            
            # Step 3: rag_retriever 실행
            print("\n📚 Step 3: RAG Retriever 실행")
            step_start_time = time.time()
            current_state = rag_retriever(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            rag_content = current_state.get('rag_result', '')
            print(f"✅ RAG Retriever 결과:")
            print(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
            print(f"   - RAG 결과: {len(rag_content)}자")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            if rag_content:
                print(f"   - RAG 미리보기: {rag_content[:100]}...")
            
            if current_state.get('next_node') != 'rag_quality_critic':
                print(f"❌ RAG Retriever: rag_quality_critic로 라우팅되지 않음. 실제: {current_state.get('next_node')}")
                continue
            
            # Step 4: rag_quality_critic 실행
            print("\n🎯 Step 4: RAG Quality Critic 실행")
            step_start_time = time.time()
            current_state = rag_quality_critic(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            next_node = current_state.get('next_node')
            print(f"✅ RAG Quality Critic 결과:")
            print(f"   - 다음 노드: {next_node}")
            print(f"   - 실행 시간: {step_duration:.2f}초")
            
            # 품질 평가 결과 확인
            router_messages = current_state.get('router_messages', [])
            if router_messages:
                print(f"   - 품질 평가: {router_messages[-1].get('decision', 'N/A')}")
            
            # Step 5: rag_quality_critic 이후 분기 처리
            if next_node == 'rag_retriever':
                print("\n🔄 RAG 재검색 필요 - RAG Retriever 재실행")
                step_start_time = time.time()
                current_state = rag_retriever(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                rag_content = current_state.get('rag_result', '')
                print(f"✅ RAG 재검색 결과:")
                print(f"   - RAG 결과: {len(rag_content)}자")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                # 재검색 후 다시 critic 실행
                print("\n🎯 RAG Quality Critic 재실행")
                step_start_time = time.time()
                current_state = rag_quality_critic(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                next_node = current_state.get('next_node')
                print(f"   - 다음 노드: {next_node}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
            
            elif next_node == 'websearch_agent':
                print("\n🌐 웹서치 필요 - Websearch Agent 실행")
                step_start_time = time.time()
                current_state = websearch_agent(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                search_content = current_state.get('search_result', '')
                print(f"✅ Websearch Agent 결과:")
                print(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
                print(f"   - 웹서치 결과: {len(search_content)}자")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                if current_state.get('next_node') == 'websearch_critic':
                    print("\n🎯 Websearch Critic 실행")
                    step_start_time = time.time()
                    current_state = websearch_critic(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    next_node = current_state.get('next_node')
                    print(f"   - 다음 노드: {next_node}")
                    print(f"   - 실행 시간: {step_duration:.2f}초")
            
            # Step 6: calendar_needed 또는 answer_planner로 분기
            if next_node == 'calendar_needed':
                print("\n📅 캘린더 필요 - Calendar Needed 실행")
                step_start_time = time.time()
                current_state = calendar_needed(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                next_node = current_state.get('next_node')
                print(f"✅ Calendar Needed 결과:")
                print(f"   - 다음 노드: {next_node}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                
                if next_node == 'calendar_agent':
                    print("\n📅 Calendar Agent 실행")
                    step_start_time = time.time()
                    current_state = calendar_agent(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    payload = current_state.get('event_payload', {})
                    print(f"✅ Calendar Agent 결과:")
                    print(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
                    print(f"   - 실행 시간: {step_duration:.2f}초")
                    if payload:
                        print(f"   - 일정 정보: {payload.get('title', 'N/A')}")
                    
                    next_node = current_state.get('next_node')
            
            # Step 7: answer_planner 실행
            if next_node == 'answer_planner':
                print("\n📝 Answer Planner 실행")
                step_start_time = time.time()
                current_state = answer_planner(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                next_node = current_state.get('next_node')
                print(f"✅ Answer Planner 결과:")
                print(f"   - 다음 노드: {next_node}")
                print(f"   - 실행 시간: {step_duration:.2f}초")
            
            # Step 8: answer_generator 실행
            if next_node == 'answer_generator':
                print("\n💬 Answer Generator 실행")
                step_start_time = time.time()
                current_state = answer_generator(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                final_answer = current_state.get('final_answer', '')
                print(f"✅ Answer Generator 결과:")
                print(f"   - 최종 답변: {len(final_answer)}자")
                print(f"   - 실행 시간: {step_duration:.2f}초")
                if final_answer:
                    print(f"   - 답변 미리보기: {final_answer[:100]}...")
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            
            # 전체 플로우 요약
            print(f"\n📊 전체 플로우 요약:")
            print(f"   - 입력: {test_case['input']}")
            print(f"   - 총 실행 시간: {total_duration:.2f}초")
            print(f"   - 최종 노드: {current_state.get('next_node', 'N/A')}")
            
            final_answer = current_state.get('final_answer', '')
            if final_answer:
                print(f"   - 최종 답변 생성: ✅ 성공")
            else:
                print(f"   - 최종 답변 생성: ❌ 실패")
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

def test_interactive_comprehensive_flow():
    """사용자 입력을 받아서 종합적인 플로우를 대화형으로 테스트합니다."""
    
    print("\n" + "=" * 80)
    print("🎯 대화형 종합 Flow 테스트")
    print("=" * 80)
    print("질문을 입력하면 RAG → 웹서치 → 캘린더 → 답변생성의 전체 플로우를 테스트합니다.")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    
    while True:
        # 사용자 입력 받기
        user_input = input("\n📝 질문을 입력하세요: ").strip()
        
        # 종료 조건 확인
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n테스트를 종료합니다.")
            break
        
        if not user_input:
            print("입력이 비어있습니다. 다시 입력해주세요.")
            continue
        
        print(f"\n🔄 '{user_input}' 처리 중...")
        
        # 초기 상태 설정
        current_state = {
            "type": "question",
            "initial_input": user_input,
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
            current_state = task_router(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            next_node = current_state.get('next_node')
            print(f"   → 다음 노드: {next_node}")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
            if next_node != 'query_refiner':
                print(f"   ❌ query_refiner로 라우팅되지 않음. 실제: {next_node}")
                continue
            
            # Step 2: query_refiner
            print("\n2️⃣ Query Refiner 실행...")
            step_start_time = time.time()
            current_state = query_refiner(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            next_node = current_state.get('next_node')
            print(f"   → 다음 노드: {next_node}")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
            if next_node != 'rag_retriever':
                print(f"   ❌ rag_retriever로 라우팅되지 않음. 실제: {next_node}")
                continue
            
            # Step 3: rag_retriever
            print("\n3️⃣ RAG Retriever 실행...")
            step_start_time = time.time()
            current_state = rag_retriever(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            rag_content = current_state.get('rag_result', '')
            print(f"   → RAG 결과: {len(rag_content)}자")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
            next_node = current_state.get('next_node')
            print(f"   → 다음 노드: {next_node}")
            
            if next_node != 'rag_quality_critic':
                print(f"   ❌ rag_quality_critic로 라우팅되지 않음. 실제: {next_node}")
                continue
            
            # Step 4: rag_quality_critic
            print("\n4️⃣ RAG Quality Critic 실행...")
            step_start_time = time.time()
            current_state = rag_quality_critic(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            next_node = current_state.get('next_node')
            print(f"   → 다음 노드: {next_node}")
            print(f"   → 실행 시간: {step_duration:.2f}초")
            
            # Step 5: rag_quality_critic 이후 분기 처리
            if next_node == 'rag_retriever':
                print("\n🔄 RAG 재검색 필요 - RAG Retriever 재실행")
                step_start_time = time.time()
                current_state = rag_retriever(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                rag_content = current_state.get('rag_result', '')
                print(f"   → RAG 재검색 결과: {len(rag_content)}자")
                print(f"   → 실행 시간: {step_duration:.2f}초")
                
                # 재검색 후 다시 critic 실행
                print("\n🎯 RAG Quality Critic 재실행")
                step_start_time = time.time()
                current_state = rag_quality_critic(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                next_node = current_state.get('next_node')
                print(f"   → 다음 노드: {next_node}")
                print(f"   → 실행 시간: {step_duration:.2f}초")
            
            elif next_node == 'websearch_agent':
                print("\n🌐 웹서치 필요 - Websearch Agent 실행")
                step_start_time = time.time()
                current_state = websearch_agent(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                search_content = current_state.get('search_result', '')
                print(f"   → 웹서치 결과: {len(search_content)}자")
                print(f"   → 실행 시간: {step_duration:.2f}초")
                
                next_node = current_state.get('next_node')
                print(f"   → 다음 노드: {next_node}")
                
                if next_node == 'websearch_critic':
                    print("\n🎯 Websearch Critic 실행")
                    step_start_time = time.time()
                    current_state = websearch_critic(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    next_node = current_state.get('next_node')
                    print(f"   → 다음 노드: {next_node}")
                    print(f"   → 실행 시간: {step_duration:.2f}초")
            
            # Step 6: calendar_needed 또는 answer_planner로 분기
            if next_node == 'calendar_needed':
                print("\n📅 캘린더 필요 - Calendar Needed 실행")
                step_start_time = time.time()
                current_state = calendar_needed(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                next_node = current_state.get('next_node')
                print(f"   → 다음 노드: {next_node}")
                print(f"   → 실행 시간: {step_duration:.2f}초")
                
                if next_node == 'calendar_agent':
                    print("\n📅 Calendar Agent 실행")
                    step_start_time = time.time()
                    current_state = calendar_agent(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    payload = current_state.get('event_payload', {})
                    print(f"   → 일정 정보: {payload.get('title', 'N/A') if payload else 'N/A'}")
                    print(f"   → 실행 시간: {step_duration:.2f}초")
                    
                    next_node = current_state.get('next_node')
            
            # Step 7: answer_planner 실행
            if next_node == 'answer_planner':
                print("\n📝 Answer Planner 실행")
                step_start_time = time.time()
                current_state = answer_planner(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                next_node = current_state.get('next_node')
                print(f"   → 다음 노드: {next_node}")
                print(f"   → 실행 시간: {step_duration:.2f}초")
            
            # Step 8: answer_generator 실행
            if next_node == 'answer_generator':
                print("\n💬 Answer Generator 실행")
                step_start_time = time.time()
                current_state = answer_generator(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                final_answer = current_state.get('final_answer', '')
                print(f"   → 최종 답변: {len(final_answer)}자")
                print(f"   → 실행 시간: {step_duration:.2f}초")
                if final_answer:
                    print(f"   → 답변 미리보기: {final_answer[:100]}...")
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            print(f"\n⏱️  총 실행 시간: {total_duration:.2f}초")
            
            # 최종 결과 확인
            final_answer = current_state.get('final_answer', '')
            if final_answer:
                print("\n✅ 전체 플로우 성공! 최종 답변이 생성되었습니다.")
            else:
                print(f"\n📋 플로우 완료. 최종 노드: {current_state.get('next_node', 'N/A')}")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("종합 RAG Flow 테스트를 시작합니다.")
    print("1. 자동 테스트 (미리 정의된 케이스들)")
    print("2. 대화형 테스트 (사용자 입력)")
    
    choice = input("\n선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        test_comprehensive_rag_flow()
    elif choice == "2":
        test_interactive_comprehensive_flow()
    else:
        print("잘못된 선택입니다. 자동 테스트를 실행합니다.")
        test_comprehensive_rag_flow() 