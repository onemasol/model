import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import calendar_agent, parse_calendar_intent, extract_event_data, extract_task_data
from models.agent_state import AgentState

def print_separator(title=""):
    """구분선을 출력합니다."""
    print("\n" + "="*60)
    if title:
        print(f" {title} ")
        print("="*60)
    else:
        print("="*60)

def print_json_pretty(data, title=""):
    """JSON 데이터를 예쁘게 출력합니다."""
    if title:
        print(f"\n📋 {title}:")
    try:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(data)

def test_parse_calendar_intent():
    """캘린더 의도 파악 테스트"""
    test_cases = [
        "내일 오후 2시에 팀 미팅 일정을 추가해줘",
        "이번 주 일정을 보여줘",
        "보고서 작성할일을 추가해줘",
        "할일 목록을 보여줘"
    ]
    
    for query in test_cases:
        intent = parse_calendar_intent(query)
        print(f"질의: {query}")
        print(f"의도: {intent}")
        print("-" * 50)

def test_extract_event_data():
    """일정 데이터 추출 테스트"""
    test_cases = [
        "내일 오후 2시에 팀 미팅 일정을 추가해줘",
        "다음 주 월요일 오전 10시부터 12시까지 회의실 A에서 프로젝트 회의",
        "금요일 저녁 7시에 저녁 약속"
    ]
    
    for query in test_cases:
        event_data = extract_event_data(query)
        print(f"질의: {query}")
        print(f"추출된 데이터: {event_data}")
        print("-" * 50)

def test_extract_task_data():
    """할일 데이터 추출 테스트"""
    test_cases = [
        "보고서 작성할일을 추가해줘",
        "내일까지 이메일 확인할일",
        "주간 실적 보고서 작성 - 금요일까지"
    ]
    
    for query in test_cases:
        task_data = extract_task_data(query)
        print(f"질의: {query}")
        print(f"추출된 데이터: {task_data}")
        print("-" * 50)

def test_calendar_agent():
    """캘린더 에이전트 통합 테스트"""
    test_cases = [
        {
            "query": "내일 오후 2시에 팀 미팅 일정을 추가해줘",
            "schedule_type": "event"
        },
        {
            "query": "이번 주 일정을 보여줘",
            "schedule_type": "event"
        },
        {
            "query": "보고서 작성할일을 추가해줘",
            "schedule_type": "task"
        },
        {
            "query": "할일 목록을 보여줘",
            "schedule_type": "task"
        }
    ]
    
    for test_case in test_cases:
        state: AgentState = {
            "type": "schedule",
            "schedule_type": test_case["schedule_type"],
            "messages": [test_case["query"]],
            "initial_input": None,
            "final_output": None,
            "rag_result": None,
            "search_result": None,
            "crud_result": None,
            "next_node": None,
            "agent_messages": [],
            "router_messages": []
        }
        
        print(f"테스트 케이스: {test_case['query']}")
        print(f"스케줄 타입: {test_case['schedule_type']}")
        
        try:
            result_state = calendar_agent(state)
            print(f"결과: {result_state.get('crud_result', 'No result')}")
        except Exception as e:
            print(f"오류: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    print("=== 캘린더 의도 파악 테스트 ===")
    test_parse_calendar_intent()
    
    print("\n=== 일정 데이터 추출 테스트 ===")
    test_extract_event_data()
    
    print("\n=== 할일 데이터 추출 테스트 ===")
    test_extract_task_data()
    
    print("\n=== 캘린더 에이전트 통합 테스트 ===")
    test_calendar_agent() 