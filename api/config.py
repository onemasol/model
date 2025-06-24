"""
OAuth 2.0 설정 파일
환경 변수를 통해 OAuth 설정을 관리
"""

import os
from typing import Dict, Any

class OAuthConfig:
    """OAuth 2.0 설정 클래스"""
    
    def __init__(self):
        self.client_id = os.getenv("OAUTH_CLIENT_ID", "your_client_id")
        self.client_secret = os.getenv("OAUTH_CLIENT_SECRET", "your_client_secret")
        self.authorization_url = os.getenv("OAUTH_AUTH_URL", "https://accounts.google.com/o/oauth2/v2/auth")
        self.token_url = os.getenv("OAUTH_TOKEN_URL", "https://oauth2.googleapis.com/token")
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
        self.scope = os.getenv("OAUTH_SCOPE", "openid email profile")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 반환"""
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "authorization_url": self.authorization_url,
            "token_url": self.token_url,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "frontend_url": self.frontend_url
        }

# 전역 설정 인스턴스
oauth_config = OAuthConfig()

# 환경 변수 예제 (실제 사용시 .env 파일에 설정)
ENV_EXAMPLE = """
# OAuth 2.0 설정
OAUTH_CLIENT_ID=your_google_client_id
OAUTH_CLIENT_SECRET=your_google_client_secret
OAUTH_AUTH_URL=https://accounts.google.com/o/oauth2/v2/auth
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/callback
OAUTH_SCOPE=openid email profile

# 프론트엔드 URL
FRONTEND_URL=http://localhost:3000
""" 