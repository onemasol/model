#!/usr/bin/env python3
"""
종합 랭그래프 플로우 테스트 파일
모든 가능한 경로와 에이전트를 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import Annotated, List, Optional, TypedDict
from dotenv import load_dotenv
from models.agent_state import AgentState

# 에이전트들
from agents.rag_retriever import rag_retriever
from agents.calendar_agent import calendar_agent
from agents.websearch_agent import websearch_agent
from agents.answer_generator import answer_generator
from agents.answer_planner import answer_planner

# 라우터들
from routers.calendar_needed import calendar_needed
from routers.rag_quality_critic import rag_quality_critic
from routers.websearch_critic import websearch_critic
from routers.task_router import task_router
from routers.query_refiner import query_refiner

load_dotenv()

def create_graph() -> StateGraph:
    """워크플로우 그래프 생성"""
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("rag_retriever", rag_retriever)
    workflow.add_node("calendar_agent", calendar_agent)
    workflow.add_node("websearch_agent", websearch_agent)
    workflow.add_node("answer_generator", answer_generator)
    workflow.add_node("answer_planner", answer_planner)
    workflow.add_node("query_refiner", query_refiner)
    workflow.add_node("calendar_needed", calendar_needed)
    workflow.add_node("rag_quality_critic", rag_quality_critic)
    workflow.add_node("websearch_critic", websearch_critic)
    workflow.add_node("task_router", task_router)
    
    # 엣지 추가
    workflow.add_edge("task_router", "calendar_agent")
    workflow.add_edge("task_router", "answer_planner")
    workflow.add_edge("task_router", "query_refiner")
    workflow.add_edge("query_refiner", "rag_retriever")
    workflow.add_edge("rag_retriever", "rag_quality_critic")
    workflow.add_edge("rag_quality_critic", "rag_retriever")
    workflow.add_edge("rag_quality_critic", "websearch_agent")
    workflow.add_edge("websearch_agent", "websearch_critic")
    workflow.add_edge("websearch_critic", "websearch_agent")
    workflow.add_edge("rag_quality_critic", "calendar_needed")
    workflow.add_edge("websearch_critic", "calendar_needed")
    workflow.add_edge("calendar_needed", "calendar_agent")
    workflow.add_edge("calendar_needed", "answer_planner")
    workflow.add_edge("answer_planner", "answer_generator")
    workflow.add_edge("answer_generator", END)
    
    workflow.set_entry_point("task_router")
    return workflow

def create_test_state(query: str) -> dict:
    """테스트용 상태 생성"""
    return {
        "type": "question",
        "initial_input": query,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
        "final_answer": None,
        "next_node": None,
        "agent_messages": [],
        "router_messages": [],
        # 추가 필드들 (기본값으로 설정)
        "schedule_type": None,
        "final_output": None,
        "title": None,
        "start_at": None,
        "end_at": None,
        "due_at": None,
        "timezone": None,
        "event_type": None,
        "calendar_classification": None,
        "calendar_operation": None,
        "calendar_type": None,
        "event_payload": None,
        "operation_type": None,
        "query_info": None
    }

def print_result(result_state: dict, test_name: str):
    """결과 출력"""
    print(f"\n{'='*60}")
    print(f"📋 테스트: {test_name}")
    print(f"{'='*60}")
    
    print(f"\n❓ 입력 질문: {result_state['initial_input']}")
    print(f"\n✅ 최종 답변:")
    print(f"{result_state.get('final_answer', '답변 없음')}")
    
    print(f"\n🔄 실행된 노드들:")
    router_msgs = result_state.get("router_messages", [])
    for msg in router_msgs:
        if isinstance(msg, dict):
            print(f"  - {msg.get('router', 'unknown')}: {msg.get('decision', 'N/A')}")
        else:
            print(f"  - {msg}")
    
    print(f"\n🤖 에이전트 메시지:")
    agent_msgs = result_state.get("agent_messages", [])
    for msg in agent_msgs:
        if isinstance(msg, dict):
            print(f"  - {msg.get('agent', 'unknown')}: {msg.get('prompt_type', 'N/A')}")
        else:
            print(f"  - {msg}")

def run_comprehensive_tests():
    """모든 플로우 테스트 실행"""
    print("🚀 종합 랭그래프 플로우 테스트 시작")
    
    # 그래프 생성
    graph = create_graph()
    workflow_app = graph.compile()
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "일정 생성 (이벤트)",
            "query": "내일 오후 2시에 팀 미팅 추가해줘"
        },
        {
            "name": "일정 생성 (할일)",
            "query": "이번 주까지 보고서 작성해야 해"
        },
        {
            "name": "일정 조회",
            "query": "이번 주 일정 보여줘"
        },
        {
            "name": "RAG 기반 질문",
            "query": "부가세 신고 절차와 필요한 서류가 뭐야?"
        },
        {
            "name": "웹 검색 필요 질문",
            "query": "2024년 12월 종합소득세 신고 일정은 언제야?"
        },
        {
            "name": "일반 대화",
            "query": "안녕하세요, 오늘 날씨 어때요?"
        },
        {
            "name": "복합 질문 (정보 + 일정)",
            "query": "부가세 신고 방법 알려주고, 내일 오후 3시에 신고 일정 잡아줘"
        },
        {
            "name": "최신 정보 필요",
            "query": "현재 코로나19 방역 정책은 어떻게 되나요?"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔄 테스트 {i}/{len(test_cases)} 실행 중...")
        
        try:
            # 테스트 상태 생성
            state = create_test_state(test_case["query"])
            
            # 그래프 실행
            result_state = workflow_app.invoke(state)
            
            # 결과 출력
            print_result(result_state, test_case["name"])
            
            # 결과 저장
            results.append({
                "test_name": test_case["name"],
                "query": test_case["query"],
                "final_answer": result_state.get("final_answer"),
                "router_messages": result_state.get("router_messages", []),
                "agent_messages": result_state.get("agent_messages", [])
            })
            
        except Exception as e:
            print(f"❌ 테스트 실패: {test_case['name']}")
            print(f"   오류: {str(e)}")
            results.append({
                "test_name": test_case["name"],
                "query": test_case["query"],
                "error": str(e)
            })
    
    # 종합 결과 요약
    print(f"\n{'='*60}")
    print("📊 종합 테스트 결과 요약")
    print(f"{'='*60}")
    
    successful_tests = [r for r in results if "error" not in r]
    failed_tests = [r for r in results if "error" in r]
    
    print(f"✅ 성공: {len(successful_tests)}/{len(test_cases)}")
    print(f"❌ 실패: {len(failed_tests)}/{len(test_cases)}")
    
    if failed_tests:
        print(f"\n❌ 실패한 테스트:")
        for test in failed_tests:
            print(f"  - {test['test_name']}: {test['error']}")
    
    return results

def interactive_test():
    """대화형 테스트 모드"""
    print("🎯 대화형 테스트 모드")
    print("질문을 입력하세요 (종료: 'quit' 또는 'exit')")
    
    graph = create_graph()
    workflow_app = graph.compile()
    
    while True:
        try:
            query = input("\n❓ 질문: ").strip()
            
            if query.lower() in ['quit', 'exit', '종료']:
                print("👋 테스트 종료")
                break
            
            if not query:
                continue
            
            # 테스트 실행
            state = create_test_state(query)
            result_state = workflow_app.invoke(state)
            
            # 결과 출력
            print_result(result_state, "사용자 입력")
            
        except KeyboardInterrupt:
            print("\n👋 테스트 종료")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="랭그래프 플로우 종합 테스트")
    parser.add_argument("--mode", choices=["comprehensive", "interactive"], 
                       default="comprehensive", help="테스트 모드 선택")
    
    args = parser.parse_args()
    
    if args.mode == "comprehensive":
        run_comprehensive_tests()
    else:
        interactive_test() 