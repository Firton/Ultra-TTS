import argparse
import json
import os
import sys
from pathlib import Path

import local_paths


local_paths.configure_local_model_env()

import numpy as np
import soundfile as sf
from kokoro import KPipeline
from kokoro.model import KModel


SAMPLE_RATE = 24000
KOKORO_REPO_OVERRIDE = os.getenv("KOKORO_REPO_ID")
LOCAL_KOKORO_REPO = local_paths.MODELS_DIR / "huggingface" / "hexgrad__Kokoro-82M"
KOKORO_REPO_ID = (
    KOKORO_REPO_OVERRIDE
    if KOKORO_REPO_OVERRIDE
    else str(LOCAL_KOKORO_REPO)
    if (LOCAL_KOKORO_REPO / "kokoro-v1_0.pth").exists()
    else "hexgrad/Kokoro-82M"
)


def safe_float(value, default, min_value, max_value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(min_value, min(number, max_value))


def lang_code_for_voice(voice):
    voice = (voice or "").strip().lower()
    if voice.startswith(("af_", "am_")):
        return "a"
    if voice.startswith(("bf_", "bm_")):
        return "b"
    raise ValueError(f"Unsupported Kokoro voice: {voice}")


def local_voice_path(voice):
    path = LOCAL_KOKORO_REPO / "voices" / f"{voice}.pt"
    return str(path) if path.exists() else voice


def load_model():
    config_path = LOCAL_KOKORO_REPO / "config.json"
    model_path = LOCAL_KOKORO_REPO / "kokoro-v1_0.pth"
    if config_path.exists() and model_path.exists():
        return KModel(
            repo_id="hexgrad/Kokoro-82M",
            config=str(config_path),
            model=str(model_path),
        ).to("cpu").eval()
    return True


def generate(request):
    output_path = Path(request["outputPath"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    speed = safe_float(request.get("speed"), 1.0, 0.5, 2.0)
    silence_ms = max(0, min(int(request.get("silenceMs") or 0), 5000))
    silence = np.zeros(int(SAMPLE_RATE * silence_ms / 1000), dtype=np.float32)
    pipelines = {}
    model = load_model()
    parts = []

    for index, segment in enumerate(request.get("segments") or []):
        text = (segment.get("text") or "").strip()
        voice = (segment.get("voice") or "af_heart").strip().lower()
        if not text:
            continue

        lang_code = lang_code_for_voice(voice)
        if lang_code not in pipelines:
            pipelines[lang_code] = KPipeline(
                lang_code=lang_code,
                repo_id="hexgrad/Kokoro-82M",
                model=model,
            )

        generated = []
        generator = pipelines[lang_code](
            text,
            voice=local_voice_path(voice),
            speed=speed,
            split_pattern=r"\n+",
        )
        for _, _, audio in generator:
            generated.append(np.asarray(audio, dtype=np.float32).reshape(-1))

        if generated:
            parts.append(np.concatenate(generated))
            if index != len(request.get("segments") or []) - 1 and silence.size:
                parts.append(silence)

    if not parts:
        raise ValueError("No Kokoro audio was generated.")

    audio = np.concatenate(parts)
    audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
    audio = np.clip(audio, -1.0, 1.0)
    sf.write(str(output_path), audio, SAMPLE_RATE, subtype="PCM_16")
    return {"ok": True, "sampleRate": SAMPLE_RATE, "frames": int(audio.shape[0])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.json:
        print("Use --json and send a request JSON object on stdin.", file=sys.stderr)
        return 2

    try:
        request = json.loads(sys.stdin.read())
        result = generate(request)
        print(json.dumps(result), flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
