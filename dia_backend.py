import gc
import json
import os
import random
import re
import subprocess
import sys
import threading
from pathlib import Path

import local_paths


local_paths.configure_local_model_env()

DEFAULT_MODEL_ID = "nari-labs/Dia-1.6B-0626"
LOCAL_MODEL_DIR = local_paths.MODELS_DIR / "huggingface" / DEFAULT_MODEL_ID.replace("/", "__")
LOCAL_DAC_DIR = local_paths.MODELS_DIR / "huggingface" / "descript__dac_44khz"
ROOT = Path(__file__).resolve().parent
DIA_WORKER = ROOT / "dia_worker.py"
MODEL_ID = os.getenv(
    "DIA_MODEL_ID",
    str(LOCAL_MODEL_DIR) if (LOCAL_MODEL_DIR / "config.json").exists() else DEFAULT_MODEL_ID,
)
DEFAULT_MAX_NEW_TOKENS = 1280
DEFAULT_GUIDANCE_SCALE = 3.0
DEFAULT_TEMPERATURE = 1.8
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 50
MIN_RECOMMENDED_VRAM_GB = 9.5
MAX_TEXT_CHARS = 1600

_processor = None
_model = None
_device = None
_model_lock = threading.Lock()
_speaker_tag_pattern = re.compile(r"\[(S[12])\]")
_cjk_pattern = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")
_word_pattern = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


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


def local_model_ready():
    return all(
        (LOCAL_MODEL_DIR / filename).exists()
        for filename in [
            "audio_tokenizer_config.json",
            "config.json",
            "model-00001-of-00002.safetensors",
            "model-00002-of-00002.safetensors",
            "preprocessor_config.json",
        ]
    )


def local_dac_ready():
    return all(
        (LOCAL_DAC_DIR / filename).exists()
        for filename in ["config.json", "model.safetensors", "preprocessor_config.json"]
    )


def patch_dia_audio_tokenizer_config():
    config_path = LOCAL_MODEL_DIR / "audio_tokenizer_config.json"
    if not config_path.exists() or not local_dac_ready():
        return

    desired_path = str(LOCAL_DAC_DIR)
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return

    if data.get("audio_tokenizer_name_or_path") == desired_path:
        return

    data["audio_tokenizer_name_or_path"] = desired_path
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def dependency_status():
    try:
        import torch
        from transformers import AutoProcessor, DiaForConditionalGeneration
    except Exception as exc:
        return {
            "installed": False,
            "loaded": False,
            "device": None,
            "error": str(exc),
            "modelId": MODEL_ID,
        }

    device = choose_device(torch)
    details = device_details(torch, device)
    recommended = device != "cpu" and details.get("recommended", True)
    return {
        "installed": True,
        "loaded": _model is not None,
        "device": device,
        **details,
        "localModelReady": local_model_ready(),
        "localDacReady": local_dac_ready(),
        "recommended": recommended,
        "error": None,
        "modelId": MODEL_ID,
    }


