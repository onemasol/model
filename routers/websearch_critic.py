# routers/websearch_critic.py

from typing import Dict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.4
)

def websearch_critic(state: Dict) -> Dict:
    user_query = state["messages"][-1]
    search_result = state.get("search_result", "")

    prompt = f"""
    다음은 사용자 질문과 웹 검색 결과입니다.

    사용자 질문:
    \"\"\"{user_query}\"\"\"

    웹 검색 결과:
    \"\"\"{search_result}\"\"\"

    검색 결과가 질문에 충분히 응답한다고 판단되면 "GOOD",
    내용이 부족하거나 정확하지 않다면 "RETRY".

    위 둘 중 하나만 응답하세요 (설명 없이).
    """

    response = model.invoke(prompt).content.strip().upper()

    if "GOOD" in response:
        state["next_node"] = "calendar_needed"
    elif "RETRY" in response:
        state["next_node"] = "websearch_agent"
    else:
        state["next_node"] = "answer_generator"
        state["final_answer"] = "[websearch_critic] 판단 실패: 답변 생성기로 이동합니다."

    # 라우터 평가 기록 저장
    state.setdefault("router_messages", []).append({
        "router": "websearch_critic",
        "decision": response
    })

    return state
