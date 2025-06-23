from typing import Dict
import os
import ast
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
load_dotenv()

model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.5,
)

def calendar_agent_2(state: Dict) -> Dict:
    user_query = state["messages"][-1]
    
    prompt = f"""
    다음 질의를 분석하여 일정/할일 관리 작업을 분류해주세요.
    
    [사용자 질의]
    "{user_query}"
    
    **분류 기준:**
    1. **타입 (type):**
       - "event": 특정 시간에 일어나는 일정 (미팅, 약속, 회의, 파티 등)
       - "task": 완료해야 할 작업 (보고서 작성, 제출, 준비 등)
    
    2. **작업 (operation):**
       - "create": 새로운 일정/할일 추가 ("추가", "등록", "만들어", "해야 해" 등)
       - "read": 기존 일정/할일 조회 ("보여줘", "확인해줘", "뭐야" 등)
       - "update": 기존 일정/할일 수정 ("수정", "변경", "바꿔" 등)
       - "delete": 기존 일정/할일 삭제 ("삭제", "취소", "지워" 등)
    
    **예시:**
    - "내일 오후 2시에 팀 미팅 추가해줘" → event, create
    - "이번 주 일정 보여줘" → event, read
    - "할일 목록에 장보기 추가해줘" → task, create
    - "오늘 할 일 보여줘" → task, read
    
    다음 형태로만 응답해주세요 (JSON 형식이 아닌 Python 딕셔너리):
    {{
        "type": "event",
        "operation": "create",
        "extracted_info": {{
            "title": "추출된 제목",
            "time": "추출된 시간",
            "date": "추출된 날짜"
        }}
    }}
    
    설명이나 추가 텍스트 없이 딕셔너리 포맷의 텍스트로만 응답해주세요.
    """
    
    try:
        response = model.invoke(prompt)
        content = response.content.strip()
        
        # JSON 코드 블록 마커 제거
        if content.startswith('```json'):
            content = content[7:]  # '```json' 제거
        elif content.startswith('```'):
            content = content[3:]  # '```' 제거
        
        if content.endswith('```'):
            content = content[:-3]  # 끝의 '```' 제거
        
        content = content.strip()
        
        # JSON으로 파싱 시도
        import json
        try:
            classification = json.loads(content)
        except json.JSONDecodeError:
            # JSON 파싱 실패시 Python 딕셔너리로 시도
            import ast
            classification = ast.literal_eval(content)
        
        # 분류 결과를 상태에 저장
        state["calendar_classification"] = classification
        state["calendar_type"] = classification.get("type", "event")
        state["calendar_operation"] = classification.get("operation", "read")
        state["extracted_info"] = classification.get("extracted_info", {})
        
        # 라우팅 정보 추가
        operation = classification.get("operation", "read")
        if operation == "create":
            state["next_node"] = "CalC"
        else:  # read, update, delete
            state["next_node"] = "CalRUD"
        
        # 작업 요약 생성
        type_name = "일정" if classification.get("type") == "event" else "할일"
        operation_name = {
            "create": "생성",
            "read": "조회", 
            "update": "수정",
            "delete": "삭제"
        }.get(classification.get("operation", "read"), "조회")
        
        summary = f"{type_name} {operation_name} 요청이 분류되었습니다. → {state['next_node']} 노드로 라우팅"
        state["crud_result"] = summary
        
        # 로그 기록
        state.setdefault("agent_messages", []).append({
            "agent": "calendar_agent_2",
            "classification": classification,
            "summary": summary
        })
        
    except Exception as e:
        error_msg = f"캘린더 에이전트 2 오류: {str(e)}"
        state["crud_result"] = error_msg
        state.setdefault("agent_messages", []).append({
            "agent": "calendar_agent_2",
            "error": str(e)
        })
    
    return state
