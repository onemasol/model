# routers/query_refiner.py

from typing import Dict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
load_dotenv()

model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.4,
)

def query_refiner(state: Dict) -> Dict:
    user_query = state["messages"][-1]

    prompt = f"""
    사용자의 질문을 RAG 기반 벡터 검색에 적합하도록 정제해주세요.

    목적:
    - 핵심 키워드만 남긴 1줄 요약 쿼리를 만들어주세요.
    - 맥락 설명은 제외하고, 검색에 필요한 핵심 단어, 숫자, 기관명 중심으로 구성하세요.

    예시:
    질문: "이번달 부가세 신고에 필요한 서류가 뭐야?"
    정제된 쿼리: "부가세 신고 서류 자영업자 2024년 6월"

    [사용자 질문]
    \"\"\"{user_query}\"\"\"

    정제된 쿼리:
    """

    response = model.invoke(prompt)
    refined_query = response.content.strip()

    state["refined_query"] = refined_query
    state["next_node"] = "rag_retriever" 
    state.setdefault("router_messages", []).append({
        "router": "query_refiner",
        "refined_query": refined_query
    })

    return state
