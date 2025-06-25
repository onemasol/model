from fastapi import FastAPI
from api.v1.router import router as v1_router

app = FastAPI(title="OneMaSol Agent API")
app.include_router(v1_router)