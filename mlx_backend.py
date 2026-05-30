import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import local_paths


local_paths.configure_local_model_env()

DEFAULT_MODEL_ID = "mlx-chatterbox"
MAX_TEXT_CHARS = 1200

CHATTERBOX_LANGUAGES = {
    "ar": "Arabic",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "sv": "Swedish",
    "sw": "Swahili",
    "tr": "Turkish",
    "zh": "Chinese",
}

QWEN_LANGUAGES = {
    "auto": "Auto",
    "japanese": "Japanese",
    "english": "English",
    "chinese": "Chinese",
    "korean": "Korean",
    "german": "German",
    "french": "French",
    "russian": "Russian",
    "portuguese": "Portuguese",
    "spanish": "Spanish",
    "italian": "Italian",
}

KOKORO_LANGUAGES = {
    "a": "American English",
    "b": "British English",
    "j": "Japanese",
}

KOKORO_VOICES = [
    "af_heart",
    "af_bella",
    "af_nicole",
    "af_sarah",
    "af_aoede",
    "af_kore",
    "af_nova",
    "af_sky",
    "am_puck",
    "am_fenrir",
    "am_michael",
    "bf_emma",
    "bf_isabella",
    "bm_george",
    "bm_fable",
    "jf_alpha",
    "jf_gongitsune",
    "jf_nezumi",
    "jf_tebukuro",
    "jm_kumo",
]

