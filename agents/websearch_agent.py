# agents/websearch_agent.py

from typing import Dict
import os
from dotenv import load_dotenv


from langchain_google_community import GoogleSearchRun, GoogleSearchAPIWrapper

from langchain_ollama import ChatOllama

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
      변환: "2024년 6월 자영업자 부가세 신고기간 필요서류"

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
        다음은 구글 웹 검색 결과입니다:
        {results}

        위 정보를 참고하여 "{search_query}"(원래 질문: "{state['messages'][-1]}")에 대한 요약 답변을 3~4문장으로 작성하세요.
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
