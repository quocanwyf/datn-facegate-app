"""Đo pipeline/WS thật 1 và 3 kiosk; CPU smoke không được báo nghiệm thu GPU."""
import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import getpass
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import httpx
import numpy as np
import torch
import uvicorn
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import get_settings
from scripts.collect_liveness import private_root
from scripts.kiosk_sim import EXTENSIONS, simulate
from scripts.review_database import context


def distribution(values):
    values = np.asarray(values, dtype=float)
    if not len(values): return None  # Không biến stage chưa chạy thành 0 ms.
    return dict(n=len(values), p50_ms=float(np.quantile(values,.5)), p95_ms=float(np.quantile(values,.95)))


def memory():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)] + [(name,ctypes.c_size_t) for name in
                ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
        value = Counters(); value.cb = ctypes.sizeof(value)
        kernel = ctypes.WinDLL('kernel32'); kernel.GetCurrentProcess.restype = wintypes.HANDLE
        query = ctypes.WinDLL('psapi').GetProcessMemoryInfo
        query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if query(kernel.GetCurrentProcess(), ctypes.byref(value), value.cb):
            return dict(process_rss_bytes=value.WorkingSetSize, process_peak_rss_bytes=value.PeakWorkingSetSize)
        return {'measurement_error': 'GetProcessMemoryInfo failed'}
    import resource
    return {'process_peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform=='darwin' else 1024)}


async def run(args, private):
    from app.main import create_app
    app = create_app()
    config = uvicorn.Config(app, host='127.0.0.1', port=args.port, log_level='warning', access_log=False)
    server = uvicorn.Server(config); task = asyncio.create_task(server.serve())
    report = dict(schema_version=1, purpose='T14 benchmark nhận dạng từ ảnh được đồng ý, không phải đo người thật đứng vào kiosk',
        created_at=datetime.now(timezone.utc).isoformat(), smoke=args.smoke, device=args.device,
        versions=dict(python=platform.python_version(), torch=str(torch.__version__), numpy=np.__version__), configurations=[])
    hub = f'http://127.0.0.1:{args.port}'
    try:
        deadline = time.monotonic()+120
        while not server.started:
            if task.done(): await task
            if time.monotonic()>deadline: raise TimeoutError('Hub benchmark chưa khởi động trong 120 giây.')
            await asyncio.sleep(.1)
        async with httpx.AsyncClient() as health_client:
            health = (await health_client.get(hub+'/api/v1/health')).json()
        if not health['model_verified'] or not health['gallery_size'] or health['gpu'] != (args.device=='cuda'):
            raise RuntimeError('Cổng kiểm mô hình/gallery/device chưa đạt; không đo giả.')
        async with httpx.AsyncClient(base_url=hub+'/api/v1', timeout=30) as client:
            password = 'Demo@123' if args.demo else os.environ.get('FACEGATE_REVIEW_PASSWORD') or getpass.getpass('Mật khẩu OWNER clone: ')
            login = await client.post('/auth/login', json={'email': args.email, 'password': password}); login.raise_for_status()
            client.headers['Authorization'] = 'Bearer '+login.json()['access_token']
            settings_response = await client.get('/settings/recognition'); settings_response.raise_for_status(); settings = settings_response.json()
            if not args.without_liveness:
                enabled = await client.put('/settings/recognition', json={'anti_spoof_enabled': True, 'liveness_threshold': args.threshold})
                if enabled.status_code!=200: raise RuntimeError('Cần báo cáo thật + approve_liveness.py cho HUB_DATA_DIR T14 trước khi bật.')
                settings = enabled.json()
            elif settings['anti_spoof_enabled']:
                disabled = await client.put('/settings/recognition', json={'anti_spoof_enabled': False}); disabled.raise_for_status(); settings = disabled.json()
            report['settings'] = settings; report['gpu_name'] = torch.cuda.get_device_name(0) if args.device=='cuda' else None
            for count in args.clients:
                timings, roundtrips, devices, tokens = [], [], [], []
                try:
                    for index in range(count):
                        gate = await client.post('/gates', json=dict(name=f'T14 measure {time.time_ns()}-{index}', mode='ACCESS_ONLY', default_policy='ALLOW_ALL_ACTIVE', threshold_level='DEFAULT_VAL'))
                        gate.raise_for_status()
                        device = await client.post('/devices', json={'gate_id': gate.json()['id'], 'name': f'T14 kiosk {index+1}'})
                        device.raise_for_status(); devices.append(device.json()['device']['id'])
                        pair = await client.post('/kiosk/pair', json={'code': device.json()['pairing_code']}); pair.raise_for_status(); tokens.append(pair.json()['device_token'])
                    if args.device=='cuda': torch.cuda.reset_peak_memory_stats()
                    app.state.recognition.timing_sink = timings.append
                    begin = time.perf_counter()
                    frames = args.frames+5
                    image_count = sum(p.suffix.lower() in EXTENSIONS for p in args.images.iterdir())
                    if not image_count: raise ValueError('Thư mục cần ảnh thật được hỗ trợ.')
                    simulations = [asyncio.create_task(simulate(hub, token, args.images, repeat=math.ceil(frames/image_count), limit=frames,
                        emit=lambda line: None, observe=roundtrips.append)) for token in tokens]
                    try:
                        messages = await asyncio.gather(*simulations)
                    finally:
                        for simulation in simulations:
                            if not simulation.done(): simulation.cancel()
                        await asyncio.gather(*simulations, return_exceptions=True)
                    elapsed = time.perf_counter()-begin
                    app.state.recognition.timing_sink = None
                    measured = timings[5*count:]
                    if len(measured) < args.frames*count: raise RuntimeError('Không đủ khung xử lý thực; xem camera/gallery/WS trước khi đo lại.')
                    errors = sum(message.get('type')=='error' for rows in messages for message in rows)
                    summary = dict(clients=count, measured_frames=len(measured), warmup_frames=5*count, elapsed_seconds=elapsed,
                        pipeline_total=distribution([row['total_ms'] for row in measured]),
                        stages={name: distribution([row['stages_ms'][name] for row in measured if name in row['stages_ms']]) for name in ('decode','yunet','liveness','embed','top1','decision')},
                        websocket_roundtrip=distribution([row['roundtrip_ms'] for row in roundtrips[5*count:]]),
                        response_counts=dict(Counter(message.get('reason') or message.get('result') or message.get('state') or message.get('type') for rows in messages for message in rows)),
                        errors=errors, memory=memory())
                    if args.device=='cuda': summary['memory'].update(torch_peak_allocated_bytes=torch.cuda.max_memory_allocated(), torch_peak_reserved_bytes=torch.cuda.max_memory_reserved())
                    report['configurations'].append(summary)
                    print(f'Đã đo {count} kiosk: {len(measured)} khung, errors={errors}', flush=True)
                finally:
                    app.state.recognition.timing_sink = None
                    for identity in devices:
                        response = await client.post(f'/devices/{identity}/revoke'); response.raise_for_status()
            report['gpu_benchmark_criteria_met'] = (not args.smoke and args.device=='cuda' and set(args.clients)=={1,3}
                and args.frames>=300 and not args.without_liveness and all(not row['errors'] for row in report['configurations']))
            report['limitations'] = 'Pipeline stage timing đồng bộ CUDA khi bật; RTT gồm WS/DB/queue. RAM peak là peak của process; VRAM PyTorch allocator, không phải toàn VRAM hệ thống. Khung không hợp lệ/bị giữ kết quả có thể không chạy mọi stage, n của từng stage được ghi riêng. Độ trễ đứng-vào→kết quả 20 lượt phải đo riêng bằng video kiosk thật.'
    finally:
        server.should_exit = True
        await task
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', type=Path); parser.add_argument('--output', required=True,type=Path)
    parser.add_argument('--device',choices=['cpu','cuda'],default='cuda'); parser.add_argument('--clients',type=int,nargs='+',default=[1,3])
    parser.add_argument('--frames',type=int,default=300); parser.add_argument('--port',type=int,default=8014)
    parser.add_argument('--smoke',action='store_true'); parser.add_argument('--without-liveness',action='store_true')
    parser.add_argument('--resume',action='store_true'); parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--threshold',type=float); parser.add_argument('--email',default='nv001@demo.local'); parser.add_argument('--demo',action='store_true')
    args = parser.parse_args()
    if not args.prepare and args.device=='cuda' and not torch.cuda.is_available():
        raise SystemExit('CUDA chưa có: PyTorch='+str(torch.__version__)+'. Không chạy CPU thay cho nghiệm thu GPU.')
    if not args.smoke and (args.frames<300 or args.without_liveness or set(args.clients)!={1,3}):
        parser.error('Nghiệm thu cần >=300 khung/kiosk, cả 1 và 3 kiosk, có liveness. Dùng --smoke cho tiền kiểm khác.')
    if not all(1<=count<=3 for count in args.clients) or args.frames<1: parser.error('clients 1..3; frames dương.')
    if not args.prepare:
        if args.images is None: parser.error('Cần --images ngoài repo.')
        args.images = private_root(args.images)
    private, url = context('T14',resume=args.resume)
    if args.prepare:
        print('Đã chuẩn bị clone T14. HUB_DATA_DIR='+private['data_dir']+'; dữ liệu T08 và review web giữ nguyên.')
        return
    os.environ.update(DATABASE_URL=url,HUB_DATA_DIR=private['data_dir'],INFER_DEVICE=args.device,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    get_settings.cache_clear(); torch.set_num_threads(2)
    asyncio.run(run(args, private))


if __name__=='__main__': main()
