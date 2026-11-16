"""Lập lịch theo thời điểm đóng ca; quét bù khi Hub khởi động lại."""
from datetime import timedelta
import logging
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import func, select
from app.auth.security import utcnow
from app.biz.attendance import DayRules, assigned_shift, bounds, finalize_day, recompute_day
from app.db.models import AttendanceDay, Company, Employee, ShiftAssignment

logger = logging.getLogger(__name__)


class AttendanceScheduler:
    def __init__(self, factory):
        self.factory = factory
        self.scheduler = AsyncIOScheduler(timezone='UTC')
        self.backfill_pending = True

    async def close_day(self, employee_id, work_date):
        async with self.factory() as session, session.begin():
            await finalize_day(session, employee_id, work_date)

    async def reconcile(self, backfill=False):
        now = utcnow()
        async with self.factory() as session:
            identities = list((await session.scalars(select(Employee.id).where(Employee.status == 'ACTIVE'))).all())
        for identity in identities:
            async with self.factory() as session, session.begin():
                employee = await session.get(Employee, identity)
                company = await session.get(Company, employee.company_id)
                today = now.astimezone(ZoneInfo(company.timezone)).date()
                begin = today - timedelta(days=1)
                if backfill:
                    earliest = await session.scalar(select(func.min(ShiftAssignment.effective_from)).where(
                        ShiftAssignment.company_id == company.id,
                        (ShiftAssignment.employee_id == employee.id) | (ShiftAssignment.department_id == employee.department_id)))
                    if earliest:
                        begin = min(begin, max(earliest, employee.joined_at) if employee.joined_at else earliest)
                stale = (await session.scalars(select(AttendanceDay.work_date).where(AttendanceDay.employee_id == identity,
                    AttendanceDay.finalized.is_(False), AttendanceDay.work_date < begin))).all()
                dates = set(stale)
                cursor = begin
                while cursor <= today:
                    dates.add(cursor)
                    cursor += timedelta(days=1)
                for work_date in sorted(dates):
                    await recompute_day(session, identity, work_date, now=now)
                for work_date in (today, today + timedelta(days=1)):
                    shift = await assigned_shift(session, employee, work_date)
                    if shift:
                        close = bounds(shift, work_date, company.timezone, DayRules.from_settings(company.settings))[3]
                        key = f'attendance/{identity}/{work_date}'
                        if close > now:
                            self.scheduler.add_job(self.close_day, 'date', run_date=close, id=key,
                                args=[identity, work_date], replace_existing=True, misfire_grace_time=None)

    async def refresh(self):
        try:
            await self.reconcile(backfill=self.backfill_pending)
            self.backfill_pending = False
        except Exception as error:
            logger.warning('Chưa đồng bộ được lịch chấm công (%s); sẽ thử lại.', type(error).__name__)

    async def start(self):
        self.scheduler.start()
        self.scheduler.add_job(self.refresh, 'interval', minutes=1, id='attendance-refresh',
                               next_run_time=utcnow(), coalesce=True, max_instances=1, misfire_grace_time=None)

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
