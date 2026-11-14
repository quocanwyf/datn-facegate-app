"""CSDL demo tương đương schema.sql v1.4.4, giữ nguyên CHECK/EXCLUDE/trigger."""
from pathlib import Path
from alembic import op

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Bản SQL cố định đi cùng revision, không đọc nguồn thiết kế có thể đổi về sau.
    sql = (Path(__file__).parent / '0001_schema.sql').read_text(encoding='utf-8')
    op.execute(sql)


def downgrade():
    tables = ('audit_log attendance_request attendance_day event_handling recognition_event '
              'holiday shift_assignment shift face_template face_embedding face_sample face_profile '
              'device gate_allowed_department gate threshold_profile recognition_model '
              'auth_refresh_token user_role user_account employee department company').split()
    op.execute('DROP TABLE ' + ', '.join(tables))
    for name in ('event_handling_check', 'recognition_event_guard', 'set_updated_at'):
        op.execute(f'DROP FUNCTION {name}()')
