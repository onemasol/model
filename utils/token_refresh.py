#!/usr/bin/env python3
"""
토큰 갱신 유틸리티
Calendar API 토큰을 갱신하는 기능
"""

import os
import requests
import json
from typing import Optional, Dict, Any

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 파일 로드 완료")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다.")
except Exception as e:
    print(f"⚠️ .env 파일 로드 실패: {e}")

def refresh_calendar_token() -> Optional[str]:
    """
    리프레시 토큰을 사용하여 새로운 access token을 받아옵니다.
    
    Returns:
        Optional[str]: 새로운 access token 또는 None
    """
    try:
        # 환경 변수에서 리프레시 토큰 가져오기
        refresh_token = os.getenv("CALENDAR_REFRESH_TOKEN")
        if not refresh_token:
            print("❌ CALENDAR_REFRESH_TOKEN이 설정되지 않았습니다.")
            return None
        
        # 토큰 갱신 API 엔드포인트
        refresh_endpoint = "http://52.79.95.55:8000/api/v1/auth/refresh"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # refresh_token을 request body에 포함
        data = {
            "refresh_token": refresh_token
        }
        
        # 토큰 갱신 요청
        response = requests.post(
            refresh_endpoint,
            headers=headers,
            json=data,  # JSON body로 전송
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            if new_access_token:
                print("✅ 토큰 갱신 성공")
                return new_access_token
            else:
                print("❌ 응답에 access_token이 없습니다.")
                return None
        else:
            print(f"❌ 토큰 갱신 실패 (상태 코드: {response.status_code})")
            print(f"   응답 내용: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 토큰 갱신 중 오류: {str(e)}")
        return None

def get_valid_calendar_token() -> Optional[str]:
    """
    유효한 Calendar API 토큰을 반환합니다.
    현재 토큰이 유효하지 않으면 갱신을 시도합니다.
    
    Returns:
        Optional[str]: 유효한 access token 또는 None
    """
    # 현재 토큰 확인
    current_token = os.getenv("CALENDAR_API_TOKEN")
    
    if current_token:
        # 토큰 유효성 검사 (간단한 테스트)
        if test_token_validity(current_token):
            print("✅ 현재 토큰이 유효합니다.")
            return current_token
        else:
            print("⚠️ 현재 토큰이 유효하지 않습니다. 갱신을 시도합니다.")
    
    # 토큰 갱신 시도
    new_token = refresh_calendar_token()
    if new_token:
        # 새로운 토큰을 환경 변수에 설정 (선택사항)
        os.environ["CALENDAR_API_TOKEN"] = new_token
        return new_token
    
    return None

def test_token_validity(token: str) -> bool:
    """
    토큰의 유효성을 테스트합니다.
    
    Args:
        token: 테스트할 토큰
        
    Returns:
        bool: 토큰이 유효하면 True
    """
    try:
        # 간단한 API 호출로 토큰 유효성 테스트
        test_endpoint = "http://52.79.95.55:8000/api/v1/calendar/all"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(test_endpoint, headers=headers, timeout=5)
        
        # 200이면 유효, 401이면 유효하지 않음
        return response.status_code == 200
        
    except:
        return False

if __name__ == "__main__":
    print("🔄 Calendar API 토큰 갱신 테스트")
    
    # 토큰 갱신 테스트
    new_token = refresh_calendar_token()
    if new_token:
        print(f"✅ 새로운 토큰: {new_token[:20]}...")
    else:
        print("❌ 토큰 갱신 실패")
    
    # 유효한 토큰 가져오기 테스트
    valid_token = get_valid_calendar_token()
    if valid_token:
        print(f"✅ 유효한 토큰: {valid_token[:20]}...")
    else:
        print("❌ 유효한 토큰을 가져올 수 없습니다.") 