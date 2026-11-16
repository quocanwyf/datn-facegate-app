import asyncio
from sqlalchemy import func, select
from app.db.models import EventHandling, FaceProfile, AttendanceRequest, RecognitionEvent


class MonitorHub:
    """Chỉ xếp ID sau commit; quyền và dữ liệu được đọc lại trước khi gửi."""
    def __init__(self, factory):
        self.factory = factory
        self.queues = set()

    def subscribe(self):
        queue = asyncio.Queue(maxsize=128)
        self.queues.add(queue)
        return queue

    def publish(self, kind, identity):
        for queue in tuple(self.queues):
            try:
                queue.put_nowait((kind, identity))
            except asyncio.QueueFull:
                # Client chậm phải nối lại và lấy REST bù; không giữ ảnh/payload
                # trong bộ nhớ và không làm chậm transaction của client khác.
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait(('overflow', None))
            except RuntimeError:
                self.queues.discard(queue)  # Vòng lặp của client đã đóng.

    async def counters(self, session, company_id):
        async def count(model, *where):
            return await session.scalar(select(func.count()).select_from(model).where(*where))
        handled = select(EventHandling.event_id).where(EventHandling.event_id == RecognitionEvent.id).exists()
        return dict(open_alerts=await count(RecognitionEvent, RecognitionEvent.company_id == company_id,
                    RecognitionEvent.result.in_(('UNKNOWN', 'SPOOF')), ~handled),
            pending_face_profiles=await count(FaceProfile, FaceProfile.company_id == company_id, FaceProfile.status == 'PENDING_REVIEW'),
            pending_requests=await count(AttendanceRequest, AttendanceRequest.company_id == company_id, AttendanceRequest.status == 'PENDING'))
