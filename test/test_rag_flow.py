import sys
import os
import json
import time
from datetime import datetime

# 출력 버퍼링 비활성화 (Python 버전 호환성 고려)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
else:
    # Python 3.7 이하 버전을 위한 대안
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

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

def print_with_flush(message):
    """출력 버퍼를 즉시 플러시하는 함수"""
    print(message, flush=True)

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
            "description": "RAG 재검색 필요 (모호한 질문)",
            "input": "음식점에서 발생할 수 있는 모든 위생 관련 문제와 해결방법을 알려주세요",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "rag_retriever"]
        },
        {
            "description": "RAG 재검색 필요 (너무 광범위한 질문)",
            "input": "요식업 관련 모든 법규와 규정을 상세히 알려주세요",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "rag_retriever"]
        },
        {
            "description": "RAG 재검색 필요 (구체적이지 않은 질문)",
            "input": "세무 관련 모든 정보를 알려주세요",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "rag_retriever"]
        },
        {
            "description": "RAG 재검색 필요 (복합적 질문)",
            "input": "음식점 운영에 필요한 모든 허가, 세무, 위생 관련 절차와 규정을 알려주세요",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "rag_retriever"]
        },
        {
            "description": "RAG 실패 후 웹서치 (최신 정보 필요)",
            "input": "2024년 12월 기준으로 요식업 위생 관리 기준이 어떻게 변경되었나요?",
            "expected_flow": ["task_router", "query_refiner", "rag_retriever", "rag_quality_critic", "websearch_agent", "websearch_critic"]
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
    
    print_with_flush("=" * 80)
    print_with_flush("🔍 종합 RAG Flow 테스트 (RAG + 웹서치 + 캘린더 + 답변생성)")
    print_with_flush("=" * 80)
    
    successful_tests = 0
    failed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print_with_flush(f"\n🧪 테스트 {i}: {test_case['description']}")
        print_with_flush("-" * 60)
        print_with_flush(f"입력: {test_case['input']}")
        
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
        test_success = True
        error_message = ""
        
        try:
            # Step 1: task_router 실행
            print_with_flush("\n📋 Step 1: Task Router 실행")
            step_start_time = time.time()
            current_state = task_router(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print_with_flush(f"✅ Task Router 결과:")
            print_with_flush(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
            print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
            
            if current_state.get('next_node') != 'query_refiner':
                print_with_flush(f"⚠️ Task Router: query_refiner로 라우팅되지 않음. 실제: {current_state.get('next_node')}")
                # 계속 진행하되 경고 표시
            
            # Step 2: query_refiner 실행
            print_with_flush("\n🔧 Step 2: Query Refiner 실행")
            step_start_time = time.time()
            current_state = query_refiner(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            print_with_flush(f"✅ Query Refiner 결과:")
            print_with_flush(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
            print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
            
            if current_state.get('next_node') != 'rag_retriever':
                print_with_flush(f"⚠️ Query Refiner: rag_retriever로 라우팅되지 않음. 실제: {current_state.get('next_node')}")
                # 계속 진행하되 경고 표시
            
            # Step 3: rag_retriever 실행
            print_with_flush("\n📚 Step 3: RAG Retriever 실행")
            step_start_time = time.time()
            try:
                current_state = rag_retriever(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                rag_content = current_state.get('rag_result', '')
                print_with_flush(f"✅ RAG Retriever 결과:")
                print_with_flush(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
                print_with_flush(f"   - RAG 결과: {len(rag_content)}자")
                print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                if rag_content:
                    print_with_flush(f"   - RAG 미리보기: {rag_content[:200]}...")
                    print_with_flush(f"   - RAG 전체 내용:")
                    print_with_flush(f"     {rag_content}")
                
                if current_state.get('next_node') != 'rag_quality_critic':
                    print_with_flush(f"⚠️ RAG Retriever: rag_quality_critic로 라우팅되지 않음. 실제: {current_state.get('next_node')}")
                
            except Exception as rag_error:
                print_with_flush(f"❌ RAG Retriever 실행 실패: {str(rag_error)}")
                print_with_flush(f"   - 오류 타입: {type(rag_error).__name__}")
                print_with_flush(f"   - 실행 시간: {time.time() - step_start_time:.2f}초")
                test_success = False
                error_message = f"RAG Retriever 오류: {str(rag_error)}"
                # RAG 실패 시에도 다음 단계로 진행 (웹서치로 대체)
                current_state['next_node'] = 'websearch_agent'
            
            # Step 4: rag_quality_critic 실행 (RAG가 성공한 경우에만)
            if current_state.get('next_node') == 'rag_quality_critic':
                print_with_flush("\n🎯 Step 4: RAG Quality Critic 실행")
                step_start_time = time.time()
                try:
                    current_state = rag_quality_critic(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    next_node = current_state.get('next_node')
                    print_with_flush(f"✅ RAG Quality Critic 결과:")
                    print_with_flush(f"   - 다음 노드: {next_node}")
                    print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                    
                    # 품질 평가 결과 확인
                    router_messages = current_state.get('router_messages', [])
                    if router_messages:
                        print_with_flush(f"   - 품질 평가: {router_messages[-1].get('decision', 'N/A')}")
                        print_with_flush(f"   - 라우터 메시지 전체:")
                        for msg in router_messages:
                            print_with_flush(f"     {msg}")
                    
                except Exception as critic_error:
                    print_with_flush(f"❌ RAG Quality Critic 실행 실패: {str(critic_error)}")
                    print_with_flush(f"   - 오류 타입: {type(critic_error).__name__}")
                    print_with_flush(f"   - 실행 시간: {time.time() - step_start_time:.2f}초")
                    test_success = False
                    error_message = f"RAG Quality Critic 오류: {str(critic_error)}"
                    # 기본값으로 설정
                    current_state['next_node'] = 'websearch_agent'
                else:
                    next_node = current_state.get('next_node')
            else:
                next_node = current_state.get('next_node')
            
            # Step 5: rag_quality_critic 이후 분기 처리
            if next_node == 'rag_retriever':
                print_with_flush("\n🔄 RAG 재검색 필요 - RAG Retriever 재실행")
                step_start_time = time.time()
                try:
                    current_state = rag_retriever(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    rag_content = current_state.get('rag_result', '')
                    print_with_flush(f"✅ RAG 재검색 결과:")
                    print_with_flush(f"   - RAG 결과: {len(rag_content)}자")
                    print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                    if rag_content:
                        print_with_flush(f"   - RAG 재검색 내용:")
                        print_with_flush(f"     {rag_content}")
                    
                    # 재검색 후 다시 critic 실행
                    print_with_flush("\n🎯 RAG Quality Critic 재실행")
                    step_start_time = time.time()
                    current_state = rag_quality_critic(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    next_node = current_state.get('next_node')
                    print_with_flush(f"   - 다음 노드: {next_node}")
                    print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                    
                except Exception as retry_error:
                    print_with_flush(f"❌ RAG 재검색 실패: {str(retry_error)}")
                    test_success = False
                    error_message = f"RAG 재검색 오류: {str(retry_error)}"
                    next_node = 'websearch_agent'
            
            elif next_node == 'websearch_agent':
                print_with_flush("\n🌐 웹서치 필요 - Websearch Agent 실행")
                step_start_time = time.time()
                try:
                    current_state = websearch_agent(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    search_content = current_state.get('search_result', '')
                    print_with_flush(f"✅ Websearch Agent 결과:")
                    print_with_flush(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
                    print_with_flush(f"   - 웹서치 결과: {len(search_content)}자")
                    print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                    if search_content:
                        print_with_flush(f"   - 웹서치 내용:")
                        print_with_flush(f"     {search_content}")
                    
                    if current_state.get('next_node') == 'websearch_critic':
                        print_with_flush("\n🎯 Websearch Critic 실행")
                        step_start_time = time.time()
                        current_state = websearch_critic(current_state.copy())
                        step_end_time = time.time()
                        step_duration = step_end_time - step_start_time
                        next_node = current_state.get('next_node')
                        print_with_flush(f"   - 다음 노드: {next_node}")
                        print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                    else:
                        next_node = current_state.get('next_node')
                        
                except Exception as websearch_error:
                    print_with_flush(f"❌ Websearch Agent 실행 실패: {str(websearch_error)}")
                    print_with_flush(f"   - 오류 타입: {type(websearch_error).__name__}")
                    print_with_flush(f"   - 실행 시간: {time.time() - step_start_time:.2f}초")
                    test_success = False
                    error_message = f"Websearch Agent 오류: {str(websearch_error)}"
                    # 기본값으로 설정
                    next_node = 'answer_planner'
            
            # Step 6: calendar_needed 또는 answer_planner로 분기
            if next_node == 'calendar_needed':
                print_with_flush("\n📅 캘린더 필요 - Calendar Needed 실행")
                step_start_time = time.time()
                try:
                    current_state = calendar_needed(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    next_node = current_state.get('next_node')
                    print_with_flush(f"✅ Calendar Needed 결과:")
                    print_with_flush(f"   - 다음 노드: {next_node}")
                    print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                    
                    if next_node == 'calendar_agent':
                        print_with_flush("\n📅 Calendar Agent 실행")
                        step_start_time = time.time()
                        current_state = calendar_agent(current_state.copy())
                        step_end_time = time.time()
                        step_duration = step_end_time - step_start_time
                        
                        payload = current_state.get('event_payload', {})
                        print_with_flush(f"✅ Calendar Agent 결과:")
                        print_with_flush(f"   - 다음 노드: {current_state.get('next_node', 'N/A')}")
                        print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                        if payload:
                            print_with_flush(f"   - 일정 정보: {payload.get('title', 'N/A')}")
                            print_with_flush(f"   - 전체 페이로드: {payload}")
                        
                        next_node = current_state.get('next_node')
                        
                except Exception as calendar_error:
                    print_with_flush(f"❌ Calendar 관련 실행 실패: {str(calendar_error)}")
                    print_with_flush(f"   - 오류 타입: {type(calendar_error).__name__}")
                    print_with_flush(f"   - 실행 시간: {time.time() - step_start_time:.2f}초")
                    test_success = False
                    error_message = f"Calendar 오류: {str(calendar_error)}"
                    next_node = 'answer_planner'
            
            # Step 7: answer_planner 실행
            if next_node == 'answer_planner':
                print_with_flush("\n📝 Answer Planner 실행")
                step_start_time = time.time()
                try:
                    current_state = answer_planner(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    next_node = current_state.get('next_node')
                    print_with_flush(f"✅ Answer Planner 결과:")
                    print_with_flush(f"   - 다음 노드: {next_node}")
                    print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                    
                except Exception as planner_error:
                    print_with_flush(f"❌ Answer Planner 실행 실패: {str(planner_error)}")
                    print_with_flush(f"   - 오류 타입: {type(planner_error).__name__}")
                    print_with_flush(f"   - 실행 시간: {time.time() - step_start_time:.2f}초")
                    test_success = False
                    error_message = f"Answer Planner 오류: {str(planner_error)}"
                    next_node = 'answer_generator'
            
            # Step 8: answer_generator 실행
            if next_node == 'answer_generator':
                print_with_flush("\n💬 Answer Generator 실행")
                step_start_time = time.time()
                try:
                    current_state = answer_generator(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    final_answer = current_state.get('final_answer', '')
                    print_with_flush(f"✅ Answer Generator 결과:")
                    print_with_flush(f"   - 최종 답변: {len(final_answer)}자")
                    print_with_flush(f"   - 실행 시간: {step_duration:.2f}초")
                    if final_answer:
                        print_with_flush(f"   - 답변 미리보기: {final_answer[:200]}...")
                        print_with_flush(f"   - 전체 답변:")
                        print_with_flush(f"     {final_answer}")
                    
                except Exception as generator_error:
                    print_with_flush(f"❌ Answer Generator 실행 실패: {str(generator_error)}")
                    print_with_flush(f"   - 오류 타입: {type(generator_error).__name__}")
                    print_with_flush(f"   - 실행 시간: {time.time() - step_start_time:.2f}초")
                    test_success = False
                    error_message = f"Answer Generator 오류: {str(generator_error)}"
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            
            # 전체 플로우 요약
            print_with_flush(f"\n📊 전체 플로우 요약:")
            print_with_flush(f"   - 입력: {test_case['input']}")
            print_with_flush(f"   - 총 실행 시간: {total_duration:.2f}초")
            print_with_flush(f"   - 최종 노드: {current_state.get('next_node', 'N/A')}")
            
            final_answer = current_state.get('final_answer', '')
            if final_answer:
                print_with_flush(f"   - 최종 답변 생성: ✅ 성공")
                successful_tests += 1
            else:
                print_with_flush(f"   - 최종 답변 생성: ❌ 실패")
                failed_tests += 1
            
            if not test_success:
                print_with_flush(f"   - 오류 정보: {error_message}")
            
        except Exception as e:
            print_with_flush(f"❌ 테스트 실행 중 예상치 못한 오류 발생: {str(e)}")
            print_with_flush(f"   - 오류 타입: {type(e).__name__}")
            import traceback
            print_with_flush("   - 상세 오류:")
            traceback.print_exc()
            failed_tests += 1
        
        print_with_flush(f"\n{'='*60}")
    
    # 전체 테스트 결과 요약
    print_with_flush(f"\n🎯 전체 테스트 결과 요약:")
    print_with_flush(f"   - 총 테스트: {len(test_cases)}개")
    print_with_flush(f"   - 성공: {successful_tests}개")
    print_with_flush(f"   - 실패: {failed_tests}개")
    print_with_flush(f"   - 성공률: {(successful_tests/len(test_cases)*100):.1f}%")

def test_interactive_comprehensive_flow():
    """사용자 입력을 받아서 종합적인 플로우를 대화형으로 테스트합니다."""
    
    print_with_flush("\n" + "=" * 80)
    print_with_flush("🎯 대화형 종합 Flow 테스트")
    print_with_flush("=" * 80)
    print_with_flush("질문을 입력하면 RAG → 웹서치 → 캘린더 → 답변생성의 전체 플로우를 테스트합니다.")
    print_with_flush("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    
    while True:
        # 사용자 입력 받기
        user_input = input("\n📝 질문을 입력하세요: ").strip()
        
        # 종료 조건 확인
        if user_input.lower() in ['quit', 'exit', 'q']:
            print_with_flush("\n테스트를 종료합니다.")
            break
        
        if not user_input:
            print_with_flush("입력이 비어있습니다. 다시 입력해주세요.")
            continue
        
        print_with_flush(f"\n🔄 '{user_input}' 처리 중...")
        
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
            print_with_flush("\n1️⃣ Task Router 실행...")
            step_start_time = time.time()
            current_state = task_router(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            next_node = current_state.get('next_node')
            print_with_flush(f"   → 다음 노드: {next_node}")
            print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
            
            if next_node != 'query_refiner':
                print_with_flush(f"   ⚠️ query_refiner로 라우팅되지 않음. 실제: {next_node}")
            
            # Step 2: query_refiner
            print_with_flush("\n2️⃣ Query Refiner 실행...")
            step_start_time = time.time()
            current_state = query_refiner(current_state.copy())
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            next_node = current_state.get('next_node')
            print_with_flush(f"   → 다음 노드: {next_node}")
            print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
            
            if next_node != 'rag_retriever':
                print_with_flush(f"   ⚠️ rag_retriever로 라우팅되지 않음. 실제: {next_node}")
            
            # Step 3: rag_retriever
            print_with_flush("\n3️⃣ RAG Retriever 실행...")
            step_start_time = time.time()
            try:
                current_state = rag_retriever(current_state.copy())
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                
                rag_content = current_state.get('rag_result', '')
                print_with_flush(f"   → RAG 결과: {len(rag_content)}자")
                print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                if rag_content:
                    print_with_flush(f"   → RAG 내용:")
                    print_with_flush(f"     {rag_content}")
                
                next_node = current_state.get('next_node')
                print_with_flush(f"   → 다음 노드: {next_node}")
                
                if next_node != 'rag_quality_critic':
                    print_with_flush(f"   ⚠️ rag_quality_critic로 라우팅되지 않음. 실제: {next_node}")
                    
            except Exception as rag_error:
                print_with_flush(f"   ❌ RAG Retriever 실패: {str(rag_error)}")
                print_with_flush(f"   → 오류 타입: {type(rag_error).__name__}")
                print_with_flush(f"   → 실행 시간: {time.time() - step_start_time:.2f}초")
                # RAG 실패 시 웹서치로 전환
                current_state['next_node'] = 'websearch_agent'
                next_node = 'websearch_agent'
            
            # Step 4: rag_quality_critic
            if next_node == 'rag_quality_critic':
                print_with_flush("\n4️⃣ RAG Quality Critic 실행...")
                step_start_time = time.time()
                try:
                    current_state = rag_quality_critic(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    next_node = current_state.get('next_node')
                    print_with_flush(f"   → 다음 노드: {next_node}")
                    print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                    
                    # 품질 평가 결과 확인
                    router_messages = current_state.get('router_messages', [])
                    if router_messages:
                        print_with_flush(f"   → 품질 평가: {router_messages[-1].get('decision', 'N/A')}")
                        print_with_flush(f"   → 라우터 메시지:")
                        for msg in router_messages:
                            print_with_flush(f"     {msg}")
                            
                except Exception as critic_error:
                    print_with_flush(f"   ❌ RAG Quality Critic 실패: {str(critic_error)}")
                    print_with_flush(f"   → 오류 타입: {type(critic_error).__name__}")
                    print_with_flush(f"   → 실행 시간: {time.time() - step_start_time:.2f}초")
                    next_node = 'websearch_agent'
            
            # Step 5: rag_quality_critic 이후 분기 처리
            if next_node == 'rag_retriever':
                print_with_flush("\n🔄 RAG 재검색 필요 - RAG Retriever 재실행")
                step_start_time = time.time()
                try:
                    current_state = rag_retriever(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    rag_content = current_state.get('rag_result', '')
                    print_with_flush(f"   → RAG 재검색 결과: {len(rag_content)}자")
                    print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                    if rag_content:
                        print_with_flush(f"   → RAG 재검색 내용:")
                        print_with_flush(f"     {rag_content}")
                    
                    # 재검색 후 다시 critic 실행
                    print_with_flush("\n🎯 RAG Quality Critic 재실행")
                    step_start_time = time.time()
                    current_state = rag_quality_critic(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    next_node = current_state.get('next_node')
                    print_with_flush(f"   → 다음 노드: {next_node}")
                    print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                    
                except Exception as retry_error:
                    print_with_flush(f"   ❌ RAG 재검색 실패: {str(retry_error)}")
                    next_node = 'websearch_agent'
            
            elif next_node == 'websearch_agent':
                print_with_flush("\n🌐 웹서치 필요 - Websearch Agent 실행")
                step_start_time = time.time()
                try:
                    current_state = websearch_agent(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    search_content = current_state.get('search_result', '')
                    print_with_flush(f"   → 웹서치 결과: {len(search_content)}자")
                    print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                    if search_content:
                        print_with_flush(f"   → 웹서치 내용:")
                        print_with_flush(f"     {search_content}")
                    
                    next_node = current_state.get('next_node')
                    print_with_flush(f"   → 다음 노드: {next_node}")
                    
                    if next_node == 'websearch_critic':
                        print_with_flush("\n🎯 Websearch Critic 실행")
                        step_start_time = time.time()
                        current_state = websearch_critic(current_state.copy())
                        step_end_time = time.time()
                        step_duration = step_end_time - step_start_time
                        next_node = current_state.get('next_node')
                        print_with_flush(f"   → 다음 노드: {next_node}")
                        print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                        
                except Exception as websearch_error:
                    print_with_flush(f"   ❌ Websearch Agent 실패: {str(websearch_error)}")
                    print_with_flush(f"   → 오류 타입: {type(websearch_error).__name__}")
                    print_with_flush(f"   → 실행 시간: {time.time() - step_start_time:.2f}초")
                    next_node = 'answer_planner'
            
            # Step 6: calendar_needed 또는 answer_planner로 분기
            if next_node == 'calendar_needed':
                print_with_flush("\n📅 캘린더 필요 - Calendar Needed 실행")
                step_start_time = time.time()
                try:
                    current_state = calendar_needed(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    next_node = current_state.get('next_node')
                    print_with_flush(f"   → 다음 노드: {next_node}")
                    print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                    
                    if next_node == 'calendar_agent':
                        print_with_flush("\n📅 Calendar Agent 실행")
                        step_start_time = time.time()
                        current_state = calendar_agent(current_state.copy())
                        step_end_time = time.time()
                        step_duration = step_end_time - step_start_time
                        
                        payload = current_state.get('event_payload', {})
                        print_with_flush(f"   → 일정 정보: {payload.get('title', 'N/A') if payload else 'N/A'}")
                        print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                        if payload:
                            print_with_flush(f"   → 전체 페이로드: {payload}")
                        
                        next_node = current_state.get('next_node')
                        
                except Exception as calendar_error:
                    print_with_flush(f"   ❌ Calendar 관련 실패: {str(calendar_error)}")
                    print_with_flush(f"   → 오류 타입: {type(calendar_error).__name__}")
                    print_with_flush(f"   → 실행 시간: {time.time() - step_start_time:.2f}초")
                    next_node = 'answer_planner'
            
            # Step 7: answer_planner 실행
            if next_node == 'answer_planner':
                print_with_flush("\n📝 Answer Planner 실행")
                step_start_time = time.time()
                try:
                    current_state = answer_planner(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    next_node = current_state.get('next_node')
                    print_with_flush(f"   → 다음 노드: {next_node}")
                    print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                    
                except Exception as planner_error:
                    print_with_flush(f"   ❌ Answer Planner 실패: {str(planner_error)}")
                    print_with_flush(f"   → 오류 타입: {type(planner_error).__name__}")
                    print_with_flush(f"   → 실행 시간: {time.time() - step_start_time:.2f}초")
                    next_node = 'answer_generator'
            
            # Step 8: answer_generator 실행
            if next_node == 'answer_generator':
                print_with_flush("\n💬 Answer Generator 실행")
                step_start_time = time.time()
                try:
                    current_state = answer_generator(current_state.copy())
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    
                    final_answer = current_state.get('final_answer', '')
                    print_with_flush(f"   → 최종 답변: {len(final_answer)}자")
                    print_with_flush(f"   → 실행 시간: {step_duration:.2f}초")
                    if final_answer:
                        print_with_flush(f"   → 답변 미리보기: {final_answer[:200]}...")
                        print_with_flush(f"   → 전체 답변:")
                        print_with_flush(f"     {final_answer}")
                    
                except Exception as generator_error:
                    print_with_flush(f"   ❌ Answer Generator 실패: {str(generator_error)}")
                    print_with_flush(f"   → 오류 타입: {type(generator_error).__name__}")
                    print_with_flush(f"   → 실행 시간: {time.time() - step_start_time:.2f}초")
            
            # 전체 실행 시간 계산
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            print_with_flush(f"\n⏱️  총 실행 시간: {total_duration:.2f}초")
            
            # 최종 결과 확인
            final_answer = current_state.get('final_answer', '')
            if final_answer:
                print_with_flush("\n✅ 전체 플로우 성공! 최종 답변이 생성되었습니다.")
            else:
                print_with_flush(f"\n📋 플로우 완료. 최종 노드: {current_state.get('next_node', 'N/A')}")
            
        except Exception as e:
            print_with_flush(f"\n❌ 오류 발생: {str(e)}")
            print_with_flush(f"   → 오류 타입: {type(e).__name__}")
            import traceback
            print_with_flush("   → 상세 오류:")
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