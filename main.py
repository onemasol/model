from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Optional
import os
from dotenv import load_dotenv
from utils.text_formatter import format_question
from utils.graph_visualizer import visualize_graph

from langgraph.graph import StateGraph, END


from agents.rag_retriever import rag_retriever
from agents.calendar_agent import calendar_agent
from agents.websearch_agent import websearch_agent
from agents.answer_generator import answer_generator

from routers.rag_feasibility_router import rag_feasibility_router
from routers.calendar_needed import calendar_needed
from routers.rag_quality_critic import rag_quality_critic
from routers.websearch_critic import websearch_critic
from routers.task_router import task_router

# Load environment variables from .env file
load_dotenv()

model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.7,
)

class AgentState(TypedDict):
    type: Annotated[str, "input_type"]  # "schedule" or "question"
    messages: Annotated[List[str], "conversation_history"]
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
    workflow.add_node("websearch_agent", websearch_agent)
    workflow.add_node("answer_generator", answer_generator)
    ## Routers
    workflow.add_node("rag_feasibility_router", rag_feasibility_router)
    workflow.add_node("calendar_needed", calendar_needed)  
    workflow.add_node("rag_quality_critic", rag_quality_critic)
    workflow.add_node("websearch_critic", websearch_critic)
    workflow.add_node("task_router", task_router)
    
    
    # Add edges
    # 일정 흐름
    workflow.add_edge("task_router", "calendar_agent")  # 일정 등록 직접

    # RAG 흐름
    workflow.add_edge("task_router", "rag_feasibility_router") # RAG 또는 웹서치가 필요할 때, 적재된 VDB에서 RAG가 가능한지 쿼리 기반 유사도 평가
    workflow.add_edge("rag_feasibility_router", "rag_retriever") # RAG 가능한 경우 RAG 리트리버로 이동
    workflow.add_edge("rag_retriever", "rag_quality_critic") # RAG 리트리버가 작업을 완료한 후 품질 비평으로 이동
    workflow.add_edge("rag_quality_critic", "rag_retriever") # 불만족스러운 경우 역전파(qa 후 없애도됨)
    workflow.add_edge("rag_quality_critic", "websearch_agent") # 웹서치가 필요한 경우 웹서치

    # 웹서치 흐름
    workflow.add_edge("rag_feasibility_router", "websearch_agent") # RAG가 불가능한 경우 웹서치 에이전트로 이동
    workflow.add_edge("websearch_agent", "websearch_critic")  # 웹서치 후 품질 비평
    workflow.add_edge("websearch_critic", "websearch_agent")  # 웹서치 후 재검색이 필요할 경우 역전파

    workflow.add_edge("rag_quality_critic", "calendar_needed") # taskrouter가 캘린더가 필요한 경우라고 규정한 경우, rag를 돌고 나온 후 캘린더 에이전트에게 어떤 행동을 시킬지 지정
    

    workflow.add_edge("websearch_critic", "calendar_needed") # taskrouter가 캘린더가 필요한 경우라고 규정한 경우, 웹서치를 돌고 나온 후 캘린더 에이전트에게 어떤 행동을 시킬지 지정

    workflow.add_edge("calendar_needed", "calendar_agent")  # 캘린더 CRUD 및 조회가 필요한 경우 캘린더 에이전트로 이동 및 부가 정보 전달
    workflow.add_edge("calendar_needed", "answer_generator") # # 캘린더가 필요하지 않은 경우 답변 생성기로 이동
    workflow.add_edge("calendar_agent", "answer_generator") # # 캘린더 에이전트가 작업을 완료한 후 답변 생성기로 이동

    # 종료 조건
    workflow.add_edge("answer_generator", END)

    #시작 조건
    workflow.set_entry_point("task_router") # 일정 등록만이 필요한 경우와, 도메인 지식을 필요로 하는 쿼리인 경우로 분리하여 간단한 캘린더 조회 및 CRUD를 하도록 하거나 RAG 및 웹서치를 돌고 나오거나 할 수 있도록 태스크 지정
    
    return workflow

if __name__ == "__main__":
    # Create and visualize the graph
    graph = create_graph()
    visualize_graph(graph, "oms_agent_graph")






# def slave_one(state: AgentState):
#     # Get the latest message from the conversation history
#     latest_message = state["messages"][-1]
#     print("\n=== [slave_one] 분석 시작 ===")
#     print(f"사용자 질문: {latest_message}")
    
