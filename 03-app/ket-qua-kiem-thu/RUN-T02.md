# Chạy T02 trên laptop An (Windows / PowerShell)

Phần GPU chưa chạy trên máy Hy. Có thể chạy lúc rảnh, không chặn T03–T12. Không tái lập BLUFR. Khi có lỗi, giữ log và dừng; không sửa vendor hoặc nới ngưỡng.

Chuẩn bị Python 3.13, Git, driver NVIDIA; checkpoint gốc ở đúng đường dẫn manifest (kiểm bằng `python 03-app/tools/kiem-checkpoint.py`), bản trích trong `C:\datn-backbones-24`. Giải nén LFW deep-funneled **ngoài repo**, thư mục gốc chứa các thư mục tên người. Không commit ảnh, LFW, checkpoint hay `.env`.

Mở PowerShell tại repo đã clone, chạy `git pull --ff-only`. Chỉnh đúng `$Lfw` trong khối dưới. Môi trường riêng ngoài repo tránh ảnh hưởng Hub đang chạy.

```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$Repo = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cần mở PowerShell trong repo' }
$Lfw = 'D:\datn-data\lfw'
$Stripped = 'C:\datn-backbones-24'
if (!(Test-Path -LiteralPath $Lfw)) { throw 'Sửa đường dẫn LFW trước' }
if (!(Test-Path -LiteralPath $Stripped)) { throw 'Thiếu thư mục bản trích' }
Set-Location "$Repo/03-app/hub"
$T02Venv = Join-Path $env:LOCALAPPDATA 'FaceGate/t02-venv'
py -3.13 -m venv $T02Venv
if ($LASTEXITCODE -ne 0) { throw 'Cần cài Python 3.13' }
$Python = Join-Path $T02Venv 'Scripts/python.exe'
& $Python -m pip install 'torch==2.11.0' --index-url https://download.pytorch.org/whl/cu130
if ($LASTEXITCODE -ne 0) { throw 'Cài torch CUDA thất bại; gửi lại lỗi' }
& $Python -m pip install 'numpy>=2,<3' 'opencv-python==4.14.0.94' 'scikit-image>=0.24,<0.27' 'PyYAML>=6,<7' 'Pillow>=11,<14' 'pytest>=8,<10'
if ($LASTEXITCODE -ne 0) { throw 'Cài dependency thất bại' }
$RunName = 'laptop-An-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$ResultRelative = '03-app/ket-qua-kiem-thu/' + (Get-Date -Format 'yyyy-MM-dd') + '_T02/' + $RunName
$Result = Join-Path $Repo $ResultRelative
New-Item -ItemType Directory -Path $Result | Out-Null
git rev-parse HEAD | Set-Content "$Result/source-commit.log"
function Invoke-T02([string]$Name, [string[]]$Arguments) {
    & $Python @Arguments 2>&1 | Tee-Object "$Result/$Name.log"
    if ($LASTEXITCODE -ne 0) { throw "DỪNG ở $Name; giữ log, gửi lại lỗi" }
}
Invoke-T02 'environment' @('scripts/check_env.py','--require-cuda','--output',"$Result/environment.json")
Invoke-T02 'tensor' @('scripts/m0_tensor_equal.py','--stripped',$Stripped,'--output',"$Result/tensor.json")
Invoke-T02 'features' @('scripts/parity_features.py','--lfw',$Lfw,'--n','100','--seed','2026','--device','cuda','--output',"$Result/features.json")
Invoke-T02 'landmarks' @('scripts/parity_landmarks.py','--lfw',$Lfw,'--output',"$Result/landmarks.json")
$env:T02_LFW_ROOT = $Lfw
$env:T02_DEVICE = 'cuda'
$env:T02_COLOR_OUTPUT = "$Result/color.json"
try { Invoke-T02 'color' @('-m','pytest','tests/test_color_order.py','-q','-s') }
finally { Remove-Item Env:T02_LFW_ROOT,Env:T02_DEVICE,Env:T02_COLOR_OUTPUT -ErrorAction SilentlyContinue }
Invoke-T02 'thresholds' @('scripts/gen_thresholds.py','--output',"$Result/thresholds.json")
Write-Host "Hoàn tất các lệnh. Log ở $Result. Gửi Codex kiểm nội dung trước khi đánh dấu T02 đạt."
```

Bản torch CUDA 13.0 có wheel Python 3.13 Windows tại [kho chính thức PyTorch](https://download.pytorch.org/whl/cu130/torch/). Nếu driver không chạy được CUDA 13, gửi `environment.log` và lỗi; chọn bản torch CUDA hợp driver rồi ghi rõ phiên bản khác. Không chạy CPU để thay nghiệm thu GPU.

Kết quả mong đợi: tensor mọi khóa bằng nhau; feature max delta ≤ 1e-5 trên 100 ảnh CUDA; landmark ≥99% **toàn bộ** ảnh lệch tối đa ≤0,5px; màu có số đo (cos ≥0,99 chỉ cần ghi đề xuất); ba ngưỡng lệch seed ≤1e-9. Script landmark có thể chạy lâu vì đọc toàn bộ LFW. Không có ảnh/vector đầu ra.

Đẩy log sau khi chạy, kể cả khi có lỗi (chỉ stage đúng thư mục kết quả vừa tạo):

```powershell
Set-Location $Repo
& $Python 03-app/tools/kiem-bi-mat.py
if ($LASTEXITCODE -ne 0) { throw 'Chưa được commit: kiểm bí mật chưa sạch' }
git add -- $ResultRelative
git diff --cached --stat
git commit -m 'T02: record laptop GPU verification logs'
if ($LASTEXITCODE -ne 0) { throw 'Commit thất bại' }
git push origin main
```

Nếu còn thay đổi khác đang stage, bỏ stage chúng trước khi dùng khối push. Gửi Hy/Codex hash commit và tên thư mục kết quả. Không ghi “đạt” khi một lệnh chưa chạy hoặc bị lỗi.
