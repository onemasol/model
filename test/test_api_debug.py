#!/usr/bin/env python3
"""
API 호출 디버깅 테스트 스크립트
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

# API 서버가 기대하는 JWT 토큰
VALID_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA0MzQ0NTUsInN1YiI6IjVkYWZjMzAxLWQ2ZmUtNDcyOC05ODNkLTE3MzhhMzgzOWI1MyJ9.US1I6Eibp8KmA3BQoiSLdRg0w5VZG6BduQdV8vZDsW4"

async def test_calendar_event_creation():
    """캘린더 이벤트 생성 API 테스트"""
    print("=" * 60)
    print("📅 캘린더 이벤트 생성 API 테스트")
    print("=" * 60)
    
    # 테스트 데이터
    base_url = "http://52.79.95.55:8000"
    api_url = f"{base_url}/api/v1/calendar/events"
    
    # 테스트 이벤트 데이터
    event_data = {
        "title": "테스트 이벤트",
        "start_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "end_at": (datetime.now() + timedelta(hours=2)).isoformat(),
        "timezone": "Asia/Seoul",
        "description": "API 테스트용 이벤트"
    }
    
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {VALID_ACCESS_TOKEN}"
    }
    
    print(f"🌐 API URL: {api_url}")
    print(f"📋 요청 데이터: {json.dumps(event_data, indent=2, ensure_ascii=False)}")
    print(f"📄 요청 헤더: {headers}")
    print(f"🔑 Access Token: {VALID_ACCESS_TOKEN[:20]}...")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 API 요청 전송 중...")
            response = await client.post(api_url, json=event_data, headers=headers, timeout=30.0)
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            print(f"📄 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"❌ 응답 내용: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ API 요청 중 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_agent_event_creation():
    """에이전트 이벤트 생성 API 테스트"""
    print("\n" + "=" * 60)
    print("🤖 에이전트 이벤트 생성 API 테스트")
    print("=" * 60)
    
    api_url = "http://52.79.95.55:8000/api/v1/agent/events"
    
    # 테스트 에이전트 이벤트 데이터
    agent_event_data = {
        "title": "테스트 에이전트 이벤트",
        "description": "API 테스트용 에이전트 이벤트",
        "start_at": datetime.now().isoformat(),
        "end_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "location": "테스트 위치",
        "created_by_agent": "test_agent"
    }
    
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {VALID_ACCESS_TOKEN}"
    }
    
    print(f"🌐 API URL: {api_url}")
    print(f"📋 요청 데이터: {json.dumps(agent_event_data, indent=2, ensure_ascii=False)}")
    print(f"📄 요청 헤더: {headers}")
    print(f"🔑 Access Token: {VALID_ACCESS_TOKEN[:20]}...")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"📡 API 요청 전송 중...")
            response = await client.post(api_url, json=agent_event_data, headers=headers, timeout=30.0)
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            print(f"📄 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"❌ 응답 내용: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ API 요청 중 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_api_connection():
    """API 서버 연결 테스트"""
    print("\n" + "=" * 60)
    print("🔗 API 서버 연결 테스트")
    print("=" * 60)
    
    base_url = "http://52.79.95.55:8000"
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"🌐 서버 연결 테스트: {base_url}")
            response = await client.get(base_url, timeout=10.0)
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            if response.status_code == 200:
                print("✅ 서버 연결 성공!")
            else:
                print(f"⚠️ 서버 응답: {response.text}")
                
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")

async def main():
    """메인 테스트 함수"""
    print("🚀 API 디버깅 테스트 시작")
    
    # 1. 서버 연결 테스트
    await test_api_connection()
    
    # 2. 캘린더 이벤트 생성 테스트
    calendar_result = await test_calendar_event_creation()
    
    # 3. 에이전트 이벤트 생성 테스트
    agent_result = await test_agent_event_creation()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"캘린더 이벤트 생성: {'✅ 성공' if calendar_result else '❌ 실패'}")
    print(f"에이전트 이벤트 생성: {'✅ 성공' if agent_result else '❌ 실패'}")

if __name__ == "__main__":
    asyncio.run(main())