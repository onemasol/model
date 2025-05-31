# agents/answer_generator.py

from typing import Dict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.5,
)

def answer_generator(state: Dict) -> Dict:
    user_query = state["messages"][-1]
    rag_info = state.get("rag_result", "없음")
    web_info = state.get("search_result", "없음")
    crud_info = state.get("crud_result", "없음")

    prompt = f"""
    당신은 스마트 어시스턴트입니다. 다음 정보를 바탕으로 사용자의 질문에 친절하고 정확하게 응답해주세요.

    [사용자 질문]
    \"\"\"{user_query}\"\"\"

    [문서 검색(RAG) 정보]
    \"\"\"{rag_info}\"\"\"

    [웹 검색 결과]
    \"\"\"{web_info}\"\"\"

    [일정 정보 또는 처리 결과]
    \"\"\"{crud_info}\"\"\"

    위 정보를 참고하여 자연스럽고 정확한 응답을 작성해주세요.
    """

    response = model.invoke(prompt)
    final_response = response.content.strip()

    state["final_answer"] = final_response
    state.setdefault("agent_messages", []).append({
        "agent": "answer_generator",
        "output": final_response
    })

    return state
