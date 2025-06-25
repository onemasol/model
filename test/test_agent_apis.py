# test/test_agent_apis.py

import asyncio
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.answer_generator import (
    create_agent_task,
    get_agent_task,
    update_agent_task,
    delete_agent_task,
    create_agent_event,
    get_agent_event,
    update_agent_event,
    delete_agent_event
)

async def test_agent_task_apis():
    """Agent Task API 테스트"""
    print("🧪 Agent Task API 테스트 시작")
    print("=" * 50)
    
    # 테스트용 데이터
    test_task_data = {
        "title": "테스트 태스크",
        "description": "Agent Task API 테스트용 태스크입니다.",
        "used_agents": [
            {
                "agent_name": "test_agent",
                "timestamp": "2025-01-25T12:00:00Z",
                "input_summary": "테스트 입력",
                "operation": "테스트 작업"
            }
        ]
    }
    
    # 1. 태스크 생성 테스트
    print("1️⃣ 태스크 생성 테스트")
    create_result = await create_agent_task(
        title=test_task_data["title"],
        description=test_task_data["description"],
        used_agents=test_task_data["used_agents"]
    )
    
    if "error" in create_result:
        print(f"❌ 태스크 생성 실패: {create_result['error']}")
        return
    else:
        print(f"✅ 태스크 생성 성공: {create_result.get('task_id', 'N/A')}")
        task_id = create_result.get('task_id')
    
    # 2. 태스크 조회 테스트
    print("\n2️⃣ 태스크 조회 테스트")
    get_result = await get_agent_task(task_id)
    
    if "error" in get_result:
        print(f"❌ 태스크 조회 실패: {get_result['error']}")
    else:
        print(f"✅ 태스크 조회 성공: {get_result.get('title', 'N/A')}")
    
    # 3. 태스크 수정 테스트
    print("\n3️⃣ 태스크 수정 테스트")
    update_result = await update_agent_task(
        task_id=task_id,
        title="수정된 테스트 태스크",
        description="수정된 설명입니다.",
        status="completed"
    )
    
    if "error" in update_result:
        print(f"❌ 태스크 수정 실패: {update_result['error']}")
    else:
        print(f"✅ 태스크 수정 성공: {update_result.get('title', 'N/A')}")
    
    # 4. 태스크 삭제 테스트
    print("\n4️⃣ 태스크 삭제 테스트")
    delete_result = await delete_agent_task(task_id)
    
    if "error" in delete_result:
        print(f"❌ 태스크 삭제 실패: {delete_result['error']}")
    else:
        print(f"✅ 태스크 삭제 성공: {delete_result.get('message', 'N/A')}")

async def test_agent_event_apis():
    """Agent Event API 테스트"""
    print("\n🧪 Agent Event API 테스트 시작")
    print("=" * 50)
    
    # 테스트용 데이터
    test_event_data = {
        "title": "테스트 이벤트",
        "description": "Agent Event API 테스트용 이벤트입니다.",
        "start_at": "2025-01-25T10:00:00Z",
        "end_at": "2025-01-25T11:00:00Z",
        "location": "테스트 장소",
        "created_by_agent": "test_agent"
    }
    
    # 1. 이벤트 생성 테스트
    print("1️⃣ 이벤트 생성 테스트")
    create_result = await create_agent_event(
        title=test_event_data["title"],
        description=test_event_data["description"],
        start_at=test_event_data["start_at"],
        end_at=test_event_data["end_at"],
        location=test_event_data["location"],
        created_by_agent=test_event_data["created_by_agent"]
    )
    
    if "error" in create_result:
        print(f"❌ 이벤트 생성 실패: {create_result['error']}")
        return
    else:
        print(f"✅ 이벤트 생성 성공: {create_result.get('event_id', 'N/A')}")
        event_id = create_result.get('event_id')
    
    # 2. 이벤트 조회 테스트
    print("\n2️⃣ 이벤트 조회 테스트")
    get_result = await get_agent_event(event_id)
    
    if "error" in get_result:
        print(f"❌ 이벤트 조회 실패: {get_result['error']}")
    else:
        print(f"✅ 이벤트 조회 성공: {get_result.get('title', 'N/A')}")
    
    # 3. 이벤트 수정 테스트
    print("\n3️⃣ 이벤트 수정 테스트")
    update_result = await update_agent_event(
        event_id=event_id,
        title="수정된 테스트 이벤트",
        description="수정된 이벤트 설명입니다.",
        location="수정된 장소"
    )
    
    if "error" in update_result:
        print(f"❌ 이벤트 수정 실패: {update_result['error']}")
    else:
        print(f"✅ 이벤트 수정 성공: {update_result.get('title', 'N/A')}")
    
    # 4. 이벤트 삭제 테스트
    print("\n4️⃣ 이벤트 삭제 테스트")
    delete_result = await delete_agent_event(event_id)
    
    if "error" in delete_result:
        print(f"❌ 이벤트 삭제 실패: {delete_result['error']}")
    else:
        print(f"✅ 이벤트 삭제 성공: {delete_result.get('message', 'N/A')}")

async def main():
    """메인 테스트 함수"""
    print("🚀 Agent APIs 통합 테스트 시작")
    print("=" * 60)
    
    try:
        # Agent Task API 테스트
        await test_agent_task_apis()
        
        # Agent Event API 테스트
        await test_agent_event_apis()
        
        print("\n🎉 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # asyncio 이벤트 루프 실행
    asyncio.run(main()) 