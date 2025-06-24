#!/usr/bin/env python3
"""
Calendar API 연결 테스트 스크립트
실제 API 서버에 연결하여 데이터를 가져오는지 확인
"""

import os
import sys
import requests
import json
from utils.token_refresh import refresh_calendar_token

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 파일 로드 완료")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다.")
except Exception as e:
    print(f"⚠️ .env 파일 로드 실패: {e}")

def test_calendar_api():
    """Calendar API 연결 테스트"""
    print("=" * 60)
    print("🌐 Calendar API 연결 테스트")
    print("=" * 60)
    
    # API 설정
    api_endpoint = os.getenv("CALENDAR_API_ENDPOINT", "http://52.79.95.55:8000/api/v1/calendar/all")
    api_token = os.getenv("CALENDAR_API_TOKEN", "")
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # 토큰이 있으면 Authorization 헤더 추가
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
        print(f"🔑 인증 토큰 사용: {api_token[:10]}...")
    else:
        print("⚠️ 인증 토큰 없음 - 인증 없이 요청")
    
    print(f"🌐 API 엔드포인트: {api_endpoint}")
    print(f"📋 요청 헤더: {json.dumps(headers, indent=2)}")
    
    try:
        print("\n📡 API 요청 전송 중...")
        
        # GET 요청 보내기
        response = requests.get(
            api_endpoint,
            headers=headers,
            timeout=10
        )
        
        print(f"📊 응답 상태 코드: {response.status_code}")
        print(f"📋 응답 헤더: {dict(response.headers)}")

        # 401/403이면 토큰 갱신 후 재시도
        if response.status_code in (401, 403):
            print("🔄 토큰 만료 감지, refresh_token으로 갱신 시도...")
            new_token = refresh_calendar_token()
            if new_token:
                print("✅ 새 토큰 발급, 재시도 진행")
                headers["Authorization"] = f"Bearer {new_token}"
                response = requests.get(
                    api_endpoint,
                    headers=headers,
                    timeout=10
                )
                print(f"📊 재시도 응답 상태 코드: {response.status_code}")
            else:
                print("❌ 토큰 갱신 실패")

        # 이후 기존 분기 유지
        if response.status_code == 200:
            # 성공적인 응답
            data = response.json()
            print(f"✅ API 호출 성공!")
            print(f"📊 받은 데이터 개수: {len(data)}개")
            
            # 데이터 분석
            events = []
            tasks = []
            
            for item in data:
                if "start_at" in item and "end_at" in item:
                    events.append(item)
                elif "task_id" in item and "status" in item:
                    tasks.append(item)
            
            print(f"📅 이벤트: {len(events)}개")
            print(f"📝 태스크: {len(tasks)}개")
            
            # 첫 번째 항목 출력 (예시)
            if data:
                print(f"\n📋 첫 번째 항목 예시:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
            
            return True
            
        elif response.status_code == 403:
            print("❌ 인증 실패 (403 Forbidden)")
            print("   - 인증 토큰이 필요하거나 잘못되었습니다.")
            print(f"   - 응답 내용: {response.text}")
            return False
            
        elif response.status_code == 404:
            print("❌ API 엔드포인트를 찾을 수 없음 (404 Not Found)")
            print(f"   - 응답 내용: {response.text}")
            return False
            
        else:
            print(f"❌ API 호출 실패 (상태 코드: {response.status_code})")
            print(f"   - 응답 내용: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 연결 오류 - 서버에 연결할 수 없습니다.")
        print("   - 서버가 실행 중인지 확인하세요.")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ 타임아웃 - 요청 시간이 초과되었습니다.")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {str(e)}")
        return False
        
    except json.JSONDecodeError:
        print("❌ JSON 파싱 오류 - 응답이 유효한 JSON이 아닙니다.")
        print(f"   - 응답 내용: {response.text}")
        return False

def test_with_different_endpoints():
    """다양한 엔드포인트로 테스트"""
    print("\n" + "=" * 60)
    print("🔍 다양한 엔드포인트 테스트")
    print("=" * 60)
    
    endpoints = [
        "http://52.79.95.55:8000/api/v1/calendar/all",
        "http://52.79.95.55:8000/api/calendar/all",
        "http://52.79.95.55:8000/api/v1/calendar",
        "http://localhost:8000/api/v1/calendar/all"
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 테스트 엔드포인트: {endpoint}")
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"   상태 코드: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ 성공!")
                break
        except:
            print(f"   ❌ 연결 실패")

if __name__ == "__main__":
    print("🚀 Calendar API 연결 테스트 시작")
    
    # 기본 API 테스트
    success = test_calendar_api()
    
    if not success:
        print("\n🔄 대체 엔드포인트 테스트 중...")
        test_with_different_endpoints()
    
    print("\n" + "=" * 60)
    print("🏁 테스트 완료")
    print("=" * 60) 