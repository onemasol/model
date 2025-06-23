# routers/websearch_critic.py

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

MAX_RETRY = 3  # 최대 재검색 허용 횟수

def websearch_critic(state: Dict) -> Dict:
    user_query = state["messages"][-1]
    search_result = state.get("search_result", "")
    retry_count = state.get("websearch_retry_count", 0)

    # 쿼리 보강/수정 프롬프트
    refine_prompt = f"""
    다음은 사용자 질문과 웹 검색 결과입니다.

    사용자 질문:
    \"\"\"{user_query}\"\"\"

    웹 검색 결과:
    \"\"\"{search_result}\"\"\"

    1. 결과가 충분하다면 "GOOD".
    2. 결과가 부족하면, 부족한 점을 보완할 수 있도록 '더 효과적인 검색 쿼리'를 한 문장(예: 핵심 키워드 추가/수정 등)으로 제안하세요. 
    아래 포맷을 꼭 지켜주세요:

    결과가 충분: GOOD
    결과가 부족: RETRY: <보완된 쿼리>

    예시)
    - GOOD
    - RETRY: "2024년 종합소득세 신고 준비 서류 자영업자"
    """

    response = model.invoke(refine_prompt).content.strip()

    # 파싱 로직
    if response.startswith("GOOD"):
        state["next_node"] = "calendar_needed"
        # 쿼리 보강 내용은 제거
        state.pop("websearch_query", None)
    elif response.startswith("RETRY"):
        retry_count += 1
        state["websearch_retry_count"] = retry_count

        if retry_count > MAX_RETRY:
            state["next_node"] = "answer_generator"
            state["final_answer"] = (
                "[websearch_critic] 웹검색 반복 한도 초과: 답변 생성기로 이동합니다.\n"
                f"마지막 검색 쿼리: {state.get('websearch_query','')}\n"
                f"마지막 검색 결과: {search_result[:400]}"
            )
        else:
            # 쿼리 보강 파트 추출
            refined_query = response.replace("RETRY:", "").strip().strip('"')
            state["websearch_query"] = refined_query
            state["next_node"] = "websearch_agent"
    else:
        # 에러 처리: 모호한 응답일 경우 종료
        state["next_node"] = "answer_generator"
        state["final_answer"] = "[websearch_critic] 판단 실패: 답변 생성기로 이동합니다."

    # 평가 기록 저장
    state.setdefault("router_messages", []).append({
        "router": "websearch_critic",
        "decision": response,
        "retry_count": retry_count
    })

    return state
