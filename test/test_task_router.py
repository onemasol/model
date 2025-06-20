import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.task_router import task_router
from models.agent_state import AgentState

def get_node_description(node, schedule_type=None):
    descriptions = {
        'rag_agent': 'RAG(정보 검색)이 필요한 질문',
        'cal_agent': f'일정 관리가 필요한 질문 ({schedule_type if schedule_type else "타입 미정"})',
        'general_agent': '일반적인 대화나 쓸데없는 질문'
    }
    return descriptions.get(node, '알 수 없는 노드')

def test_user_input():
    while True:
        user_input = input("\n질문을 입력하세요 (종료하려면 'q' 입력): ")
        if user_input.lower() == 'q':
            break
            
        state = AgentState(
            type="question",
            schedule_type=None,
            messages=[user_input],
            initial_input=None,
            final_output=None,
            rag_result=None,
            search_result=None,
            crud_result=None,
            next_node=None,
            agent_messages=[],
            router_messages=[]
        )
        
        result = task_router(state)
        print(f"\n입력: {user_input}")
        print(f"결정된 노드: {result['next_node']}")
        print(f"설명: {get_node_description(result['next_node'], result.get('schedule_type'))}")
        print("\n상태 정보:")
        print(f"- 최초 입력: {result['initial_input']}")
        print(f"- 최종 출력: {result['final_output']}")
        print(f"- 일정 타입: {result.get('schedule_type', '해당 없음')}")
        print(f"- 입력 유형: {result['type']}")
        print(f"- 대화 기록: {result['messages']}")
        print(f"- 에이전트 대화 기록: {result['agent_messages']}")
        print(f"- 라우터 대화 기록: {result['router_messages']}")

if __name__ == "__main__":
    print("Task Router 테스트를 시작합니다.")
    print("질문을 입력하면 어떤 노드로 라우팅되는지 확인할 수 있습니다.")
    print("가능한 노드:")
    print("- rag_agent: 정보 검색이 필요한 질문")
    print("- cal_agent: 일정 관리 관련 질문")
    print("  - event: 특정 시간에 진행되는 일정 (예: 회의, 약속)")
    print("  - task: 완료해야 할 작업 (예: 보고서 작성, 이메일 확인)")
    print("- general_agent: 일반적인 대화나 쓸데없는 질문")
    test_user_input()
