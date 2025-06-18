# routers/calendar_needed.py

from typing import Dict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.4
)

def calendar_needed(state: Dict) -> Dict:
    user_query = state["messages"][-1]
    rag_info = state.get("rag_result", "")
    search_info = state.get("search_result", "")
    
    prompt = f"""
    당신은 사용자의 질문에 대해 검색 및 DB에서 증강 생성을 완료한 RAG Quality Critic, Web search Critic 노드로부터 결과물을 받아, 
    1. 사용자의 질문을 다시 확인하고 캘린더 CRUD와 같은 일정 관련 처리가 필요한지, 
    2. 캘린더 관련 일정 처리와 무관한 단순 도메인 지식에 대한 답변만 해주면 되는지를 판단하는
    캘린더 필요 여부를 판단하는 agent입니다. 아래 정보들을 바탕으로 일정 관련 처리가 필요한지 판단해주세요.   

    [사용자 질문]
    \"\"\"{user_query}\"\"\"

    [RAG 결과]
    \"\"\"{rag_info}\"\"\"

    [웹 검색 결과]
    \"\"\"{search_info}\"\"\"

    - 일정 생성, 조회, 수정, 삭제 등 **캘린더 작업이 필요하면** "CAL"
    - 그 외 단순 정보 응답이면 **캘린더 없이도 가능하므로** "NO_CAL"

    위 둘 중 하나만 정확히 답변하세요 (설명 없이).
    """

    response = model.invoke(prompt).content.strip().upper()

    if "CAL" in response:
        state["next_node"] = "calendar_agent"
    elif "NO_CAL" in response:
        state["next_node"] = "answer_planner"
    else:
        state["next_node"] = "answer_planner"
        state["final_answer"] = "[calendar_needed] 판단 실패: 답변 생성기로 이동합니다."

    # 라우터 판단 기록
    state.setdefault("router_messages", []).append({
        "router": "calendar_needed",
        "decision": response
    })

    return state
