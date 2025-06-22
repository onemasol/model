from typing import Dict, Any

def calrud(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read, Update, Delete 요청을 처리하기 위해 라우팅만 수행합니다.

    Args:
        state: 현재 상태 딕셔너리

    Returns:
        state: 업데이트된 상태 딕셔너리
    """
    try:
        # calendar_agent에서 분류한 정보 가져오기
        operation = state.get("calendar_operation", "read")

        print("=== CalRUD 노드 실행: 라우팅 처리 ===")
        print(f"작업: {operation}")

        if operation not in ["read", "update", "delete"]:
            raise ValueError(f"CalRUD 노드는 'read', 'update', 'delete' 작업만 처리합니다. 현재 작업: {operation}")

        # 상태 업데이트
        state["crud_result"] = "CRUD 작업 라우팅 완료"
        state["next_node"] = "answer_planner"

        # 로그 기록
        state.setdefault("agent_messages", []).append({
            "agent": "calrud",
            "summary": state["crud_result"],
            "next_node": state["next_node"]
        })

    except Exception as e:
        error_msg = f"CalRUD 오류: {str(e)}"
        state["crud_result"] = error_msg
        state["next_node"] = "answer_generator"
        state.setdefault("agent_messages", []).append({
            "agent": "calrud",
            "error": str(e)
        })

    return state
