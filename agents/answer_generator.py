# agents/answer_generator.py

from typing import Dict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
<<<<<<< HEAD
    # Load environment variables from .env file         
=======

>>>>>>> origin/main
load_dotenv()

model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.5,
)

def answer_generator(state: Dict) -> Dict:
    user_query = state["messages"][-1]
    rag_info = state.get("rag_result", "")
    web_info = state.get("search_result", "")
    crud_info = state.get("crud_result", "")
    prev_answer = state.get("final_answer", "")  # answer_planner/이전 에이전트 답변

    prompt = f"""
    당신은 자영업자를 위한 스마트 어시스턴트입니다.
    아래 정보와 맥락을 바탕으로, **실무적으로 유익하고 신뢰감 있게** 사용자 질문에 답변해주세요.

    [사용자 질문]
    \"\"\"{user_query}\"\"\"

    [문서 검색(RAG) 정보]
<<<<<<< HEAD
    \"\"\"{rag_info if rag_info else "관련 문서 검색 정보 없음"}\"\"\"`
=======
    \"\"\"{rag_info if rag_info else "관련 문서 검색 정보 없음"}\"\"\"
>>>>>>> origin/main

    [웹 검색 결과]
    \"\"\"{web_info if web_info else "관련 웹 검색 결과 없음"}\"\"\"

    [일정 정보 또는 처리 결과]
    \"\"\"{crud_info if crud_info else "일정/처리 결과 없음"}\"\"\"

    [AnswerPlanner/이전 생성 답변]
    \"\"\"{prev_answer if prev_answer else "이전 답변 없음"}\"\"\"

    --- 작성 가이드 ---
    - 위 모든 정보를 종합적으로 고려해, 실질적으로 도움이 되는 답변을 제공하세요.
    - 내용이 중복되거나 불필요한 반복이 없도록, 필요한 정보만 자연스럽게 녹여서 서술하세요.
    - 일정 정보나 행동 방법이 있으면, 해당 내용을 명확하게 안내하세요.
    - 사용자가 추가 질문을 할 수 있도록 유도하거나, FAQ 등으로 자연스럽게 확장될 수 있는 마무리 멘트를 추가해도 좋습니다.
    - 답변 톤은 너무 딱딱하지 않게, 신뢰감 있고 부드럽게 해주세요. 특히 요식업 자영업자들이 이해할 수 있도록 쉽고, 실무적인 언어로 답변 부탁드려요.

    최종 요약/응답을 완성해서 1회만 출력하세요.
    """

    response = model.invoke(prompt)
    final_response = response.content.strip()

    state["final_answer"] = final_response
    state.setdefault("agent_messages", []).append({
        "agent": "answer_generator",
        "input_snapshot": {
            "user_query": user_query,
            "rag_info": rag_info,
            "web_info": web_info,
            "crud_info": crud_info,
            "prev_answer": prev_answer
        },
        "output": final_response
    })

    return state
