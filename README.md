## for model team setup

1. cd model
2. chmod +x setup.sh
3. ./setup.sh
3. ollama serve & ollama pull exaone3.5:7.8b : 약 10분 or 
    scp -r ~/.ollama/models root@vessl-onemasol:/root/.ollama/ : 3번 대신 선택 가능 약 17분
5. ./run.sh <실행할 Python 스크립트 경로> [추가 인자]

-  scp -r /Users/yiji/.cache/huggingface root@vessl-onemasol:/root/.cache/ : 약 1분 : 생략하고 추후 진행

6. ollama kill 및 재 실행: ps aux | grep ollama -> kill 13198 16236 -> 다시 실행 : ollama serve &

## 이 아래는 for 이지 only

1. cd /root/model
2. uvicorn api.api:app --host 0.0.0.0 --port 8000
3. ngrok config add-authtoken $YOUR_AUTHTOKEN(새로 파면 다시 해야함)
4. ngrok http 8000
5. 테스트 : curl -X POST https://76e6-165-132-46-93.ngrok-free.app/calendar -H "Content-Type: application/json" -d '{"prompt": "내일 오후 2시에 미팅 추가해줘"}'