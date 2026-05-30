$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\pythonw.exe"
$App = Join-Path $Root "web_app.py"
$Url = "http://127.0.0.1:8765"

function Test-OrpheusWeb {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "$Url/api/status" -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python virtual environment not found: $Python"
}

if (-not (Test-Path -LiteralPath $App)) {
    throw "Web app not found: $App"
}

if (-not (Test-OrpheusWeb)) {
    Start-Process `
        -FilePath $Python `
        -ArgumentList @($App, "--port", "8765", "--open") `
        -WorkingDirectory $Root `
        -WindowStyle Hidden
    exit 0
}

Start-Process $Url
