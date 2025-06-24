import os
import sys
import pandas as pd
from typing import Dict, Callable, Any

# ✅ Jupyter 환경에서도 동작하도록 현재 디렉토리 기준으로 설정
ROOT_DIR = os.path.abspath("..")  # check_agent_state.py가 utils/ 아래 있다는 가정
sys.path.append(ROOT_DIR)

# ✅ 프로젝트 import
from models.agent_state import AgentState
from agents.answer_generator import answer_generator
from agents.rag_retriever import rag_retriever
from agents.calendar_agent import calendar_agent

# ✅ agent 목록
agent_functions: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "answer_generator": answer_generator,
    "rag_retriever": rag_retriever,
    "calendar_agent": calendar_agent,
}

expected_fields = set(AgentState.__annotations__.keys())

results = []

for agent_name, agent_func in agent_functions.items():
    print(f"▶ {agent_name} 시작")

    # 테스트용 상태 생성
    test_state = {
        "type": "schedule",
        "schedule_type": "event",
        "initial_input": "7월 3일에 세무사 보러 가는 일정 잡아줘",
        "final_output": None,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
        "final_answer": None,
        "next_node": None,
        "agent_messages": [],
        "router_messages": [],
        "title": None,
        "start_at": None,
        "end_at": None,
        "due_at": None,
        "timezone": None,
        "event_type": None,
    }

    try:
        result_state = agent_func(dummy_state.copy())
        actual_keys = set(result_state.keys())
        missing_fields = expected_fields - actual_keys
        unexpected_fields = actual_keys - expected_fields

        results.append({
            "agent": agent_name,
            "missing_fields": sorted(list(missing_fields)),
            "unexpected_fields": sorted(list(unexpected_fields)),
        })

    except Exception as e:
        results.append({
            "agent": agent_name,
            "error": str(e)
        })

df = pd.DataFrame(results)

# 방법 1: 터미널에 바로 보기
print(df.to_string(index=False))