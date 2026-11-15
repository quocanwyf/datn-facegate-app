from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def install_error_handlers(app: FastAPI):
    @app.exception_handler(ApiError)
    async def api_error(request: Request, error: ApiError):
        return JSONResponse(status_code=error.status, content={'error': {'code': error.code, 'message': error.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # Không echo input: có thể chứa mật khẩu hoặc refresh token.
        status = 400 if request.url.path.endswith(('/auth/login', '/kiosk/pair', '/devices', '/kiosk/enroll/sessions')) else 422
        return JSONResponse(status_code=status, content={'error': {'code': 'VALIDATION_ERROR', 'message': 'Dữ liệu không hợp lệ.'}})

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        return JSONResponse(status_code=error.status_code, content={'error': {'code': f'HTTP_{error.status_code}', 'message': 'Không thể thực hiện yêu cầu.'}})

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, error: SQLAlchemyError):
        return JSONResponse(status_code=503, content={'error': {'code': 'SERVICE_UNAVAILABLE', 'message': 'Không thể kết nối cơ sở dữ liệu. Vui lòng thử lại.'}})

    @app.exception_handler(IntegrityError)
    async def integrity_error(request:Request,error:IntegrityError):
        cause=error.orig
        state=getattr(cause,'sqlstate',None) or getattr(getattr(cause,'__cause__',None),'sqlstate',None)
        duplicate=state=='23505'
        return JSONResponse(status_code=409 if duplicate else 422,content={'error':{'code':'CONFLICT' if duplicate else 'VALIDATION_ERROR',
                'message':'Dữ liệu bị trùng.' if duplicate else 'Dữ liệu vi phạm ràng buộc nghiệp vụ.'}})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        return JSONResponse(status_code=500, content={'error': {'code': 'INTERNAL_ERROR', 'message': 'Có lỗi xử lý. Vui lòng thử lại.'}})
