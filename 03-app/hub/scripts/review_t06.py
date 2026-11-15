"""Nghiệm thu quản trị sinh trắc bằng ảnh thật trên DB mới, không seed khuôn mặt."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.config import ROOT,get_settings
from kiosk_sim import jpeg_frame


def main():
    report=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else ROOT/'03-app/ket-qua-kiem-thu/2026-11-15_T06/real-run'
    report.mkdir(parents=True,exist_ok=True)
    base=make_url(get_settings().database_url.get_secret_value());stamp=datetime.now().strftime('%Y%m%d%H%M%S')
    database='facegate_t06_'+stamp
    private=Path(os.environ['LOCALAPPDATA'])/'FaceGate'/('T06-'+stamp)
    password=(Path(os.environ['LOCALAPPDATA'])/'FaceGate/postgresql16/admin-password.txt').read_text().strip()
    admin=base.set(drivername='postgresql',database='postgres',username='postgres',password=password).render_as_string(hide_password=False)
    with psycopg.connect(admin,autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(database),sql.Identifier(base.username)))
    url=base.set(database=database).render_as_string(hide_password=False)
    os.environ.update(DATABASE_URL=url,HUB_DATA_DIR=str(private),INFER_DEVICE='cpu',PYTHONUTF8='1')
    get_settings.cache_clear()
    for name,command in [('alembic',[sys.executable,'-m','alembic','upgrade','head']),('seed',[sys.executable,'scripts/seed.py'])]:
        result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8')
        (report/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(name+' thất bại')
    (report/'private-inputs.json').write_text(json.dumps({'database':database,'data_dir':str(private),'known_dir':str(Path(sys.argv[1]))},indent=2),encoding='utf-8')
    def query(statement,params=()):
        with psycopg.connect(url.replace('postgresql+asyncpg:','postgresql:')) as connection:
            cursor=connection.execute(statement,params)
            return cursor.fetchall() if cursor.description else []
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.biz.files import data_path
    app=create_app();checks={}
    cache=[jpeg_frame(path,640,80) for path in sorted(Path(sys.argv[1]).glob('*.jpg'))]
    with TestClient(app) as client:
        logins={}
        for role,number in [('OWNER',1),('HR',2),('EMPLOYEE',8)]:
            response=client.post('/api/v1/auth/login',json={'email':f'nv{number:03}@demo.local','password':'Demo@123'})
            assert response.status_code==200
            logins[role]=response.json()
        credentials={role:{'Authorization':'Bearer '+pair['access_token']} for role,pair in logins.items()}
        gate_id=query("SELECT id FROM gate WHERE name='Cửa chính'")[0][0]
        invitation=client.post('/api/v1/devices',headers=credentials['OWNER'],json={'gate_id':str(gate_id),'name':'T06 ảnh thật'}).json()
        paired=client.post('/api/v1/kiosk/pair',json={'code':invitation['pairing_code']}).json()
        token=paired['device_token'];device_headers={'Authorization':'Bearer '+token}
        def enroll(code):
            opened=client.post('/api/v1/kiosk/enroll/sessions',headers=device_headers,json={'user_id':logins['OWNER']['user']['id'],'pin':'2468'})
            assert opened.status_code==201
            id=opened.json()['enroll_session_id']
            employee=next(item for item in client.get('/api/v1/kiosk/enroll/sessions/'+id+'/employees',headers=device_headers,params={'q':code}).json() if item['code']==code)
            response=client.post('/api/v1/kiosk/enroll/sessions/'+id+'/consent',headers=device_headers,json={'employee_id':employee['id'],'agree':True})
            assert response.status_code==200
            with client.websocket_connect('/api/v1/ws/kiosk') as ws:
                ws.send_json({'type':'auth','device_token':token});assert ws.receive_json()['type']=='config'
                for seq,data in enumerate(cache,1):
                    ws.send_json({'type':'frame','seq':seq,'mode':'enroll','enroll_session_id':id,'employee_id':employee['id']});ws.send_bytes(data)
                    response=ws.receive_json();print(json.dumps(response,ensure_ascii=False),flush=True)
                    if response['type']=='enroll_done':return employee['id'],response['profile_id']
                    assert response['type']!='error',response
                    time.sleep(.25)
            raise AssertionError('Chưa có đủ 5 mẫu thật')
        employee_id,profile=enroll('NV006')
        view=client.get('/api/v1/face-profiles/'+profile,headers=credentials['HR'])
        assert view.status_code==200 and len(view.json()['samples'])==5
        from PIL import Image
        from io import BytesIO
        for sample in view.json()['samples']:
            for role in ('OWNER','HR'):
                image=client.get(sample['image_url'],headers=credentials[role])
                assert image.status_code==200 and Image.open(BytesIO(image.content)).size==(112,112)
        checks['owner_hr_read_five_authorized_samples']=True
        def approve(role):return role,client.post('/api/v1/face-profiles/'+profile+'/approve',headers=credentials[role],json={}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(approve,['OWNER','HR']))
        assert sorted(status for _,status in results)==[200,409],results
        assert app.state.recognition.gallery.size==1
        checks['concurrent_approval_one_success_one_409']=results
        winner=next(role for role,status in results if status==200)
        other='HR' if winner=='OWNER' else 'OWNER'
        _,pending=enroll('NV006')
        rejected=client.post('/api/v1/face-profiles/'+pending+'/reject',headers=credentials[other],json={'note':'Kiểm từ chối bộ đăng ký lại'})
        assert rejected.status_code==200 and rejected.json()['status']=='REJECTED'
        assert app.state.recognition.gallery.size==1
        checks['owner_hr_both_review_and_reject_keeps_active']=True
        # Tái hiện race bằng MATCH từ ảnh thật; giữ trước INSERT bằng advisory lock.
        # Không tạo event giả: frame vẫn đi qua detector/backbone/quyết định thật.
        from sqlalchemy import event,text
        from sqlalchemy.orm import Session as SyncSession
        from app.db.models import RecognitionEvent
        from threading import Event
        waiting=Event();key=96062026
        controller=psycopg.connect(url.replace('postgresql+asyncpg:','postgresql:'),autocommit=True)
        controller.execute('SELECT pg_advisory_lock(%s)',(key,))
        def hold_match(session,context,instances):
            if any(isinstance(row,RecognitionEvent) for row in session.new):
                waiting.set()
                session.connection().execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':key})
        event.listen(SyncSession,'before_flush',hold_match)
        def recognize():
            with client.websocket_connect('/api/v1/ws/kiosk') as ws:
                ws.send_json({'type':'auth','device_token':token});ws.receive_json()
                for seq in range(1,5):
                    ws.send_json({'type':'frame','seq':seq,'mode':'recognize'});ws.send_bytes(cache[5])
                    response=ws.receive_json()
                    if response['type']=='result':return response
                    time.sleep(.25)
            raise AssertionError('Chưa có MATCH thật cho ca concurrent')
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                recognition=pool.submit(recognize)
                try:
                    assert waiting.wait(15),'Chưa tới bước commit event'
                    mutation=pool.submit(lambda:client.post('/api/v1/employees/'+employee_id+'/suspend',headers=credentials['OWNER']))
                    deadline=time.monotonic()+5
                    while time.monotonic()<deadline:
                        blocked=query("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock'")[0][0]
                        if blocked>=2:break
                        time.sleep(.05)
                    assert blocked>=2 and not mutation.done(),'Khóa nhân viên phải đợi event commit'
                finally:
                    controller.execute('SELECT pg_advisory_unlock(%s)',(key,))
                assert recognition.result(timeout=15)['result']=='OK'
                assert mutation.result(timeout=15).status_code==200
        finally:
            controller.execute('SELECT pg_advisory_unlock(%s)',(key,));controller.close()
            event.remove(SyncSession,'before_flush',hold_match)
        assert query("SELECT count(*) FROM recognition_event WHERE result='MATCH'")[0][0]==1
        assert client.post('/api/v1/employees/'+employee_id+'/reactivate',headers=credentials['OWNER']).status_code==200
        checks['concurrent_suspend_waits_for_real_match_commit']=True
        import app.biz.face_data as face_data
        original=face_data.delete_private
        def failed_delete(*args):raise OSError('Injected deletion failure on real files')
        face_data.delete_private=failed_delete
        try:failed=client.delete('/api/v1/employees/'+employee_id+'/face',headers=credentials['OWNER'])
        finally:face_data.delete_private=original
        assert failed.status_code==503 and failed.json()['error']['code']=='BIOMETRIC_DELETE_INCOMPLETE'
        assert query('SELECT face_consent_at,attendance_method FROM employee WHERE id=%s',(employee_id,))==[(None,'MANUAL')]
        assert app.state.recognition.gallery.size==0
        checks['administrative_delete_failure_keeps_consent_revoked']=True
        paths=query('SELECT fs.image_path FROM face_sample fs JOIN face_profile fp ON fp.id=fs.profile_id WHERE fp.employee_id=%s',(employee_id,))
        removed=client.delete('/api/v1/employees/'+employee_id+'/face',headers=credentials['OWNER'])
        assert removed.status_code==204 and not removed.content
        assert not any(data_path(path).exists() for path, in paths)
        assert query('SELECT count(*) FROM face_profile WHERE employee_id=%s',(employee_id,))[0][0]==0
        checks['delete_retry_removes_files_rows_gallery_and_audits']=bool(query("SELECT id FROM audit_log WHERE action='FACE_DELETE' AND entity_id=%s",(employee_id,)))
        employee_id,profile=enroll('NV007')
        assert client.post('/api/v1/face-profiles/'+profile+'/approve',headers=credentials['HR'],json={}).status_code==200
        _,pending=enroll('NV007')
        original_reload=app.state.kiosk_service.reload
        async def failed_reload(completed=None):raise OSError('Injected gallery reload failure')
        app.state.kiosk_service.reload=failed_reload
        try:failed=client.post('/api/v1/face-profiles/'+pending+'/approve',headers=credentials['OWNER'],json={})
        finally:app.state.kiosk_service.reload=original_reload
        assert failed.status_code==503 and failed.json()['error']['code']=='RECOGNITION_UNAVAILABLE'
        assert not app.state.recognition.ready
        recovered=client.post('/api/v1/face-profiles/'+pending+'/approve',headers=credentials['OWNER'],json={})
        assert recovered.status_code==409 and app.state.recognition.ready
        checks['gallery_failure_pauses_and_processed_retry_recovers']=True
        paths=query('SELECT fs.image_path FROM face_sample fs JOIN face_profile fp ON fp.id=fs.profile_id WHERE fp.employee_id=%s',(employee_id,))
        assert app.state.recognition.gallery.size==1
        terminated=client.post('/api/v1/employees/'+employee_id+'/terminate',headers=credentials['HR'])
        assert terminated.status_code==200 and terminated.json()['status']=='TERMINATED'
        assert not any(data_path(path).exists() for path, in paths)
        assert app.state.recognition.gallery.size==0
        assert query('SELECT count(*) FROM face_profile WHERE employee_id=%s',(employee_id,))[0][0]==0
        checks['terminate_removes_files_rows_gallery_and_audits']=bool(query("SELECT id FROM audit_log WHERE action='EMPLOYEE_TERMINATE' AND entity_id=%s",(employee_id,)))
        employee_id,profile=enroll('NV008')
        assert client.post('/api/v1/face-profiles/'+profile+'/approve',headers=credentials['OWNER'],json={}).status_code==200
        own=client.post('/api/v1/me/face/revoke',headers=credentials['EMPLOYEE'])
        assert own.status_code==200 and own.json()['attendance_method']=='MANUAL' and own.json()['face_consent_at'] is None
        assert app.state.recognition.gallery.size==0
        checks['employee_withdraws_only_own_biometrics']=True
    (report/'summary.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
