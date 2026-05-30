import argparse
import ipaddress
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import local_paths

local_paths.configure_local_model_env()

import chatterbox_backend
import dia_backend
import kokoro_backend
import mlx_backend
import model_registry
import piper_backend
import text_pipeline
from gguf_orpheus import AVAILABLE_VOICES, DEFAULT_VOICE, SAMPLE_RATE, generate_speech_from_api
from multi_speaker_tts import write_combined_wav


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
OUTPUT_DIR = ROOT / "outputs" / "web"
LOG_DIR = ROOT / "logs"
MODEL_KEY = "orpheus-3b-0.1-ft"
LMSTUDIO_BASE_URL = "http://127.0.0.1:1234"
BACKEND_ORPHEUS = "orpheus"
BACKEND_CHATTERBOX = "chatterbox"
BACKEND_KOKORO = "kokoro"
BACKEND_PIPER = "piper"
BACKEND_DIA = "dia"
BACKEND_MLX = "mlx"
BACKENDS = {BACKEND_ORPHEUS, BACKEND_CHATTERBOX, BACKEND_KOKORO, BACKEND_PIPER, BACKEND_DIA, BACKEND_MLX}
LONGFORM_LIMITS = {
    BACKEND_ORPHEUS: 600,
    BACKEND_CHATTERBOX: chatterbox_backend.MAX_TEXT_CHARS,
    BACKEND_KOKORO: kokoro_backend.MAX_TEXT_CHARS,
    BACKEND_PIPER: piper_backend.MAX_TEXT_CHARS,
    BACKEND_MLX: mlx_backend.MAX_TEXT_CHARS,
}
SPEAKER_PATTERN = re.compile(r"^\s*(?P<label>[A-Za-z0-9_-]+)\s*[:：]\s*(?P<text>.+?)\s*$")
generation_lock = threading.Lock()


