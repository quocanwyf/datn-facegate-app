"""Nghiệm thu thật T05 trên DB mới + thư mục sinh trắc riêng ngoài repo."""
import argparse
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.config import ROOT,get_settings
from kiosk_sim import simulate


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--known-dir',required=True,type=Path)
    parser.add_argument('--unknown-dir',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--port',type=int,default=8001)
    args=parser.parse_args()
    report=args.output.resolve();report.mkdir(parents=True,exist_ok=True)
    base=make_url(get_settings().database_url.get_secret_value())
    stamp=datetime.now().strftime('%Y%m%d%H%M%S')
    database='facegate_t05_'+stamp
    private=Path(os.environ['LOCALAPPDATA'])/'FaceGate'/('T05-'+stamp)
    admin_password=(Path(os.environ['LOCALAPPDATA'])/'FaceGate/postgresql16/admin-password.txt').read_text().strip()
    admin_url=base.set(drivername='postgresql',username='postgres',password=admin_password,database='postgres').render_as_string(hide_password=False)
    with psycopg.connect(admin_url,autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(database),sql.Identifier(base.username)))
    url=base.set(database=database).render_as_string(hide_password=False)
    env=dict(os.environ,DATABASE_URL=url,HUB_DATA_DIR=str(private),INFER_DEVICE='cpu',PYTHONUTF8='1')
    for name,command in [('alembic',[sys.executable,'-m','alembic','upgrade','head']),('seed',[sys.executable,'scripts/seed.py'])]:
        process=subprocess.run(command,env=env,capture_output=True,text=True,encoding='utf-8')
        (report/(name+'.log')).write_text(process.stdout+process.stderr,encoding='utf-8')
        if process.returncode:raise RuntimeError(name+' thất bại')
    (report/'private-inputs.json').write_text(json.dumps({'database':database,'known_dir':str(args.known_dir),'unknown_dir':str(args.unknown_dir),'data_dir':str(private)},indent=2),encoding='utf-8')
    hub=f'http://127.0.0.1:{args.port}'
    server=None;server_log=None
    async def start():
        nonlocal server,server_log
        server_log=(report/'server.log').open('a',encoding='utf-8')
        server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(args.port),'--no-proxy-headers'],
                                env=env,stdout=server_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        deadline=time.monotonic()+180
        async with httpx.AsyncClient(timeout=2) as client:
            while time.monotonic()<deadline:
                if server.poll() is not None:raise RuntimeError('Hub đã dừng; xem server.log')
                try:
                    health=await client.get(hub+'/api/v1/health')
                    if health.status_code==200:
                        (report/'health.json').write_text(json.dumps(health.json(),indent=2),encoding='utf-8')
                        if not health.json()['model_verified']:raise RuntimeError('Model chưa xác minh')
                        return
                except httpx.TransportError:pass
                await asyncio.sleep(.25)
        raise TimeoutError('Không chờ được Hub')
    def stop():
        nonlocal server,server_log
        if server and server.poll() is None:
            server.terminate()
            server.wait(timeout=15)
        if server_log:server_log.close()
    messages=[]
    def emit(line):
        print(line,flush=True)
        messages.append(json.loads(line))
        with (report/'messages.jsonl').open('a',encoding='utf-8') as stream:stream.write(line+'\n')
    try:
        await start()
        async with httpx.AsyncClient(base_url=hub+'/api/v1',timeout=20) as client:
            response=await client.post('/auth/login',json={'email':'nv001@demo.local','password':'Demo@123'});response.raise_for_status()
            owner=response.json();client.headers['Authorization']='Bearer '+owner['access_token']
            # Dùng đúng cửa chấm công mặc định và ngưỡng từ seed, không điều chỉnh để đạt.
            with psycopg.connect(url.replace('postgresql+asyncpg:','postgresql:')) as connection:
                gate_id=connection.execute("SELECT id FROM gate WHERE name='Cửa chính'").fetchone()[0]
                reviewer=connection.execute("SELECT id FROM user_account WHERE email='nv002@demo.local'").fetchone()[0]
            invitation=await client.post('/devices',json={'gate_id':str(gate_id),'name':'Tablet kiểm thật T05'});invitation.raise_for_status()
            paired=await client.post('/kiosk/pair',json={'code':invitation.json()['pairing_code']});paired.raise_for_status()
            token=paired.json()['device_token'];client.headers['Authorization']='Bearer '+token
            empty=await simulate(hub,token,args.known_dir,emit=emit)
            assert empty and all(message.get('state')=='NO_GALLERY' for message in empty)
            opened=await client.post('/kiosk/enroll/sessions',json={'user_id':owner['user']['id'],'pin':'2468'});opened.raise_for_status()
            enrollment=opened.json()['enroll_session_id']
            employees=await client.get('/kiosk/enroll/sessions/'+enrollment+'/employees',params={'q':'NV006'});employees.raise_for_status()
            employee=next(item for item in employees.json() if item['code']=='NV006')
            consent=await client.post('/kiosk/enroll/sessions/'+enrollment+'/consent',json={'employee_id':employee['id'],'agree':True});consent.raise_for_status()
            enrolled=await simulate(hub,token,args.known_dir,mode='enroll',enrollment=enrollment,employee_id=employee['id'],emit=emit)
            assert enrolled[-1].get('type')=='enroll_done','Chưa thu đủ 5 mẫu thật; không thay bằng mẫu giả'
            profile=enrolled[-1]['profile_id']
        with psycopg.connect(url.replace('postgresql+asyncpg:','postgresql:')) as connection:
            count=connection.execute('SELECT count(*) FROM face_sample WHERE profile_id=%s',(profile,)).fetchone()[0]
            assert count==5
            assert connection.execute('SELECT count(*) FROM recognition_event').fetchone()[0]==0
            connection.execute("UPDATE face_profile SET status='ACTIVE',reviewed_by_user_id=%s,reviewed_at=now() WHERE id=%s AND status='PENDING_REVIEW'",(reviewer,profile))
        print('Duyệt tay DB theo T05; khởi động lại Hub để nạp gallery đã duyệt.',flush=True)
        stop();await start()
        known=await simulate(hub,token,args.known_dir,repeat=2,emit=emit)
        assert any(message.get('result')=='OK' for message in known),'Ảnh đã đăng ký chưa ra OK'
        assert any(message.get('result')=='ALREADY' for message in known),'Chưa có bằng chứng cooldown thật'
        unknown=await simulate(hub,token,args.unknown_dir,repeat=2,emit=emit)
        assert any(message.get('reason')=='UNKNOWN' for message in unknown),'Ảnh người khác chưa ra DENY/UNKNOWN'
        assert not any(message.get('result') in ('OK','ALREADY') for message in unknown),'Có ảnh người khác được cho qua; giữ log, không nới ngưỡng'
        with psycopg.connect(url.replace('postgresql+asyncpg:','postgresql:')) as connection:
            connection.row_factory=psycopg.rows.dict_row
            events=connection.execute('SELECT result,model_id,top1_score,threshold_used,threshold_level,n_frames,snapshot_path IS NOT NULL AS has_snapshot FROM recognition_event ORDER BY occurred_at').fetchall()
            assert any(event['result']=='MATCH' for event in events)
            assert sum(event['result']=='MATCH' for event in events)==1,'Cooldown đã tạo MATCH trùng'
            assert all(not event['has_snapshot'] for event in events if event['result']=='MATCH')
            (report/'events.json').write_text(json.dumps(events,default=str,indent=2),encoding='utf-8')
        (report/'summary.json').write_text(json.dumps({'real_enrollment_samples':5,'no_gallery_frames':len(empty),
            'known_ok':sum(m.get('result')=='OK' for m in known),'known_already':sum(m.get('result')=='ALREADY' for m in known),
            'unknown_denied':sum(m.get('reason')=='UNKNOWN' for m in unknown),'events':len(events),'all_checks_passed':True},indent=2),encoding='utf-8')
    finally:
        stop()


if __name__=='__main__':
    asyncio.run(main())
