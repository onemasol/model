#!/usr/bin/env python3
"""
JWT 토큰 디버깅 스크립트
"""

import json
import base64
from datetime import datetime

def decode_jwt_token(token):
    """JWT 토큰을 디코딩하여 내용을 확인합니다."""
    try:
        # JWT 토큰은 3부분으로 구성: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            print("❌ 유효하지 않은 JWT 토큰 형식")
            return None
        
        # Payload 부분 디코딩 (두 번째 부분)
        payload = parts[1]
        
        # Base64 디코딩 (패딩 추가)
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        # 디코딩
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_json = json.loads(decoded_bytes.decode('utf-8'))
        
        return decoded_json
        
    except Exception as e:
        print(f"❌ 토큰 디코딩 실패: {str(e)}")
        return None

def analyze_token(token, token_name):
    """토큰을 분석하고 정보를 출력합니다."""
    print(f"\n🔍 {token_name} 분석:")
    print(f"토큰: {token[:50]}...")
    
    decoded = decode_jwt_token(token)
    if decoded:
        print("✅ 토큰 디코딩 성공")
        print(f"📋 토큰 내용:")
        print(json.dumps(decoded, indent=2, ensure_ascii=False))
        
        # 만료 시간 확인
        if 'exp' in decoded:
            exp_timestamp = decoded['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            current_time = datetime.now()
            
            print(f"\n⏰ 만료 시간: {exp_datetime}")
            print(f"🕐 현재 시간: {current_time}")
            
            if exp_datetime > current_time:
                remaining = exp_datetime - current_time
                print(f"✅ 토큰 유효 (남은 시간: {remaining})")
            else:
                print(f"❌ 토큰 만료됨")
        else:
            print("⚠️ 만료 시간 정보 없음")
    else:
        print("❌ 토큰 디코딩 실패")

if __name__ == "__main__":
    print("🔍 JWT 토큰 디버깅")
    print("=" * 50)
    
    # 새로운 토큰들
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA0MzQ0NTUsInN1YiI6IjVkYWZjMzAxLWQ2ZmUtNDcyOC05ODNkLTE3MzhhMzgzOWI1MyJ9.US1I6Eibp8KmA3BQoiSLdRg0w5VZG6BduQdV8vZDsW4"
    refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTEwMzU2NTUsInN1YiI6IjVkYWZjMzAxLWQ2ZmUtNDcyOC05ODNkLTE3MzhhMzgzOWI1MyJ9.L0u8UBOrfzR-kwYdJg_vVrOt-1yHdwxs_MhNOD26FCs"
    
    # 토큰 분석
    analyze_token(access_token, "Access Token")
    analyze_token(refresh_token, "Refresh Token")
    
    print("\n" + "=" * 50)
    print("🏁 토큰 분석 완료") 