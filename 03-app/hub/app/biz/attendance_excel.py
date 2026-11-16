from io import BytesIO
import json
from zoneinfo import ZoneInfo
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from sqlalchemy import select
from app.biz.attendance_views import WORK_STATUSES, month_bounds
from app.config import ROOT
from app.db.models import AttendanceDay, AttendanceRequest, Company, Department, Shift

TOTAL_COLUMNS = ['Mã NV', 'Họ tên', 'Phòng ban', 'Ngày công', 'Số lần muộn', 'Tổng phút muộn',
                 'Tổng phút về sớm', 'Số ngày vắng', 'Số ngày thiếu giờ ra', 'Số ngày nghỉ phép']
DETAIL_COLUMNS = ['Mã NV', 'Họ tên', 'Ngày', 'Ca', 'Giờ vào', 'Giờ ra', 'Trạng thái', 'Nguồn',
                  'Phút muộn', 'Phút về sớm', 'Ghi chú']


def safe(value):
    # Dữ liệu người dùng luôn là văn bản, không trở thành công thức Excel.
    return "'" + value if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')) else value


async def export_month(session, employees, month):
    begin, end = month_bounds(month)
    workbook = Workbook()
    total = workbook.active
    total.title = 'Tổng hợp'
    detail = workbook.create_sheet('Chi tiết')
    total.append(TOTAL_COLUMNS)
    detail.append(DETAIL_COLUMNS)
    labels = json.loads((ROOT / '03-app/ui/tokens/status.json').read_text(encoding='utf8'))['enums']['attendance_day.status']
    for employee in employees:
        company = await session.get(Company, employee.company_id)
        tz = ZoneInfo(company.timezone)
        department = await session.get(Department, employee.department_id)
        rows = (await session.scalars(select(AttendanceDay).where(AttendanceDay.employee_id == employee.id,
            AttendanceDay.work_date >= begin, AttendanceDay.work_date <= end).order_by(AttendanceDay.work_date))).all()
        unique = list({(row.employee_id, row.work_date): row for row in rows}.values())
        total.append([safe(employee.code), safe(employee.full_name), safe(department.name),
            sum(row.status in WORK_STATUSES for row in unique), sum(row.late_min > 0 or row.status in ('LATE', 'LATE_EARLY') for row in unique),
            sum(row.late_min for row in unique), sum(row.early_min for row in unique),
            sum(row.status == 'ABSENT' for row in unique), sum(row.status == 'MISSING_OUT' for row in unique),
            sum(row.status == 'LEAVE' for row in unique)])
        for row in unique:
            shift = await session.get(Shift, row.shift_id) if row.shift_id else None
            note = row.edit_reason
            if row.source == 'ADJUSTED':
                request = await session.scalar(select(AttendanceRequest).where(AttendanceRequest.employee_id == employee.id,
                    AttendanceRequest.work_date == row.work_date, AttendanceRequest.status == 'APPROVED')
                    .order_by(AttendanceRequest.reviewed_at.desc()).limit(1))
                note = request.reason if request else note
            label = labels[row.status]
            detail.append([safe(employee.code), safe(employee.full_name), row.work_date, safe(shift.name) if shift else None,
                row.check_in_at.astimezone(tz).time().replace(tzinfo=None) if row.check_in_at else None,
                row.check_out_at.astimezone(tz).time().replace(tzinfo=None) if row.check_out_at else None,
                label['label_vi'] if isinstance(label, dict) else label, row.source, row.late_min, row.early_min, safe(note)])
            detail.cell(detail.max_row, 3).number_format = 'dd/mm/yyyy'
            for column in (5, 6):
                detail.cell(detail.max_row, column).number_format = 'hh:mm'
    for sheet in workbook:
        sheet.freeze_panes = 'A2'
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='1C1C19')
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = min(48, max(16, len(str(column[0].value)) + 3))
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
