import requests

LOG_API_URL = "http://your.api.endpoint/agent_logs"

def send_log_to_backend(payload: dict) -> bool:
    try:
        response = requests.post(LOG_API_URL, json=payload)
        response.raise_for_status()
        print("✅ 로그 전송 성공")
        return True
    except Exception as e:
        print(f"❌ 로그 전송 실패: {e}")
        return False
