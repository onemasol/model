from typing import TypedDict, Annotated, List, Optional

class AgentState(TypedDict):
    type: Annotated[str, "input_type"]  # "schedule" or "question"
    messages: Annotated[List[str], "conversation_history"]
    rag_result: Annotated[Optional[str], "rag_output"]
    search_result: Annotated[Optional[str], "search_output"]
    crud_result: Annotated[Optional[str], "crud_output"]
    final_answer: Annotated[Optional[str], "final_output"]
    next_node: Annotated[Optional[str], "next_node"]
    agent_messages: Annotated[List[str], "agent_conversation_history"]  # agent 간 대화 기록
    router_messages: Annotated[List[str], "router_conversation_history"]  # router 간 대화 기록