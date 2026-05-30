#!/usr/bin/env python3
import json
import os
import sys
import hashlib
from pathlib import Path

import local_paths


local_paths.configure_local_model_env()


def fail(message):
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False), file=sys.stderr)
    return 1


def normalize_audio(mx, audio):
    if len(audio.shape) == 2:
        if audio.shape[0] == 1:
            return audio[0]
        if audio.shape[1] == 1:
            return audio[:, 0]
    return audio


def stable_segment_seed(base_seed, segment, fallback_key):
    try:
        seed = int(base_seed or 0)
    except (TypeError, ValueError):
        return 0
    if seed <= 0:
        return 0

    key = (segment.get("label") or segment.get("voice") or fallback_key or "").strip()
    if not key:
        return seed
    digest = hashlib.blake2b(key.encode("utf-8"), digest_size=4).digest()
    offset = int.from_bytes(digest, "big") % 1_000_000
    return (seed + offset) % 2_147_483_647


def generate(payload):
    import mlx.core as mx
    import numpy as np

    from mlx_audio.audio_io import write as audio_write
    from mlx_audio.tts.utils import load_model

    model_path = payload["modelPath"]
    output_path = Path(payload["outputPath"])
    segments = payload["segments"]
    options = payload.get("options") or {}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    if temp_path.exists():
        temp_path.unlink()

    model = load_model(model_path)
    all_audio = []
    sample_rate = None
    silence_ms = max(0, int(payload.get("silenceMs") or 0))

    for index, segment in enumerate(segments):
        text = (segment.get("text") or "").strip()
        if not text:
            continue

        voice = segment.get("voice") or options.get("voice") or None
        if voice == "default":
            voice = None

        seed = stable_segment_seed(options.get("seed"), segment, voice or str(index))
        if seed:
            mx.random.seed(seed)

        kwargs = {
            "text": text,
            "voice": voice,
            "speed": float(options.get("speed") or 1.0),
            "temperature": float(options.get("temperature") or 0.7),
            "top_p": float(options.get("topP") or 0.9),
            "top_k": int(options.get("topK") or 50),
            "repetition_penalty": float(options.get("repetitionPenalty") or 1.1),
            "max_tokens": int(options.get("maxTokens") or 1200),
            "lang_code": options.get("languageId") or "auto",
            "exaggeration": float(options.get("exaggeration") or 0.5),
            "cfg_weight": float(options.get("cfgWeight") or 0.5),
            "min_p": float(options.get("minP") or 0.05),
            "verbose": False,
            "stream": False,
        }

        ref_audio = (options.get("refAudioPath") or "").strip()
        ref_text = (options.get("refText") or "").strip()
        instruct = (options.get("instruct") or "").strip()
        if ref_audio:
            kwargs["ref_audio"] = ref_audio
        if ref_text:
            kwargs["ref_text"] = ref_text
        if instruct:
            kwargs["instruct"] = instruct

        chunks = []
        for result in model.generate(**kwargs):
            audio = normalize_audio(mx, result.audio)
            chunks.append(audio)
            sample_rate = int(result.sample_rate)

        if not chunks:
            raise RuntimeError(f"No audio generated for segment {index + 1}.")

        segment_audio = chunks[0] if len(chunks) == 1 else mx.concatenate(chunks, axis=0)
        all_audio.append(segment_audio)
        if index != len(segments) - 1 and silence_ms and sample_rate:
            silence_samples = int(sample_rate * silence_ms / 1000)
            all_audio.append(mx.zeros((silence_samples,), dtype=segment_audio.dtype))

    if not all_audio or not sample_rate:
        raise RuntimeError("No MLX audio was generated.")

    audio = all_audio[0] if len(all_audio) == 1 else mx.concatenate(all_audio, axis=0)
    audio_write(str(temp_path), np.array(audio), sample_rate, format="wav")
    os.replace(temp_path, output_path)
    return {
        "ok": True,
        "outputPath": str(output_path),
        "sampleRate": sample_rate,
        "segments": len(segments),
    }


def main():
    try:
        payload = json.loads(sys.stdin.read())
        result = generate(payload)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        return fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
