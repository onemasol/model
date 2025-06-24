import sys
import os
sys.path.append(os.path.abspath(".")) 

from typing import TypedDict, Annotated, List, Optional, Literal, Dict, Any

class AgentState(TypedDict):
    ### 유저 인풋과 모델 아웃풋 스테이트에 추가하기
    type: Annotated[str, "input_type"]  # "schedule" or "question"
    schedule_type: Annotated[Optional[Literal["event", "task"]], "type_of_schedule"]
    messages: Annotated[List[str], "conversation_history"]
    initial_input: Annotated[Optional[str], "user's_initial_input"]
    final_output: Annotated[Optional[str], "model's_final_output"]
    rag_result: Annotated[Optional[str], "rag_output"]
    search_result: Annotated[Optional[str], "search_output"]
    crud_result: Annotated[Optional[str], "crud_output"]

    next_node: Annotated[Optional[str], "next_node"]
    agent_messages: Annotated[List[str], "agent_conversation_history"]
    router_messages: Annotated[List[str], "router_conversation_history"]

    ### 캘린더 관련 플레이스홀더 (5개 필드)
    title: Annotated[Optional[str], "이벤트/할일 제목"]
    start_at: Annotated[Optional[str], "시작 시간 (ISO 형식, event용)"]
    end_at: Annotated[Optional[str], "종료 시간 (ISO 형식, event용)"]
    due_at: Annotated[Optional[str], "마감 시간 (ISO 형식, task용)"]
    timezone: Annotated[Optional[str], "시간대"]
    event_type: Annotated[Optional[str], "이벤트 타입 (event/task)"]

    ### 추가 필드 (RUD 및 분류/작업 관련)
    rud_candidate_ids: Annotated[Optional[List[str]], "RUD를 위한 유사도 기준 Top3 ID 리스트"]
    selected_item_id: Annotated[Optional[str], "실제 선택된 항목의 ID (RUD 작업용)"]
    calendar_classification: Annotated[Optional[dict], "캘린더 분류 응답"]
    calendar_operation: Annotated[Optional[str], "캘린더 작업 타입 (create, read 등)"]
    calendar_type: Annotated[Optional[str], "event / task"]
    event_payload: Annotated[Optional[dict], "캘린더 이벤트용 payload"]
    operation_type: Annotated[Optional[str], "CalRUD용 작업 타입"]
    query_info: Annotated[Optional[dict], "조회용 쿼리 정보"]