"""
메인 API 애플리케이션
모든 API 엔드포인트를 통합하는 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import app as auth_app
import uvicorn

# 메인 애플리케이션 생성
app = FastAPI(
    title="Model API",
    description="프론트엔드에서 access token을 받아오는 API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드에서 API 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인증 라우터 포함
app.mount("/api", auth_app)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Model API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "auth_endpoints": {
            "login": "/api/auth/login",
            "callback": "/api/auth/callback",
            "token_info": "/api/auth/token",
            "refresh": "/api/auth/refresh",
            "validate": "/api/auth/validate",
            "logout": "/api/auth/logout"
        }
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "model-api"}

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 