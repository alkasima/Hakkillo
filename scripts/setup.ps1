$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskProjectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not update pip.' }
& '.\.venv\Scripts\python.exe' -m pip install --no-cache-dir -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
Write-Host 'Ready. Start Hakkillo with: .\.venv\Scripts\python.exe app.py'
