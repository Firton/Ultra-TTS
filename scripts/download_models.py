#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import local_paths
import piper_backend


PIPER_REPO = "rhasspy/piper-voices"
PIPER_DEFAULT_VOICES = [
    "en_US-lessac-medium",
    "en_GB-alba-medium",
    "de_DE-thorsten-medium",
    "fr_FR-siwis-medium",
    "es_ES-sharvard-medium",
    "zh_CN-huayan-medium",
]
CURRENT_HF_REPOS = {
    "orpheus": "isaiahbjork/orpheus-3b-0.1-ft-Q4_K_M-GGUF",
    "snac": "hubertsiuzdak/snac_24khz",
    "kokoro": "hexgrad/Kokoro-82M",
    "chatterbox": "ResembleAI/chatterbox",
    "dia": "nari-labs/Dia-1.6B-0626",
    "dia-dac": "descript/dac_44khz",
}
MLX_HF_REPOS = {
    "mlx-chatterbox": "mlx-community/chatterbox-fp16",
    "mlx-qwen3-tts": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit",
    "mlx-qwen3-custom": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit",
    "mlx-qwen3-voice-design": "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit",
    "mlx-kokoro": "mlx-community/Kokoro-82M-8bit",
    "mlx-dia": "mlx-community/Dia-1.6B-fp16",
}
MLX_BASIC_REPOS = ["mlx-chatterbox", "mlx-qwen3-tts", "mlx-kokoro"]
HF_FILE_FILTERS = {
    "dia": {
        "audio_tokenizer_config.json",
        "config.json",
        "generation_config.json",
        "model-00001-of-00002.safetensors",
        "model-00002-of-00002.safetensors",
        "model.safetensors.index.json",
        "preprocessor_config.json",
        "special_tokens_map.json",
        "tokenizer_config.json",
    },
    "dia-dac": {
        "config.json",
        "model.safetensors",
        "preprocessor_config.json",
    },
    "mlx-chatterbox": {
        "Cangjie5_TC.json",
        "conds.safetensors",
        "config.json",
        "model.safetensors",
        "tokenizer.json",
    },
    "mlx-qwen3-tts": {
        "config.json",
        "generation_config.json",
        "merges.txt",
        "model.safetensors",
        "model.safetensors.index.json",
        "preprocessor_config.json",
        "speech_tokenizer/config.json",
        "speech_tokenizer/configuration.json",
        "speech_tokenizer/model.safetensors",
        "speech_tokenizer/preprocessor_config.json",
        "tokenizer_config.json",
        "vocab.json",
    },
    "mlx-qwen3-custom": {
        "config.json",
        "generation_config.json",
        "merges.txt",
        "model.safetensors",
        "model.safetensors.index.json",
        "preprocessor_config.json",
        "speech_tokenizer/config.json",
        "speech_tokenizer/configuration.json",
        "speech_tokenizer/model.safetensors",
        "speech_tokenizer/preprocessor_config.json",
        "tokenizer_config.json",
        "vocab.json",
    },
    "mlx-qwen3-voice-design": {
        "config.json",
        "generation_config.json",
        "merges.txt",
        "model.safetensors",
        "model.safetensors.index.json",
        "preprocessor_config.json",
        "speech_tokenizer/config.json",
        "speech_tokenizer/configuration.json",
        "speech_tokenizer/model.safetensors",
        "speech_tokenizer/preprocessor_config.json",
        "tokenizer_config.json",
        "vocab.json",
    },
    "mlx-dia": {
        "config.json",
        "model.safetensors",
    },
}


def http_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")

    if target.exists() and target.stat().st_size > 0:
        print(f"skip {target.relative_to(ROOT)}")
        return

    print(f"download {target.relative_to(ROOT)}")
    request = urllib.request.Request(url, headers={"User-Agent": "Ultra-TTS model downloader"})
    with urllib.request.urlopen(request, timeout=120) as response, temp.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
    temp.replace(target)


def hf_resolve_url(repo_id, filename, revision="main"):
    encoded = "/".join(urllib.parse.quote(part) for part in filename.split("/"))
    return f"https://huggingface.co/{repo_id}/resolve/{revision}/{encoded}"


def hf_api_url(repo_id):
    return f"https://huggingface.co/api/models/{repo_id}"


def download_piper_voice(voice):
    if voice not in piper_backend.VOICE_CATALOG:
        raise ValueError(f"Unknown Piper voice: {voice}")

    model_rel = piper_backend.VOICE_CATALOG[voice]["path"]
    config_rel = f"{model_rel}.json"
    for rel_path in [model_rel, config_rel]:
        download_file(
            hf_resolve_url(PIPER_REPO, rel_path),
            local_paths.PIPER_MODELS_DIR / rel_path,
        )


def download_piper_basic():
    for voice in PIPER_DEFAULT_VOICES:
        download_piper_voice(voice)


def download_hf_repo(name, repo_id):
    data = http_json(hf_api_url(repo_id))
    target_root = local_paths.MODELS_DIR / "huggingface" / repo_id.replace("/", "__")
    siblings = data.get("siblings") or []
    allowed_files = HF_FILE_FILTERS.get(name)
    for sibling in siblings:
        filename = sibling.get("rfilename")
        if not filename or filename == ".gitattributes":
            continue
        if name == "mlx-kokoro":
            if filename in {"config.json", "kokoro-v1_0.safetensors"}:
                pass
            elif filename.startswith("voices/") and filename.endswith(".safetensors"):
                pass
            else:
                continue
        if allowed_files is not None and filename not in allowed_files:
            continue
        download_file(hf_resolve_url(repo_id, filename), target_root / filename)
    print(f"done {name}: {target_root.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Download Ultra-TTS local model files into this repository.")
    parser.add_argument("--piper-basic", action="store_true", help="Download the default Piper voice set.")
    parser.add_argument("--piper-voice", action="append", default=[], help="Download one Piper voice by id.")
    parser.add_argument(
        "--current-hf",
        nargs="*",
        choices=sorted(CURRENT_HF_REPOS),
        help="Download current Hugging Face model repos. With no names, downloads all.",
    )
    parser.add_argument(
        "--mlx",
        nargs="*",
        choices=sorted(MLX_HF_REPOS),
        help="Download MLX-Audio model repos. With no names, downloads all MLX models.",
    )
    parser.add_argument(
        "--mlx-basic",
        action="store_true",
        help="Download the recommended Mac MLX set: Chatterbox, Qwen3-TTS, and Kokoro.",
    )
    parser.add_argument("--mlx-all", action="store_true", help="Download all configured MLX-Audio repos.")
    parser.add_argument("--all", action="store_true", help="Download Piper defaults and all current HF repos.")
    args = parser.parse_args()

    local_paths.configure_local_model_env()

    if args.all:
        args.piper_basic = True
        args.current_hf = sorted(CURRENT_HF_REPOS)
    if args.mlx_basic:
        args.mlx = MLX_BASIC_REPOS
    if args.mlx_all:
        args.mlx = sorted(MLX_HF_REPOS)

    did_work = False
    if args.piper_basic:
        download_piper_basic()
        did_work = True

    for voice in args.piper_voice:
        download_piper_voice(voice)
        did_work = True

    if args.current_hf is not None:
        names = args.current_hf or sorted(CURRENT_HF_REPOS)
        for name in names:
            download_hf_repo(name, CURRENT_HF_REPOS[name])
        did_work = True

    if args.mlx is not None:
        names = args.mlx or sorted(MLX_HF_REPOS)
        for name in names:
            download_hf_repo(name, MLX_HF_REPOS[name])
        did_work = True

    if not did_work:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
