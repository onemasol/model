import requests

LOG_API_URL = "http://52.79.95.55:8000/api/v1/agent/logs"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA3NzUzMDAsInN1YiI6IjFiYTc2OTMzLWQ1ZTUtNDA0My05ODAzLWUyZTM3MTU5MjhkMyJ9.0fXJjZmoayPoVQNHAFEV3Q2sNhCL3yUxCNySRRl2E1Y"

def send_log_to_backend(payload: dict) -> bool:
    headers = {
    "Authorization": f"Bearer {access_token}"
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
