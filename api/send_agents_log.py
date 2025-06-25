import requests

LOG_API_URL = "http://52.79.95.55:8000/api/v1/agent/logs"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA4NzgyOTcsInN1YiI6IjRhNzI4OTUyLTUzYTAtNGFiZS1hZThjLTBmZjQ0MGQ2NTg1ZSJ9.9r4F6Lazb0P0utAbh7FdLM-tTz5zOJUcxgdrX8vhMmo"

def send_log_to_backend(payload: dict) -> bool:
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
