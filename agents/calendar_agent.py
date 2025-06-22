from typing import Dict
import os
import ast
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b"),
    temperature=0.5,
)

def clean_json_response(content: str) -> str:
    """JSON 응답을 정리하여 파싱 가능한 형태로 만듭니다."""
    content = content.strip()
    
    # JSON 코드 블록 마커 제거
    if content.startswith('```json'):
        content = content[7:]
    elif content.startswith('```'):
        content = content[3:]
    
    if content.endswith('```'):
        content = content[:-3]
    
    content = content.strip()
    
    # 중괄호가 포함된 부분만 추출
    brace_match = re.search(r'\{.*\}', content, re.DOTALL)
    if brace_match:
        content = brace_match.group()
    
    return content

def parse_classification_response(content: str) -> Dict:
    """응답을 안전하게 파싱하여 딕셔너리로 변환합니다."""
    try:
        # JSON으로 파싱 시도
        cleaned_content = clean_json_response(content)
        return json.loads(cleaned_content)
    except json.JSONDecodeError:
        try:
            # Python 딕셔너리로 파싱 시도
            return ast.literal_eval(content)
        except (ValueError, SyntaxError):
            # 파싱 실패시 기본값 반환
            return {
                "type": "event",
                "operation": "read",
                "extracted_info": {
                    "title": "",
                    "dateTime": "",
                    "date": ""
                }
            }

def calendar_agent(state: Dict) -> Dict:
    """
    캘린더 노드: 사용자 질의를 분석하여 일정/할일 관리 작업을 분류하고 다음 노드를 결정합니다.
    
    Args:
        state: 현재 상태 딕셔너리
        
    Returns:
        state: 업데이트된 상태 딕셔너리
    """
    user_query = state["messages"][-1]
    
    # 현재 날짜 가져오기
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y-%m-%d")
    
    prompt = f"""
    다음 질의를 분석하여 일정/할일 관리 작업을 분류해주세요.
    
    [현재 날짜]
    {current_date_str}
    
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
    
    **날짜/시간 처리 규칙:**
    - 현재 날짜({current_date_str})를 기준으로 상대적 날짜 계산
    - 날짜는 YYYY-MM-DD 형식으로 변환 (예: "내일" → {current_date_str} + 1일, "다음주 월요일" → 해당 날짜)
    - 시간이 있는 경우 dateTime 필드에 RFC3339 형식 사용 (예: "2024-01-15T14:00:00+09:00")
    - 시간이 없는 경우 date 필드에 YYYY-MM-DD 형식 사용
    - 시간대는 한국 시간대 (+09:00) 사용
    - 시간은 24시간 형식으로 변환 (예: "오후 2시" → 14, "오전 9시" → 9)
    - 분이 없으면 00으로 설정
    
    **예시:**
    - "내일 오후 2시에 팀 미팅 추가해줘" → event, create, dateTime: "2024-01-16T14:00:00+09:00"
    - "이번 주 일정 보여줘" → event, read, date: "{current_date_str}" (시작일)
    - "할일 목록에 장보기 추가해줘" → task, create, date: "{current_date_str}" (오늘)
    - "오늘 할 일 보여줘" → task, read, date: "{current_date_str}"
    
    다음 형태로만 응답해주세요 (JSON 형식):
    {{
        "type": "event",
        "operation": "create",
        "extracted_info": {{
            "title": "추출된 제목",
            "dateTime": "2024-01-16T14:00:00+09:00",
            "date": "2024-01-16"
        }}
    }}
    
    설명이나 추가 텍스트 없이 JSON 형식으로만 응답해주세요.
    """
    
    try:
        # LLM 호출
        response = model.invoke(prompt)
        content = response.content.strip()
        
        # 응답 파싱
        classification = parse_classification_response(content)
        
        # 상태 업데이트
        state.update({
            "calendar_classification": classification,
            "calendar_type": classification.get("type", "event"),
            "calendar_operation": classification.get("operation", "read"),
            "extracted_info": classification.get("extracted_info", {})
        })
        
        # 다음 노드 결정
        operation = classification.get("operation", "read")
        if operation == "create":
            state["next_node"] = "CalC"
        else:  # read, update, delete
            state["next_node"] = "CalRUD"
        
        # 결과 요약 생성
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
            "agent": "calendar_agent",
            "classification": classification,
            "summary": summary,
            "next_node": state["next_node"]
        })
        
    except Exception as e:
        # 에러 처리
        error_msg = f"캘린더 노드 오류: {str(e)}"
        state["crud_result"] = error_msg
        state["next_node"] = "answer_generator"  # 에러시 답변 생성기로
        
        state.setdefault("agent_messages", []).append({
            "agent": "calendar_agent",
            "error": str(e),
            "next_node": "answer_generator"
        })
    
    return state
