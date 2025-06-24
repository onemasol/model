#!/bin/bash

# API 서버 실행 스크립트

echo "🚀 Model API 서버를 시작합니다..."

# 환경 변수 파일이 있는지 확인
if [ -f ".env" ]; then
    echo "📄 .env 파일을 로드합니다..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  .env 파일이 없습니다. 기본 설정을 사용합니다."
    echo "📝 .env 파일을 생성하려면 example_usage.md를 참조하세요."
fi

# Python 가상환경 확인
if [ -d "venv" ]; then
    echo "🐍 가상환경을 활성화합니다..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🐍 가상환경을 활성화합니다..."
    source .venv/bin/activate
fi

# 필요한 패키지 설치 확인
echo "📦 필요한 패키지를 확인합니다..."
pip install -r ../requirements.txt

# API 서버 실행
echo "🌐 API 서버를 시작합니다..."
echo "📍 서버 주소: http://localhost:8000"
echo "📚 API 문서: http://localhost:8000/docs"
echo "🔍 헬스 체크: http://localhost:8000/health"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo ""

python main.py 