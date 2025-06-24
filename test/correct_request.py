#!/usr/bin/env python3
"""
정확한 API 요청 형식 테스트
"""

import requests
import json

def test_correct_request():
    """정확한 요청 형식으로 API 호출"""
    print("=" * 60)
    print("🔍 정확한 API 요청 형식 테스트")
    print("=" * 60)
    
    # 토큰
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA0MzQ0NTUsInN1YiI6IjVkYWZjMzAxLWQ2ZmUtNDcyOC05ODNkLTE3MzhhMzgzOWI1MyJ9.US1I6Eibp8KmA3BQoiSLdRg0w5VZG6BduQdV8vZDsW4"
    
    # API 엔드포인트
    api_endpoint = "http://52.79.95.55:8000/api/v1/calendar/all"
    
    print(f"🌐 API 엔드포인트: {api_endpoint}")
    print(f"🔑 Access Token: {access_token[:20]}...")
    
    # 테스트 1: API 문서와 동일한 요청 (Authorization 헤더 없음)
    print("\n📡 테스트 1: API 문서와 동일한 요청 (Authorization 헤더 없음)")
    headers1 = {
        "accept": "application/json"
    }
    
    try:
        response1 = requests.get(api_endpoint, headers=headers1, timeout=10)
        print(f"   상태 코드: {response1.status_code}")
        print(f"   응답: {response1.text}")
    except Exception as e:
        print(f"   오류: {str(e)}")
    
    # 테스트 2: Authorization 헤더 포함
    print("\n📡 테스트 2: Authorization 헤더 포함")
    headers2 = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response2 = requests.get(api_endpoint, headers=headers2, timeout=10)
        print(f"   상태 코드: {response2.status_code}")
        print(f"   응답: {response2.text}")
    except Exception as e:
        print(f"   오류: {str(e)}")
    
    # 테스트 3: Content-Type 헤더 추가
    print("\n📡 테스트 3: Content-Type 헤더 추가")
    headers3 = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response3 = requests.get(api_endpoint, headers=headers3, timeout=10)
        print(f"   상태 코드: {response3.status_code}")
        print(f"   응답: {response3.text}")
    except Exception as e:
        print(f"   오류: {str(e)}")
    
    # 테스트 4: 다른 Authorization 형식
    print("\n📡 테스트 4: 다른 Authorization 형식")
    headers4 = {
        "accept": "application/json",
        "Authorization": access_token  # Bearer 없이
    }
    
    try:
        response4 = requests.get(api_endpoint, headers=headers4, timeout=10)
        print(f"   상태 코드: {response4.status_code}")
        print(f"   응답: {response4.text}")
    except Exception as e:
        print(f"   오류: {str(e)}")

if __name__ == "__main__":  
    test_correct_request()
    print("\n" + "=" * 60)
    print("🏁 테스트 완료") 