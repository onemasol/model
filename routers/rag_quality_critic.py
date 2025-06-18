# routers/rag_quality_critic.py

from typing import Dict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.4
)

def rag_quality_critic(state: Dict) -> Dict:
    user_query = state["messages"][-1]
    rag_result = state.get("rag_result", "")

    prompt = f"""
    다음은 사용자의 질문과 RAG 에이전트가 생성한 응답입니다.
    
    사용자 질문:
    \"\"\"{user_query}\"\"\"
    
    RAG 응답:
    \"\"\"{rag_result}\"\"\"
    
    응답의 품질을 평가해주세요.
    - 사용자의 질문에 충분히 답하고 있으면 "GOOD"
    - 응답이 불충분하거나 정확하지 않으면 "RETRY_RAG"
    - RAG로도 해결이 어려워 보이면 "TRY_WEB"
    
    위 3가지 중 하나만 응답하세요 (다른 부가 설명 없이).
    """

    response = model.invoke(prompt).content.strip().upper()

    # 응답 결과에 따라 분기
    if "GOOD" in response:
        state["next_node"] = "calendar_needed"
    elif "RETRY_RAG" in response:
        state["next_node"] = "rag_retriever"
    elif "TRY_WEB" in response:
        state["next_node"] = "websearch_agent"
    else:
        state["next_node"] = "answer_generator"
        state["final_answer"] = "[rag_quality_critic] 판단 실패: 답변을 생성기로 넘깁니다."

    # 라우터 로그 남기기
    state.setdefault("router_messages", []).append({
        "router": "rag_quality_critic",
        "decision": response
    })

    return state
