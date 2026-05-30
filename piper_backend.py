import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import local_paths


local_paths.configure_local_model_env()

DEFAULT_VOICE = "en_US-lessac-medium"
MAX_TEXT_CHARS = 1000
PIPER_MODELS_DIR = local_paths.PIPER_MODELS_DIR

VOICE_CATALOG = {
    "en_US-lessac-medium": {
        "name": "English US / Lessac",
        "language": "en_US",
        "path": "en/en_US/lessac/medium/en_US-lessac-medium.onnx",
    },
    "en_GB-alba-medium": {
        "name": "English UK / Alba",
        "language": "en_GB",
        "path": "en/en_GB/alba/medium/en_GB-alba-medium.onnx",
    },
    "de_DE-thorsten-medium": {
        "name": "German / Thorsten",
        "language": "de_DE",
        "path": "de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx",
    },
    "fr_FR-siwis-medium": {
        "name": "French / Siwis",
        "language": "fr_FR",
        "path": "fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx",
    },
    "es_ES-sharvard-medium": {
        "name": "Spanish / Sharvard",
        "language": "es_ES",
        "path": "es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx",
    },
    "zh_CN-huayan-medium": {
        "name": "Chinese / Huayan",
        "language": "zh_CN",
        "path": "zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx",
    },
}


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


def piper_binary():
    override = os.getenv("PIPER_BIN")
    if override:
        return Path(override).expanduser()

    candidates = [
        local_paths.ROOT / ".venv-piper" / ("Scripts/piper.exe" if os.name == "nt" else "bin/piper"),
        local_paths.ROOT / ".venv" / ("Scripts/piper.exe" if os.name == "nt" else "bin/piper"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    found = shutil.which("piper")
    return Path(found) if found else None


def voice_model_path(voice):
    entry = VOICE_CATALOG[safe_voice(voice)]
    return PIPER_MODELS_DIR / entry["path"]


def voice_config_path(voice):
    return Path(str(voice_model_path(voice)) + ".json")


def installed_voices():
    return [
        voice
        for voice in VOICE_CATALOG
        if voice_model_path(voice).exists() and voice_config_path(voice).exists()
    ]


def dependency_status():
    binary = piper_binary()
    voices = installed_voices()
    return {
        "installed": binary is not None,
        "loaded": False,
        "device": "local-process",
        "error": None if binary else "Piper executable was not found. Install piper-tts into .venv-piper or set PIPER_BIN.",
        "binary": str(binary) if binary else None,
        "voices": voices or list(VOICE_CATALOG),
        "installedVoices": voices,
        "voiceCatalog": VOICE_CATALOG,
        "defaultVoice": DEFAULT_VOICE if DEFAULT_VOICE in voices else (voices[0] if voices else DEFAULT_VOICE),
        "modelDir": str(PIPER_MODELS_DIR),
    }


def ensure_model(options=None):
    options = options or {}
    status = dependency_status()
    voice = safe_voice(options.get("voice") or status["defaultVoice"])
    if not status["installed"]:
        return {"ok": False, "status": status}
    if voice not in installed_voices():
        status["error"] = f"Piper voice is not downloaded: {voice}. Run scripts/download_models.py --piper-basic."
        return {"ok": False, "status": status}
    return {"ok": True, "status": status}


def unload_model():
    return None


def safe_voice(value):
    voice = (value or DEFAULT_VOICE).strip()
    if voice not in VOICE_CATALOG:
        raise ValueError(f"Unknown Piper voice: {voice}")
    return voice


def run_piper(text, output_path, voice, options=None):
    binary = piper_binary()
    if not binary:
        raise RuntimeError("Piper executable was not found. Install piper-tts into .venv-piper or set PIPER_BIN.")

    text = (text or "").strip()
    if not text:
        raise ValueError("Text is empty.")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"Piper text is limited to {MAX_TEXT_CHARS} characters per segment.")

    model_path = voice_model_path(voice)
    config_path = voice_config_path(voice)
    if not model_path.exists() or not config_path.exists():
        raise RuntimeError(f"Piper voice files are missing for {voice}. Expected {model_path} and {config_path}.")

    command = [
        str(binary),
        "--model",
        str(model_path),
        "--config",
        str(config_path),
        "--output_file",
        str(output_path),
    ]
    result = subprocess.run(
        command,
        input=text + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=900,
        **hidden_subprocess_kwargs(),
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "piper failed").strip()
        raise RuntimeError(f"Piper generation failed: {detail}")


def generate_to_file(segments, output_path, options=None, silence_ms=0):
    options = options or {}
    voice = safe_voice(options.get("voice"))
    normalized = []
    for segment in segments:
        text = (segment.get("text") or "").strip()
        if text:
            normalized.append(text)

    if not normalized:
        raise ValueError("Text is empty.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="piper-", dir=str(output_path.parent)) as temp_dir:
        part_paths = []
        for index, text in enumerate(normalized, start=1):
            part_path = Path(temp_dir) / f"part-{index:04d}.wav"
            run_piper(text, part_path, voice, options)
            part_paths.append(part_path)
        combine_wavs(part_paths, output_path, silence_ms)

    return {"ok": True, "voice": voice}


def combine_wavs(part_paths, output_path, silence_ms):
    if not part_paths:
        raise ValueError("No Piper audio was generated.")

    with wave.open(str(part_paths[0]), "rb") as first:
        channels = first.getnchannels()
        sample_width = first.getsampwidth()
        sample_rate = first.getframerate()

    silence_frames = int(sample_rate * max(0, silence_ms) / 1000)
    silence = b"\x00" * silence_frames * channels * sample_width

    with wave.open(str(output_path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(sample_width)
        output.setframerate(sample_rate)

        for index, part_path in enumerate(part_paths):
            with wave.open(str(part_path), "rb") as part:
                if (
                    part.getnchannels() != channels
                    or part.getsampwidth() != sample_width
                    or part.getframerate() != sample_rate
                ):
                    raise RuntimeError("Piper generated WAV parts with incompatible formats.")
                output.writeframes(part.readframes(part.getnframes()))

            if index != len(part_paths) - 1 and silence:
                output.writeframes(silence)
