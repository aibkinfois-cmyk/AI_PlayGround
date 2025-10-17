from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers.health import router as health_router
from app.routers.webhook import router as webhook_router
from app.routers.simulator import router as simulator_router
from app.providers.twilio_provider import router as twilio_router
from app.providers.vonage_provider import router as vonage_router
from app.providers.solapi_provider import router as solapi_router


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title="Call Orchestrator", version="0.1.0")
    
    # CORS 설정 - 외부 접속 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 모든 도메인 허용
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 라우터 등록
    app.include_router(health_router)
    app.include_router(webhook_router)
    app.include_router(simulator_router)
    app.include_router(twilio_router)
    app.include_router(vonage_router)
    app.include_router(solapi_router)
    
    # Static 파일 마운트 (HTML 시뮬레이터)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    return app


app = create_app()





