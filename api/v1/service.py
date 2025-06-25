from .dto import InputRequest, AgentResponse
from routers.task_router import task_router
from agents.calendar_agent import calendar_agent
from agents.answer_planner import answer_planner
from agents.answer_generator import answer_generator
from routers.query_refiner import query_refiner
from agents.rag_retriever import rag_retriever
from routers.rag_quality_critic import rag_quality_critic

def execute_agent_flow(state: dict) -> dict:
    """
    task_router 의 next_node 에 따라
    calendar vs. RAG 흐름을 분기 실행하고
    planner, generator 까지 모두 돌립니다.
    """
    state = task_router(state)
    if state["next_node"] in ("calendar_needed", "calendar_agent"):
        state = calendar_agent(state)
        state = answer_planner(state)
        state = answer_generator(state)
    else:
        state = query_refiner(state)
        state = rag_retriever(state)
        state = rag_quality_critic(state)
        if state["next_node"] == "answer_planner":
            state = answer_planner(state)
        if state["next_node"] == "answer_generator":
            state = answer_generator(state)
    return state

def handle_agent_input(req: InputRequest) -> AgentResponse:
    """
    API 로 받은 InputRequest 를 내부 state dict 로 바꿔서
    execute_agent_flow 를 호출하고 결과를 AgentResponse 로 리턴.
    """
    state = {
        "type": "question",
        "initial_input": req.user_input,
        "user_id": req.user_id,
        "session_id": req.session_id,
        "access_token": req.access_token,
        "ocr_result": req.ocr_result,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
        "final_answer": None,
        "next_node": None,
        "agent_messages": [],
        "router_messages": [],
    }
    result = execute_agent_flow(state)
    return AgentResponse(
        final_answer=result["final_answer"],
        agent_messages=result["agent_messages"],
        router_messages=result["router_messages"],
        crud_result=result.get("crud_result")
    )