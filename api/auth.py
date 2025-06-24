"""
OAuth 2.0 인증 API
프론트엔드에서 access token을 받아오는 API 엔드포인트들
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
import secrets
from datetime import datetime, timedelta
import json

# OAuth 2.0 설정
OAUTH_CONFIG = {
    "client_id": os.getenv("OAUTH_CLIENT_ID", "your_client_id"),
    "client_secret": os.getenv("OAUTH_CLIENT_SECRET", "your_client_secret"),
    "authorization_url": os.getenv("OAUTH_AUTH_URL", "https://accounts.google.com/o/oauth2/v2/auth"),
    "token_url": os.getenv("OAUTH_TOKEN_URL", "https://oauth2.googleapis.com/token"),
    "redirect_uri": os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback"),
    "scope": os.getenv("OAUTH_SCOPE", "openid email profile"),
}

# 임시 토큰 저장소 (실제로는 Redis나 데이터베이스 사용 권장)
token_store: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="OAuth Authentication API", version="1.0.0")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    expires_at: Optional[datetime] = None

@app.get("/api/auth/login")
async def login():
    """
    OAuth 2.0 인증 시작
    사용자를 인증 서비스로 리다이렉트
    """
    state = secrets.token_urlsafe(32)
    
    # state를 임시 저장 (실제로는 세션이나 Redis 사용)
    token_store[state] = {
        "created_at": datetime.now(),
        "used": False
    }
    
    auth_url = (
        f"{OAUTH_CONFIG['authorization_url']}?"
        f"client_id={OAUTH_CONFIG['client_id']}&"
        f"redirect_uri={OAUTH_CONFIG['redirect_uri']}&"
        f"response_type=code&"
        f"scope={OAUTH_CONFIG['scope']}&"
        f"state={state}&"
        f"access_type=offline"
    )
    
    return RedirectResponse(url=auth_url)

@app.get("/api/auth/callback")
async def auth_callback(
    code: str,
    state: str,
    error: Optional[str] = None
):
    """
    OAuth 2.0 콜백 처리
    인증 코드를 access token으로 교환
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    # state 검증
    if state not in token_store or token_store[state]["used"]:
        raise HTTPException(status_code=400, detail="Invalid or used state parameter")
    
    # state를 사용됨으로 표시
    token_store[state]["used"] = True
    
    try:
        # 인증 코드를 access token으로 교환
        token_data = await exchange_code_for_token(code)
        
        # 토큰 정보 저장
        user_info = await get_user_info(token_data["access_token"])
        token_store[token_data["access_token"]] = {
            "user_id": user_info.get("id"),
            "email": user_info.get("email"),
            "expires_at": datetime.now() + timedelta(seconds=token_data["expires_in"]),
            "refresh_token": token_data.get("refresh_token"),
            "scope": token_data.get("scope")
        }
        
        # 프론트엔드로 리다이렉트 (실제 구현에서는 적절한 프론트엔드 URL 사용)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?access_token={token_data['access_token']}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")

@app.post("/api/auth/token", response_model=TokenResponse)
async def get_token_info(access_token: str):
    """
    토큰 정보 조회
    """
    if access_token not in token_store:
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    token_info = token_store[access_token]
    
    # 토큰 만료 확인
    if token_info["expires_at"] < datetime.now():
        raise HTTPException(status_code=401, detail="Access token expired")
    
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=int((token_info["expires_at"] - datetime.now()).total_seconds()),
        refresh_token=token_info.get("refresh_token"),
        scope=token_info.get("scope")
    )

@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    """
    Refresh token을 사용하여 새로운 access token 발급
    """
    try:
        new_token_data = await refresh_access_token(refresh_token)
        
        # 새로운 토큰 정보 저장
        user_info = await get_user_info(new_token_data["access_token"])
        token_store[new_token_data["access_token"]] = {
            "user_id": user_info.get("id"),
            "email": user_info.get("email"),
            "expires_at": datetime.now() + timedelta(seconds=new_token_data["expires_in"]),
            "refresh_token": new_token_data.get("refresh_token"),
            "scope": new_token_data.get("scope")
        }
        
        return TokenResponse(
            access_token=new_token_data["access_token"],
            token_type="Bearer",
            expires_in=new_token_data["expires_in"],
            refresh_token=new_token_data.get("refresh_token"),
            scope=new_token_data.get("scope")
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

@app.get("/api/auth/validate", response_model=TokenValidationResponse)
async def validate_token(access_token: str):
    """
    Access token 유효성 검증
    """
    if access_token not in token_store:
        return TokenValidationResponse(valid=False)
    
    token_info = token_store[access_token]
    
    # 토큰 만료 확인
    if token_info["expires_at"] < datetime.now():
        return TokenValidationResponse(valid=False)
    
    return TokenValidationResponse(
        valid=True,
        user_id=token_info["user_id"],
        email=token_info["email"],
        expires_at=token_info["expires_at"]
    )

@app.post("/api/auth/logout")
async def logout(access_token: str):
    """
    로그아웃 - 토큰 무효화
    """
    if access_token in token_store:
        del token_store[access_token]
    
    return {"message": "Successfully logged out"}

async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """
    인증 코드를 access token으로 교환
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OAUTH_CONFIG["token_url"],
            data={
                "client_id": OAUTH_CONFIG["client_id"],
                "client_secret": OAUTH_CONFIG["client_secret"],
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": OAUTH_CONFIG["redirect_uri"]
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Token exchange failed")
        
        return response.json()

async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh token을 사용하여 새로운 access token 발급
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OAUTH_CONFIG["token_url"],
            data={
                "client_id": OAUTH_CONFIG["client_id"],
                "client_secret": OAUTH_CONFIG["client_secret"],
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Token refresh failed")
        
        return response.json()

async def get_user_info(access_token: str) -> Dict[str, Any]:
    """
    Access token을 사용하여 사용자 정보 조회
    """
    # Google OAuth의 경우 userinfo 엔드포인트 사용
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        return response.json()

# 의존성 함수 - 다른 API에서 토큰 검증에 사용
async def get_current_user(access_token: str = Depends(OAuth2AuthorizationCodeBearer(tokenUrl="/api/auth/token"))):
    """
    현재 사용자 정보를 반환하는 의존성 함수
    """
    if access_token not in token_store:
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    token_info = token_store[access_token]
    
    if token_info["expires_at"] < datetime.now():
        raise HTTPException(status_code=401, detail="Access token expired")
    
    return {
        "user_id": token_info["user_id"],
        "email": token_info["email"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 