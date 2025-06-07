from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import Annotated, List, Optional
import os
from dotenv import load_dotenv
from utils.text_formatter import format_question
from utils.graph_visualizer import visualize_graph
from models.agent_state import AgentState

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

