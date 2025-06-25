from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import Annotated, List, Optional, TypedDict
import os
from dotenv import load_dotenv
from utils.text_formatter import format_question
from utils.graph_visualizer import visualize_graph
from models.agent_state import AgentState

from langgraph.graph import StateGraph, END
from shared import AgentState, model

from agents.rag_retriever import rag_retriever
from agents.calendar_agent import calendar_agent
from agents.calselector import calselector
from agents.websearch_agent import websearch_agent
from agents.answer_generator import answer_generator
from agents.answer_planner import answer_planner

#from routers.rag_feasibility_router import rag_feasibility_router
from routers.calendar_needed import calendar_needed
from routers.rag_quality_critic import rag_quality_critic
from routers.websearch_critic import websearch_critic
from routers.task_router import task_router
from routers.query_refiner import query_refiner



# Load environment variables from .env file
load_dotenv()

model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.7,
)


class AgentState(TypedDict):
    type: Annotated[str, "input_type"]  # "schedule" or "question"
    initial_input: Annotated[str, "user's_initial_input"]
    rag_result: Annotated[Optional[str], "rag_output"]
    search_result: Annotated[Optional[str], "search_output"]
    crud_result: Annotated[Optional[str], "crud_output"]
    final_answer: Annotated[Optional[str], "final_output"]
    next_node: Annotated[Optional[str], "next_node"]
    agent_messages: Annotated[List[str], "agent_conversation_history"]  # agent 간 대화 기록
    router_messages: Annotated[List[str], "router_conversation_history"]  # router 간 대화 기록


def create_graph() -> StateGraph:
    """Create and return the workflow graph."""
    # Create a new graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    ## Agents
    workflow.add_node("rag_retriever",rag_retriever)
    workflow.add_node("calendar_agent", calendar_agent)
    workflow.add_node("calselector", calselector)
    workflow.add_node("websearch_agent", websearch_agent)
    workflow.add_node("answer_generator", answer_generator)
    workflow.add_node("answer_planner", answer_planner) 

    ## Routers
    #workflow.add_node("rag_feasibility_router", rag_feasibility_router)
    workflow.add_node("query_refiner", query_refiner)
    workflow.add_node("calendar_needed", calendar_needed)  
    workflow.add_node("rag_quality_critic", rag_quality_critic)
    workflow.add_node("websearch_critic", websearch_critic)
    workflow.add_node("task_router", task_router)
    
    
    # Add edges
    # 일정 흐름
    workflow.add_edge("task_router", "calendar_agent")  # 일정 등록 직접
    workflow.add_edge("calendar_agent", "calselector")  # calendar_agent에서 calselector로
    workflow.add_edge("calselector", "answer_generator")  # calselector에서 answer_generator로
    #무관 더미
    workflow.add_edge("task_router", "answer_planner")
    # RAG 흐름
    workflow.add_edge("task_router", "query_refiner") # RAG 가능한 경우 RAG 리트리버로 이동
    workflow.add_edge("query_refiner", "rag_retriever") # RAG 리트리버로 이동
    workflow.add_edge("rag_retriever", "rag_quality_critic") # RAG 리트리버가 작업을 완료한 후 품질 비평으로 이동
    workflow.add_edge("rag_quality_critic", "rag_retriever") # 불만족스러운 경우 역전파(qa 후 없애도됨)
    workflow.add_edge("rag_quality_critic", "websearch_agent") # 웹서치가 필요한 경우 웹서치

    # 웹서치 흐름
    workflow.add_edge("websearch_agent", "websearch_critic")  # 웹서치 후 품질 비평
    workflow.add_edge("websearch_critic", "websearch_agent")  # 웹서치 후 재검색이 필요할 경우 역전파

    workflow.add_edge("rag_quality_critic", "calendar_needed") # taskrouter가 캘린더가 필요한 경우라고 규정한 경우, rag를 돌고 나온 후 캘린더 에이전트에게 어떤 행동을 시킬지 지정
    workflow.add_edge("websearch_critic", "calendar_needed") # taskrouter가 캘린더가 필요한 경우라고 규정한 경우, 웹서치를 돌고 나온 후 캘린더 에이전트에게 어떤 행동을 시킬지 지정

    workflow.add_edge("calendar_needed", "calendar_agent")  # 캘린더 CRUD 및 조회가 필요한 경우 캘린더 에이전트로 이동 및 부가 정보 전달
    workflow.add_edge("calendar_needed", "answer_planner") # # 캘린더가 필요하지 않은 경우 답변 생성기로 이동
    workflow.add_edge("answer_planner", "answer_generator") # # 캘린더 에이전트가 작업을 완료한 후 답변 생성기로 이동

    # 종료 조건
    workflow.add_edge("answer_generator", END)
    
    #시작 조건
    workflow.set_entry_point("task_router") # 일정 등록만이 필요한 경우와, 도메인 지식을 필요로 하는 쿼리인 경우로 분리하여 간단한 캘린더 조회 및 CRUD를 하도록 하거나 RAG 및 웹서치를 돌고 나오거나 할 수 있도록 태스크 지정
    
    return workflow

if __name__ == "__main__":
    # 그래프 생성
    graph = create_graph()
    #visualize_graph(graph, "oms_agent_graph")  # 시각화 파일 저장
    workflow_app = graph.compile()
    # 1. 테스트 입력 준비 (예시)
    test_query = "2024년 7월 부가세 신고 일정과 준비 서류가 궁금해"  # 원하는 질문으로!
    state = {
        "type": "question",
        "initial_input": test_query,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
        "final_answer": None,
        "next_node": None,
        "agent_messages": [],
        "router_messages": []
    }

    # 2. 그래프 실행: LangGraph의 run/invoke 메서드로 상태 전달
    # 일반적으로 .invoke(state) 형태(최신 버전)
        # 1) 그래프 실행
    result_state = workflow_app.invoke(state)
    
    # 3. 결과 출력
    print("\n=== 최종 출력 ===")
    print("최종 답변:", result_state.get("final_answer"))
    print("\n=== 상세 로그 ===")
    for msg in result_state.get("agent_messages", []):
        print(msg)
    print("\n--- Router 로그 ---")
    for msg in result_state.get("router_messages", []):
        print(msg)



