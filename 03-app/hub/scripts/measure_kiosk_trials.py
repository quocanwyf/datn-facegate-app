"""T14: tổng hợp 20 lượt từ video kiosk thật được người xem đánh dấu thời điểm."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import cv2
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.collect_liveness import private_root


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',required=True,type=Path,help='Thư mục video ngoài repo')
    parser.add_argument('--csv',required=True,type=Path,help='trial_id,video,enter_sec,result_sec,result')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--conditions',required=True,help='Kiosk/camera/ánh sáng thực tế')
    args=parser.parse_args(); root=private_root(args.data)
    rows=list(csv.DictReader(args.csv.open(encoding='utf-8-sig',newline='')))
    if len(rows)<20: raise SystemExit('Cần >=20 lượt kiosk thật; không điền số minh họa để đạt.')
    values=[]; identities=set(); intervals={}; sources={}; results={}
    for row in rows:
        identity=row['trial_id']; path=(root/row['video']).resolve()
        if not identity or identity in identities or not path.is_relative_to(root): raise ValueError('ID trùng hoặc video ngoài bộ riêng.')
        identities.add(identity)
        begin,end=float(row['enter_sec']),float(row['result_sec'])
        if not np.isfinite([begin,end]).all() or not 0<=begin<end: raise ValueError('Mốc thời gian không hợp lệ.')
        if row['result'] not in ('OK','ALREADY','DENY'): raise ValueError('Ghi đúng kết quả hiển thị trên kiosk.')
        if path not in sources:
            video=cv2.VideoCapture(str(path))
            try:
                fps=video.get(cv2.CAP_PROP_FPS); frames=video.get(cv2.CAP_PROP_FRAME_COUNT)
                if fps<=0 or frames<=0: raise ValueError('Video không đọc được.')
                sources[path]=(frames/fps,hashlib.sha256(path.read_bytes()).hexdigest())
            finally: video.release()
        if end>sources[path][0]+.1: raise ValueError('Mốc vượt thời lượng video thật.')
        if any(begin<old_end and end>old_begin for old_begin,old_end in intervals.setdefault(path,[])): raise ValueError('Hai lượt chồng nhau trong video.')
        intervals[path].append((begin,end)); values.append((end-begin)*1000); results[row['result']]=results.get(row['result'],0)+1
    report=dict(purpose='T14 đo người thật đứng-vào→kết quả trên UI kiosk, đánh dấu thủ công từ video; không phải RTT WS',
        conditions=args.conditions,n=len(values),p50_ms=float(np.quantile(values,.5)),p95_ms=float(np.quantile(values,.95)),
        result_counts=results,source_videos=len(sources),source_digest=hashlib.sha256(''.join(sorted(value[1] for value in sources.values())).encode()).hexdigest(),
        limits='Mốc enter_sec: mặt đi vào vùng quét; result_sec: kết quả đầu tiên đọc được trên UI. Sai số theo khung hình/người đánh dấu. Video riêng không commit.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    print('Đã tổng hợp',len(values),'lượt thật được đánh dấu; không xuất video hay ảnh.')


if __name__=='__main__': main()
