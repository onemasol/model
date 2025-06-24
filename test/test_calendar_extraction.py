#!/usr/bin/env python3
"""
캘린더 에이전트 정보 추출 테스트 스크립트
자연어 문장에서 일정/할일 정보가 어떻게 추출되는지 확인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import (
    parse_calendar_intent, 
    extract_event_data, 
    extract_task_data,
    prepare_calendar_payload,
    calendar_agent
)
from utils.calendar_api_utils import create_api_request_from_payload
import json

def test_intent_parsing():
    """의도 파악 테스트"""
    print("=" * 60)
    print("의도 파악 테스트")
    print("=" * 60)
    
    test_queries = [
        "내일 오후 2시에 팀 미팅이 있어",
        "다음 주 월요일 10시부터 12시까지 고객사 미팅",
        "오늘 할 일 목록 보여줘",
        "내일까지 보고서 작성해야 해",
        "3월 15일 생일 파티 일정 삭제해줘",
        "다음 주 화요일 오후 3시에 의사 예약으로 수정해줘",
        "이번 주 일정 전체 보여줘",
        "내일 아침 9시에 운동하기로 했어",
        "주간 회의를 다음 주 월요일로 변경해줘",
        "할 일 목록에 '장보기' 추가해줘"
    ]
    
    for query in test_queries:
        intent = parse_calendar_intent(query)
        print(f"질의: {query}")
        print(f"의도: {intent}")
        print("-" * 40)

def test_event_data_extraction():
    """일정 데이터 추출 테스트"""
    print("\n" + "=" * 60)
    print("일정 데이터 추출 테스트")
    print("=" * 60)
    
    test_queries = [
        "내일 오후 2시에 팀 미팅이 있어",
        "다음 주 월요일 10시부터 12시까지 고객사 미팅",
        "3월 15일 오후 3시에 생일 파티",
        "내일 아침 9시에 운동하기로 했어",
        "다음 주 화요일 오후 3시에 의사 예약",
        "오늘 저녁 7시에 친구들과 저녁 약속",
        "주간 회의를 다음 주 월요일 오전 10시로 변경해줘",
        "이번 주 금요일 오후 2시부터 4시까지 프로젝트 발표 준비",
        "내일 오전 11시에 점심 약속",
        "다음 주 수요일 오후 1시부터 3시까지 고객사 방문"
    ]
    
    for query in test_queries:
        event_data = extract_event_data(query)
        print(f"질의: {query}")
        print(f"추출된 일정 데이터: {json.dumps(event_data, ensure_ascii=False, indent=2)}")
        print("-" * 40)

def test_task_data_extraction():
    """할일 데이터 추출 테스트"""
    print("\n" + "=" * 60)
    print("할일 데이터 추출 테스트")
    print("=" * 60)
    
    test_queries = [
        "오늘 할 일 목록 보여줘",
        "내일까지 보고서 작성해야 해",
        "할 일 목록에 '장보기' 추가해줘",
        "이번 주 금요일까지 프로젝트 제안서 완성하기",
        "다음 주 월요일까지 월간 실적 보고서 제출",
        "오늘 저녁까지 이메일 정리하기",
        "내일 아침까지 프레젠테이션 자료 준비",
        "이번 주까지 회의록 정리하기",
        "다음 주 화요일까지 고객사 자료 준비",
        "오늘까지 주간 업무 보고서 작성"
    ]
    
    for query in test_queries:
        task_data = extract_task_data(query)
        print(f"질의: {query}")
        print(f"추출된 할일 데이터: {json.dumps(task_data, ensure_ascii=False, indent=2)}")
        print("-" * 40)

def test_full_agent():
    """전체 에이전트 테스트"""
    print("\n" + "=" * 60)
    print("전체 에이전트 테스트")
    print("=" * 60)
    
    # 테스트용 상태 설정
    test_state = {
        "initial_input": "내일 오후 2시에 팀 미팅 일정 추가해줘",
        "available_calendars": [
            {"id": "primary", "summary": "기본 캘린더", "primary": True},
            {"id": "work@company.com", "summary": "업무 캘린더", "primary": False}
        ],
        "available_task_lists": [
            {"id": "@default", "title": "내 할일"},
            {"id": "work_tasks", "title": "업무 할일"}
        ]
    }
    
    # 에이전트 실행
    result_state = calendar_agent(test_state)
    
    print("입력 질의:", test_state["initial_input"])
    print("\n결과 요약:", result_state["crud_result"])
    print("\n페이로드:")
    print(json.dumps(result_state["calendar_payload"], ensure_ascii=False, indent=2))
    print("\nAPI 요청 본문:")
    print(json.dumps(result_state["calendar_api_request"], ensure_ascii=False, indent=2))

def test_api_request_generation():
    """API 요청 본문 생성 테스트"""
    print("\n" + "=" * 60)
    print("API 요청 본문 생성 테스트")
    print("=" * 60)
    
    test_cases = [
        {
            "query": "내일 오후 2시에 팀 미팅 일정 추가해줘",
            "description": "일정 생성"
        },
        {
            "query": "이번 주 일정 전체 보여줘",
            "description": "일정 조회"
        },
        {
            "query": "할 일 목록에 '장보기' 추가해줘",
            "description": "할일 생성"
        },
        {
            "query": "오늘 할 일 목록 보여줘",
            "description": "할일 조회"
        }
    ]
    
    available_calendars = [
        {"id": "primary", "summary": "기본 캘린더", "primary": True},
        {"id": "work@company.com", "summary": "업무 캘린더", "primary": False}
    ]
    
    available_task_lists = [
        {"id": "@default", "title": "내 할일"},
        {"id": "work_tasks", "title": "업무 할일"}
    ]
    
    for case in test_cases:
        print(f"\n테스트 케이스: {case['description']}")
        print(f"질의: {case['query']}")
        
        # 의도 파악
        intent = parse_calendar_intent(case['query'])
        operation = intent.get("operation", "read")
        type_ = intent.get("type", "event")
        
        # 페이로드 준비
        payload = prepare_calendar_payload(intent, operation, type_, case['query'])
        
        # API 요청 본문 생성
        api_request = create_api_request_from_payload(
            payload, available_calendars, available_task_lists
        )
        
        print(f"의도: {intent}")
        print(f"API 요청 본문:")
        print(json.dumps(api_request, ensure_ascii=False, indent=2))
        print("-" * 40)

if __name__ == "__main__":
    print("캘린더 에이전트 정보 추출 테스트 시작")
    print("Ollama 모델을 사용하여 자연어 처리를 수행합니다...")
    
    try:
        # 각 테스트 실행
        test_intent_parsing()
        test_event_data_extraction()
        test_task_data_extraction()
        test_full_agent()
        test_api_request_generation()
        
        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc() 