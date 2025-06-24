import os
import sys

# 루트 경로 등록 (utils 폴더 기준으로 한 단계 위)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from main import create_graph
from models.agent_state import AgentState

def run_calendar_query_test():
    graph = create_graph()

    # 캘린더 관련 테스트 쿼리
    test_query = "7월 3일 오후 2시에 세무사 만나기로 일정 등록해줘"

    initial_state: AgentState = {
        "type": "question",
        "schedule_type": None,
        "messages": [test_query],
        "initial_input": test_query,
        "final_output": None,
        "rag_result": None,
        "search_result": None,
        "crud_result": None,
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

    final_state = graph.invoke(initial_state)

    print("\n=== 최종 답변 (final_output) ===")
    print(final_state.get("final_output"))

    print("\n=== 이벤트 페이로드 (event_payload) ===")
    print(final_state.get("event_payload"))

    print("\n=== CRUD 처리 결과 (crud_result) ===")
    print(final_state.get("crud_result"))

    print("\n=== Agent 메시지 로그 ===")
    for msg in final_state.get("agent_messages", []):
        print(f"[{msg.get('agent')}] {msg}")

if __name__ == "__main__":
    run_calendar_query_test()
