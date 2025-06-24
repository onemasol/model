#!/usr/bin/env python3
"""
새로운 토큰으로 Calendar API 테스트
"""

import os
import requests
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def test_with_new_tokens():
    """새로운 토큰으로 API 호출 테스트"""
    print("=" * 60)
    print("🔄 새로운 토큰으로 Calendar API 테스트")
    print("=" * 60)
    
    # 새로운 토큰들
    new_access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA0MzQ0NTUsInN1YiI6IjVkYWZjMzAxLWQ2ZmUtNDcyOC05ODNkLTE3MzhhMzgzOWI1MyJ9.US1I6Eibp8KmA3BQoiSLdRg0w5VZG6BduQdV8vZDsW4"
    new_refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTEwMzU2NTUsInN1YiI6IjVkYWZjMzAxLWQ2ZmUtNDcyOC05ODNkLTE3MzhhMzgzOWI1MyJ9.L0u8UBOrfzR-kwYdJg_vVrOt-1yHdwxs_MhNOD26FCs"
    
    # API 엔드포인트
    api_endpoint = "http://52.79.95.55:8000/api/v1/calendar/all"
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {new_access_token}"
    }
    
    print(f"🌐 API 엔드포인트: {api_endpoint}")
    print(f"🔑 Access Token: {new_access_token[:20]}...")
    print(f"🔄 Refresh Token: {new_refresh_token[:20]}...")
    
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
            
            return True, data
            
        elif response.status_code == 401:
            print("❌ 인증 실패 (401 Unauthorized)")
            print(f"   응답 내용: {response.text}")
            return False, None
            
        elif response.status_code == 403:
            print("❌ 인증 실패 (403 Forbidden)")
            print(f"   응답 내용: {response.text}")
            return False, None
            
        else:
            print(f"❌ API 호출 실패 (상태 코드: {response.status_code})")
            print(f"   응답 내용: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ 연결 오류 - 서버에 연결할 수 없습니다.")
        return False, None
        
    except requests.exceptions.Timeout:
        print("❌ 타임아웃 - 요청 시간이 초과되었습니다.")
        return False, None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {str(e)}")
        return False, None
        
    except json.JSONDecodeError:
        print("❌ JSON 파싱 오류 - 응답이 유효한 JSON이 아닙니다.")
        print(f"   응답 내용: {response.text}")
        return False, None

def update_env_tokens():
    """환경변수에 새로운 토큰 업데이트"""
    new_access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA0MzQ0NTUsInN1YiI6IjVkYWZjMzAxLWQ2ZmUtNDcyOC05ODNkLTE3MzhhMzgzOWI1MyJ9.US1I6Eibp8KmA3BQoiSLdRg0w5VZG6BduQdV8vZDsW4"
    new_refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTEwMzU2NTUsInN1YiI6IjVkYWZjMzAxLWQ2ZmUtNDcyOC05ODNkLTE3MzhhMzgzOWI1MyJ9.L0u8UBOrfzR-kwYdJg_vVrOt-1yHdwxs_MhNOD26FCs"
    
    # 환경변수 업데이트
    os.environ["CALENDAR_API_TOKEN"] = new_access_token
    os.environ["CALENDAR_REFRESH_TOKEN"] = new_refresh_token
    
    print("✅ 환경변수 업데이트 완료")
    print(f"   CALENDAR_API_TOKEN: {new_access_token[:20]}...")
    print(f"   CALENDAR_REFRESH_TOKEN: {new_refresh_token[:20]}...")

if __name__ == "__main__":
    print("🚀 새로운 토큰으로 Calendar API 테스트 시작")
    
    # 환경변수 업데이트
    update_env_tokens()
    
    # API 테스트
    success, data = test_with_new_tokens()
    
    if success:
        print("\n✅ 테스트 성공! 이제 시스템이 정상 작동할 것입니다.")
    else:
        print("\n❌ 테스트 실패. 토큰을 다시 확인해주세요.")
    
    print("\n" + "=" * 60)
    print("🏁 테스트 완료")
    print("=" * 60) 