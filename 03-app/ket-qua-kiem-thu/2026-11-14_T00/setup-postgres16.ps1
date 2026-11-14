# Cài cụm PostgreSQL 16 riêng của FaceGate, không đụng dịch vụ PostgreSQL khác.
# Chạy ở gốc repo sau khi đã giải nén PostgreSQL 16 vào LOCALAPPDATA/FaceGate/postgresql16.
$ErrorActionPreference = 'Stop'
$workspaceRoot = (Get-Location).Path
$nativeRoot = Join-Path $env:LOCALAPPDATA 'FaceGate/postgresql16'
$binDir = Join-Path $nativeRoot 'pgsql/bin'
$dataDir = Join-Path $nativeRoot 'data'
$adminFile = Join-Path $nativeRoot 'admin-password.txt'
$reportDir = Join-Path $workspaceRoot '03-app/ket-qua-kiem-thu/2026-11-14_T00'
$utf8 = New-Object System.Text.UTF8Encoding($false)
function New-LocalSecret {
    $bytes = New-Object byte[] 48
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}
if (!(Test-Path -LiteralPath (Join-Path $binDir 'initdb.exe'))) { throw 'Chưa có binary PostgreSQL 16.' }
if (!(Test-Path -LiteralPath $adminFile)) { [IO.File]::WriteAllText($adminFile, (New-LocalSecret), $utf8) }
if (!(Test-Path -LiteralPath (Join-Path $dataDir 'PG_VERSION'))) {
    if (Test-Path -LiteralPath $dataDir) { throw 'Thư mục data đã tồn tại nhưng chưa xác định được phiên bản; không tự ghi đè.' }
    & (Join-Path $binDir 'initdb.exe') -D $dataDir -U postgres --auth=scram-sha-256 --encoding=UTF8 --locale=C --pwfile=$adminFile 2>&1 | Tee-Object (Join-Path $reportDir 'postgresql16-initdb.log')
    if ($LASTEXITCODE -ne 0) { throw 'initdb thất bại.' }
}
if (([IO.File]::ReadAllText((Join-Path $dataDir 'PG_VERSION'))).Trim() -ne '16') { throw 'Thư mục data không thuộc PostgreSQL 16.' }
& (Join-Path $binDir 'pg_ctl.exe') -D $dataDir status *> $null
if ($LASTEXITCODE -ne 0) {
    $startArgs = @('-D', ('"' + $dataDir + '"'), '-l', ('"' + (Join-Path $nativeRoot 'server.log') + '"'), '-o', '"-p 5433 -h 127.0.0.1"', '-w', 'start')
    $startProcess = Start-Process -FilePath (Join-Path $binDir 'pg_ctl.exe') -ArgumentList $startArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $reportDir 'postgresql16-start.log') -RedirectStandardError (Join-Path $reportDir 'postgresql16-start-error.log')
    if (!$startProcess.WaitForExit(30000)) { throw 'Hết thời gian chờ pg_ctl.' }
    if ($startProcess.ExitCode -ne 0) { throw 'Không khởi động được PostgreSQL 16 tại 127.0.0.1:5433.' }
}
$envPath = Join-Path $workspaceRoot '.env'
if (!(Test-Path -LiteralPath $envPath)) {
    $dbPassword = New-LocalSecret
    $text = [IO.File]::ReadAllText((Join-Path $workspaceRoot '.env.example'))
    $text = $text -replace '(?m)^DATABASE_URL=.*$', "DATABASE_URL=postgresql+asyncpg://facegate:${dbPassword}@127.0.0.1:5433/facegate_dev"
    $text = $text -replace '(?m)^JWT_SECRET=.*$', ('JWT_SECRET=' + (New-LocalSecret))
    $text = $text -replace '(?m)^INFER_DEVICE=.*$', 'INFER_DEVICE=cpu'
    [IO.File]::WriteAllText($envPath, $text, $utf8)
} else {
    $match = [regex]::Match([IO.File]::ReadAllText($envPath), '(?m)^DATABASE_URL=postgresql\+asyncpg://facegate:([A-Za-z0-9_-]+)@127\.0\.0\.1:5433/facegate_dev\s*$')
    if (!$match.Success) { throw '.env đã có cấu hình khác; không tự thay thế.' }
    $dbPassword = $match.Groups[1].Value
}
$previousPgPassword = $env:PGPASSWORD
try {
    $env:PGPASSWORD = ([IO.File]::ReadAllText($adminFile)).Trim()
    $roleExists = & (Join-Path $binDir 'psql.exe') -h 127.0.0.1 -p 5433 -U postgres -d postgres -At -c "SELECT 1 FROM pg_roles WHERE rolname='facegate'"
    if ($LASTEXITCODE -ne 0) { throw 'Không kết nối được PostgreSQL 16.' }
    if ($roleExists -ne '1') {
        # Mật khẩu chỉ đi qua stdin, không in ra terminal/log hoặc nằm trong command line.
        "CREATE ROLE facegate LOGIN PASSWORD '$dbPassword';" | & (Join-Path $binDir 'psql.exe') -h 127.0.0.1 -p 5433 -U postgres -d postgres -v ON_ERROR_STOP=1
        if ($LASTEXITCODE -ne 0) { throw 'Tạo role thất bại.' }
    }
    $dbExists = & (Join-Path $binDir 'psql.exe') -h 127.0.0.1 -p 5433 -U postgres -d postgres -At -c "SELECT 1 FROM pg_database WHERE datname='facegate_dev'"
    if ($LASTEXITCODE -ne 0) { throw 'Không kiểm tra được database.' }
    if ($dbExists -ne '1') {
        & (Join-Path $binDir 'createdb.exe') -h 127.0.0.1 -p 5433 -U postgres -O facegate facegate_dev
        if ($LASTEXITCODE -ne 0) { throw 'Tạo database thất bại.' }
    }
    'PostgreSQL 16 sẵn sàng tại 127.0.0.1:5433; role facegate, DB facegate_dev. Không in thông tin xác thực.'
} finally {
    $env:PGPASSWORD = $previousPgPassword
}
