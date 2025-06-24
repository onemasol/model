import uuid

def make_agent_logs_payload(state: dict) -> dict:
    user_message = state["messages"][-1]
    agent_response = state.get("final_answer") or state.get("final_output") or ""
    event_id = ""
    task_id = ""

    schedule_type = state.get("schedule_type")
    event_payload = state.get("event_payload", {})

    if schedule_type == "event":
        event_id = event_payload.get("id", "")
    elif schedule_type == "task":
        task_id = event_payload.get("id", "")

    return {
        "user_message": user_message,
        "agent_response": agent_response,
        "event_id": event_id,
        "task_id": task_id,
        "session_id": str(uuid.uuid4()),
        "task_id_log": str(uuid.uuid4())
    }
