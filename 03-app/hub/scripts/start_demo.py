"""Hub + web build cùng origin; app ghép vào cùng Hub/DB. Không tự bật liveness."""
import argparse
import os
from pathlib import Path
import sys
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import ROOT, get_settings
from scripts.review_database import context


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',choices=['cpu','cuda'],default='cuda')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--public-url',default='http://10.0.2.2:8000',help='URL mà kiosk truy cập được; dùng IP LAN nếu khác máy')
    parser.add_argument('--require-liveness',action='store_true')
    args=parser.parse_args()
    if args.device=='cuda' and not torch.cuda.is_available():
        raise SystemExit('CUDA chưa khả dụng. --device cpu chỉ cho review/tiền kiểm; không đạt cổng demo GPU T14.')
    dist=(ROOT/'03-app/web/dist').resolve()
    if not (dist/'index.html').is_file(): raise SystemExit('Chạy pnpm build ở web trước khi mở demo.')
    private,url=context('T14',resume=args.resume)
    os.environ.update(DATABASE_URL=url,HUB_DATA_DIR=private['data_dir'],INFER_DEVICE=args.device,
        HUB_PUBLIC_URL=args.public_url,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    get_settings.cache_clear();torch.set_num_threads(2)
    if args.require_liveness:
        from sqlalchemy import create_engine,select
        from app.db.models import Company
        from app.recog.decision import validate_liveness_threshold
        from app.recog.liveness import verify_bundle
        engine=create_engine(url.replace('postgresql+asyncpg:','postgresql+psycopg:'),hide_parameters=True)
        try:
            with engine.connect() as connection: settings=connection.scalar(select(Company.settings))
            if not settings['anti_spoof_enabled']: raise SystemExit('Chưa bật liveness bằng API sau khi chốt L.')
            validate_liveness_threshold(settings['liveness_threshold'])
            verify_bundle()
        finally:engine.dispose()
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from app.main import create_app
    app=create_app()
    @app.get('/{path:path}',include_in_schema=False)
    async def web(path:str):
        if path=='api' or path.startswith('api/'): raise HTTPException(404)
        target=(dist/path).resolve()
        if not target.is_relative_to(dist): raise HTTPException(404)
        if target.is_file(): return FileResponse(target)
        if Path(path).suffix: raise HTTPException(404)
        return FileResponse(dist/'index.html',headers={'Cache-Control':'no-store'})
    print(f'Demo chung: web http://127.0.0.1:{args.port}/login, kiosk {args.public_url}; DB/kho T14 riêng. device={args.device}',flush=True)
    print('CPU chưa đạt tiêu chí GPU T14; chống giả mạo chỉ hoạt động sau phê duyệt và bật cấu hình.',flush=True)
    import uvicorn
    uvicorn.run(app,host=args.host,port=args.port)


if __name__=='__main__':main()
