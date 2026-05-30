# Ultra-TTS

Ultra-TTS is a local browser app and CLI workspace for experimenting with text-to-speech backends.

The current app supports:

- Orpheus through LM Studio's local OpenAI-compatible API
- Chatterbox Multilingual for local multilingual generation
- Kokoro through a separate lightweight local worker
- Piper through downloaded ONNX voice files in `models/piper/`
- Dia as an experimental English dialogue backend
- MLX-Audio on Apple Silicon for Chatterbox, Qwen3-TTS, Kokoro, and Dia MLX models
- Single-text, multi-speaker script, and long-form article generation
- Long-form text splitting with a `manifest.json` next to generated audio

Generated audio, model files, logs, virtual environments, and local cache files are intentionally ignored by Git.

## Web App

Start the browser UI on macOS/Linux:

```bash
./launch-web.sh
```

Or run it directly:

```bash
python3 web_app.py --host 127.0.0.1 --port 8765 --open
```

On Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\launch-web.ps1
```

Then open:

```text
http://127.0.0.1:8765
```

On this machine, the desktop launcher is:

```text
C:\Users\firto\Desktop\Ultra-TTS Web.bat
```

## Orpheus / LM Studio

1. Install [LM Studio](https://lmstudio.ai/).
2. Download an Orpheus GGUF model, for example `orpheus-3b-0.1-ft-q4_k_m.gguf`.
3. Load the model in LM Studio.
4. Start the local server in LM Studio at `http://127.0.0.1:1234`.
5. Use the Orpheus backend in the Ultra-TTS web UI.

CLI example:

```powershell
python .\gguf_orpheus.py --text "Hello, this is a test" --voice tara
```

## Backends

Orpheus voices:

```text
tara, leah, jess, leo, dan, mia, zac, zoe
```

Chatterbox is the default practical option for Japanese and multilingual local TTS in the web UI.

Kokoro is a lightweight English backend and runs through `.venv-kokoro`.

Piper is a lightweight local-process backend. Download the default voice set into `models/piper/`:

```bash
python3 scripts/download_models.py --piper-basic
```

Dia is dialogue-focused and expects English speaker-tagged dialogue. It runs in a separate worker process because the model is heavy and MPS failures should not take down the web app. The first generation can take around a minute on Apple Silicon.

MLX-Audio is the recommended Mac mini M4 path. It runs from a separate `.venv-mlx` so its MLX/transformers dependencies do not disturb the PyTorch, Piper, or LM Studio backends.

```bash
.venv/bin/python -m venv .venv-mlx
.venv-mlx/bin/python -m pip install -r requirements-mlx.txt
.venv-mlx/bin/python -m unidic download
python3 scripts/download_models.py --mlx-basic
```

The configured MLX models are:

- `mlx-chatterbox`: `mlx-community/chatterbox-fp16`
- `mlx-qwen3-tts`: `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit`
- `mlx-qwen3-custom`: `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit`
- `mlx-qwen3-voice-design`: `mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit`
- `mlx-kokoro`: `mlx-community/Kokoro-82M-8bit`
- `mlx-dia`: `mlx-community/Dia-1.6B-fp16`

## Local Model Storage

Ultra-TTS keeps model files inside the project when possible:

- `models/piper/` for Piper ONNX voice files
- `models/huggingface/` for direct Hugging Face repo snapshots downloaded by `scripts/download_models.py`
- `.cache/huggingface/` and `.cache/torch/` for library-managed caches

The app sets `HF_HOME`, `HF_HUB_CACHE`, `HF_ASSETS_CACHE`, `HF_XET_CACHE`, `TRANSFORMERS_CACHE`, `TORCH_HOME`, and `XDG_CACHE_HOME` at startup so Chatterbox, Kokoro, Dia, SNAC, and MLX-Audio cache under this repository by default.

Download the current Hugging Face model repos manually:

```bash
python3 scripts/download_models.py --current-hf snac kokoro chatterbox
```

Download the Orpheus GGUF used with LM Studio:

```bash
python3 scripts/download_models.py --current-hf orpheus
lms import models/huggingface/isaiahbjork__orpheus-3b-0.1-ft-Q4_K_M-GGUF/orpheus-3b-0.1-ft-q4_k_m.gguf --user-repo Firton/Ultra-TTS -L -y
```

Dia is much larger, so download it only when you actually want to test Dia:

```bash
python3 scripts/download_models.py --current-hf dia dia-dac
```

Download MLX models:

```bash
python3 scripts/download_models.py --mlx-basic
python3 scripts/download_models.py --mlx mlx-qwen3-custom mlx-qwen3-voice-design mlx-dia
```

## Long-form Generation

Use the `長文` tab for articles, lessons, and pasted long-form text.

The app splits text before calling a backend, because local engines have different practical limits:

- Chatterbox: 300 characters per segment
- Kokoro: 1200 characters per segment
- Orpheus: 600 characters per segment
- Piper: 1000 characters per segment
- MLX Chatterbox: 300 characters per segment
- MLX Qwen3-TTS: 500 characters per segment
- MLX Kokoro: 1200 characters per segment

The generated WAV is written under `outputs/web/`. A sibling `*.manifest.json` records the backend, voice, language, segment boundaries, and text used for each generated segment.

## Local Files

Ignored by Git:

- `.venv/`
- `.venv-kokoro/`
- `.venv-mlx/`
- `logs/`
- `outputs/`
- audio outputs such as `*.wav`, `*.mp3`, `*.flac`
- downloaded model files such as `*.gguf`, `*.safetensors`, `*.ckpt`, `*.pt`, `*.onnx`

## License

Apache 2.0
