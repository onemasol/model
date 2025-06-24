1. chmod +x setup.sh
2. scp -r /Users/yiji/.cache/huggingface root@vessl-onemasol:/root/.cache/ : 약 1분
3. ./setup.sh
3. ollama serve & ollama pull exaone3.5:7.8b : 약 10분 or 
    scp -r ~/.ollama/models root@vessl-onemasol:/root/.ollama/ : 3번 대신 선택 가능 약 17분
5. ./run.sh <실행할 Python 스크립트 경로> [추가 인자]