# utils/check_router_state.py

import os
import sys
import pandas as pd
from typing import Dict, Callable, Any

# ✅ 상대경로로 루트 디렉토리 추가
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

# ✅ 프로젝트 내부 import
from main import create_graph
from routers.task_router import task_router
from routers.query_refiner import query_refiner
from routers.rag_quality_critic import rag_quality_critic
from routers.websearch_critic import websearch_critic
from routers.calendar_needed import calendar_needed
from models.agent_state import AgentState

# ✅ 라우터 함수 목록
router_functions: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "task_router": task_router,
    "query_refiner": query_refiner,
    "rag_quality_critic": rag_quality_critic,
    "websearch_critic": websearch_critic,
    "calendar_needed": calendar_needed,
}

expected_fields = set(AgentState.__annotations__.keys())
graph_nodes = set(create_graph().nodes)

results = []

for router_name, router_func in router_functions.items():
    print(f"▶ {router_name} 시작")
    dummy_state = {
        "type": "question",
        "schedule_type": None,
        "initial_input": "부가세 신고 서류 알려줘",
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
        result_state = router_func(dummy_state.copy())
        print(f"✅ {router_name} 성공")
        next_node = result_state.get("next_node", None)

        next_node_status = "✅"
        if next_node not in graph_nodes:
            next_node_status = "❌"

        actual_keys = set(result_state.keys())
        missing_fields = expected_fields - actual_keys
        unexpected_fields = actual_keys - expected_fields

        results.append({
            "router": router_name,
            "next_node": next_node,
            "next_node_status": next_node_status,
            "missing_fields": sorted(list(missing_fields)),
            "unexpected_fields": sorted(list(unexpected_fields))
        })

    except Exception as e:
        print(f"❌ {router_name} 오류 발생: {e}")
        results.append({
            "router": router_name,
            "error": str(e)
        })

# ✅ CLI에서 실행했을 때만 출력
if __name__ == "__main__":
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
