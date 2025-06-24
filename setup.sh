#!/bin/bash

# unzip, curl 설치
apt update && apt install -y unzip curl

# 패키지 설치
pip install -r /root/model/requirements.txt --root-user-action=ignore

# Ollama 설치 (존재 여부 체크)
if ! which ollama > /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed"
fi
