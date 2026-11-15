param(
    [string]$Sdk = 'C:\Developer\Tools\Android\SDK',
    [string]$VideoPath,
    [switch]$Headless
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$root = Split-Path (Split-Path $project -Parent) -Parent
$report = Join-Path $root ('03-app\ket-qua-kiem-thu\' + (Get-Date -Format 'yyyy-MM-dd') + '_T08')
New-Item -ItemType Directory -Path $report -Force | Out-Null
$front = 'webcam0'
if ($VideoPath) {
    $resolvedVideo = (Resolve-Path -LiteralPath $VideoPath).Path
    if ($resolvedVideo.StartsWith($root + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Video chứa mặt thật phải ở ngoài repo.' }
    $front = 'videofile:' + $resolvedVideo.Replace('\', '/')
}
# -lowram giữ RAM đã yêu cầu, thay vì emulator tự nâng lên 4 GB theo profile
# tablet lớn. Skin vật lý 1280×800/density160 vẫn đúng bố cục 1280×800 dp.
if ($front -match '\s') { $front = '"' + $front + '"' }
$emulatorArguments = @('-avd', 'FaceGate_PixelTablet_API34', '-port', '5556', '-no-snapshot', '-no-boot-anim', '-lowram', '-memory', '2048', '-cores', '2', '-skin', '1280x800', '-dpi-device', '160', '-gpu', 'swiftshader', '-feature', '-Vulkan', '-camera-back', 'emulated', '-camera-front', $front)
if ($Headless) { $emulatorArguments += @('-no-window', '-no-audio') }
$stamp = Get-Date -Format 'HHmmss'
$process = Start-Process -FilePath (Join-Path $Sdk 'emulator\emulator.exe') -ArgumentList $emulatorArguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $report "avd-lowram-$stamp.log") -RedirectStandardError (Join-Path $report "avd-lowram-$stamp-error.log")
Write-Output "Emulator PID=$($process.Id); serial=emulator-5556; requested RAM=2048 MB, framebuffer=1280x800."
Write-Output "Log: $report\avd-lowram-$stamp.log"
