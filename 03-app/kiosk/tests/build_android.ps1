param(
    [string]$Sdk = 'C:\Developer\Tools\Android\SDK',
    [string]$Java = 'C:\Program Files\Android\Android Studio\jbr',
    [string]$GradleHome = 'D:\.gradle-facegate'
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$env:ANDROID_HOME = $Sdk
$env:JAVA_HOME = $Java
$env:GRADLE_USER_HOME = $GradleHome
$env:Path = "$Java\bin;C:\Program Files\nodejs;$env:APPDATA\npm;$env:Path"
$previousMakeFlags = $env:MAKEFLAGS
$previousStatus = $env:NINJA_STATUS
# Ninja 1.13 hỗ trợ jobserver Windows bằng semaphore. Một slot chia sẻ + slot
# ngầm của Ninja = tối đa 2 compiler; Gradle một worker tránh thêm Ninja khác.
# https://ninja-build.org/manual.html#_gnu_jobserver_support
$poolName = 'Local\FaceGateBuild-' + [guid]::NewGuid().ToString('N')
$pool = [System.Threading.Semaphore]::new(1, 1, $poolName)
$env:MAKEFLAGS = "-j --jobserver-auth=$poolName"
$env:NINJA_STATUS = '[%r running %f/%t] '
try {
    Write-Output 'Android x86_64 debug build; Gradle workers=1; Ninja jobserver=2 slots.'
    & (Join-Path $project 'android\gradlew.bat') -p (Join-Path $project 'android') :app:assembleDebug -PreactNativeArchitectures=x86_64 --max-workers=1 --console=plain
    if ($LASTEXITCODE -ne 0) { throw "Gradle failed: $LASTEXITCODE" }
} finally {
    $pool.Dispose()
    $env:MAKEFLAGS = $previousMakeFlags
    $env:NINJA_STATUS = $previousStatus
}
