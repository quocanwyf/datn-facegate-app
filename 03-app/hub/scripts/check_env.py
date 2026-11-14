"""Ghi môi trường thật; --require-cuda chặn chạy nhầm CPU ở laptop nghiệm thu."""
import argparse
import platform
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m0_common import write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-cuda', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    import torch
    import cv2
    import numpy as np
    try:
        driver = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'],
                                capture_output=True, text=True, timeout=20)
        driver_text = driver.stdout.strip() if driver.returncode == 0 else driver.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        driver_text = type(error).__name__
    report = {'python': sys.version, 'platform': platform.platform(), 'torch': torch.__version__,
              'torch_cuda_build': torch.version.cuda, 'cuda_available': torch.cuda.is_available(),
              'gpus': [torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())],
              'nvidia_smi': driver_text, 'opencv': cv2.__version__, 'numpy': np.__version__,
              'require_cuda': args.require_cuda, 'blufr_repeated': False}
    if args.require_cuda and report['cuda_available']:
        # Kiểm có thể cấp phát/thực thi thật, không chỉ dựa vào cờ available.
        value = (torch.ones(1, device='cuda') + 1).item()
        report['cuda_smoke_ok'] = value == 2
    write_report(args.output, report)
    if args.require_cuda and not report.get('cuda_smoke_ok'):
        raise SystemExit('DỪNG: môi trường CUDA chưa chạy được; không nới điều kiện GPU.')


if __name__ == '__main__':
    main()
