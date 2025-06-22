#!/usr/bin/env python3
"""
간단한 캘린더 의도 파악 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import parse_calendar_intent, extract_event_data, extract_task_data
import json

def test_simple_intents():
    """간단한 의도 파악 테스트"""
    print("=" * 60)
    print("캘린더 의도 파악 테스트")
    print("=" * 60)
    
    test_cases = [
        {
            "query": "내일 오후 2시에 팀 미팅 일정 추가해줘",
            "expected": "CREATE_EVENT"
        },
        {
            "query": "이번 주 일정 전체 보여줘",
            "expected": "READ_EVENT"
        },
        {
            "query": "할 일 목록에 '장보기' 추가해줘",
            "expected": "CREATE_TASK"
        },
        {
            "query": "오늘 할 일 목록 보여줘",
            "expected": "READ_TASK"
        },
        {
            "query": "3월 15일 생일 파티 일정 삭제해줘",
            "expected": "DELETE_EVENT"
        },
        {
            "query": "다음 주 화요일 오후 3시에 의사 예약으로 수정해줘",
            "expected": "UPDATE_EVENT"
        },
        {
            "query": "내일까지 보고서 작성해야 해",
            "expected": "CREATE_TASK"
        },
        {
            "query": "내일 아침 9시에 운동하기로 했어",
            "expected": "CREATE_EVENT"
        }
    ]
    
    for case in test_cases:
        print(f"\n질의: {case['query']}")
        print(f"예상 의도: {case['expected']}")
        
        try:
            intent = parse_calendar_intent(case['query'])
            print(f"실제 의도: {intent}")
            
            if intent.get('intent') == case['expected']:
                print("✅ 정확히 파악됨!")
            else:
                print("❌ 잘못 파악됨")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        print("-" * 40)

def test_data_extraction():
    """데이터 추출 테스트"""
    print("\n" + "=" * 60)
    print("데이터 추출 테스트")
    print("=" * 60)
    
    # 일정 데이터 추출 테스트
    event_query = "내일 오후 2시에 팀 미팅 일정 추가해줘"
    print(f"일정 질의: {event_query}")
    try:
        event_data = extract_event_data(event_query)
        print(f"추출된 일정 데이터:")
        print(json.dumps(event_data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    print("\n" + "-" * 40)
    
    # 할일 데이터 추출 테스트
    task_query = "내일까지 보고서 작성해야 해"
    print(f"할일 질의: {task_query}")
    try:
        task_data = extract_task_data(task_query)
        print(f"추출된 할일 데이터:")
        print(json.dumps(task_data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("간단한 캘린더 테스트 시작")
    print("Ollama 모델을 사용하여 자연어 처리를 수행합니다...")
    
    try:
        test_simple_intents()
        test_data_extraction()
        
        print("\n" + "=" * 60)
        print("테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc() 