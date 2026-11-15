param(
    [string]$Sdk = 'C:\Developer\Tools\Android\SDK',
    [string]$Cache = 'D:\.gradle-facegate\tools'
)
$ErrorActionPreference = 'Stop'
# Ninja SDK 3.22.1 là 1.10.2, không hỗ trợ các đường dẫn C++ dài của pnpm.
# Bản chính thức, cố định phiên bản và SHA-256 từ GitHub Releases ninja-build/ninja.
$version = '1.13.2'
$expected = '07fc8261b42b20e71d1720b39068c2e14ffcee6396b76fb7a795fb460b78dc65'
$target = Join-Path $Sdk 'cmake\3.22.1\bin\ninja.exe'
if (-not (Test-Path -LiteralPath $target)) { throw 'Cần cài CMake 3.22.1 trong Android SDK trước.' }
if ((Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem').LongPathsEnabled -ne 1) {
    throw 'Windows chưa bật LongPathsEnabled; cần cấu hình Windows trước khi build native.'
}
$download = Join-Path $Cache "ninja-$version"
New-Item -ItemType Directory -Path $download -Force | Out-Null
$archive = Join-Path $download 'ninja-win.zip'
& curl.exe --fail --location --max-time 120 --silent --show-error -o $archive "https://github.com/ninja-build/ninja/releases/download/v$version/ninja-win.zip"
if ($LASTEXITCODE -ne 0) { throw 'Tải Ninja thất bại; giữ nguyên SDK.' }
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'SHA-256 Ninja không khớp; giữ nguyên SDK.' }
Expand-Archive -LiteralPath $archive -DestinationPath $download -Force
$original = Join-Path $Cache 'ninja-sdk-3.22.1-original.exe'
if (-not (Test-Path -LiteralPath $original)) { Copy-Item -LiteralPath $target -Destination $original }
Copy-Item -LiteralPath (Join-Path $download 'ninja.exe') -Destination $target -Force
Write-Output "Ninja archive SHA256 verified: $expected"
Write-Output "Original SDK executable retained: $original"
& $target --version
if ($LASTEXITCODE -ne 0) { throw 'Không chạy được Ninja mới.' }
