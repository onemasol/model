from fastapi import APIRouter

router = APIRouter(prefix="/input", tags=["agent"])
# 예: @router.get("/logs") 같은 테스트용 출력 라우터를 둘 수 있습니다.