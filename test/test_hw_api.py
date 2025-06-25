import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.answer_generator import answer_generator
from datetime import datetime, timedelta

def test_answer_generator_api():
    # 테스트용 임시 상태(state) 설정
    # 내일 오전 10시 설정
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    
    test_state = {
        "initial_input": "내일 오전 10시에 미팅 일정을 추가해줘",
        "messages": ["내일 오전 10시에 미팅 일정을 추가해줘"],
        "calendar_type": "event",
        "calendar_operation": "create",
        "title": "미팅",
        "start_at": start_time.isoformat(),
        "end_at": end_time.isoformat(),
        "timezone": "Asia/Seoul",
        # 로그 전송을 위한 세션 ID
        "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA4NzgyOTcsInN1YiI6IjRhNzI4OTUyLTUzYTAtNGFiZS1hZThjLTBmZjQ0MGQ2NTg1ZSJ9.9r4F6Lazb0P0utAbh7FdLM-tTz5zOJUcxgdrX8vhMmo"
    }

    # answer_generator 함수 실행 (동기)
    result_state = answer_generator(test_state)

    # 결과 출력
    print("=== 테스트 완료 ===")
    print(f"최종 답변:\n{result_state.get('final_answer', '없음')}")
    print(f"API 처리 결과: {result_state.get('crud_result', '없음')}")
    print(f"로그 전송 여부: {'성공' if result_state.get('log_sent') else '실패 또는 미전송'}")

if __name__ == "__main__":
    test_answer_generator_api()
