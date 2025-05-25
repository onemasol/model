from langchain_ollama.llms import OllamaLLM
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Optional

class AgentState(TypedDict):
    type: Annotated[str, "input_type"]  # "schedule" or "question"
    messages: Annotated[List[str], "conversation_history"]
    rag_result: Annotated[Optional[str], "rag_output"]
    search_result: Annotated[Optional[str], "search_output"]
    crud_result: Annotated[Optional[str], "crud_output"]
    final_answer: Annotated[Optional[str], "final_output"]
    next_node: Annotated[Optional[str], "next_node"]