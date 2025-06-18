# agents/answer_planner.py

from typing import Dict
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()
model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.5,
)

def answer_planner(state: Dict) -> Dict:
    user_query = state["messages"][-1]
    rag_info = state.get("rag_result", "")
    search_info = state.get("search_result", "")
    crud_info = state.get("crud_result", "")

    # 잡 질문인지(RAG/검색/캘린더 결과물 없음) 판단
    if not rag_info and not search_info and not crud_info:
        prompt = f"""
        너는 친절한 AI 챗봇이다.
        아래는 사용자의 질문이야.

        [질문]
        \"\"\"{user_query}\"\"\"

        - 너무 딱딱하지 않게, 친근한 말투로, 핵심만 간결하게 답변해줘.
        - 도메인 정보가 부족하면 "관련 도메인 정보가 더 필요하면 물어봐주세요" 등 안내도 추가해도 좋음.
        """
    else:
        # 도메인/검색 정보가 있을 경우, 최대한 자세하고 구체적으로
        prompt = f"""
        너는 자영업자를 위한 전문가 AI야. 아래 정보를 바탕으로 볼륨감 있고, 체계적이며 실무적으로 도움되는 답변을 만들어줘.

        [사용자 질문]
        \"\"\"{user_query}\"\"\"

        [문서 검색 결과(RAG)]
        \"\"\"{rag_info}\"\"\"

        [웹 검색 결과]
        \"\"\"{search_info}\"\"\"

        - 위 결과들을 종합해서, 현업 자영업자에게 실질적으로 도움이 되도록, 
          구체적인 가이드·주의사항·행동 방법 등을 최대한 자세하게 작성해줘.
        - 필요한 경우 표/목록 등으로 정리해줘.
        - 단순 복붙이 아니라, 질문의 맥락에 맞춰 요약/조합/정리해서 답변 생성.
        """

    response = model.invoke(prompt).content.strip()
    state["final_answer"] = response  # answer_generator에서 정제/통합하도록 state에 미리 기록

    # (선택) 로그 기록
    state.setdefault("agent_messages", []).append({
        "agent": "answer_planner",
        "prompt_type": "faq" if not rag_info and not search_info and not crud_info else "domain_summarize",
        "raw_answer": response
    })

    return state
