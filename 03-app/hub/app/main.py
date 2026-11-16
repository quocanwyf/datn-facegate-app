from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.api.auth import router as auth_router, me_router
from app.api.schemas import Health, Version
from app.api.devices import router as devices_router
from app.auth.pairing import PairingAttempts
from app.api.kiosk import router as kiosk_router
from app.biz.enroll_sessions import EnrollSessions
from app.api.ws_kiosk import router as ws_router
from app.api.organization import router as organization_router
from app.api.employees import router as employees_router
from app.api.faces import router as faces_router
from app.api.gates import router as gates_router
from app.api.settings import router as settings_router
from app.api.dashboard import router as dashboard_router
from app.api.contract import install_contract_docs
from app.api.schedule import router as schedule_router
from app.api.attendance import router as attendance_router
from app.config import get_settings
from app.db.session import Session
from app.errors import install_error_handlers

VERSION = '0.1.0'


def create_app(*, attendance_factory=Session) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        runtime = None
        from app.biz.attendance_scheduler import AttendanceScheduler
        scheduler = AttendanceScheduler(attendance_factory) if attendance_factory else None
        if app.state.kiosk_service is None:
            from app.recog.runtime import RecognitionRuntime
            from app.biz.kiosk_service import KioskService
            runtime = RecognitionRuntime()
            app.state.recognition = runtime
            await asyncio.wrap_future(runtime.worker.ready)
            app.state.kiosk_service = KioskService(app,runtime)
        try:
            if scheduler:
                await scheduler.start()
            yield
        finally:
            if scheduler:
                scheduler.stop()
            if runtime:
                await asyncio.to_thread(runtime.close)
    app = FastAPI(title='FaceGate Hub', version=VERSION, lifespan=lifespan)
    install_error_handlers(app)
    app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in get_settings().cors_origins.split(',') if origin.strip()],
                       allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'], allow_headers=['Authorization', 'Content-Type'])
    app.include_router(auth_router)
    app.include_router(me_router)
    app.include_router(devices_router)
    app.include_router(kiosk_router)
    app.include_router(ws_router)
    for router in (organization_router,employees_router,faces_router,gates_router,settings_router,dashboard_router,schedule_router,attendance_router):
        app.include_router(router)
    app.state.pairing_attempts = PairingAttempts()
    app.state.kiosk_connections = {}
    app.state.enroll_sessions = EnrollSessions()
    app.state.kiosk_service = None
    app.state.recognition = None
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
        runtime = app.state.recognition
        ready = runtime.ready if runtime else app.state.recognition_ready
        return Health(status='ok' if db and ready else 'degraded', db=db,
                      gpu=runtime.device.type == 'cuda' if runtime and runtime.model_verified else False,
                      model_verified=runtime.model_verified if runtime else False,
                      gallery_size=runtime.gallery.size if runtime and runtime.gallery else 0, version=VERSION)

    @app.get('/api/v1/version', tags=['System'], operation_id='getVersion')
    def version() -> Version:
        return Version(version=VERSION, api='v1')

    install_contract_docs(app)
    return app


app = create_app()
