from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.api.auth import router as auth_router, me_router
from app.api.schemas import Health, Version
from app.config import get_settings
from app.db.session import Session
from app.errors import install_error_handlers

VERSION = '0.1.0'


def create_app() -> FastAPI:
    app = FastAPI(title='FaceGate Hub', version=VERSION)
    install_error_handlers(app)
    app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in get_settings().cors_origins.split(',') if origin.strip()],
                       allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'], allow_headers=['Authorization', 'Content-Type'])
    app.include_router(auth_router)
    app.include_router(me_router)
    # T03 chưa khởi tạo pipeline nhận dạng. T04 chỉ bật sau cổng kiểm + worker/gallery.
    app.state.model_verified = False
    app.state.gpu = False
    app.state.gallery_size = 0
    app.state.recognition_ready = False

    @app.get('/api/v1/health', tags=['System'], operation_id='getHealth')
    async def health() -> Health:
        try:
            async with Session() as session:
                db = await session.scalar(text('SELECT 1')) == 1
        except (SQLAlchemyError, OSError):
            db = False
        return Health(status='ok' if db and app.state.recognition_ready else 'degraded', db=db,
                      gpu=app.state.gpu, model_verified=app.state.model_verified, gallery_size=app.state.gallery_size, version=VERSION)

    @app.get('/api/v1/version', tags=['System'], operation_id='getVersion')
    def version() -> Version:
        return Version(version=VERSION, api='v1')

    return app


app = create_app()
