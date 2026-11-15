"""Ca T05 trên dữ liệu ảnh thật đã tạo bởi review_t05.py; không seed dữ liệu mặt."""
import asyncio
import json
from pathlib import Path
import sys
import time
from uuid import UUID
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
import psycopg
from app.config import get_settings
from app.main import create_app
from kiosk_sim import jpeg_frame


def main():
    evidence=Path(sys.argv[1])
    source=json.loads((evidence/'private-inputs.json').read_text())
    url=get_settings().database_url.get_secret_value().replace('postgresql+asyncpg:','postgresql:')
    def query(statement,params=()):
        with psycopg.connect(url) as connection:
            cursor=connection.execute(statement,params)
            return cursor.fetchall() if cursor.description else []
    employee_id=query("SELECT id FROM employee WHERE code='NV006'")[0][0]
    old_active=query("SELECT id FROM face_profile WHERE employee_id=%s AND status='ACTIVE'",(employee_id,))[0][0]
    paths=sorted(Path(source['known_dir']).glob('*.jpg'))
    cache=[jpeg_frame(path,640,80) for path in paths]
    app=create_app()
    checks={}
    def emit(response):
        print(json.dumps(response,ensure_ascii=False),flush=True)
    with TestClient(app) as client:
        owner=client.post('/api/v1/auth/login',json={'email':'nv001@demo.local','password':'Demo@123'}).json()
        owner_headers={'Authorization':'Bearer '+owner['access_token']}
        gate_id=query("SELECT id FROM gate WHERE name='Cửa chính'")[0][0]
        invitation=client.post('/api/v1/devices',headers=owner_headers,json={'name':'T05 kiểm lỗi','gate_id':str(gate_id)}).json()
        paired=client.post('/api/v1/kiosk/pair',json={'code':invitation['pairing_code']}).json()
        token=paired['device_token'];headers={'Authorization':'Bearer '+token}
        opened=client.post('/api/v1/kiosk/enroll/sessions',headers=headers,json={'user_id':owner['user']['id'],'pin':'2468'})
        assert opened.status_code==201,opened.text
        session_id=opened.json()['enroll_session_id']
        consent_path='/api/v1/kiosk/enroll/sessions/'+session_id+'/consent'
        assert client.post(consent_path,headers=headers,json={'employee_id':str(employee_id),'agree':True}).status_code==200
        def capture(*,stop_accepted=None,same_image=False):
            result=[]
            with client.websocket_connect('/api/v1/ws/kiosk') as ws:
                ws.send_json({'type':'auth','device_token':token})
                assert ws.receive_json()['type']=='config'
                for seq,data in enumerate(([cache[5]]*3 if same_image else cache),1):
                    ws.send_json({'type':'frame','seq':seq,'mode':'enroll','enroll_session_id':session_id,'employee_id':str(employee_id)})
                    ws.send_bytes(data)
                    response=ws.receive_json();emit(response);result.append(response)
                    if response['type'] in ('enroll_done','error') or (stop_accepted and response.get('accepted')==stop_accepted):break
                    time.sleep(.25)
            return result
        first=capture()
        assert first[-1]['type']=='enroll_done'
        pending=first[-1]['profile_id']
        def pending_ids():
            return [str(row[0]) for row in query("SELECT id FROM face_profile WHERE employee_id=%s AND status='PENDING_REVIEW'",(employee_id,))]
        assert pending_ids()==[pending]
        duplicate=capture(same_image=True)
        assert any(message.get('reason')=='TOO_SIMILAR' for message in duplicate)
        assert pending_ids()==[pending]
        checks['too_similar_rejected_old_pending_preserved']=True
        partial=capture(stop_accepted=4)
        assert partial[-1].get('accepted')==4 and pending_ids()==[pending]
        checks['disconnect_after_four_preserves_old_pending']=True
        import app.biz.enrollment as enrollment
        original=enrollment.write_private
        def failed_write(*args):raise OSError('Injected write failure on real samples')
        enrollment.write_private=failed_write
        try:
            failed=capture()
        finally:
            enrollment.write_private=original
        assert failed[-1].get('code')=='OPERATION_INCOMPLETE' and pending_ids()==[pending]
        assert query('SELECT count(*) FROM face_sample WHERE profile_id=%s',(pending,))[0][0]==5
        checks['file_write_failure_preserves_old_pending_and_samples']=True
        replaced=capture()
        assert replaced[-1]['type']=='enroll_done' and replaced[-1]['profile_id']!=pending
        assert query('SELECT count(*) FROM face_profile WHERE id=%s',(pending,))[0][0]==0
        assert query("SELECT count(*) FROM face_profile WHERE id=%s AND status='ACTIVE'",(old_active,))[0][0]==1
        checks['new_five_replace_pending_keep_active']=True
        # SUSPENDED vẫn thuộc gallery nhưng không mở cửa hay ghi công.
        query("UPDATE employee SET status='SUSPENDED' WHERE id=%s",(employee_id,))
        asyncio.run_coroutine_threadsafe(app.state.kiosk_service.reload(),client.portal.call(asyncio.get_running_loop)).result(timeout=10)
        with client.websocket_connect('/api/v1/ws/kiosk') as ws:
            ws.send_json({'type':'auth','device_token':token});ws.receive_json()
            for seq,data in enumerate(cache,1):
                ws.send_json({'type':'frame','seq':seq,'mode':'recognize'});ws.send_bytes(data)
                response=ws.receive_json();emit(response)
                if response['type']=='result':break
                time.sleep(.25)
        assert response.get('reason')=='INACTIVE' and response['door']=='DENY'
        checks['suspended_denied_no_open']=True
        query("UPDATE employee SET status='ACTIVE' WHERE id=%s",(employee_id,))
        # Xóa lỗi vẫn thu hồi consent/quyền nhận dạng; retry hoàn tất được.
        import app.biz.face_data as face_data
        original_delete=face_data.delete_private
        def failed_delete(*args):raise OSError('Injected deletion failure')
        face_data.delete_private=failed_delete
        try:
            response=client.post(consent_path,headers=headers,json={'employee_id':str(employee_id),'agree':False})
        finally:
            face_data.delete_private=original_delete
        assert response.status_code==503 and response.json()['error']['code']=='BIOMETRIC_DELETE_INCOMPLETE',response.text
        assert query('SELECT face_consent_at,face_consent_by,attendance_method FROM employee WHERE id=%s',(employee_id,))==[(None,None,'MANUAL')]
        assert app.state.recognition.gallery.size==0
        checks['delete_failure_keeps_consent_revoked_no_gallery']=True
        response=client.post(consent_path,headers=headers,json={'employee_id':str(employee_id),'agree':False})
        assert response.status_code==200,response.text
        assert query('SELECT count(*) FROM face_profile WHERE employee_id=%s',(employee_id,))[0][0]==0
        checks['delete_retry_completes']=True
        assert query('SELECT count(*) FROM attendance_day')[0][0]==0
        checks['no_attendance_before_T09']=True
    (evidence/'resilience-summary.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2),flush=True)


if __name__=='__main__':main()
