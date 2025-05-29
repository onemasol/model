import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.task_router import task_router
from models.agent_state import AgentState
from langchain_ollama import ChatOllama

# Initialize the model for testing
model = ChatOllama(
    model="exaone3.5:7.8b",
    temperature=0.7,
)

def test_task_router():
    print("\n=== Task Router 테스트 시작 ===")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    
    while True:
        # Get user input
        question = input("\n질문을 입력하세요: ").strip()
        
        # Check for exit command
        if question.lower() in ['quit', 'exit']:
            print("\n테스트를 종료합니다.")
            break
        
        # Initialize test state
        test_state = {
            "type": "question",
            "messages": [question],
            "rag_result": None,
            "search_result": None,
            "crud_result": None,
            "final_answer": None,
            "next_node": None,
            "agent_messages": [],
            "router_messages": []
        }
        
        # Run task_router
        result = task_router(test_state)
        
        # Print result
        print(f"\n결과:")
        print(f"다음 노드: {result['next_node']}")
        if result['final_answer']:
            print(f"최종 답변: {result['final_answer']}")

if __name__ == "__main__":
    test_task_router() 