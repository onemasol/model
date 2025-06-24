# shared.py
from langchain_ollama import ChatOllama
from typing import Annotated, List, Optional, TypedDict

model = ChatOllama(model="exaone3.5:7.8b", temperature=0.7)

class AgentState(TypedDict):
    type: Annotated[str, "input_type"]
    messages: Annotated[List[str], "conversation_history"]
    rag_result: Annotated[Optional[str], "rag_output"]
    search_result: Annotated[Optional[str], "search_output"]
    crud_result: Annotated[Optional[str], "crud_output"]
    final_answer: Annotated[Optional[str], "final_output"]
    next_node: Annotated[Optional[str], "next_node"]
    agent_messages: Annotated[List[str], "agent_conversation_history"]
    router_messages: Annotated[List[str], "router_conversation_history"]