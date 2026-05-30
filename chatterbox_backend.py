import os
import random
import gc
import threading
from inspect import signature
from pathlib import Path

import numpy as np


SUPPORTED_LANGUAGES = {
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

DEFAULT_LANGUAGE = "ja"
DEFAULT_T3_MODEL = os.getenv("CHATTERBOX_MULTILINGUAL_T3_MODEL", "v2")
MAX_TEXT_CHARS = 300
DEFAULT_TEMPERATURE = 0.65
DEFAULT_REPETITION_PENALTY = 2.4
DEFAULT_MIN_P = 0.05
DEFAULT_TOP_P = 0.85

_model = None
_model_key = None
_model_device = None
_model_lock = threading.Lock()


def dependency_status():
    try:
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    except Exception as exc:
        return {
            "installed": False,
            "loaded": False,
            "device": None,
            "error": str(exc),
            "supportsT3Model": False,
            "languages": SUPPORTED_LANGUAGES,
            "defaultLanguage": DEFAULT_LANGUAGE,
        }

    supports_t3_model = supports_t3(ChatterboxMultilingualTTS)
    return {
        "installed": True,
        "loaded": _model is not None,
        "device": choose_device(torch),
        "t3Model": _model_key,
        "supportsT3Model": supports_t3_model,
        "languages": SUPPORTED_LANGUAGES,
        "defaultLanguage": DEFAULT_LANGUAGE,
        "error": None,
    }


def choose_device(torch_module):
    if torch_module.cuda.is_available():
        return "cuda"

    mps = getattr(torch_module.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps"

    return "cpu"


def safe_language(value):
    language_id = (value or DEFAULT_LANGUAGE).strip().lower()
    if language_id not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported Chatterbox language: {language_id}")
    return language_id


def safe_t3_model(value):
    t3_model = (value or DEFAULT_T3_MODEL).strip().lower()
    if t3_model not in {"v2", "v3"}:
        raise ValueError("Chatterbox T3 model must be v2 or v3.")
    return t3_model


def supports_t3(model_class):
    return "t3_model" in signature(model_class.from_pretrained).parameters


def safe_float(value, default, min_value, max_value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(min_value, min(number, max_value))


def safe_int(value, default, min_value, max_value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(min_value, min(number, max_value))


def resolve_audio_prompt(value):
    audio_prompt = (value or "").strip()
    if not audio_prompt:
        return None
    if audio_prompt.startswith(("http://", "https://")):
        return audio_prompt

    path = Path(audio_prompt).expanduser()
    if not path.is_file():
        raise ValueError(f"Reference audio file not found: {audio_prompt}")
    return str(path)


def set_seed(torch_module, seed, device):
    if seed <= 0:
        return

    random.seed(seed)
    np.random.seed(seed)
    torch_module.manual_seed(seed)
    if device == "cuda":
        torch_module.cuda.manual_seed(seed)
        torch_module.cuda.manual_seed_all(seed)


def get_or_load_model(t3_model=None):
    global _model, _model_key, _model_device

    t3_model = safe_t3_model(t3_model)
    with _model_lock:
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        device = choose_device(torch)
        model_key = t3_model if supports_t3(ChatterboxMultilingualTTS) else "default"
        if _model is not None and _model_key == model_key:
            return _model, _model_device

        if supports_t3(ChatterboxMultilingualTTS):
            _model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model=t3_model)
        else:
            _model = ChatterboxMultilingualTTS.from_pretrained(device=device)
        _model_key = model_key
        _model_device = device
        return _model, device


def ensure_model(options=None):
    options = options or {}
    get_or_load_model(options.get("t3Model"))
    return {"ok": True, "status": dependency_status()}


def unload_model():
    global _model, _model_key, _model_device

    with _model_lock:
        _model = None
        _model_key = None
        _model_device = None

    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    gc.collect()


def generate_waveform(text, options=None):
    options = options or {}
    text = (text or "").strip()
    if not text:
        raise ValueError("Text is empty.")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"Chatterbox text is limited to {MAX_TEXT_CHARS} characters per line.")

    language_id = safe_language(options.get("languageId"))
    t3_model = safe_t3_model(options.get("t3Model"))
    audio_prompt = resolve_audio_prompt(options.get("audioPromptPath"))
    exaggeration = safe_float(options.get("exaggeration"), 0.5, 0.25, 2.0)
    temperature = safe_float(options.get("temperature"), DEFAULT_TEMPERATURE, 0.05, 5.0)
    cfg_weight = safe_float(options.get("cfgWeight"), 0.5, 0.0, 1.0)
    repetition_penalty = safe_float(
        options.get("repetitionPenalty"),
        DEFAULT_REPETITION_PENALTY,
        1.0,
        5.0,
    )
    min_p = safe_float(options.get("minP"), DEFAULT_MIN_P, 0.0, 1.0)
    top_p = safe_float(options.get("topP"), DEFAULT_TOP_P, 0.05, 1.0)
    seed = safe_int(options.get("seed"), 0, 0, 2_147_483_647)

    import torch

    model, device = get_or_load_model(t3_model)
    set_seed(torch, seed, device)

    generate_kwargs = {
        "language_id": language_id,
        "exaggeration": exaggeration,
        "temperature": temperature,
        "cfg_weight": cfg_weight,
        "repetition_penalty": repetition_penalty,
        "min_p": min_p,
        "top_p": top_p,
    }
    if audio_prompt:
        generate_kwargs["audio_prompt_path"] = audio_prompt

    wav = model.generate(text, **generate_kwargs)
    return model.sr, waveform_to_pcm16(wav)


def waveform_to_pcm16(wav):
    if hasattr(wav, "detach"):
        wav = wav.detach().cpu().numpy()

    array = np.asarray(wav, dtype=np.float32).squeeze()
    if array.ndim > 1:
        array = array.reshape(-1)

    array = np.nan_to_num(array, nan=0.0, posinf=1.0, neginf=-1.0)
    array = np.clip(array, -1.0, 1.0)
    return (array * 32767.0).astype("<i2").tobytes()
