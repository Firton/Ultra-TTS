[CmdletBinding(DefaultParameterSetName = "Single")]
param(
    [Parameter(Mandatory = $true, Position = 0, ParameterSetName = "Single")]
    [string]$Text,

    [Parameter(ParameterSetName = "Single")]
    [ValidateSet("tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe")]
    [string]$Voice = "tara",

    [Parameter(Mandatory = $true, ParameterSetName = "Script")]
    [string]$ScriptFile,

    [Parameter()]
    [string]$Output
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "gguf_orpheus.py"
$MultiScript = Join-Path $Root "multi_speaker_tts.py"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python virtual environment not found: $Python"
}

if (-not (Test-Path -LiteralPath $Script)) {
    throw "TTS script not found: $Script"
}

if ($PSCmdlet.ParameterSetName -eq "Script") {
    if (-not (Test-Path -LiteralPath $MultiScript)) {
        throw "Multi-speaker script not found: $MultiScript"
    }

    if (-not (Test-Path -LiteralPath $ScriptFile)) {
        throw "Script file not found: $ScriptFile"
    }

    if (-not $Output) {
        throw "Output is required for multi-speaker mode."
    }

    $ArgsList = @($MultiScript, "--script", $ScriptFile)
} else {
    $ArgsList = @($Script, "--text", $Text, "--voice", $Voice)
}

if ($Output) {
    $ArgsList += @("--output", $Output)
}

& $Python @ArgsList
exit $LASTEXITCODE
