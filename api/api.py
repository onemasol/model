from fastapi import FastAPI
from pydantic import BaseModel
from routers.task_router import task_router
from agents.calendar_agent import calendar_agent
from agents.answer_planner import answer_planner
from agents.answer_generator import answer_generator
from agents.rag_retriever import rag_retriever
from routers.rag_quality_critic import rag_quality_critic
from routers.query_refiner import query_refiner
    
app = FastAPI(root_path="/agent")

class Query(BaseModel):
    prompt: str
    access_token: str

@app.post("/calendar")
def calendar_flow(q: Query):
    """캘린더 플로우 전체 실행 API"""
    state = {
        "type": "question",
        "initial_input": q.prompt,
        "access_token": q.access_token,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
        "final_answer": None,
        "next_node": None,
        "agent_messages": [],
        "router_messages": [],
        "user_id": "test-user"
    }

    try:
        state = task_router(state)
        if state.get("next_node") != "calendar_agent":
            return {"error": "task_router 결과 오류", "next_node": state.get("next_node")}

        state = calendar_agent(state)
        if state.get("next_node") != "answer_planner":
            return {"error": "calendar_agent 결과 오류", "next_node": state.get("next_node")}

        state = answer_planner(state)
        if state.get("next_node") != "answer_generator":
            return {"error": "answer_planner 결과 오류", "next_node": state.get("next_node")}

        state = answer_generator(state)

        return {
            "final_answer": state.get("final_answer"),
            "agent_messages": state.get("agent_messages")
        }

    except Exception as e:
        return {"error": str(e)}

@app.post("/calendar/test")
def calendar_test_flow(q: Query):
    """캘린더 플로우 테스트 전용 API"""
    state = {
        "type": "question",
        "initial_input": q.prompt,
        "access_token": q.access_token,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
        "final_answer": None,
        "next_node": None,
        "agent_messages": [],
        "router_messages": [],
        "user_id": "test-user"
    }

    try:
        state = task_router(state)
        if state.get("next_node") != "calendar_agent":
            return {"error": "task_router 결과 오류", "next_node": state.get("next_node")}

        # calendar_agent 대신 테스트용 로직
        state["crud_result"] = {"title": "테스트 일정 생성 완료"}
        state["next_node"] = "answer_planner"

        state = answer_planner(state)
        if state.get("next_node") != "answer_generator":
            return {"error": "answer_planner 결과 오류", "next_node": state.get("next_node")}

        state = answer_generator(state)

        return {
            "final_answer": state.get("final_answer"),
            "agent_messages": state.get("agent_messages"),
            "note": "테스트용 플로우 실행 결과"
        }

    except Exception as e:
        return {"error": str(e)}

# RAG 전체 플로우 실행 API
@app.post("/rag")
def rag_flow(q: Query):
    """RAG 전체 플로우 실행 API"""
    state = {
        "type": "question",
        "initial_input": q.prompt,
        "access_token": q.access_token,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
        "final_answer": None,
        "next_node": None,
        "agent_messages": [],
        "router_messages": [],
        "user_id": "test-user"
    }

    try:
        state = task_router(state)
        if state.get("next_node") != "query_refiner":
            return {"error": "task_router 결과 오류", "next_node": state.get("next_node")}

        state = query_refiner(state)
        if state.get("next_node") != "rag_retriever":
            return {"error": "query_refiner 결과 오류", "next_node": state.get("next_node")}

        state = rag_retriever(state)
        if state.get("next_node") != "rag_quality_critic":
            return {"error": "rag_retriever 결과 오류", "next_node": state.get("next_node")}

        state = rag_quality_critic(state)

        return {
            "rag_result": state.get("rag_result"),
            "router_messages": state.get("router_messages"),
            "next_node": state.get("next_node")
        }

    except Exception as e:
        return {"error": str(e)}

@app.post("/rag/test")
def rag_test_flow(q: Query):
    """RAG 플로우 테스트 전용 API"""
    state = {
        "type": "question",
        "initial_input": q.prompt,
        "access_token": q.access_token,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
        "final_answer": None,
        "next_node": None,
        "agent_messages": [],
        "router_messages": [],
        "user_id": "test-user"
    }

    try:
        state = task_router(state)
        if state.get("next_node") != "query_refiner":
            return {"error": "task_router 결과 오류", "next_node": state.get("next_node")}

        state = query_refiner(state)
        if state.get("next_node") != "rag_retriever":
            return {"error": "query_refiner 결과 오류", "next_node": state.get("next_node")}

        state = rag_retriever(state)
        if state.get("next_node") != "rag_quality_critic":
            return {"error": "rag_retriever 결과 오류", "next_node": state.get("next_node")}

        state = rag_quality_critic(state)

        return {
            "rag_result": state.get("rag_result"),
            "router_messages": state.get("router_messages"),
            "note": "테스트용 플로우 실행 결과"
        }

    except Exception as e:
        return {"error": str(e)}