from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import Annotated, List, Optional
import os
from dotenv import load_dotenv
from utils.text_formatter import format_question
from utils.graph_visualizer import visualize_graph
from agent_state import AgentState

# Load environment variables from .env file
load_dotenv()

model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.7,
)

def slave_one(state: AgentState):
    # Get the latest message from the conversation history
    latest_message = state["messages"][-1]
    print("\n=== [slave_one] 분석 시작 ===")
    print(f"사용자 질문: {latest_message}")
    
    # Analyze the message to determine if RAG or CAL agent is needed
    analysis_prompt = f"""
    다음 질문이 문서 검색(RAG)이나 일정 관리(CAL)와 관련된 것인지 분석해주세요.
    
    RAG는 다음 경우에만 사용됩니다:
    - 문서나 파일의 내용을 검색하거나 요약하는 경우
    - 기존 문서에서 특정 정보를 찾는 경우
    
    CAL은 다음 경우에만 사용됩니다:
    - 회의나 일정을 잡는 경우
    - 일정을 확인하거나 수정하는 경우
    
    질문: {latest_message}
    
    다음 중 하나로만 응답해주세요 (설명 없이):
    RAG
    CAL
    """
    
    # print("\n분석 프롬프트:")
    # print(analysis_prompt)
    
    analysis_response = model.invoke(analysis_prompt)
    decision = analysis_response.content.strip().upper()
    
    # Clean up the decision (remove any additional text)
    if "RAG" in decision:
        decision = "RAG"
    elif "CAL" in decision:
        decision = "CAL"
    else:
        state["final_answer"] = "[slave_one] 죄송합니다. 질문을 이해하지 못했습니다. 문서 검색이나 일정 관리와 관련된 질문을 해주세요."
        state["next_node"] = END
        return state
    
    # Update state based on the decision
    if decision == "RAG":
        state["next_node"] = "rag_agent"
    elif decision == "CAL":
        state["next_node"] = "cal_agent"
    
    print(f"\n[slave_one] 결정: {decision}")
    print("=== [slave_one] 분석 완료 ===")
    return state

def slave_two(state: AgentState):
    # Get the latest message and context
    latest_message = format_question(state["messages"][-1])
    print("\n=== [slave_two] 분석 시작 ===")
    print(f"사용자 질문: {latest_message}")
    
    # Check if we have any previous results
    has_rag_result = state["rag_result"] is not None
    has_search_result = state["search_result"] is not None
    has_crud_result = state["crud_result"] is not None
    
    # Analyze if we have enough information to answer
    analysis_prompt = f"""
    당신은 캘린더 관리 비서입니다. 사용자의 일정을 등록하고 조회하는 것이 주 역할입니다.
    
    주요 기능:
    1. 일정 등록 (미팅, 할일, 약속 등)
    2. 일정 조회 (특정 날짜/기간의 일정 확인)
    3. 일정 수정 및 삭제
    
    다음 질문에 답하기 위해 충분한 정보가 있는지 분석해주세요.
    
    질문: {latest_message}
    
    현재 가용 정보:
    - RAG 결과: {'있음' if has_rag_result else '없음'}
    - 검색 결과: {'있음' if has_search_result else '없음'}
    - CRUD 결과: {'있음' if has_crud_result else '없음'}
    
    다음 중 하나로 응답해주세요:
    - RAG: 문서 검색이 더 필요함 (예: 회의록, 일정 정책 등)
    - CAL: 일정 정보가 더 필요함 (예: 다른 날짜의 일정 등)
    - WEB: 웹 검색이 필요함 (예: 공휴일 정보 등)
    - SUFFICIENT: 답변하기에 충분한 정보가 있음
    """
    
    print("\n분석 프롬프트:")
    print(analysis_prompt)
    
    analysis_response = model.invoke(analysis_prompt)
    decision = analysis_response.content.strip().upper()
    
    # Update state based on the decision
    if decision == "SUFFICIENT":
        # Generate final answer using available information
        answer_prompt = f"""
        다음 정보를 바탕으로 질문에 답변해주세요.
        
        질문: {latest_message}
        
        RAG 결과: {state['rag_result'] if has_rag_result else '없음'}
        검색 결과: {state['search_result'] if has_search_result else '없음'}
        CRUD 결과: {state['crud_result'] if has_crud_result else '없음'}
        """
        
        response = model.invoke(answer_prompt)
        state["final_answer"] = f"[slave_two] {response.content}"
        state["next_node"] = END
    else:
        # Route to appropriate node
        state["next_node"] = decision.lower() + "_agent"
    
    print(f"\n[slave_two] 결정: {decision}")
    print("=== [slave_two] 분석 완료 ===")
    return state

def create_graph() -> StateGraph:
    """Create and return the workflow graph."""
    # Create a new graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("slave_one", slave_one)
    workflow.add_node("slave_two", slave_two)
    workflow.add_node("rag_agent", lambda x: x)  # Placeholder
    workflow.add_node("cal_agent", lambda x: x)  # Placeholder
    workflow.add_node("web_agent", lambda x: x)  # Placeholder
    
    # Add edges
    workflow.add_edge("slave_one", "rag_agent")
    workflow.add_edge("slave_one", "cal_agent")
    workflow.add_edge("slave_two", "rag_agent")
    workflow.add_edge("slave_two", "cal_agent")
    workflow.add_edge("slave_two", "web_agent")
    workflow.add_edge("slave_two", END)
    
    # Set entry point
    workflow.set_entry_point("slave_one")
    
    return workflow

if __name__ == "__main__":
    # Create and visualize the graph
    graph = create_graph()
    visualize_graph(graph, "oms_agent_graph")
