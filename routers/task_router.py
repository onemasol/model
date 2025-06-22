from models.agent_state import AgentState
from langchain_ollama import ChatOllama
import os
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
# Initialize the ChatOllama model
model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.7,
)

def task_router(state: AgentState): 

    """TaskRouter는 User query를 분석합니다. 
    - RAG가 필요한 경우 next node: RAGFeasibility Router
    - 일정 관리 관련인 경우 next node: CalendarAgent  
    - 그 외 일반적인 질문인 경우 next node: GeneralAgent
    
    일정 관리의 경우 event와 task를 구분합니다:
    - event: 특정 시간에 진행되는 일정 (예: 회의, 약속)
    - task: 완료해야 할 작업 (예: 보고서 작성, 이메일 확인)
    """
    latest_message = state["messages"][-1]
    
    # 최초 입력이 없을 경우에만 저장
    if state.get("initial_input") is None:
        state["initial_input"] = latest_message


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
    CAL_EVENT
    CAL_TASK
    GENERAL

    """

    analysis_response = model.invoke(analysis_prompt)
    decision = analysis_response.content.strip().upper()

    # Update state based on the decision
    if decision == "RAG":
        state["next_node"] = "rag_agent"

    elif decision == "CAL_EVENT":
        state["next_node"] = "cal_agent"
        state["schedule_type"] = "event"
    elif decision == "CAL_TASK":
        state["next_node"] = "cal_agent"
        state["schedule_type"] = "task"
    else:  # GENERAL 또는 기타 경우
        state["next_node"] = "general_agent"

    # 최종 출력 저장
    state["final_output"] = decision


    return state


