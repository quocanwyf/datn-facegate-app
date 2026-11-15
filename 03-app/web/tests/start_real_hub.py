"""Hub nghiệm thu T07: DB mới, seed hợp lệ, ảnh thật chỉ ở thư mục riêng ngoài Git."""
from datetime import datetime
import gc,json,os,subprocess,sys,time
from threading import Event,Lock,Thread
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HUB=ROOT/'03-app/hub';os.chdir(HUB);sys.path[:0]=[str(HUB),str(HUB/'scripts')]
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.config import get_settings
stamp=datetime.now().strftime('%Y%m%d%H%M%S');database='facegate_t07_'+stamp
report=ROOT/'03-app/ket-qua-kiem-thu/2026-11-15_T07';report.mkdir(parents=True,exist_ok=True)
base=make_url(get_settings().database_url.get_secret_value())
password=(Path(os.environ['LOCALAPPDATA'])/'FaceGate/postgresql16/admin-password.txt').read_text().strip()
admin=base.set(drivername='postgresql',database='postgres',username='postgres',password=password).render_as_string(hide_password=False)
with psycopg.connect(admin,autocommit=True) as connection:connection.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(database),sql.Identifier(base.username)))
private=Path(os.environ['LOCALAPPDATA'])/'FaceGate'/('T07-'+stamp)
os.environ.update(DATABASE_URL=base.set(database=database).render_as_string(hide_password=False),HUB_DATA_DIR=str(private),HUB_PUBLIC_URL='http://10.0.2.2:8007',PYTHONUTF8='1')
get_settings.cache_clear()
for name,command in [('alembic',[sys.executable,'-m','alembic','upgrade','head']),('seed',[sys.executable,'scripts/seed.py'])]:
    result=subprocess.run(command,capture_output=True,text=True,encoding='utf8');(report/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf8')
    if result.returncode:raise RuntimeError(name+' thất bại')
from fastapi.testclient import TestClient
from app.main import create_app
from kiosk_sim import jpeg_frame
with TestClient(create_app()) as client:
    pair=client.post('/api/v1/auth/login',json={'email':'nv001@demo.local','password':'Demo@123'}).json()
    headers={'Authorization':'Bearer '+pair['access_token']}
    gate=client.get('/api/v1/gates',headers=headers).json()[0]
    invitation=client.post('/api/v1/devices',headers=headers,json={'gate_id':gate['id'],'name':'T07 ảnh thật'}).json()
    token=client.post('/api/v1/kiosk/pair',json={'code':invitation['pairing_code']}).json()['device_token'];device_headers={'Authorization':'Bearer '+token}
    session=client.post('/api/v1/kiosk/enroll/sessions',headers=device_headers,json={'user_id':pair['user']['id'],'pin':'2468'}).json()['enroll_session_id']
    employee=next(item for item in client.get(f'/api/v1/kiosk/enroll/sessions/{session}/employees',headers=device_headers,params={'q':'NV006'}).json() if item['code']=='NV006')
    client.post(f'/api/v1/kiosk/enroll/sessions/{session}/consent',headers=device_headers,json={'employee_id':employee['id'],'agree':True}).raise_for_status()
    cache=[jpeg_frame(path,640,80) for path in sorted(Path(sys.argv[1]).glob('*.jpg'))]
    with client.websocket_connect('/api/v1/ws/kiosk') as ws:
        ws.send_json({'type':'auth','device_token':token});ws.receive_json()
        stopped=Event();send_lock=Lock()
        def heartbeat():
            while not stopped.wait(3):
                try:
                    with send_lock:ws.send_json({'type':'ping'})
                except Exception:return
        ping_thread=Thread(target=heartbeat,daemon=True);ping_thread.start()
        try:
            for seq,data in enumerate(cache,1):
                with send_lock:
                    ws.send_json({'type':'frame','seq':seq,'mode':'enroll','enroll_session_id':session,'employee_id':employee['id']});ws.send_bytes(data)
                while True:
                    response=ws.receive_json()
                    if response['type']!='pong':break
                print(json.dumps(response,ensure_ascii=False),flush=True)
                if response['type']=='enroll_done':break
                assert response['type']!='error',response
                time.sleep(.25)
            else:raise RuntimeError('Chưa đủ 5 mẫu thật')
        finally:stopped.set();ping_thread.join(timeout=2)
    (report/'private-inputs.json').write_text(json.dumps({'database':database,'data_dir':str(private),'employee_id':employee['id'],'profile_id':response['profile_id']},indent=2),encoding='utf8')
    from app.db.session import engine
    client.portal.call(engine.dispose)
del client,ws
gc.collect()
print('T07_READY port=8007 database='+database,flush=True)
import uvicorn
uvicorn.run(create_app(),host='127.0.0.1',port=8007,proxy_headers=False)
