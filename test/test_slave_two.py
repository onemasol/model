from main import slave_two, AgentState

def test_slave_two():
    print("\n=== Slave Two 테스트 시작 ===")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    
    while True:
        # Get user input
        question = input("\n질문을 입력하세요: ").strip()
        
        # Check for exit command
        if question.lower() in ['quit', 'exit']:
            print("\n테스트를 종료합니다.")
            break
        
        # Get test data
        print("\n테스트 데이터를 입력하세요 (없으면 빈칸으로 두세요):")
        rag_result = input("RAG 결과: ").strip() or None
        search_result = input("검색 결과: ").strip() or None
        crud_result = input("CRUD 결과: ").strip() or None
        
        # Initialize test state
        state = {
            "type": "question",
            "initial_input": question,
            "rag_result": None,
            "search_result": None,
            "crud_result": None,
            "final_answer": None,
            "next_node": None,
            "agent_messages": [],
            "router_messages": []
        }
        
        # Run slave_two
        result = slave_two(state)
        
        # Print result
        print(f"\n결과:")
        print(f"다음 노드: {result['next_node']}")
        if result['final_answer']:
            print(f"최종 답변: {result['final_answer']}")

if __name__ == "__main__":
    test_slave_two() 