MODEL_CATALOG = {
    "mlx-chatterbox": {
        "name": "Chatterbox MLX",
        "repo": "mlx-community/chatterbox-fp16",
        "path": local_paths.MODELS_DIR / "huggingface" / "mlx-community__chatterbox-fp16",
        "languages": CHATTERBOX_LANGUAGES,
        "defaultLanguage": "ja",
        "voices": ["default"],
        "defaultVoice": "default",
        "maxTextChars": 300,
        "supportsLongform": True,
        "supportsReferenceAudio": True,
        "supportsInstruct": False,
        "role": "MLX多言語TTS",
    },
    "mlx-qwen3-tts": {
        "name": "Qwen3-TTS MLX Base 8bit (参照音声)",
        "repo": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit",
        "path": local_paths.MODELS_DIR
        / "huggingface"
        / "mlx-community__Qwen3-TTS-12Hz-1.7B-Base-8bit",
        "languages": QWEN_LANGUAGES,
        "defaultLanguage": "japanese",
        "voices": ["reference"],
        "defaultVoice": "reference",
        "maxTextChars": 500,
        "supportsLongform": True,
        "supportsReferenceAudio": True,
        "supportsInstruct": False,
        "role": "MLX TTS LLM",
    },
    "mlx-qwen3-custom": {
        "name": "Qwen3-TTS MLX CustomVoice 8bit (プリセット声)",
        "repo": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit",
        "path": local_paths.MODELS_DIR
        / "huggingface"
        / "mlx-community__Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit",
        "languages": QWEN_LANGUAGES,
        "defaultLanguage": "japanese",
        "voices": ["Ryan", "Vivian", "Aiden", "Serena", "Uncle_Fu", "Ono_Anna", "Sohee", "Eric", "Dylan"],
        "defaultVoice": "Ryan",
        "maxTextChars": 500,
        "supportsLongform": True,
        "supportsReferenceAudio": False,
        "supportsInstruct": True,
        "role": "MLX TTS LLM",
    },
    "mlx-qwen3-voice-design": {
        "name": "Qwen3-TTS MLX VoiceDesign 8bit",
        "repo": "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit",
        "path": local_paths.MODELS_DIR
        / "huggingface"
        / "mlx-community__Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit",
        "languages": QWEN_LANGUAGES,
        "defaultLanguage": "japanese",
        "voices": ["designed"],
        "defaultVoice": "designed",
        "maxTextChars": 500,
        "supportsLongform": True,
        "supportsReferenceAudio": False,
        "supportsInstruct": True,
        "role": "MLX TTS LLM",
    },
    "mlx-kokoro": {
        "name": "Kokoro MLX 82M 8bit",
        "repo": "mlx-community/Kokoro-82M-8bit",
        "path": local_paths.MODELS_DIR / "huggingface" / "mlx-community__Kokoro-82M-8bit",
        "languages": KOKORO_LANGUAGES,
        "defaultLanguage": "j",
        "voices": KOKORO_VOICES,
        "defaultVoice": "jf_alpha",
        "maxTextChars": 1200,
        "supportsLongform": True,
        "supportsReferenceAudio": False,
        "supportsInstruct": False,
        "role": "MLX軽量TTS",
    },
    "mlx-dia": {
        "name": "Dia MLX 1.6B fp16",
        "repo": "mlx-community/Dia-1.6B-fp16",
        "path": local_paths.MODELS_DIR / "huggingface" / "mlx-community__Dia-1.6B-fp16",
        "languages": {"en": "English"},
        "defaultLanguage": "en",
        "voices": ["S1/S2"],
        "defaultVoice": "S1/S2",
        "maxTextChars": 1600,
        "supportsLongform": False,
        "supportsReferenceAudio": True,
        "supportsInstruct": False,
        "role": "MLX会話TTS",
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


def mlx_python():
    override = os.getenv("MLX_PYTHON")
    if override:
        return Path(override).expanduser()

    candidate = local_paths.ROOT / ".venv-mlx" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if candidate.exists():
        return candidate

    found = shutil.which("python3")
    return Path(found) if found else None


def model_meta(model_id):
    model_id = safe_model_id(model_id)
    return MODEL_CATALOG[model_id]


def safe_model_id(value):
    model_id = (value or DEFAULT_MODEL_ID).strip()
    if model_id not in MODEL_CATALOG:
        raise ValueError(f"Unknown MLX model: {model_id}")
    return model_id


def safe_language(value, model_id=None):
    meta = model_meta(model_id or DEFAULT_MODEL_ID)
    language = (value or meta["defaultLanguage"]).strip()
    if language not in meta["languages"]:
        raise ValueError(f"Unknown language for {meta['name']}: {language}")
    return language


def safe_voice(value, model_id=None):
    meta = model_meta(model_id or DEFAULT_MODEL_ID)
    voices = meta.get("voices") or []
    voice = (value or meta.get("defaultVoice") or (voices[0] if voices else "")).strip()
    if voices and voice not in voices:
        raise ValueError(f"Unknown voice for {meta['name']}: {voice}")
    return voice


def safe_seed(value):
    try:
        seed = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, min(seed, 2_147_483_647))


def model_installed(model_id):
    meta = model_meta(model_id)
    path = meta["path"]
    return path.exists() and (path / "config.json").exists() and bool(
        list(path.glob("*.safetensors")) or list(path.glob("*.npz"))
    )


def installed_model_ids():
    return [model_id for model_id in MODEL_CATALOG if model_installed(model_id)]


def default_model_id():
    installed = set(installed_model_ids())
    for model_id in [
        "mlx-chatterbox",
        "mlx-qwen3-tts",
        "mlx-qwen3-custom",
        "mlx-qwen3-voice-design",
        "mlx-kokoro",
        "mlx-dia",
    ]:
        if model_id in installed:
            return model_id
    return DEFAULT_MODEL_ID


def catalog_status():
    return {
        model_id: {
            "id": model_id,
            "name": meta["name"],
            "repo": meta["repo"],
            "path": str(meta["path"]),
            "installed": model_installed(model_id),
            "languages": meta["languages"],
            "defaultLanguage": meta["defaultLanguage"],
            "voices": meta["voices"],
            "defaultVoice": meta["defaultVoice"],
            "maxTextChars": meta["maxTextChars"],
            "supportsLongform": meta["supportsLongform"],
            "supportsReferenceAudio": meta["supportsReferenceAudio"],
            "supportsInstruct": meta["supportsInstruct"],
            "role": meta["role"],
        }
        for model_id, meta in MODEL_CATALOG.items()
    }


def dependency_status():
    python = mlx_python()
    installed_ids = installed_model_ids()
    selected = default_model_id()
    selected_meta = MODEL_CATALOG[selected]
    return {
        "installed": python is not None,
        "loaded": False,
        "device": "mlx",
        "error": None if python else "MLX Python environment was not found. Create .venv-mlx and install requirements-mlx.txt.",
        "python": str(python) if python else None,
        "models": installed_ids,
        "defaultModelId": selected,
        "modelCatalog": catalog_status(),
        "voices": selected_meta["voices"],
        "defaultVoice": selected_meta["defaultVoice"],
        "languages": selected_meta["languages"],
        "defaultLanguage": selected_meta["defaultLanguage"],
    }


def ensure_model(options=None):
    options = options or {}
    status = dependency_status()
    model_id = safe_model_id(options.get("mlxModelId") or status["defaultModelId"])
    if not status["installed"]:
        return {"ok": False, "status": status}
    if not model_installed(model_id):
        status["error"] = (
            f"MLX model is not downloaded: {model_id}. "
            f"Run scripts/download_models.py --mlx {model_id}."
        )
        return {"ok": False, "status": status}
    return {"ok": True, "status": status}


def unload_model():
    return None


def segment_limit(options=None):
    options = options or {}
    return model_meta(options.get("mlxModelId"))["maxTextChars"]


def supports_longform(options=None):
    options = options or {}
    return bool(model_meta(options.get("mlxModelId"))["supportsLongform"])


def worker_options(options, model_id):
    meta = model_meta(model_id)
    language = safe_language(options.get("mlxLanguageId") or options.get("languageId"), model_id)
    voice = safe_voice(options.get("voice"), model_id)
    ref_audio = (options.get("mlxRefAudioPath") or "").strip()
    ref_text = (options.get("mlxRefText") or "").strip()

    if ref_audio and model_id == "mlx-qwen3-tts" and not ref_text:
        raise ValueError("Qwen3-TTS voice cloning needs reference text for the reference audio.")
    if ref_audio and not meta["supportsReferenceAudio"]:
        raise ValueError(f"{meta['name']} does not support reference audio in this app.")
    if model_id == "mlx-qwen3-voice-design" and not (options.get("mlxInstruct") or "").strip():
        raise ValueError("Qwen3-TTS VoiceDesign needs a voice description in the instruction field.")

    return {
        "modelId": model_id,
        "languageId": language,
        "voice": voice,
        "refAudioPath": ref_audio,
        "refText": ref_text,
        "instruct": (options.get("mlxInstruct") or "").strip(),
        "speed": float(options.get("mlxSpeed") or 1.0),
        "maxTokens": int(options.get("mlxMaxTokens") or 1200),
        "temperature": float(options.get("mlxTemperature") or 0.7),
        "topP": float(options.get("mlxTopP") or 0.9),
        "topK": int(options.get("mlxTopK") or 50),
        "repetitionPenalty": float(options.get("mlxRepetitionPenalty") or 1.1),
        "exaggeration": float(options.get("mlxExaggeration") or 0.5),
        "cfgWeight": float(options.get("mlxCfgWeight") or 0.5),
        "minP": float(options.get("mlxMinP") or 0.05),
        "seed": safe_seed(options.get("mlxSeed")),
    }


def generate_to_file(segments, output_path, options=None, silence_ms=0):
    options = options or {}
    model_id = safe_model_id(options.get("mlxModelId"))
    meta = model_meta(model_id)
    if not model_installed(model_id):
        raise RuntimeError(f"MLX model files are missing for {model_id}. Run scripts/download_models.py --mlx {model_id}.")

    normalized = []
    for segment in segments:
        text = (segment.get("text") or "").strip()
        if not text:
            continue
        if len(text) > meta["maxTextChars"]:
            raise ValueError(f"{meta['name']} text is limited to {meta['maxTextChars']} characters per segment.")
        normalized.append(
            {
                "label": (segment.get("label") or "").strip(),
                "text": text,
                "voice": safe_voice(segment.get("voice") or options.get("voice"), model_id),
            }
        )

    if not normalized:
        raise ValueError("Text is empty.")

    python = mlx_python()
    if not python:
        raise RuntimeError("MLX Python environment was not found. Create .venv-mlx and install requirements-mlx.txt.")

    request = {
        "modelId": model_id,
        "modelPath": str(meta["path"]),
        "outputPath": str(output_path),
        "segments": normalized,
        "silenceMs": silence_ms,
        "options": worker_options({**options, "voice": normalized[0]["voice"]}, model_id),
    }
    env = os.environ.copy()
    local_paths.configure_local_model_env()
    env.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONNOUSERSITE": "1",
            "ULTRA_TTS_MODELS_DIR": str(local_paths.MODELS_DIR),
            "HF_HOME": str(local_paths.HF_HOME),
            "HF_HUB_CACHE": str(local_paths.HF_HUB_CACHE),
            "HUGGINGFACE_HUB_CACHE": str(local_paths.HF_HUB_CACHE),
            "HF_ASSETS_CACHE": str(local_paths.HF_ASSETS_CACHE),
            "HF_XET_CACHE": str(local_paths.HF_XET_CACHE),
            "XDG_CACHE_HOME": str(local_paths.CACHE_DIR),
            "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
            "HF_HUB_DISABLE_XET": "1",
        }
    )

    result = subprocess.run(
        [str(python), str(local_paths.ROOT / "mlx_worker.py")],
        input=json.dumps(request, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=3600,
        env=env,
        **hidden_subprocess_kwargs(),
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "MLX generation failed").strip()
        raise RuntimeError(f"MLX generation failed: {detail}")

    output_path = Path(output_path)
    if not output_path.exists() or output_path.stat().st_size == 0:
        detail = (result.stderr or result.stdout or "MLX worker did not create an audio file").strip()
        raise RuntimeError(f"MLX generation failed: {detail}")

    return {"ok": True, "modelId": model_id, "voice": request["options"]["voice"]}
