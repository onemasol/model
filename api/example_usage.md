# OAuth 2.0 Access Token API 사용 가이드

## 개요
이 API는 프론트엔드에서 OAuth 2.0을 통해 access token을 받아오는 기능을 제공합니다.

## API 엔드포인트

### 1. 로그인 시작
```
GET /api/auth/login
```
- 사용자를 OAuth 인증 서비스로 리다이렉트
- 브라우저에서 직접 호출

### 2. 인증 콜백
```
GET /api/auth/callback?code={code}&state={state}
```
- OAuth 인증 후 자동으로 호출됨
- 프론트엔드로 access token과 함께 리다이렉트

### 3. 토큰 정보 조회
```
POST /api/auth/token
Content-Type: application/json

{
  "access_token": "your_access_token"
}
```

### 4. 토큰 갱신
```
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token"
}
```

### 5. 토큰 유효성 검증
```
GET /api/auth/validate?access_token={access_token}
```

### 6. 로그아웃
```
POST /api/auth/logout
Content-Type: application/json

{
  "access_token": "your_access_token"
}
```

## 프론트엔드 사용 예제

### React 예제

```javascript
// 1. 로그인 시작
const startLogin = () => {
  window.location.href = 'http://localhost:8000/api/auth/login';
};

// 2. 콜백 처리 (React Router 사용)
import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    if (accessToken) {
      // 토큰을 로컬 스토리지에 저장
      localStorage.setItem('access_token', accessToken);
      
      // 메인 페이지로 리다이렉트
      window.location.href = '/dashboard';
    }
  }, [searchParams]);
  
  return <div>인증 처리 중...</div>;
};

// 3. 토큰 유효성 검증
const validateToken = async (accessToken) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/auth/validate?access_token=${accessToken}`
    );
    const data = await response.json();
    return data.valid;
  } catch (error) {
    console.error('Token validation failed:', error);
    return false;
  }
};

// 4. 토큰 갱신
const refreshToken = async (refreshToken) => {
  try {
    const response = await fetch('http://localhost:8000/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      return data.access_token;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
    return null;
  }
};

// 5. 로그아웃
const logout = async () => {
  const accessToken = localStorage.getItem('access_token');
  
  try {
    await fetch('http://localhost:8000/api/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ access_token: accessToken }),
    });
  } catch (error) {
    console.error('Logout failed:', error);
  } finally {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  }
};
```

### Vue.js 예제

```javascript
// 1. 로그인 시작
const startLogin = () => {
  window.location.href = 'http://localhost:8000/api/auth/login';
};

// 2. 콜백 처리
const handleAuthCallback = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const accessToken = urlParams.get('access_token');
  
  if (accessToken) {
    localStorage.setItem('access_token', accessToken);
    this.$router.push('/dashboard');
  }
};

// 3. API 호출 헬퍼 함수
const apiCall = async (url, options = {}) => {
  const accessToken = localStorage.getItem('access_token');
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { 'Authorization': `Bearer ${accessToken}` }),
      ...options.headers,
    },
  };
  
  try {
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (response.status === 401) {
      // 토큰이 만료된 경우 로그인 페이지로 리다이렉트
      localStorage.removeItem('access_token');
      this.$router.push('/login');
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    return null;
  }
};
```

## 환경 설정

### 1. 환경 변수 설정 (.env 파일)
```bash
# OAuth 2.0 설정
OAUTH_CLIENT_ID=your_google_client_id
OAUTH_CLIENT_SECRET=your_google_client_secret
OAUTH_AUTH_URL=https://accounts.google.com/o/oauth2/v2/auth
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/callback
OAUTH_SCOPE=openid email profile

# 프론트엔드 URL
FRONTEND_URL=http://localhost:3000
```

### 2. Google OAuth 설정
1. Google Cloud Console에서 프로젝트 생성
2. OAuth 2.0 클라이언트 ID 생성
3. 승인된 리디렉션 URI에 `http://localhost:8000/api/auth/callback` 추가
4. 클라이언트 ID와 시크릿을 환경 변수에 설정

## 보안 고려사항

1. **HTTPS 사용**: 프로덕션 환경에서는 반드시 HTTPS 사용
2. **토큰 저장**: access token은 안전하게 저장 (httpOnly 쿠키 권장)
3. **토큰 만료**: 토큰 만료 시간을 체크하고 자동 갱신 구현
4. **CSRF 보호**: state 파라미터를 통한 CSRF 공격 방지
5. **환경 변수**: 민감한 정보는 환경 변수로 관리

## 에러 처리

```javascript
// 토큰 만료 시 자동 갱신
const handleTokenExpiration = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (refreshToken) {
    const newToken = await refreshToken(refreshToken);
    if (newToken) {
      return newToken;
    }
  }
  
  // 갱신 실패 시 로그인 페이지로 리다이렉트
  window.location.href = '/login';
  return null;
};
```

## 테스트

API 서버 실행:
```bash
cd api
python main.py
```

브라우저에서 `http://localhost:8000/docs`로 접속하여 Swagger UI로 API 테스트 가능 