def choose_device(torch_module):
    forced = (os.getenv("DIA_DEVICE") or "").strip().lower()
    if forced == "cpu":
        return "cpu"
    if forced == "cuda" and torch_module.cuda.is_available():
        return "cuda"
    if forced == "mps":
        mps = getattr(torch_module.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"

    if torch_module.cuda.is_available():
        return "cuda"

    mps = getattr(torch_module.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps"

    return "cpu"


def device_details(torch_module, device):
    if device != "cuda":
        return {}

    props = torch_module.cuda.get_device_properties(0)
    vram_gb = props.total_memory / (1024**3)
    recommended = vram_gb >= MIN_RECOMMENDED_VRAM_GB
    details = {
        "vramGb": round(vram_gb, 1),
        "minRecommendedVramGb": MIN_RECOMMENDED_VRAM_GB,
        "recommended": recommended,
    }
    if not recommended:
        details["warning"] = (
            f"Dia is below its practical VRAM target on this GPU "
            f"({details['vramGb']}GB < {MIN_RECOMMENDED_VRAM_GB}GB)."
        )
    return details


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


def estimate_min_tokens(dialogue):
    words = len(_word_pattern.findall(dialogue))
    turns = len(_speaker_tag_pattern.findall(dialogue))
    estimate = int((words * 16) + (turns * 60))
    return max(512, min(estimate, 3072))


def set_seed(torch_module, seed, device):
    if seed <= 0:
        return

    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    torch_module.manual_seed(seed)
    if device == "cuda":
        torch_module.cuda.manual_seed(seed)
        torch_module.cuda.manual_seed_all(seed)


def get_or_load_model(options=None):
    global _processor, _model, _device
    options = options or {}

    with _model_lock:
        import torch
        from transformers import AutoProcessor, DiaForConditionalGeneration

        device = choose_device(torch)
        details = device_details(torch, device)
        if _model is not None and _processor is not None and _device == device:
            return _processor, _model, device

        if device == "cpu":
            raise RuntimeError("Dia needs a CUDA or MPS GPU for practical local generation.")
        if details.get("recommended") is False and not options.get("diaAllowLowVram"):
            raise RuntimeError(
                "Dia needs about 10GB VRAM for practical local use. "
                f"This GPU has {details['vramGb']}GB, so output can become broken audio. "
                "Use Kokoro for English, or enable the low-VRAM Dia option if you still want to test it."
            )

        dtype = torch.float16 if device == "cuda" else torch.float32
        if str(MODEL_ID) == str(LOCAL_MODEL_DIR):
            if not local_model_ready():
                raise RuntimeError("Dia model files are missing. Run scripts/download_models.py --current-hf dia dia-dac.")
            if not local_dac_ready():
                raise RuntimeError("Dia DAC audio tokenizer is missing. Run scripts/download_models.py --current-hf dia-dac.")
            patch_dia_audio_tokenizer_config()

        local_only = str(MODEL_ID) == str(LOCAL_MODEL_DIR)
        _processor = AutoProcessor.from_pretrained(MODEL_ID, local_files_only=local_only)
        load_kwargs = {
            "attn_implementation": "eager",
            "local_files_only": local_only,
        }
        try:
            _model = DiaForConditionalGeneration.from_pretrained(MODEL_ID, dtype=dtype, **load_kwargs)
        except TypeError:
            _model = DiaForConditionalGeneration.from_pretrained(MODEL_ID, torch_dtype=dtype, **load_kwargs)
        _model.to(device)
        _model.eval()
        _device = device
        return _processor, _model, device


def ensure_model(options=None):
    status = dependency_status()
    ok = bool(status.get("installed")) and bool(status.get("localModelReady")) and bool(status.get("localDacReady"))
    return {"ok": ok, "status": status}


def unload_model():
    global _processor, _model, _device

    with _model_lock:
        _processor = None
        _model = None
        _device = None

    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    gc.collect()


def single_text(text):
    text = (text or "").strip()
    if not text:
        raise ValueError("Text is empty.")
    if not _speaker_tag_pattern.search(text):
        raise ValueError(
            "Dia is a dialogue model. Use Kokoro for plain single-speaker TTS, "
            "or write an English Dia dialogue with [S1] and [S2] tags."
        )
    return prepare_dialogue(text)


def script_to_dialogue(script_text, speaker_pattern):
    lines = []
    speaker_tags = {}
    next_tag = 1

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if _speaker_tag_pattern.search(stripped):
            lines.append(stripped)
            continue

        match = speaker_pattern.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text' or Dia '[S1] text'.")

        label = match.group("label").strip().upper()
        if label not in speaker_tags:
            if next_tag > 2:
                raise ValueError("Dia supports two speakers. Use only two labels, such as A and B.")
            speaker_tags[label] = f"S{next_tag}"
            next_tag += 1

        lines.append(f"[{speaker_tags[label]}] {match.group('text').strip()}")

    if not lines:
        raise ValueError("Script has no lines to generate.")

    dialogue = " ".join(lines)
    if not dialogue.startswith("[S1]"):
        dialogue = f"[S1] {dialogue}"
    return prepare_dialogue(dialogue)


def prepare_dialogue(dialogue):
    dialogue = (dialogue or "").strip()
    if not dialogue:
        raise ValueError("Text is empty.")
    if _cjk_pattern.search(dialogue):
        raise ValueError("Dia only supports English well. Use Kokoro for English or Chatterbox for Japanese.")
    if not dialogue.startswith("[S1]"):
        raise ValueError("Dia text must start with [S1]. Use a two-speaker English script such as 'A: ...' and 'B: ...'.")

    tags = _speaker_tag_pattern.findall(dialogue)
    if not tags:
        raise ValueError("Dia text needs [S1] or [S2] speaker tags.")
    if len(tags) < 2:
        raise ValueError("Dia needs an English dialogue with [S1] and [S2]. Use Kokoro for single-speaker TTS.")

    for previous, current in zip(tags, tags[1:]):
        if previous == current:
            raise ValueError("Dia works best when [S1] and [S2] alternate. Avoid consecutive lines from the same speaker.")

    ending_tag = tags[-2] if len(tags) > 1 else tags[-1]
    if not dialogue.endswith(f"[{ending_tag}]"):
        dialogue = f"{dialogue} [{ending_tag}]"
    return dialogue


def _generate_to_file_local(dia_text, output_path, options=None):
    options = options or {}
    dia_text = (dia_text or "").strip()
    if not dia_text:
        raise ValueError("Text is empty.")
    if len(dia_text) > MAX_TEXT_CHARS:
        raise ValueError(f"Dia text is limited to {MAX_TEXT_CHARS} characters.")

    max_new_tokens = safe_int(options.get("diaMaxNewTokens"), DEFAULT_MAX_NEW_TOKENS, 128, 4096)
    estimated_min_tokens = estimate_min_tokens(dia_text)
    if max_new_tokens < estimated_min_tokens:
        raise ValueError(
            f"Dia max tokens is too low for this script. Current: {max_new_tokens}, "
            f"recommended: {estimated_min_tokens} or higher. 256 is only for a very short one-turn test."
        )

    import torch

    processor, model, device = get_or_load_model(options)
    seed = safe_int(options.get("diaSeed"), 0, 0, 2_147_483_647)
    set_seed(torch, seed, device)

    inputs = processor(text=[dia_text], padding=True, return_tensors="pt").to(device)
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            do_sample=True,
            max_new_tokens=max_new_tokens,
            guidance_scale=safe_float(options.get("diaGuidanceScale"), DEFAULT_GUIDANCE_SCALE, 1.0, 8.0),
            temperature=safe_float(options.get("diaTemperature"), DEFAULT_TEMPERATURE, 0.1, 3.0),
            top_p=safe_float(options.get("diaTopP"), DEFAULT_TOP_P, 0.05, 1.0),
            top_k=safe_int(options.get("diaTopK"), DEFAULT_TOP_K, 0, 200),
        )

    decoded = processor.batch_decode(outputs)
    processor.save_audio(decoded[0], str(output_path))
    return {"ok": True, "modelId": MODEL_ID}


def generate_to_file(dia_text, output_path, options=None):
    options = options or {}
    if not DIA_WORKER.exists():
        raise RuntimeError(f"Dia worker was not found at {DIA_WORKER}.")

    request = {
        "diaText": dia_text,
        "outputPath": str(output_path),
        "options": options,
    }
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    env.setdefault("HF_HUB_DISABLE_XET", "1")

    result = subprocess.run(
        [sys.executable, str(DIA_WORKER), "--json"],
        input=json.dumps(request, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
        timeout=safe_int(options.get("diaTimeoutSeconds"), 1800, 60, 7200),
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
        detail = parsed.get("error") if parsed else stderr or stdout or f"worker exited with {result.returncode}"
        raise RuntimeError(f"Dia generation failed: {detail}")

    return parsed
