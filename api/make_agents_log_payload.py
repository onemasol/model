import uuid
from api.getset import (
    set_current_session_id, get_current_session_id,
    set_current_access_token, get_current_access_token,
    set_current_user_input, set_current_ocr_result
)

def make_agent_logs_payload(state: dict) -> dict:
    user_message = state.get("initial_input", "")
    agent_response = state.get("final_output", "") or ""
    event_id = ""
    task_id = ""

    schedule_type = state.get("schedule_type")
    event_payload = state.get("event_payload", {})

    if schedule_type == "event":
        event_id = event_payload.get("id", "")
    elif schedule_type == "task":
        task_id = event_payload.get("id", "")
    else:
        print("🔍 no schedule type found in state")

    payload = {
        "user_message": user_message,
        "agent_response": agent_response,
        "event_id": event_id,
        "task_id": task_id,
        "session_id": get_current_session_id(),
    }

    # Remove empty ids
    if not payload["event_id"]:
        payload.pop("event_id")
    if not payload["task_id"]:
        payload.pop("task_id")
    return payload
