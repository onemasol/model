from typing import TypedDict, Annotated, List, Optional, Literal, Dict, Any

from typing import TypedDict, Annotated, List, Optional, Literal, Dict, Any

class AgentState(TypedDict):
    ### 유저 인풋과 모델 아웃풋 스테이트에 추가하기
    type: Annotated[str, "input_type"]  # "schedule" or "question"
    schedule_type: Annotated[Optional[Literal["event", "task"]], "type_of_schedule"]  # 일정이 event인지 task인지 구분
    messages: Annotated[List[str], "conversation_history"]
    initial_input: Annotated[Optional[str], "user's_initial_input"]  # 유저의 최초 입력
    final_output: Annotated[Optional[str], "model's_final_output"]  # 모델의 최종 출력
    rag_result: Annotated[Optional[str], "rag_output"]
    search_result: Annotated[Optional[str], "search_output"]
    crud_result: Annotated[Optional[str], "crud_output"]

    next_node: Annotated[Optional[str], "next_node"]
    agent_messages: Annotated[List[str], "agent_conversation_history"]  # agent 간 대화 기록
    router_messages: Annotated[List[str], "router_conversation_history"]  # router 간 대화 기록

    ### 캘린더 관련 플레이스홀더 (5개 필드)
    title: Annotated[Optional[str], "이벤트/할일 제목"]
    start_at: Annotated[Optional[str], "시작 시간 (ISO 형식, event용)"]
    end_at: Annotated[Optional[str], "종료 시간 (ISO 형식, event용)"]
    due_at: Annotated[Optional[str], "마감 시간 (ISO 형식, task용)"]
    timezone: Annotated[Optional[str], "시간대"]
    event_type: Annotated[Optional[str], "이벤트 타입 (event/task)"]