from app.errors import ApiError


async def reload_gallery(app,completed=None):
    runtime=getattr(app.state,'recognition',None)
    if runtime is None:
        raise ApiError(503,'RECOGNITION_UNAVAILABLE','Máy chủ tạm ngưng nhận dạng.')
    try:
        await app.state.kiosk_service.reload(completed=completed)
    except Exception:
        runtime.paused.set()
        raise ApiError(503,'RECOGNITION_UNAVAILABLE','Máy chủ tạm ngưng nhận dạng.') from None
