import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
KOKORO_PYTHON = ROOT / ".venv-kokoro" / "Scripts" / "python.exe"
KOKORO_PACKAGE = ROOT / ".venv-kokoro" / "Lib" / "site-packages" / "kokoro"
WORKER = ROOT / "kokoro_worker.py"
DEFAULT_VOICE = "af_heart"
DEFAULT_SPEED = 1.0
MAX_TEXT_CHARS = 1200

AVAILABLE_VOICES = [
    "af_heart",
    "af_bella",
    "af_nicole",
    "af_sarah",
    "af_aoede",
    "af_kore",
    "af_nova",
    "af_sky",
    "af_alloy",
    "af_jessica",
    "af_river",
    "am_puck",
    "am_fenrir",
    "am_michael",
    "am_liam",
    "am_adam",
    "am_echo",
    "am_eric",
    "am_onyx",
    "am_santa",
    "bf_emma",
    "bf_isabella",
    "bf_alice",
    "bf_lily",
    "bm_george",
    "bm_fable",
    "bm_lewis",
    "bm_daniel",
]


def hidden_subprocess_kwargs():
    if os.name != "nt":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
        "startupinfo": startupinfo,
    }


def dependency_status():
    installed = KOKORO_PYTHON.exists() and KOKORO_PACKAGE.exists() and WORKER.exists()
    return {
        "installed": installed,
        "loaded": False,
        "device": "cpu",
        "error": None if installed else "Kokoro Python 3.11 environment is not installed.",
        "voices": AVAILABLE_VOICES,
        "defaultVoice": DEFAULT_VOICE,
        "defaultSpeed": DEFAULT_SPEED,
        "languages": {"a": "American English", "b": "British English"},
        "defaultLanguage": "a",
    }


def ensure_model(options=None):
    status = dependency_status()
    return {"ok": status["installed"], "status": status}


def unload_model():
    return None


def safe_voice(value):
    voice = (value or DEFAULT_VOICE).strip().lower()
    if voice not in AVAILABLE_VOICES:
        raise ValueError(f"Unknown Kokoro voice: {voice}")
    return voice


def safe_float(value, default, min_value, max_value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(min_value, min(number, max_value))


def generate_to_file(segments, output_path, options=None, silence_ms=0):
    status = dependency_status()
    if not status["installed"]:
        raise RuntimeError(status["error"])

    options = options or {}
    normalized = []
    for segment in segments:
        text = (segment.get("text") or "").strip()
        if not text:
            continue
        if len(text) > MAX_TEXT_CHARS:
            raise ValueError(f"Kokoro text is limited to {MAX_TEXT_CHARS} characters per line.")
        normalized.append({"text": text, "voice": safe_voice(segment.get("voice"))})

    if not normalized:
        raise ValueError("Text is empty.")

    request = {
        "outputPath": str(output_path),
        "segments": normalized,
        "silenceMs": silence_ms,
        "speed": safe_float(options.get("kokoroSpeed"), DEFAULT_SPEED, 0.5, 2.0),
    }
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    result = subprocess.run(
        [str(KOKORO_PYTHON), str(WORKER), "--json"],
        input=json.dumps(request, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
        timeout=900,
        **hidden_subprocess_kwargs(),
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    parsed = None
    if stdout:
        try:
            parsed = json.loads(stdout.splitlines()[-1])
        except json.JSONDecodeError:
            parsed = None

    if result.returncode != 0 or not parsed or not parsed.get("ok"):
        detail = parsed.get("error") if parsed else stderr or stdout
        raise RuntimeError(f"Kokoro generation failed: {detail}")

    return parsed
