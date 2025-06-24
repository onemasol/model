# test_websearch_agent.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.websearch_agent import websearch_agent
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
def run_test():
    while True:
        user_query = input("\n검색할 질문을 입력하세요(종료는 엔터): ").strip()
        if not user_query:
            print("테스트 종료!")
            break
        # 테스트용 상태(state) 딕셔너리 생성
        state = {
            "initial_input": user_query,
            "agent_messages": []
        }
        # 웹서치 에이전트 실행
        result_state = websearch_agent(state)
        print("\n=== 요약 결과 ===")
        print(result_state.get("search_result", "검색 결과 없음"))
        print("\n=== 에이전트 메시지 ===")
        print(result_state["agent_messages"][-1])

if __name__ == "__main__":
    run_test()
