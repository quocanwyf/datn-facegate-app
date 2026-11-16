"""Kiosk giả lập từ ảnh thật ngoài repo, không ghi ảnh/vector/token vào log."""
import argparse
import asyncio
import getpass
import json
import os
from pathlib import Path
import time
import cv2
import httpx
import numpy as np
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from websockets.asyncio.client import connect

register_heif_opener(thumbnails=False)
EXTENSIONS = {'.jpg','.jpeg','.png','.heic','.heif','.webp'}


def jpeg_frame(path, long_side, quality):
    with Image.open(path) as source:
        rgb = np.asarray(ImageOps.exif_transpose(source).convert('RGB'))
    image = cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
    scale = min(1,long_side / max(image.shape[:2]))
    if scale < 1:
        image = cv2.resize(image,(round(image.shape[1]*scale),round(image.shape[0]*scale)),interpolation=cv2.INTER_AREA)
    ok,data = cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,quality])
    if not ok:
        raise RuntimeError('Không mã hóa được ảnh thử')
    return data.tobytes()


async def simulate(hub, token, images, *, mode='recognize', enrollment=None, employee_id=None, repeat=1, limit=None, emit=print, observe=None):
    url = hub.rstrip('/').replace('https://','wss://').replace('http://','ws://') + '/api/v1/ws/kiosk'
    paths = sorted(path for path in Path(images).iterdir() if path.suffix.lower() in EXTENSIONS)
    if not paths:
        raise ValueError('Thư mục không có ảnh thật được hỗ trợ')
    messages, seq, last_sent = [], 0, 0.0
    async with connect(url,max_size=None) as socket:
        await socket.send(json.dumps({'type':'auth','device_token':token,'app_version':'kiosk-sim-0.1'}))
        config = json.loads(await socket.recv())
        emit(json.dumps(config,ensure_ascii=False))
        if config.get('type') != 'config':
            raise RuntimeError('Kiosk chưa xác thực được')
        # Ảnh điện thoại HEIF cần giải mã trước; không giả làm camera với nhịp decode chậm.
        # Chỉ giữ JPEG trong RAM, không lưu lại khung hình. Ping trong khi chuẩn bị.
        cache={}
        last_ping=time.monotonic()
        for path in paths:
            cache[path]=await asyncio.to_thread(jpeg_frame,path,config['frame_long_side'],config['jpeg_quality'])
            if time.monotonic()-last_ping > 8:
                await socket.send(json.dumps({'type':'ping'}))
                pong=json.loads(await socket.recv());emit(json.dumps(pong,ensure_ascii=False))
                last_ping=time.monotonic()
        for path in (paths * repeat)[:limit]:
            delay = 1 / config['max_fps'] - (time.monotonic()-last_sent)
            if delay > 0:
                await asyncio.sleep(delay)
            data = cache[path]
            seq += 1
            header = {'type':'frame','seq':seq,'mode':mode}
            if mode == 'enroll':
                header.update(enroll_session_id=enrollment,employee_id=employee_id)
            request_started = time.perf_counter()
            await socket.send(json.dumps(header))
            await socket.send(data)
            last_sent = time.monotonic()
            while True:
                response = json.loads(await socket.recv())
                emit(json.dumps(response,ensure_ascii=False))
                if response.get('type') == 'config':
                    config = response
                    continue
                if response.get('type') == 'pong':
                    continue
                break
            messages.append(response)
            if observe:
                observe({'seq': seq, 'roundtrip_ms': (time.perf_counter()-request_started)*1000,
                         'type': response.get('type'), 'result': response.get('result'), 'state': response.get('state')})
            if response.get('type') == 'enroll_done':
                break
            if response.get('type') == 'result':
                await asyncio.sleep(config['result_display_sec'])
            if response.get('state') == 'BUSY':
                await asyncio.sleep(.2)
            if response.get('type') == 'error' and response.get('code') != 'FRAME_DECODE_FAILED':
                break
    return messages


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hub',required=True)
    parser.add_argument('--pair-code',required=True)
    parser.add_argument('--images',required=True,type=Path)
    parser.add_argument('--mode',choices=['recognize','enroll'],default='recognize')
    parser.add_argument('--employee-code')
    parser.add_argument('--repeat',type=int,default=1)
    args=parser.parse_args()
    if args.repeat < 1:
        parser.error('--repeat phải dương')
    async with httpx.AsyncClient(base_url=args.hub.rstrip('/')+'/api/v1',timeout=20) as client:
        paired=await client.post('/kiosk/pair',json={'code':args.pair_code,'device_info':{'app_version':'kiosk-sim-0.1'}})
        paired.raise_for_status()
        token=paired.json()['device_token']
        client.headers['Authorization']='Bearer '+token
        enrollment=employee_id=None
        if args.mode == 'enroll':
            if not args.employee_code:
                parser.error('--mode enroll cần --employee-code')
            enrollers=(await client.get('/kiosk/enrollers')).json()
            for index,item in enumerate(enrollers):
                print(index,item['name'])
            chosen=int(input('Chọn số người đăng ký: '))
            pin=os.environ.get('KIOSK_SIM_PIN') or getpass.getpass('PIN cá nhân: ')
            opened=await client.post('/kiosk/enroll/sessions',json={'user_id':enrollers[chosen]['user_id'],'pin':pin})
            opened.raise_for_status()
            enrollment=opened.json()['enroll_session_id']
            found=await client.get('/kiosk/enroll/sessions/'+enrollment+'/employees',params={'q':args.employee_code})
            found.raise_for_status()
            employee=next(item for item in found.json() if item['code'] == args.employee_code)
            employee_id=employee['id']
            consent=await client.post('/kiosk/enroll/sessions/'+enrollment+'/consent',json={'employee_id':employee_id,'agree':True})
            consent.raise_for_status()
    await simulate(args.hub,token,args.images,mode=args.mode,enrollment=enrollment,employee_id=employee_id,repeat=args.repeat)


if __name__ == '__main__':
    asyncio.run(main())
