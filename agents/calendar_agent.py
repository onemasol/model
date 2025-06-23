from typing import Dict, Any
import os
import ast
import json
import re
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

from utils.calendar_api_utils import create_api_request_from_payload
import torch


device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
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
                "event_type": "event",
                "operation": "read",
                "title": "",
                "start_at": "",
                "end_at": "",
                "due_at": "",
                "timezone": "Asia/Seoul"
            }

def create_event_payload(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    추출된 정보를 바탕으로 이벤트 페이로드를 생성합니다.
    """
    title = extracted_info.get("title")
    if not title:
        raise ValueError("이벤트 제목(title)이 추출되지 않았습니다.")

    # 새로운 형식에서 직접 가져오기
    start_at = extracted_info.get("start_at")
    end_at = extracted_info.get("end_at")
    due_at = extracted_info.get("due_at")
    timezone = extracted_info.get("timezone", "Asia/Seoul")
    event_type = extracted_info.get("event_type", "event")

    # event_type에 따른 처리
    if event_type == "task":
        # task의 경우 start_at, end_at은 None, due_at만 사용
        if not due_at:
            # 마감일이 없으면 오늘 하루로 설정
            due_dt = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
            due_at = due_dt.isoformat()
        
        return {
            "id": str(uuid.uuid4()),
            "title": title,
            "event_type": event_type,
            "start_at": None,
            "end_at": None,
            "due_at": due_at,
            "description": extracted_info.get("description"),
            "location": extracted_info.get("location"),
            "timezone": timezone,
            "status": "pending",
            "source_type": "manual",
            "created_by_agent": "calendar_agent",
            "used_agents": [{'agent': 'calendar_agent'}],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    else:
        # event의 경우 start_at, end_at 사용, due_at은 None
        if not start_at:
            # 기본값으로 오늘 날짜 설정
            start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_at = start_dt.isoformat()

        if not end_at:
            # end_at이 없으면 start_at + 1시간으로 설정
            try:
                start_dt = datetime.fromisoformat(start_at.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(hours=1)
                end_at = end_dt.isoformat()
            except ValueError:
                end_at = start_at

        # start_at과 end_at이 같으면 적절한 duration 추가 (event만)
        if start_at == end_at:
            try:
                start_dt = datetime.fromisoformat(start_at.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(hours=1)  # 이벤트는 1시간
                end_at = end_dt.isoformat()
            except ValueError:
                # 파싱 실패시 기본값으로 1시간 추가
                try:
                    start_dt = datetime.fromisoformat(start_at.replace('Z', '+00:00'))
                    end_dt = start_dt + timedelta(hours=1)
                    end_at = end_dt.isoformat()
                except ValueError:
                    # 최종 실패시 현재 시간 + 1시간
                    end_dt = datetime.now() + timedelta(hours=1)
                    end_at = end_dt.isoformat()

        return {
            "id": str(uuid.uuid4()),
            "title": title,
            "event_type": event_type,
            "start_at": start_at,
            "end_at": end_at,
            "due_at": None,
            "description": extracted_info.get("description"),
            "location": extracted_info.get("location"),
            "timezone": timezone,
            "status": "pending",
            "source_type": "manual",
            "created_by_agent": "calendar_agent",
            "used_agents": [{'agent': 'calendar_agent'}],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
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
    1. **event_type:**
       - "event": 특정 시간에 일어나는 일정 (미팅, 약속, 회의, 파티 등)
       - "task": 완료해야 할 작업 (보고서 작성, 제출, 준비 등)
    
    2. **operation:**
       - "create": 새로운 일정/할일 추가 ("추가", "등록", "만들어", "해야 해" 등)
       - "read": 기존 일정/할일 조회 ("보여줘", "확인해줘", "뭐야" 등)
       - "update": 기존 일정/할일 수정 ("수정", "변경", "바꿔" 등)
       - "delete": 기존 일정/할일 삭제 ("삭제", "취소", "지워" 등)
    
    **날짜/시간 처리 규칙:**
    - 현재 날짜({current_date_str})를 기준으로 상대적 날짜 계산
    - event의 경우: start_at과 end_at 모두 ISO 형식 (예: "2024-01-15T14:00:00+09:00")
    - task의 경우: start_at은 null, end_at만 마감일로 설정 (예: "2024-01-15T23:59:59+09:00")
    - event의 기본 duration: 1시간 (end_at = start_at + 1시간)
    - 조회(read)의 경우: start_at은 해당 기간 시작, end_at은 해당 기간 끝
    - timezone은 "Asia/Seoul"로 고정
    - 시간은 24시간 형식으로 변환 (예: "오후 2시" → 14, "오전 9시" → 9)
    - 분이 없으면 00으로 설정
    
    **예시:**
    - "내일 오후 2시에 팀 미팅 추가해줘" → event, create, start_at: "2024-01-16T14:00:00+09:00", end_at: "2024-01-16T15:00:00+09:00"
    - "이번 주 일정 보여줘" → event, read, start_at: "{current_date_str}T00:00:00+09:00", end_at: "2024-01-21T23:59:59+09:00"
    - "할일 목록에 장보기 추가해줘" → task, create, start_at: null, end_at: "{current_date_str}T23:59:59+09:00"
    - "오늘 할 일 보여줘" → task, read, start_at: "{current_date_str}T00:00:00+09:00", end_at: "{current_date_str}T23:59:59+09:00"
    
    다음 형태로만 응답해주세요 (JSON 형식):
    {{
        "event_type": "event",
        "operation": "create",
        "title": "추출된 제목",
        "start_at": "2024-01-16T14:00:00+09:00",
        "end_at": "2024-01-16T15:00:00+09:00",
        "timezone": "Asia/Seoul"
    }}
    
    설명이나 추가 텍스트 없이 JSON 형식으로만 응답해주세요.
    """
    
    try:
        # LLM 호출
        response = model.invoke(prompt)
        content = response.content.strip()
        
        # 응답 파싱
        classification = parse_classification_response(content)
        
        # AgentState의 5개 캘린더 필드 직접 업데이트
        event_type = classification.get("event_type", "event")
        title = classification.get("title", "")
        timezone = classification.get("timezone", "Asia/Seoul")
        
        if event_type == "event":
            # event: start_at, end_at 사용, due_at은 null
            state.update({
                "calendar_classification": classification,
                "calendar_type": event_type,
                "calendar_operation": classification.get("operation", "read"),
                "title": title,
                "start_at": classification.get("start_at", ""),
                "end_at": classification.get("end_at", ""),
                "due_at": None,
                "timezone": timezone,
                "event_type": event_type,
                "schedule_type": "event"
            })
        else:
            # task: due_at 사용, start_at, end_at은 null
            state.update({
                "calendar_classification": classification,
                "calendar_type": event_type,
                "calendar_operation": classification.get("operation", "read"),
                "title": title,
                "start_at": None,
                "end_at": None,
                "due_at": classification.get("end_at", ""),  # task의 경우 end_at을 due_at으로 사용
                "timezone": timezone,
                "event_type": event_type,
                "schedule_type": "task"
            })
        
        # 작업에 따른 처리
        operation = classification.get("operation", "read")
        
        if operation == "create":
            # create 작업: 바로 페이로드 생성
            print("=== Calendar Agent: 페이로드 생성 ===")
            event_payload = create_event_payload({
                "title": state["title"],
                "start_at": state["start_at"],
                "end_at": state["end_at"],
                "due_at": state["due_at"],
                "timezone": state["timezone"],
                "event_type": state["event_type"]
            })
            state["event_payload"] = event_payload
            state["next_node"] = "answer_planner"
            state["crud_result"] = f"이벤트 페이로드 생성 완료: {event_payload.get('title', 'N/A')}"
        else:
            # read, update, delete 작업: calselector로 라우팅
            state["next_node"] = "calselector"
            state["crud_result"] = f"CRUD 작업 요청이 분류되었습니다. → calselector 노드로 라우팅"
            
            # RUD 작업 정보를 state에 추가
            state["operation_type"] = operation
            state["query_info"] = {
                "title": state["title"],
                "start_at": state["start_at"],
                "end_at": state["end_at"],
                "due_at": state["due_at"],
                "timezone": state["timezone"],
                "event_type": state["event_type"]
            }
        
        # 결과 요약 생성
        type_name = "일정" if classification.get("event_type") == "event" else "할일"
        operation_name = {
            "create": "생성",
            "read": "조회", 
            "update": "수정",
            "delete": "삭제"
        }.get(classification.get("operation", "read"), "조회")
        
        summary = f"{type_name} {operation_name} 요청이 분류되었습니다. → {state['next_node']} 노드로 라우팅"
        
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