#     # Analyze the message to determine if RAG or CAL agent is needed
#     analysis_prompt = f"""
#     다음 질문이 문서 검색(RAG)이나 일정 관리(CAL)와 관련된 것인지 분석해주세요.
    
#     RAG는 다음 경우에만 사용됩니다:
#     - 문서나 파일의 내용을 검색하거나 요약하는 경우
#     - 기존 문서에서 특정 정보를 찾는 경우
    
#     CAL은 다음 경우에만 사용됩니다:
#     - 회의나 일정을 잡는 경우
#     - 일정을 확인하거나 수정하는 경우
    
#     질문: {latest_message}
    
#     다음 중 하나로만 응답해주세요 (설명 없이):
#     RAG
#     CAL
#     """
    
#     # print("\n분석 프롬프트:")
#     # print(analysis_prompt)
    
#     analysis_response = model.invoke(analysis_prompt)
#     decision = analysis_response.content.strip().upper()
    
#     # Clean up the decision (remove any additional text)
#     if "RAG" in decision:
#         decision = "RAG"
#     elif "CAL" in decision:
#         decision = "CAL"
#     else:
#         state["final_answer"] = "[slave_one] 죄송합니다. 질문을 이해하지 못했습니다. 문서 검색이나 일정 관리와 관련된 질문을 해주세요."
#         state["next_node"] = END
#         return state
    
#     # Update state based on the decision
#     if decision == "RAG":
#         state["next_node"] = "rag_agent"
#     elif decision == "CAL":
#         state["next_node"] = "cal_agent"
    
#     print(f"\n[slave_one] 결정: {decision}")
#     print("=== [slave_one] 분석 완료 ===")
#     return state

# def slave_two(state: AgentState):
#     # Get the latest message and context
#     latest_message = format_question(state["messages"][-1])
#     print("\n=== [slave_two] 분석 시작 ===")
#     print(f"사용자 질문: {latest_message}")
    
#     # Check if we have any previous results
#     has_rag_result = state["rag_result"] is not None
#     has_search_result = state["search_result"] is not None
#     has_crud_result = state["crud_result"] is not None
    
#     # Analyze if we have enough information to answer
#     analysis_prompt = f"""
#     당신은 캘린더 관리 비서입니다. 사용자의 일정을 등록하고 조회하는 것이 주 역할입니다.
    
#     주요 기능:
#     1. 일정 등록 (미팅, 할일, 약속 등)
#     2. 일정 조회 (특정 날짜/기간의 일정 확인)
#     3. 일정 수정 및 삭제
    
#     다음 질문에 답하기 위해 충분한 정보가 있는지 분석해주세요.
    
#     질문: {latest_message}
    
#     현재 가용 정보:
#     - RAG 결과: {'있음' if has_rag_result else '없음'}
#     - 검색 결과: {'있음' if has_search_result else '없음'}
#     - CRUD 결과: {'있음' if has_crud_result else '없음'}
    
#     다음 중 하나로 응답해주세요:
#     - RAG: 문서 검색이 더 필요함 (예: 회의록, 일정 정책 등)
#     - CAL: 일정 정보가 더 필요함 (예: 다른 날짜의 일정 등)
#     - WEB: 웹 검색이 필요함 (예: 공휴일 정보 등)
#     - SUFFICIENT: 답변하기에 충분한 정보가 있음
#     """
    
#     print("\n분석 프롬프트:")
#     print(analysis_prompt)
    
#     analysis_response = model.invoke(analysis_prompt)
#     decision = analysis_response.content.strip().upper()
    
#     # Update state based on the decision
#     if decision == "SUFFICIENT":
#         # Generate final answer using available information
#         answer_prompt = f"""
#         다음 정보를 바탕으로 질문에 답변해주세요.
        
#         질문: {latest_message}
        
#         RAG 결과: {state['rag_result'] if has_rag_result else '없음'}
#         검색 결과: {state['search_result'] if has_search_result else '없음'}
#         CRUD 결과: {state['crud_result'] if has_crud_result else '없음'}
#         """
        
#         response = model.invoke(answer_prompt)
#         state["final_answer"] = f"[slave_two] {response.content}"
#         state["next_node"] = END
#     else:
#         # Route to appropriate node
#         state["next_node"] = decision.lower() + "_agent"
    
#     print(f"\n[slave_two] 결정: {decision}")
#     print("=== [slave_two] 분석 완료 ===")
#     return state