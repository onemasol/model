from typing import Dict, Optional
import os
import json
import requests
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from dotenv import load_dotenv

load_dotenv()

# Google Calendar API 스코프
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/tasks'
]

def exchange_id_token_for_access_token(id_token: str) -> Optional[str]:
    """
    Google ID Token을 access token으로 교환합니다.
    
    Args:
        id_token: Google OAuth ID Token
        
    Returns:
        access_token: 교환된 access token 또는 None
    """
    try:
        # Google Token Info API를 사용하여 ID Token 검증
        token_info_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        response = requests.get(token_info_url)
        
        if response.status_code != 200:
            print(f"❌ ID Token 검증 실패: {response.status_code}")
            return None
        
        token_info = response.json()
        
        # Google OAuth 2.0 토큰 교환 엔드포인트
        token_exchange_url = "https://oauth2.googleapis.com/token"
        
        # 클라이언트 ID는 .env에서 가져오거나 하드코딩
        client_id = os.getenv("GOOGLE_CLIENT_ID", "31757329668-q4ga33d33k5644e8g1amc82rl955hb6l.apps.googleusercontent.com")
        
        exchange_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": id_token,
            "client_id": client_id,
            "scope": " ".join(SCOPES)
        }
        
        exchange_response = requests.post(token_exchange_url, data=exchange_data)
        
        if exchange_response.status_code == 200:
            token_data = exchange_response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print(f"✅ ID Token을 access token으로 성공적으로 교환했습니다.")
                return access_token
            else:
                print("❌ 교환된 응답에 access_token이 없습니다.")
                return None
        else:
            print(f"❌ 토큰 교환 실패: {exchange_response.status_code} - {exchange_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 토큰 교환 중 오류 발생: {str(e)}")
        return None

def get_google_credentials() -> Optional[Credentials]:
    """
    Google OAuth 인증을 통해 credentials를 가져옵니다.
    """
    creds = None
    
    # 토큰 파일이 있으면 로드
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # 유효한 credentials가 없거나 만료되었으면 새로 인증
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.json 파일이 필요합니다 (Google Cloud Console에서 다운로드)
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json 파일이 필요합니다. "
                    "Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 다운로드하세요."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # 토큰 저장
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_access_token() -> Optional[str]:
    """
    현재 유효한 access token을 반환합니다.
    """
    try:
        creds = get_google_credentials()
        if creds and creds.token:
            return creds.token
        return None
    except Exception as e:
        print(f"Access token 가져오기 실패: {e}")
        return None

def refresh_access_token() -> Optional[str]:
    """
    Access token을 새로고침합니다.
    """
    try:
        creds = get_google_credentials()
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
            # 토큰 저장
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
            
            return creds.token
        return None
    except Exception as e:
        print(f"Access token 새로고침 실패: {e}")
        return None

def is_token_valid(token: str) -> bool:
    """
    토큰이 유효한지 확인합니다.
    """
    try:
        creds = Credentials(token)
        # 간단한 API 호출로 토큰 유효성 검증
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=creds)
        service.calendarList().list().execute()
        return True
    except Exception:
        return False 