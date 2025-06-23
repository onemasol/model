# agents/answer_generator.py

from typing import Dict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
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
    당신은 '요식업 자영업자'를 도와주는 실무 전문 어시스턴트입니다.  
세무, 위생, 일정, 민원 대응 등 실생활에서 마주치는 행정·정보적 이슈를 **전문적이되 친절한 상담 톤**으로 도와주세요.

[사용자 질문]
\"\"\"{user_query}\"\"\"  

[문서 기반 정보 (RAG)]
\"\"\"{rag_info if rag_info else "관련 문서 검색 정보 없음"}\"\"\"  

[웹 검색 결과]
\"\"\"{web_info if web_info else "관련 웹 검색 결과 없음"}\"\"\"  

[일정 정보 또는 처리 결과]
\"\"\"{crud_info if crud_info else "일정/처리 결과 없음"}\"\"\"  

[이전 생성된 응답 또는 초안 (AnswerPlanner)]
\"\"\"{prev_answer if prev_answer else "이전 답변 없음"}\"\"\"  

---

작성 지침:
- **일정 정보 또는 처리 방법**이 있다면 가장 먼저 안내하세요.
- 모든 정보(RAG/웹/이전 답변 등)를 종합하여, 중복 없이 핵심만 정리해 실무적으로 설명해주세요.
- 필요 시 관련 배경 지식도 간단히 덧붙이되, 복잡한 법령 해석보다는 **실행 중심**으로 답변하세요.
- 답변 톤은 “동네 세무사/상담사/법무사처럼 도메인 지식에 대한 전문성을 바탕으로, 자영업자들이 이해할 수 있게 친절하게” 유지해주세요.
- 마지막엔 **사용자의 후속 질문을 유도**하거나 **관련 이슈에 대한 안내**로 마무리하면 좋습니다.

👉 위 정보를 바탕으로, 사용자의 질문에 대해 실질적으로 도움 되는 요약형 응답을 아래에 작성해주세요. (1회 출력만)

    """

    response = model.invoke(prompt)
    final_response = response.content.strip()

    state["final_output"] = final_response
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
