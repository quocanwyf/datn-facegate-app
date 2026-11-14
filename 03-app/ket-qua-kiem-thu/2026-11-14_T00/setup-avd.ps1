# Tạo AVD riêng, không ghi đè máy ảo đã có. System image phải được cài trước.
param([switch]$Start)
$ErrorActionPreference = 'Stop'
$sdkRoot = 'C:/Developer/Tools/Android/SDK'
$managerRoot = Join-Path $sdkRoot 'cmdline-tools/22.0/bin'
$env:JAVA_HOME = 'C:/Program Files/Android/Android Studio/jbr'
$env:ANDROID_HOME = $sdkRoot
$env:ANDROID_SDK_ROOT = $sdkRoot
$avdName = 'FaceGate_PixelTablet_API34'
$avdRoot = Join-Path $env:USERPROFILE '.android/avd'
$avdDir = Join-Path $avdRoot ($avdName + '.avd')
$reportDir = Join-Path (Get-Location) '03-app/ket-qua-kiem-thu/2026-11-14_T00'
if (!(Test-Path -LiteralPath (Join-Path $sdkRoot 'system-images/android-34/default/x86_64/source.properties'))) {
    throw 'Chưa cài system image Android 34 x86_64; không tạo máy ảo giả.'
}
if (!(Test-Path -LiteralPath (Join-Path $avdDir 'config.ini'))) {
    'no' | & (Join-Path $managerRoot 'avdmanager.bat') create avd -n $avdName -k 'system-images;android-34;default;x86_64' -d pixel_tablet 2>&1 | Tee-Object (Join-Path $reportDir 'avd-create.log')
    if ($LASTEXITCODE -ne 0) { throw 'Không tạo được AVD.' }
}
$configFile = Join-Path $avdDir 'config.ini'
$config = [IO.File]::ReadAllText($configFile)
$settings = @{ 'hw.camera.front'='webcam0'; 'hw.camera.back'='emulated'; 'hw.initialOrientation'='landscape'; 'hw.ramSize'='2048' }
foreach ($entry in $settings.GetEnumerator()) {
    $pattern = '(?m)^' + [regex]::Escape($entry.Key) + '=.*$'
    if ([regex]::IsMatch($config, $pattern)) { $config = [regex]::Replace($config, $pattern, ($entry.Key + '=' + $entry.Value)) }
    else { $config += "`n$($entry.Key)=$($entry.Value)" }
}
[IO.File]::WriteAllText($configFile, $config, (New-Object System.Text.UTF8Encoding($false)))
Get-Content -LiteralPath $configFile | Out-File (Join-Path $reportDir 'avd-config.log')
& (Join-Path $sdkRoot 'emulator/emulator.exe') -webcam-list 2>&1 | Tee-Object (Join-Path $reportDir 'emulator-webcams.log')
if ($Start) {
    if (Get-NetTCPConnection -State Listen -LocalPort 5556,5557 -ErrorAction SilentlyContinue) { throw 'Cổng 5556/5557 đang dùng; không thay thế thiết bị đang chạy.' }
    $emulatorArgs = @('-avd', $avdName, '-port', '5556', '-no-snapshot', '-no-window', '-no-audio', '-gpu', 'software', '-camera-front', 'webcam0', '-camera-back', 'emulated', '-memory', '2048')
    $process = Start-Process -FilePath (Join-Path $sdkRoot 'emulator/emulator.exe') -ArgumentList $emulatorArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $reportDir 'emulator-start.log') -RedirectStandardError (Join-Path $reportDir 'emulator-start-error.log')
    "Emulator launcher PID=$($process.Id), serial=emulator-5556" | Tee-Object (Join-Path $reportDir 'emulator-process.log')
}
