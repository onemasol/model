# test/test_title_debug.py

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import calendar_agent
from agents.answer_planner import answer_planner
from agents.answer_generator import answer_generator

def test_title_debug():
    """제목이 제대로 전달되는지 디버깅하는 테스트"""
    
    test_input = "내일 오후 2시에 팀 미팅 추가해줘"
    
    print("🔍 제목 디버깅 테스트 시작")
    print("=" * 50)
    print(f"입력: {test_input}")
    print()
    
    # 1. Calendar Agent 실행
    print("1️⃣ Calendar Agent 실행")
    state = {
        "initial_input": test_input,
        "agent_messages": []
    }
    
    calendar_result = calendar_agent(state)
    
    print(f"✅ Calendar Agent 결과:")
    print(f"   - title: {calendar_result.get('title', 'N/A')}")
    print(f"   - calendar_type: {calendar_result.get('calendar_type', 'N/A')}")
    print(f"   - calendar_operation: {calendar_result.get('calendar_operation', 'N/A')}")
    print(f"   - event_payload: {calendar_result.get('event_payload', {})}")
    
    if calendar_result.get('event_payload'):
        payload = calendar_result['event_payload']
        print(f"   - payload.title: {payload.get('title', 'N/A')}")
        print(f"   - payload.event_type: {payload.get('event_type', 'N/A')}")
    
    print()
    
    # 2. Answer Planner 실행
    print("2️⃣ Answer Planner 실행")
    planner_result = answer_planner(calendar_result)
    
    print(f"✅ Answer Planner 결과:")
    print(f"   - title: {planner_result.get('title', 'N/A')}")
    print(f"   - event_payload: {planner_result.get('event_payload', {})}")
    
    if planner_result.get('event_payload'):
        payload = planner_result['event_payload']
        print(f"   - payload.title: {payload.get('title', 'N/A')}")
    
    print()
    
    # 3. Answer Generator 실행 (캘린더 API 호출 부분만)
    print("3️⃣ Answer Generator - 캘린더 API 호출 부분")
    
    # 이벤트 생성용 payload 구성 시뮬레이션
    event_data = {
        "title": planner_result.get("title", ""),
        "start_at": planner_result.get("start_at"),
        "end_at": planner_result.get("end_at"),
        "timezone": planner_result.get("timezone", "Asia/Seoul"),
        "description": planner_result.get("initial_input", "")
    }
    
    # event_payload가 있으면 사용
    if planner_result.get("event_payload"):
        event_data.update(planner_result["event_payload"])
    
    print(f"✅ 최종 API 요청 데이터:")
    print(f"   - title: {event_data.get('title')}")
    print(f"   - start_at: {event_data.get('start_at')}")
    print(f"   - end_at: {event_data.get('end_at')}")
    print(f"   - timezone: {event_data.get('timezone')}")
    print(f"   - description: {event_data.get('description')}")
    
    # JSON 형태로 출력
    print(f"\n📋 JSON 형태:")
    print(json.dumps(event_data, indent=2, ensure_ascii=False))
    
    print()
    print("🎯 문제 분석:")
    
    if not event_data.get('title') or event_data.get('title') == '':
        print("❌ 제목이 비어있습니다!")
    elif event_data.get('title') == '새 일정':
        print("❌ 기본값 '새 일정'이 사용되고 있습니다!")
    else:
        print(f"✅ 제목이 정상적으로 설정되어 있습니다: {event_data.get('title')}")

if __name__ == "__main__":
    test_title_debug() 