$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$TtsScript = Join-Path $Root "tts.ps1"
$OutputDir = Join-Path $Root "outputs"
$SpeakerScriptFile = Join-Path $Root "scripts\Ultra-TTS Script.txt"
$ModelKey = "orpheus-3b-0.1-ft"
$SpeakerLinePattern = "^\s*(tara|leah|jess|leo|dan|mia|zac|zoe)\s*[:：]\s*\S"

function Invoke-LmsText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    $Output = & cmd.exe /d /c "$Command 2>&1"
    [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = $Output
        Text = $Output -join "`n"
    }
}

function Get-Utf8Text {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Base64
    )

    [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Base64))
}

function Write-Alert {
    param(
        [Parameter(Mandatory = $true)]
        [string]$MessageBase64
    )

    Write-Host ""
    Write-Host "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" -ForegroundColor Yellow
    Write-Host (Get-Utf8Text $MessageBase64) -ForegroundColor Yellow
    Write-Host "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" -ForegroundColor Yellow
    Write-Host ""
}

function Ensure-SpeakerScriptFile {
    if (Test-Path -LiteralPath $SpeakerScriptFile) {
        return
    }

    @(
        "# Ultra-TTS multi-speaker script",
        "# Use one line per utterance:",
        "#",
        "# tara: Hello. This is Tara.",
        "# leo: Hi. This is Leo.",
        "#",
        "# Valid voices: tara, leah, jess, leo, dan, mia, zac, zoe"
    ) | Set-Content -LiteralPath $SpeakerScriptFile -Encoding UTF8
}

function Test-SpeakerScriptHasLines {
    if (-not (Test-Path -LiteralPath $SpeakerScriptFile)) {
        return $false
    }

    $Match = Get-Content -LiteralPath $SpeakerScriptFile -Encoding UTF8 |
        Where-Object { $_ -match $SpeakerLinePattern } |
        Select-Object -First 1

    return $null -ne $Match
}

if (-not (Test-Path -LiteralPath $TtsScript)) {
    throw "TTS script not found: $TtsScript"
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$SpeakerScriptDir = Split-Path -Parent $SpeakerScriptFile
if (-not (Test-Path -LiteralPath $SpeakerScriptDir)) {
    New-Item -ItemType Directory -Path $SpeakerScriptDir | Out-Null
}

Write-Host ""
Write-Host "Ultra-TTS via LM Studio"
Write-Host "Output folder: $OutputDir"
Write-Host ""
Write-Host "Checking LM Studio server..."
$ServerStatus = Invoke-LmsText "lms server status"
if ($ServerStatus.ExitCode -ne 0 -or $ServerStatus.Text -notmatch "is running") {
    Write-Alert "TE0gU3R1ZGlv6LW35YuV44GX44Gm44Gq44GE44KI77yB77yB77yB"
    Write-Host "Trying to start LM Studio server..."
    $ServerStart = Invoke-LmsText "lms server start --port 1234"
    $ServerStart.Output | ForEach-Object { Write-Host $_ }
    if ($ServerStart.ExitCode -ne 0) {
        Write-Host ""
        Write-Host (Get-Utf8Text "TE0gU3R1ZGlv44KS6LW35YuV44GX44Gm44GL44KJ44CB44KC44GG5LiA5bqm44GT44Gu44OV44Kh44Kk44Or44KS6ZaL44GE44Gm44Gt44CC") -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to close"
        exit 1
    }
} else {
    Write-Host $ServerStatus.Text
}

Write-Host "Checking LM Studio Orpheus model..."
$LoadedModels = Invoke-LmsText "lms ps"
if ($LoadedModels.ExitCode -ne 0 -or $LoadedModels.Text -notmatch [regex]::Escape($ModelKey)) {
    Write-Alert "T3JwaGV1c+ODouODh+ODq+OBjOiqreOBv+i+vOOBvuOCjOOBpuOBquOBhOOCiO+8ge+8ge+8gQ=="
    Write-Host "Loading $ModelKey..."
    $LoadResult = Invoke-LmsText "lms load $ModelKey --identifier $ModelKey -y"
    $LoadResult.Output | ForEach-Object { Write-Host $_ }
    if ($LoadResult.ExitCode -ne 0) {
        Write-Host ""
        Write-Host "Failed to load $ModelKey." -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to close"
        exit 1
    }
} else {
    Write-Host "$ModelKey is already loaded."
}

Write-Host ""

Ensure-SpeakerScriptFile
$HasSpeakerScript = Test-SpeakerScriptHasLines
$DefaultScriptAnswer = if ($HasSpeakerScript) { "Y" } else { "n" }
Write-Host "Multi-speaker script file: $SpeakerScriptFile"
Write-Host "Format: tara: Hello. / leo: Hi."
$UseSpeakerScript = Read-Host "Use multi-speaker script file? [$DefaultScriptAnswer]"
if ([string]::IsNullOrWhiteSpace($UseSpeakerScript)) {
    $UseSpeakerScript = $DefaultScriptAnswer
}

if ($UseSpeakerScript -match "^(y|yes)$") {
    if (-not $HasSpeakerScript) {
        Write-Host ""
        Write-Host "No speaker lines found in: $SpeakerScriptFile" -ForegroundColor Yellow
        Write-Host "Edit the file with lines like: tara: Hello." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to close"
        exit 1
    }

    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Output = Join-Path $OutputDir "multi-$Timestamp.wav"

    & $TtsScript -ScriptFile $SpeakerScriptFile -Output $Output
    $ExitCode = $LASTEXITCODE

    if ($ExitCode -eq 0) {
        Write-Host ""
        Write-Host "Done: $Output"
    } else {
        Write-Host ""
        Write-Host "Failed with exit code $ExitCode."
    }

    Write-Host ""
    Read-Host "Press Enter to close"
    exit $ExitCode
}

Write-Host ""
$Text = Read-Host "Text"
if ([string]::IsNullOrWhiteSpace($Text)) {
    Write-Host "Canceled: empty text."
    exit 0
}

$Voice = Read-Host "Voice [tara/leah/jess/leo/dan/mia/zac/zoe] (default: tara)"
if ([string]::IsNullOrWhiteSpace($Voice)) {
    $Voice = "tara"
}

$AllowedVoices = @("tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe")
if ($AllowedVoices -notcontains $Voice) {
    Write-Host "Unknown voice '$Voice'. Using tara."
    $Voice = "tara"
}

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Output = Join-Path $OutputDir "$Voice-$Timestamp.wav"

& $TtsScript $Text -Voice $Voice -Output $Output
$ExitCode = $LASTEXITCODE

if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "Done: $Output"
} else {
    Write-Host ""
    Write-Host "Failed with exit code $ExitCode."
}

Write-Host ""
Read-Host "Press Enter to close"
exit $ExitCode
