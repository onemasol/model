import requests
from api.getset import (
    set_current_session_id, get_current_session_id,
    set_current_access_token, get_current_access_token,
    set_current_user_input, set_current_ocr_result
)   

def send_log_to_backend(payload: dict) -> bool:
    # 디버깅: payload 내용 확인
    print(f"🔍 로그 전송 디버깅 - payload 내용:")

    LOG_API_URL = "http://52.79.95.55:8000/api/v1/agent/logs"
    access_token = get_current_access_token()
    for key, value in payload.items():
        print(f"   {key}: {repr(value)} (타입: {type(value)})")
    
    # None 값이 있는지 확인
    none_keys = [key for key, value in payload.items() if value is None]
    if none_keys:
        print(f"⚠️  None 값 발견: {none_keys}")
        # None 값을 빈 문자열로 변환
        for key in none_keys:
            payload[key] = ""
        print(f"✅ None 값을 빈 문자열로 변환 완료")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    try:
        response = requests.post(LOG_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        print("✅ 로그 전송 성공")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTPError: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ 기타 오류: {e}")
        return False
