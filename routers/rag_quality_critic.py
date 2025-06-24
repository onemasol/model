# routers/rag_quality_critic.py

from typing import Dict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
load_dotenv()

model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.4
)

def rag_quality_critic(state: Dict) -> Dict:
    user_query = state["initial_input"]
    rag_result = state.get("rag_result", "")

    prompt = f"""
    다음은 사용자의 질문과 RAG 에이전트가 생성한 응답입니다.
    
    사용자 질문:
    \"\"\"{user_query}\"\"\"
    
    RAG 응답:
    \"\"\"{rag_result}\"\"\"
    
    응답의 품질을 엄격하게 평가해주세요.
    
    판단 기준:
    - "GOOD": 사용자의 질문에 구체적이고 정확한 답변을 제공하고 있음
    - "RETRY_RAG": 응답이 불충분하거나 모호하지만 RAG로 더 나은 답변을 찾을 수 있을 것 같음
    - "TRY_WEB": 다음 중 하나라도 해당되면 웹서치 필요
      * 최신 정보가 필요한 질문 (2024년, 2025년 등 구체적 연도 언급)
      * 실시간 정보가 필요한 질문 (현재, 지금, 진행 중 등)
      * RAG 응답에서 "정보가 없음", "명시적으로 포함되어 있지 않음" 등이 언급됨
      * 사용자 질문에 구체적인 답변을 제공하지 못함
    
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
