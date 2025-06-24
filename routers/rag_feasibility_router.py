# routers/rag_feasibility_router.py

from typing import Dict
from langchain_ollama import ChatOllama
from shared import AgentState, model 
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 

def rag_feasibility_router(state: AgentState) -> AgentState:
    user_question = state["initial_input"]
    
    prompt = f"""
    당신은 질문이 벡터DB 기반 문서(RAG)로 답변 가능한지를 판단하는 전문가입니다.

    다음 질문이 충분히 벡터 DB에 있는 정보로 처리 가능하면 "RAG", 불가능하다면 "WEB"이라고만 답하세요.

    [질문]: "{user_question}"

    반드시 아래 중 하나로만 답변하세요:
    - RAG
    - WEB
    """

    response = model.invoke(prompt).content.strip().upper()

    if "RAG" in response:
        state["next_node"] = "rag_retriever"
    else:
        state["next_node"] = "websearch_agent"

    # optional: logging
    state["router_messages"].append(f"[RAG Feasibility] 판단 결과: {response}")
    
    return state
