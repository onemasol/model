#!/bin/bash

# Ensure project root is on PYTHONPATH for module imports

export PYTHONPATH="$(cd "$(dirname "$0")" && pwd)"

# 실행할 기본 파일 설정
DEFAULT_SCRIPT="/root/model/test/test_flow.py"

# 인자 없으면 기본 실행s
if [ $# -eq 0 ]; then
  python "$DEFAULT_SCRIPT"
else
  python "$@"
fi