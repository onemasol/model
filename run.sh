#!/bin/bash

# 실행할 기본 파일 설정
DEFAULT_SCRIPT="/root/model/test/test_rag_flow.py"

# 인자 없으면 기본 실행s
if [ $# -eq 0 ]; then
  python "$DEFAULT_SCRIPT"
else
  python "$@"
fi