from fastapi import APIRouter
from api.v1.routers import start_session, session_messages

router = APIRouter(prefix="/v1")
router.include_router(start_session.router)
router.include_router(session_messages.router)