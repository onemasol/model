# agents/websearch_agent.py

from typing import Dict
import os
from dotenv import load_dotenv


from langchain_google_community import GoogleSearchRun, GoogleSearchAPIWrapper

from langchain_ollama import ChatOllama
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")


search_api = GoogleSearchAPIWrapper(
    google_api_key=GOOGLE_API_KEY,
    google_cse_id=GOOGLE_CSE_ID,
)
search_tool = GoogleSearchRun(api_wrapper=search_api)


model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.5,
)

def refine_query_for_search(user_query: str, model) -> str:
    prompt = f"""
    아래 사용자의 질문을 구글 검색엔진에 적합한 형태(핵심 키워드만 남긴 간결한 문장 또는 구문)로 정제해서 한 줄로 만들어줘.
    - 불필요한 수식어나 맥락은 생략하고, 정확한 정보 탐색에 필요한 핵심 단어, 날짜, 기관, 숫자 등만 남겨.
    - 예시:
      질문: "나 자영업자고, 이번달 부가세 신고기간과 필요한 서류를 정확히 알려줘"
      변환: "자영업자 부가세 신고기간 필요서류"

    사용자 질문:
    \"\"\"{user_query}\"\"\"

    변환:
    """
    return model.invoke(prompt).content.strip().replace('"', '')

def websearch_agent(state: Dict) -> Dict:
    # 1. 크리틱에서 보강한 쿼리가 있으면 우선 사용
    search_query = state.get("websearch_query", "").strip()

    # 2. 없으면 user_query를 LLM으로 정제해서 검색용 쿼리 생성
    if not search_query:
        user_query = state["messages"][-1]
        search_query = refine_query_for_search(user_query, model)

    try:
        # 3. 구글 API로 검색
        results = search_tool.run(search_query)
        
        # 4. 검색 결과 요약
        summary_prompt = f"""
당신은 요식업 자영업자의 질문에 대해, 구글 웹 검색 결과를 바탕으로 신뢰도 높은 요약 답변을 작성하는 전문가입니다.

[사용자 질문]
"{state['messages'][-1]}"

[검색용 키워드]
"{search_query}"

[웹 검색 결과 (전문)]
\"\"\"{results}\"\"\"

---

📌 작성 지침:
- 위 웹 검색 내용을 바탕으로, 질문에 대해 실질적으로 도움이 되는 **사실 기반 도메인 지식 답변**을 5~6문장으로 작성해주세요.
- **불확실하거나 출처가 불명확한 정보는 포함하지 말고**, 핵심 정보 위주로 간결하게 정리해주세요.
- 정보가 많을 경우, 아래 우선순위를 기준으로 요약하세요:
  1. 관련 일정/기간/시기
  2. 구체적인 절차 또는 방법
  3. 예외사항이나 유의사항
- 어투는 자영업자가 읽기 편하도록 **친절하고 실무적인 톤**으로 작성해주세요.
- "구글 검색 결과에 따르면~" 같은 불필요한 서두는 생략하세요.

🧾 요약 답변:

        """
        summary = model.invoke(summary_prompt).content.strip()
        state["search_result"] = summary

        # 5. 로그 기록
        state.setdefault("agent_messages", []).append({
            "agent": "websearch_agent",
            "query_used": search_query,
            "origin_query": state["messages"][-1],
            "search_raw": results[:500],
            "summary": summary,
        })

        # 6. 검색 쿼리 보강 정보는 한 번 사용 후 삭제 (다음에 또 검색시 혼동 방지)
        state.pop("websearch_query", None)

    except Exception as e:
        state["search_result"] = f"[GoogleSearch Error] {e}"
        state.setdefault("agent_messages", []).append({
            "agent": "websearch_agent",
            "query_used": search_query,
            "error": str(e)
        })

    return state