def ensure_stdio():
    if sys.stdout is not None and sys.stderr is not None:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = open(LOG_DIR / "web_app.log", "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = log_file
    if sys.stderr is None:
        sys.stderr = log_file


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


def run_lms(*args):
    try:
        result = subprocess.run(
            ["lms", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            **hidden_subprocess_kwargs(),
        )
    except FileNotFoundError:
        return {"ok": False, "exit_code": 127, "text": "lms command was not found."}

    text = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
    return {"ok": result.returncode == 0, "exit_code": result.returncode, "text": text}


def get_lmstudio_models_http():
    try:
        with urllib.request.urlopen(f"{LMSTUDIO_BASE_URL}/v1/models", timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {
            "serverRunning": False,
            "modelLoaded": False,
            "serverText": str(exc),
            "modelsText": "",
        }

    model_ids = [
        str(item.get("id", ""))
        for item in payload.get("data", [])
        if isinstance(item, dict)
    ]
    return {
        "serverRunning": True,
        "modelLoaded": MODEL_KEY in model_ids,
        "serverText": f"LM Studio server responded at {LMSTUDIO_BASE_URL}.",
        "modelsText": "\n".join(model_ids),
    }


def get_lmstudio_status():
    status = get_lmstudio_models_http()
    return {
        "serverRunning": status["serverRunning"],
        "modelLoaded": status["modelLoaded"],
        "modelKey": MODEL_KEY,
        "voices": AVAILABLE_VOICES,
        "defaultVoice": DEFAULT_VOICE,
        "serverText": status["serverText"],
        "modelsText": status["modelsText"],
    }


def get_app_status():
    orpheus = get_lmstudio_status()
    chatterbox = chatterbox_backend.dependency_status()
    kokoro = kokoro_backend.dependency_status()
    piper = piper_backend.dependency_status()
    dia = dia_backend.dependency_status()
    mlx = mlx_backend.dependency_status()
    chatterbox_files_ready = model_registry.is_installed("chatterbox")
    dia_files_ready = model_registry.is_installed("dia") and model_registry.is_installed("dia-dac")
    return {
        **orpheus,
        "backends": {
            BACKEND_ORPHEUS: {
                **orpheus,
                "name": "Orpheus",
                "kind": "lmstudio",
                "ready": orpheus["serverRunning"] and orpheus["modelLoaded"],
            },
            BACKEND_CHATTERBOX: {
                **chatterbox,
                "name": "Chatterbox Multilingual",
                "kind": "local",
                "ready": chatterbox["installed"] and chatterbox_files_ready,
                "filesReady": chatterbox_files_ready,
            },
            BACKEND_KOKORO: {
                **kokoro,
                "name": "Kokoro",
                "kind": "local-process",
                "ready": kokoro["installed"],
            },
            BACKEND_PIPER: {
                **piper,
                "name": "Piper",
                "kind": "local-process",
                "ready": piper["installed"] and bool(piper.get("installedVoices")),
            },
            BACKEND_DIA: {
                **dia,
                "name": "Dia",
                "kind": "local-process",
                "ready": dia["installed"] and dia_files_ready and dia["device"] != "cpu" and dia.get("recommended", True),
                "filesReady": dia_files_ready,
            },
            BACKEND_MLX: {
                **mlx,
                "name": "MLX-Audio",
                "kind": "local-process",
                "ready": mlx["installed"] and bool(mlx.get("models")),
            },
        },
    }


def get_model_inventory():
    inventory = model_registry.model_inventory()
    status = get_app_status()["backends"]
    for item in inventory["models"]:
        backend_status = status.get(item["backend"], {})
        item["runtimeReady"] = bool(backend_status.get("ready"))
        item["runtimeInstalled"] = bool(backend_status.get("installed", item["installed"]))
        item["runtimeError"] = backend_status.get("error")
    return inventory


def ensure_lmstudio():
    steps = []
    status = get_lmstudio_status()

    if not status["serverRunning"]:
        started = run_lms("server", "start", "--port", "1234")
        steps.append({"step": "server start", **started})
        if not started["ok"]:
            return {"ok": False, "steps": steps, "status": get_lmstudio_status()}

    status = get_lmstudio_status()
    if not status["modelLoaded"]:
        loaded = run_lms("load", MODEL_KEY, "--identifier", MODEL_KEY, "-y")
        steps.append({"step": "model load", **loaded})
        if not loaded["ok"]:
            return {"ok": False, "steps": steps, "status": get_lmstudio_status()}

    return {"ok": True, "steps": steps, "status": get_lmstudio_status()}


def safe_backend(value):
    backend = (value or BACKEND_ORPHEUS).strip().lower()
    if backend not in BACKENDS:
        raise ValueError(f"Unknown backend: {backend}")
    return backend


def ensure_backend(payload):
    backend = safe_backend((payload or {}).get("backend"))
    release_inactive_backends(backend)
    if backend == BACKEND_CHATTERBOX:
        return chatterbox_backend.ensure_model(payload or {})
    if backend == BACKEND_KOKORO:
        return kokoro_backend.ensure_model(payload or {})
    if backend == BACKEND_PIPER:
        return piper_backend.ensure_model(payload or {})
    if backend == BACKEND_DIA:
        return dia_backend.ensure_model(payload or {})
    if backend == BACKEND_MLX:
        return mlx_backend.ensure_model(payload or {})
    return ensure_lmstudio()


def release_inactive_backends(active_backend):
    if active_backend != BACKEND_CHATTERBOX:
        chatterbox_backend.unload_model()
    if active_backend != BACKEND_DIA:
        dia_backend.unload_model()
    if active_backend != BACKEND_KOKORO:
        kokoro_backend.unload_model()
    if active_backend != BACKEND_PIPER:
        piper_backend.unload_model()
    if active_backend != BACKEND_MLX:
        mlx_backend.unload_model()


def safe_voice(value):
    voice = (value or DEFAULT_VOICE).strip().lower()
    if voice not in AVAILABLE_VOICES:
        raise ValueError(f"Unknown voice: {voice}")
    return voice


def safe_kokoro_voice(value):
    return kokoro_backend.safe_voice(value)


def safe_piper_voice(value):
    return piper_backend.safe_voice(value)


def safe_mlx_voice(value, model_id=None):
    return mlx_backend.safe_voice(value, model_id)


def output_path(prefix):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    counter = 0
    while True:
        suffix = f"-{counter}" if counter else ""
        path = OUTPUT_DIR / f"{prefix}-{stamp}{suffix}.wav"
        if not path.exists():
            return path
        counter += 1


def generated_url(path):
    return f"/generated/{urllib.parse.quote(path.name)}"


def manifest_path(audio_path):
    return audio_path.with_suffix(".manifest.json")


def write_manifest(audio_path, payload):
    path = manifest_path(audio_path)
    payload = {
        "schema": "ultra-tts-manifest-v1",
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "audioFile": audio_path.name,
        "audioUrl": generated_url(audio_path),
        **payload,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def safe_int(value, default, min_value, max_value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(min_value, min(number, max_value))


def longform_segment_limit(backend, payload):
    if backend not in LONGFORM_LIMITS:
        raise ValueError(f"{backend} does not support long-form generation.")
    if backend == BACKEND_MLX:
        if not mlx_backend.supports_longform(payload or {}):
            raise ValueError("Selected MLX model does not support long-form narration.")
        backend_limit = mlx_backend.segment_limit(payload or {})
    else:
        backend_limit = LONGFORM_LIMITS[backend]

    requested = safe_int((payload or {}).get("maxSegmentChars"), backend_limit, 80, backend_limit)
    return min(requested, backend_limit)


def looks_like_speaker_script(text):
    lines = [
        line.strip()
        for line in (text or "").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if len(lines) < 2:
        return False
    return sum(1 for line in lines if SPEAKER_PATTERN.match(line)) == len(lines)


def split_for_backend_limit(text, max_chars):
    text = (text or "").strip()
    if len(text) <= max_chars:
        return [text] if text else []
    return [segment["text"] for segment in text_pipeline.segment_text(text, max_chars)]


def write_pcm16_wav(output_file, audio_chunks, sample_rate, silence_ms=0):
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    silence_frames = int(sample_rate * silence_ms / 1000)
    silence = b"\x00\x00" * silence_frames

    with wave.open(str(output_file), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        for index, chunk in enumerate(audio_chunks):
            wav_file.writeframes(chunk)
            if index != len(audio_chunks) - 1 and silence:
                wav_file.writeframes(silence)


def audio_duration(path):
    with wave.open(str(path), "rb") as wav_file:
        return wav_file.getnframes() / wav_file.getframerate()


def parse_script(script_text, speaker_map):
    utterances = []
    normalized_map = {
        str(label).strip().upper(): safe_voice(voice)
        for label, voice in (speaker_map or {}).items()
        if str(label).strip()
    }

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = SPEAKER_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text' or 'tara: text'.")

        label = match.group("label").strip()
        voice = normalized_map.get(label.upper())
        if voice is None and label.lower() in AVAILABLE_VOICES:
            voice = label.lower()
        if voice is None:
            raise ValueError(f"Line {line_number}: speaker '{label}' has no assigned voice.")

        utterances.append(
            {
                "label": label,
                "voice": voice,
                "text": match.group("text").strip(),
                "lineNumber": line_number,
            }
        )

    if not utterances:
        raise ValueError("Script has no lines to generate.")

    return utterances


def parse_chatterbox_script(script_text):
    utterances = []

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = SPEAKER_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text'.")

        utterances.append(
            {
                "label": match.group("label").strip(),
                "voice": "chatterbox",
                "text": match.group("text").strip(),
                "lineNumber": line_number,
            }
        )

    if not utterances:
        raise ValueError("Script has no lines to generate.")

    return utterances


def parse_kokoro_script(script_text, speaker_map):
    utterances = []
    normalized_map = {
        str(label).strip().upper(): safe_kokoro_voice(voice)
        for label, voice in (speaker_map or {}).items()
        if str(label).strip()
    }

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = SPEAKER_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text' or a Kokoro voice label.")

        label = match.group("label").strip()
        voice = normalized_map.get(label.upper())
        if voice is None and label.lower() in kokoro_backend.AVAILABLE_VOICES:
            voice = label.lower()
        if voice is None:
            raise ValueError(f"Line {line_number}: speaker '{label}' has no assigned Kokoro voice.")

        utterances.append(
            {
                "label": label,
                "voice": voice,
                "text": match.group("text").strip(),
                "lineNumber": line_number,
            }
        )

    if not utterances:
        raise ValueError("Script has no lines to generate.")

    return utterances


def parse_piper_script(script_text, speaker_map):
    utterances = []
    normalized_map = {
        str(label).strip().upper(): safe_piper_voice(voice)
        for label, voice in (speaker_map or {}).items()
        if str(label).strip()
    }

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = SPEAKER_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text' or a Piper voice label.")

        label = match.group("label").strip()
        voice = normalized_map.get(label.upper())
        if voice is None and label in piper_backend.VOICE_CATALOG:
            voice = label
        if voice is None:
            raise ValueError(f"Line {line_number}: speaker '{label}' has no assigned Piper voice.")

        utterances.append(
            {
                "label": label,
                "voice": voice,
                "text": match.group("text").strip(),
                "lineNumber": line_number,
            }
        )

    if not utterances:
        raise ValueError("Script has no lines to generate.")

    return utterances


def parse_mlx_script(script_text, speaker_map, model_id):
    model_id = mlx_backend.safe_model_id(model_id)
    if model_id == "mlx-dia":
        return [
            {
                "label": "dia",
                "voice": "S1/S2",
                "text": dia_backend.script_to_dialogue(script_text or "", SPEAKER_PATTERN),
                "lineNumber": 1,
            }
        ]

    utterances = []
    max_chars = mlx_backend.segment_limit({"mlxModelId": model_id})
    normalized_map = {
        str(label).strip().upper(): safe_mlx_voice(voice, model_id)
        for label, voice in (speaker_map or {}).items()
        if str(label).strip()
    }

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = SPEAKER_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text' or an MLX voice label.")

        label = match.group("label").strip()
        voice = normalized_map.get(label.upper())
        if voice is None:
            try:
                voice = safe_mlx_voice(label, model_id)
            except ValueError:
                voice = None
        if voice is None:
            raise ValueError(f"Line {line_number}: speaker '{label}' has no assigned MLX voice.")

        for chunk_index, chunk_text in enumerate(split_for_backend_limit(match.group("text"), max_chars), start=1):
            utterances.append(
                {
                    "label": label,
                    "voice": voice,
                    "text": chunk_text,
                    "lineNumber": line_number,
                    "chunkIndex": chunk_index,
                }
            )

    if not utterances:
        raise ValueError("Script has no lines to generate.")

    return utterances


def generate_single(payload):
    backend = safe_backend(payload.get("backend"))
    text = (payload.get("text") or "").strip()
    if not text:
        raise ValueError("Text is empty.")

    if backend == BACKEND_CHATTERBOX:
        language_id = chatterbox_backend.safe_language(payload.get("languageId"))
        out_path = output_path(f"single-chatterbox-{language_id}")
        sample_rate, audio = chatterbox_backend.generate_waveform(text, payload)
        write_pcm16_wav(out_path, [audio], sample_rate)
        return audio_result(
            out_path,
            [{"label": "chatterbox", "voice": "chatterbox", "text": text}],
        )

    if backend == BACKEND_KOKORO:
        voice = safe_kokoro_voice(payload.get("voice"))
        out_path = output_path(f"single-kokoro-{voice}")
        kokoro_backend.generate_to_file([{"voice": voice, "text": text}], out_path, payload)
        return audio_result(out_path, [{"label": voice, "voice": voice, "text": text}])

    if backend == BACKEND_PIPER:
        voice = safe_piper_voice(payload.get("voice"))
        out_path = output_path(f"single-piper-{voice}")
        piper_backend.generate_to_file([{"voice": voice, "text": text}], out_path, {**payload, "voice": voice})
        return audio_result(out_path, [{"label": voice, "voice": voice, "text": text}])

    if backend == BACKEND_DIA:
        out_path = output_path("single-dia")
        dia_backend.generate_to_file(dia_backend.single_text(text), out_path, payload)
        return audio_result(out_path, [{"label": "S1", "voice": "dia", "text": text}])

    if backend == BACKEND_MLX:
        model_id = mlx_backend.safe_model_id(payload.get("mlxModelId"))
        voice = safe_mlx_voice(payload.get("voice"), model_id)
        out_path = output_path(f"single-{model_id}-{voice}")
        mlx_backend.generate_to_file([{"voice": voice, "text": text}], out_path, payload)
        return audio_result(out_path, [{"label": voice, "voice": voice, "text": text}])

    voice = safe_voice(payload.get("voice"))
    out_path = output_path(f"single-{voice}")
    chunks = generate_speech_from_api(text, voice=voice, output_file=str(out_path))
    if not chunks:
        raise RuntimeError("No audio was generated.")

    return audio_result(out_path, [{"label": voice, "voice": voice, "text": text}])


def generate_script(payload):
    backend = safe_backend(payload.get("backend"))
    silence_ms = max(0, min(int(payload.get("silenceMs") or 250), 5000))

    if backend == BACKEND_CHATTERBOX:
        language_id = chatterbox_backend.safe_language(payload.get("languageId"))
        utterances = parse_chatterbox_script(payload.get("script") or "")
        out_path = output_path(f"script-chatterbox-{language_id}")
        all_audio = []
        sample_rate = None

        for utterance in utterances:
            sample_rate, audio = chatterbox_backend.generate_waveform(utterance["text"], payload)
            all_audio.append(audio)

        write_pcm16_wav(str(out_path), all_audio, sample_rate, silence_ms)
        return audio_result(out_path, utterances)

    if backend == BACKEND_KOKORO:
        utterances = parse_kokoro_script(payload.get("script") or "", payload.get("speakerMap") or {})
        out_path = output_path("script-kokoro")
        kokoro_backend.generate_to_file(utterances, out_path, payload, silence_ms)
        return audio_result(out_path, utterances)

    if backend == BACKEND_PIPER:
        utterances = parse_piper_script(payload.get("script") or "", payload.get("speakerMap") or {})
        out_path = output_path("script-piper")
        piper_backend.generate_to_file(utterances, out_path, payload, silence_ms)
        return audio_result(out_path, utterances)

    if backend == BACKEND_DIA:
        dia_text = dia_backend.script_to_dialogue(payload.get("script") or "", SPEAKER_PATTERN)
        out_path = output_path("script-dia")
        dia_backend.generate_to_file(dia_text, out_path, payload)
        return audio_result(
            out_path,
            [{"label": "dia", "voice": "dia", "text": dia_text}],
        )

    if backend == BACKEND_MLX:
        model_id = mlx_backend.safe_model_id(payload.get("mlxModelId"))
        utterances = parse_mlx_script(payload.get("script") or "", payload.get("speakerMap") or {}, model_id)
        out_path = output_path(f"script-{model_id}")
        mlx_backend.generate_to_file(utterances, out_path, payload, silence_ms)
        return audio_result(out_path, utterances)

    utterances = parse_script(payload.get("script") or "", payload.get("speakerMap") or {})
    out_path = output_path("script")
    all_audio = []

    for utterance in utterances:
        chunks = generate_speech_from_api(utterance["text"], voice=utterance["voice"])
        if not chunks:
            raise RuntimeError(
                f"No audio generated for line {utterance['lineNumber']} ({utterance['label']})."
            )
        all_audio.append(chunks)

    write_combined_wav(str(out_path), all_audio, silence_ms)
    return audio_result(out_path, utterances)


def generate_longform(payload):
    backend = safe_backend(payload.get("backend"))
    if backend == BACKEND_DIA:
        raise ValueError("Dia is dialogue-only and is not available for long-form narration.")

    text = (payload.get("text") or "").strip()
    if not text:
        raise ValueError("Long-form text is empty.")

    title = (payload.get("title") or "").strip()
    segment_limit = longform_segment_limit(backend, payload)
    silence_ms = safe_int(payload.get("silenceMs"), 450, 0, 5000)
    if backend == BACKEND_MLX and looks_like_speaker_script(text):
        model_id = mlx_backend.safe_model_id(payload.get("mlxModelId"))
        utterances = parse_mlx_script(text, payload.get("speakerMap") or {}, model_id)
        prefix = f"longscript-{model_id}-{text_pipeline.clean_slug(title, 'script')}"
        out_path = output_path(prefix)
        mlx_backend.generate_to_file(utterances, out_path, payload, silence_ms)
        language = mlx_backend.safe_language(payload.get("mlxLanguageId") or payload.get("languageId"), model_id)
        manifest = write_manifest(
            out_path,
            {
                "type": "longscript",
                "title": title,
                "backend": backend,
                "modelId": model_id,
                "voice": "speaker-map",
                "language": language,
                "segmentLimit": segment_limit,
                "silenceMs": silence_ms,
                "duration": round(audio_duration(out_path), 2),
                "segments": utterances,
            },
        )
        return audio_result(out_path, utterances, manifest)

    segments = text_pipeline.segment_text(text, segment_limit)
    prefix_backend = mlx_backend.safe_model_id(payload.get("mlxModelId")) if backend == BACKEND_MLX else backend
    prefix = f"longform-{prefix_backend}-{text_pipeline.clean_slug(title, 'article')}"
    out_path = output_path(prefix)

    if backend == BACKEND_CHATTERBOX:
        language_id = chatterbox_backend.safe_language(payload.get("languageId"))
        all_audio = []
        sample_rate = None
        for segment in segments:
            sample_rate, audio = chatterbox_backend.generate_waveform(segment["text"], payload)
            all_audio.append(audio)
        write_pcm16_wav(str(out_path), all_audio, sample_rate, silence_ms)
        voice = "chatterbox"
        language = language_id

    elif backend == BACKEND_KOKORO:
        voice = safe_kokoro_voice(payload.get("voice"))
        kokoro_segments = [{"voice": voice, "text": segment["text"]} for segment in segments]
        kokoro_backend.generate_to_file(kokoro_segments, out_path, payload, silence_ms)
        language = payload.get("languageId") or kokoro_backend.dependency_status().get("defaultLanguage")

    elif backend == BACKEND_PIPER:
        voice = safe_piper_voice(payload.get("voice"))
        piper_segments = [{"voice": voice, "text": segment["text"]} for segment in segments]
        piper_backend.generate_to_file(piper_segments, out_path, {**payload, "voice": voice}, silence_ms)
        language = piper_backend.VOICE_CATALOG[voice]["language"]

    elif backend == BACKEND_MLX:
        model_id = mlx_backend.safe_model_id(payload.get("mlxModelId"))
        if not mlx_backend.supports_longform(payload):
            raise ValueError("Selected MLX model does not support long-form narration.")
        voice = safe_mlx_voice(payload.get("voice"), model_id)
        mlx_segments = [{"voice": voice, "text": segment["text"]} for segment in segments]
        mlx_backend.generate_to_file(mlx_segments, out_path, payload, silence_ms)
        language = mlx_backend.safe_language(payload.get("mlxLanguageId") or payload.get("languageId"), model_id)

    else:
        voice = safe_voice(payload.get("voice"))
        all_audio = []
        for segment in segments:
            chunks = generate_speech_from_api(segment["text"], voice=voice)
            if not chunks:
                raise RuntimeError(f"No audio generated for segment {segment['index']}.")
            all_audio.append(chunks)
        write_combined_wav(str(out_path), all_audio, silence_ms)
        language = payload.get("languageId") or "en"

    utterances = [
        {
            "label": segment["id"],
            "voice": voice,
            "text": segment["text"],
            "lineNumber": segment["index"],
            "paragraphIndex": segment["paragraphIndex"],
            "chars": segment["chars"],
        }
        for segment in segments
    ]
    manifest = write_manifest(
        out_path,
        {
            "type": "longform",
            "title": title,
            "backend": backend,
            "modelId": payload.get("mlxModelId") if backend == BACKEND_MLX else None,
            "voice": voice,
            "language": language,
            "segmentLimit": segment_limit,
            "silenceMs": silence_ms,
            "duration": round(audio_duration(out_path), 2),
            "segments": utterances,
        },
    )
    return audio_result(out_path, utterances, manifest)


def audio_result(path, utterances, manifest=None):
    result = {
        "fileName": path.name,
        "url": generated_url(path),
        "duration": round(audio_duration(path), 2),
        "utterances": utterances,
    }
    if manifest:
        result["manifestFileName"] = manifest.name
        result["manifestUrl"] = generated_url(manifest)
    return result


def app_is_running(url):
    try:
        with urllib.request.urlopen(f"{url}/api/status", timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False


def open_url(url):
    if os.name == "nt":
        subprocess.Popen(
            ["cmd.exe", "/d", "/c", "start", "", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **hidden_subprocess_kwargs(),
        )
    else:
        webbrowser.open(url)


def hostname_is_loopback(hostname):
    if not hostname:
        return False
    if hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def request_is_local_control(handler):
    if not hostname_is_loopback(handler.client_address[0]):
        return False

    host = handler.headers.get("Host")
    if host:
        if not hostname_is_loopback(urllib.parse.urlparse(f"//{host}").hostname):
            return False

    origin = handler.headers.get("Origin")
    if origin:
        if not hostname_is_loopback(urllib.parse.urlparse(origin).hostname):
            return False

    return True


def schedule_process_control(server, restart=False):
    def worker():
        time.sleep(0.35)
        action = "Restarting" if restart else "Stopping"
        print(f"{action} Ultra-TTS Web from UI.")
        server.shutdown()
        server.server_close()
        if restart:
            os.execv(sys.executable, [sys.executable, *sys.argv])
        os._exit(0)

    thread = threading.Thread(target=worker, name="app-control", daemon=False)
    thread.start()


class AppHandler(BaseHTTPRequestHandler):
    server_version = "UltraTTSWeb/1.0"

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_json({"ok": True, **get_app_status()})
            return

        if path == "/api/models":
            self.send_json({"ok": True, **get_model_inventory()})
            return

        if path.startswith("/generated/"):
            self.send_generated(path.removeprefix("/generated/"))
            return

        if path == "/":
            path = "/index.html"

        self.send_static(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            payload = self.read_json()
            if parsed.path == "/api/restart":
                if not request_is_local_control(self):
                    self.send_json({"ok": False, "error": "App control is only available from localhost."}, 403)
                    return
                self.send_json({"ok": True, "action": "restart"})
                schedule_process_control(self.server, restart=True)
                return

            if parsed.path == "/api/shutdown":
                if not request_is_local_control(self):
                    self.send_json({"ok": False, "error": "App control is only available from localhost."}, 403)
                    return
                self.send_json({"ok": True, "action": "shutdown"})
                schedule_process_control(self.server, restart=False)
                return

            if parsed.path == "/api/ensure":
                result = ensure_backend(payload)
                self.send_json(result, 200 if result["ok"] else 500)
                return

            if parsed.path == "/api/generate-single":
                self.ensure_before_generate(payload)
                with generation_lock:
                    self.send_json({"ok": True, **generate_single(payload)})
                return

            if parsed.path == "/api/generate-script":
                self.ensure_before_generate(payload)
                with generation_lock:
                    self.send_json({"ok": True, **generate_script(payload)})
                return

            if parsed.path == "/api/generate-longform":
                if safe_backend(payload.get("backend")) == BACKEND_DIA:
                    raise ValueError("Dia is dialogue-only and is not available for long-form narration.")
                if safe_backend(payload.get("backend")) == BACKEND_MLX and not mlx_backend.supports_longform(payload):
                    raise ValueError("Selected MLX model does not support long-form narration.")
                self.ensure_before_generate(payload)
                with generation_lock:
                    self.send_json({"ok": True, **generate_longform(payload)})
                return

            self.send_json({"ok": False, "error": "Not found."}, 404)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)

    def ensure_before_generate(self, payload):
        backend = safe_backend(payload.get("backend"))
        release_inactive_backends(backend)

        if backend == BACKEND_CHATTERBOX:
            status = chatterbox_backend.dependency_status()
            if not status["installed"]:
                raise RuntimeError(f"Chatterbox is not installed: {status['error']}")
            if not model_registry.is_installed("chatterbox"):
                raise RuntimeError("Chatterbox model files are missing. Run scripts/download_models.py --current-hf chatterbox.")
            return

        if backend == BACKEND_KOKORO:
            status = kokoro_backend.dependency_status()
            if not status["installed"]:
                raise RuntimeError(f"Kokoro is not installed: {status['error']}")
            return

        if backend == BACKEND_PIPER:
            status = piper_backend.dependency_status()
            if not status["installed"]:
                raise RuntimeError(f"Piper is not installed: {status['error']}")
            voice = payload.get("voice") or status.get("defaultVoice")
            if voice not in status.get("installedVoices", []):
                raise RuntimeError(
                    f"Piper voice is not downloaded: {voice}. "
                    "Run scripts/download_models.py --piper-basic."
                )
            return

        if backend == BACKEND_DIA:
            status = dia_backend.dependency_status()
            if not status["installed"]:
                raise RuntimeError(f"Dia is not installed: {status['error']}")
            if not model_registry.is_installed("dia"):
                raise RuntimeError("Dia model files are missing. Run scripts/download_models.py --current-hf dia.")
            if not model_registry.is_installed("dia-dac"):
                raise RuntimeError("Dia DAC audio tokenizer is missing. Run scripts/download_models.py --current-hf dia-dac.")
            if status["device"] == "cpu":
                raise RuntimeError("Dia needs a CUDA or MPS GPU for practical local generation.")
            if status.get("recommended") is False and not payload.get("diaAllowLowVram"):
                raise RuntimeError(
                    "Dia needs about 10GB VRAM for practical local use. "
                    f"This GPU has {status.get('vramGb')}GB, so output can become broken audio. "
                    "Use Kokoro for English, or enable the low-VRAM Dia option if you still want to test it."
                )
            return

        if backend == BACKEND_MLX:
            status = mlx_backend.dependency_status()
            model_id = mlx_backend.safe_model_id(payload.get("mlxModelId") or status.get("defaultModelId"))
            if not status["installed"]:
                raise RuntimeError(f"MLX-Audio is not installed: {status['error']}")
            if not mlx_backend.model_installed(model_id):
                raise RuntimeError(
                    f"MLX model files are missing for {model_id}. "
                    f"Run scripts/download_models.py --mlx {model_id}."
                )
            return

        result = ensure_lmstudio()
        if not result["ok"]:
            raise RuntimeError("LM Studio server or Orpheus model could not be started.")

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, request_path):
        relative = request_path.lstrip("/")
        target = (WEB_ROOT / relative).resolve()
        if not str(target).startswith(str(WEB_ROOT.resolve())) or not target.is_file():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_generated(self, encoded_name):
        name = urllib.parse.unquote(encoded_name)
        target = (OUTPUT_DIR / name).resolve()
        if not str(target).startswith(str(OUTPUT_DIR.resolve())) or not target.is_file():
            self.send_error(404)
            return

        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    ensure_stdio()
    parser = argparse.ArgumentParser(description="Local Ultra-TTS web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the app in the default browser")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    if app_is_running(url):
        print(f"Ultra-TTS Web is already running at {url}")
        if args.open:
            open_url(url)
        return 0

    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f"Ultra-TTS Web is running at {url}")
    print("Close this window to stop the web app.")

    if args.open:
        threading.Timer(0.4, lambda: open_url(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping Ultra-TTS Web.")
    finally:
        server.server_close()


if __name__ == "__main__":
    sys.exit(main())
