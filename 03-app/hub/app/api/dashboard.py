from datetime import datetime,timedelta
from typing import Annotated
from zoneinfo import ZoneInfo
from fastapi import APIRouter,Depends,Request
from sqlalchemy import select,func,text
from app.auth.dependencies import Database,Principal,require_roles
from app.db.models import AttendanceDay,AttendanceRequest,Company,Device,EventHandling,FaceProfile,Holiday,RecognitionEvent,Shift

router=APIRouter(prefix='/api/v1/dashboard',tags=['Dashboard'])
Reader=Annotated[Principal,Depends(require_roles('OWNER','HR'))]


@router.get('/today',operation_id='getDashboardToday')
async def today(session:Database,principal:Reader,request:Request)->dict:
    company=await session.get(Company,principal.account.company_id)
    zone=ZoneInfo(company.timezone);now=datetime.now(zone);day=now.date()
    beginning=datetime.combine(day,datetime.min.time(),zone);end=beginning+timedelta(days=1)
    present=late=not_arrived=0
    is_holiday=await session.scalar(select(Holiday.date).where(Holiday.company_id==company.id,Holiday.date==day)) is not None
    if not is_holiday:
        scheduled=(await session.execute(text('''
            SELECT e.id, (SELECT sa.shift_id FROM shift_assignment sa
              WHERE sa.company_id=e.company_id AND sa.weekday=:weekday
                AND sa.effective @> CAST(:day AS date)
                AND (sa.employee_id=e.id OR sa.department_id=e.department_id)
              ORDER BY (sa.employee_id IS NOT NULL) DESC LIMIT 1) AS shift_id
            FROM employee e WHERE e.company_id=:company AND e.status='ACTIVE'
        '''),{'weekday':day.isoweekday(),'day':day,'company':company.id})).all()
        days={row.employee_id:row for row in (await session.scalars(select(AttendanceDay).where(AttendanceDay.company_id==company.id,AttendanceDay.work_date==day))).all()}
        shifts={row.id:row for row in (await session.scalars(select(Shift).where(Shift.company_id==company.id))).all()}
        for employee_id,shift_id in scheduled:
            shift=shifts.get(shift_id);attendance=days.get(employee_id)
            if shift is None or attendance and attendance.status in ('HOLIDAY','LEAVE','OFF'):continue
            start=datetime.combine(day,shift.start_time,zone)
            check_in=attendance.check_in_at if attendance else None
            if check_in:
                present+=1
                late+=check_in>start+timedelta(minutes=shift.grace_in_min)
            elif now>=start:
                not_arrived+=1
    async def count(model,*conditions):
        return await session.scalar(select(func.count()).select_from(model).where(*conditions))
    strangers=await count(RecognitionEvent,RecognitionEvent.company_id==company.id,RecognitionEvent.result=='UNKNOWN',RecognitionEvent.occurred_at>=beginning,RecognitionEvent.occurred_at<end)
    open_alerts=await session.scalar(select(func.count()).select_from(RecognitionEvent).outerjoin(EventHandling,EventHandling.event_id==RecognitionEvent.id)
                                   .where(RecognitionEvent.company_id==company.id,RecognitionEvent.result.in_(('UNKNOWN','SPOOF')),EventHandling.event_id.is_(None)))
    devices=list((await session.scalars(select(Device.id).where(Device.company_id==company.id,Device.status=='ACTIVE'))).all())
    return {'date':day,'present':present,'late':late,'not_arrived':not_arrived,'strangers':strangers,
            'pending_face_profiles':await count(FaceProfile,FaceProfile.company_id==company.id,FaceProfile.status=='PENDING_REVIEW'),
            'pending_requests':await count(AttendanceRequest,AttendanceRequest.company_id==company.id,AttendanceRequest.status=='PENDING'),
            'open_alerts':open_alerts,'devices_offline':sum(id not in request.app.state.kiosk_connections for id in devices)}
