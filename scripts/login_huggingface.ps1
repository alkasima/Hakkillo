$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
& "$taskProjectRoot\.venv\Scripts\hf.exe" auth login
if ($LASTEXITCODE -ne 0) { throw 'Hugging Face login did not complete.' }
& "$taskProjectRoot\.venv\Scripts\hf.exe" auth whoami
