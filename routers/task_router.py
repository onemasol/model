from models.agent_state import AgentState
from langchain_ollama import ChatOllama
import os

# Initialize the ChatOllama model
model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.7,
)

def task_router(state: AgentState): 
    """TaskRouter는 User query를 분석합니다. 만약 RAG, Web Search 등이 필요한 경우 next node: RAGFeasibility 
    Router, 그렇지 않고 일정의 추가 및 수정 등에 관련된 경우 next node: CalendarAgent
    """
    latest_message = state["messages"][-1]

    # Read system prompt from file
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "task_router.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()

    # Format the prompt with the latest message
    analysis_prompt = f"""
    {system_prompt}
    
    질문: {latest_message}
    
    다음 중 하나로만 응답해주세요 (설명 없이):
    RAG
    CAL
    """

    analysis_response = model.invoke(analysis_prompt)
    decision = analysis_response.content.strip().upper()

    # Update state based on the decision
    if decision == "RAG":
        state["next_node"] = "rag_agent"
    else:
        state["next_node"] = "cal_agent"


    return state


