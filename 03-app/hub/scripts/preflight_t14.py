"""Ghi phần cứng/runtime thật, không in env/token/serial máy."""
import argparse
import json
import platform
from pathlib import Path
import shutil
import subprocess
import torch


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', required=True,type=Path); args = parser.parse_args()
    report = dict(os=platform.platform(), processor=platform.processor(), python=platform.python_version(),
        torch=str(torch.__version__), compiled_cuda=torch.version.cuda, cuda_available=torch.cuda.is_available(),
        cuda_devices=[torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())], nvidia_smi_found=bool(shutil.which('nvidia-smi')))
    if platform.system()=='Windows':
        result = subprocess.run(['powershell','-NoProfile','-Command', 'Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json -Compress'], capture_output=True,text=True,encoding='utf8',errors='replace')
        if result.returncode==0:
            try: report['windows_video_controllers'] = json.loads(result.stdout)
            except ValueError: report['windows_video_controllers'] = 'Chưa đọc được JSON phần cứng.'
    report['gpu_gate_passed'] = bool(report['cuda_available'] and report['cuda_devices'])
    report['next_step'] = 'Có thể kiểm cổng mô hình CUDA.' if report['gpu_gate_passed'] else 'Chưa đạt CUDA. Intel UHD không phải GPU CUDA; kiểm máy/NVIDIA driver/PyTorch CUDA trước khi đo GPU. Không báo CPU là GPU.'
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
