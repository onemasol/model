#!/bin/bash

# unzip, curl 설치
apt update && apt install -y unzip curl software-properties-common

# ngrok 설치
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list
apt update
apt install -y ngrok

# PPA 추가 (에러 무시)
add-apt-repository ppa:deadsnakes/ppa -y || true
apt update

# python3.13 설치 (3.13.5 버전 설치됨)
apt install -y python3.13 python3.13-venv python3.13-dev

# Ensure python3 refers to python3.13
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1
update-alternatives --set python3 /usr/bin/python3.13

# pip 설치
curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
/usr/bin/python3.13 get-pip.py

# Ensure pip3 refers to pip for python3.13
update-alternatives --install /usr/bin/pip3 pip3 /usr/local/bin/pip 1
update-alternatives --set pip3 /usr/local/bin/pip

# 패키지 설치
/usr/bin/python3.13 -m pip install -r /root/model/requirements_2.txt --root-user-action=ignore

# Ollama 설치 (존재 여부 체크)
if ! which ollama > /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed"
fi