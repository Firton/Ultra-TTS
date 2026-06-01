# Ultra-TTS

Ultra-TTS is an open-source local browser GUI and CLI workspace for running Japanese and
multilingual text-to-speech models.

It is designed for developers, creators, educators, and accessibility-focused users who want
to run local TTS workflows without relying only on cloud APIs.

The project is still early, but it already provides a practical workspace for local TTS
experimentation, backend comparison, long-form text splitting, and multi-speaker generation.

## Why Ultra-TTS

Local TTS workflows are useful when users need more control over privacy, cost, latency,
model choice, or offline experimentation than a cloud-only workflow can provide.

Ultra-TTS focuses on making local Japanese and multilingual TTS easier to try from one workspace.

The project combines a browser-based GUI, CLI entry points, backend setup notes, local model
storage conventions, and lightweight tests so maintainers can keep improving the workflow
without requiring model downloads for every development task.

Demo screenshots and audio samples will be added in a future release.

## Features

- Local browser-based TTS GUI served from `web_app.py`
- CLI workspace for local TTS experiments and backend scripts
- Japanese and multilingual TTS workflows
- Single-text generation
- Multi-speaker script generation with speaker labels
- Long-form generation for articles, lessons, and pasted text
- Long-form text splitting before backend calls
- Manifest metadata next to generated long-form audio
- Local model, cache, output, and log directory handling
- Windows PowerShell and macOS/Linux shell launch scripts

## Supported backends

Ultra-TTS integrates several local TTS workflows.

Backend availability depends on the models and dependencies installed in your local environment.

- **LM Studio / Orpheus**: uses LM Studio's local OpenAI-compatible API for Orpheus-style
  speech token generation.
- **Chatterbox Multilingual**: local multilingual TTS workflow used for Japanese and multilingual generation.
- **Kokoro worker**: lightweight worker-based Kokoro workflow, primarily for English voices.
- **Piper**: local-process backend using downloaded ONNX voice files in `models/piper/`.
- **Dia**: experimental English dialogue backend for speaker-tagged dialogue.
- **MLX-Audio**: Apple Silicon workflow for Chatterbox, Qwen3-TTS, Kokoro, and Dia MLX models.

## Quick start

Clone the repository and enter the project directory:

```bash
git clone https://github.com/Firton/Ultra-TTS.git
cd Ultra-TTS
```

Create a Python environment appropriate for your platform and backend. For lightweight
development and tests, no model downloads are required.

Run the browser UI on macOS/Linux:

```bash
./launch-web.sh
```

Run the browser UI on Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\launch-web.ps1
```

Or run the app directly:

```bash
python web_app.py --host 127.0.0.1 --port 8765 --open
```

Then open:

```text
http://127.0.0.1:8765
```

For a desktop shortcut, create a shortcut that runs `launch-web.ps1` on Windows or
`launch-web.sh` on macOS/Linux.

Run lightweight tests:

```bash
python -m unittest discover -s tests
```

## Backend setup notes

### LM Studio / Orpheus

1. Install LM Studio.
2. Download an Orpheus GGUF model, for example `orpheus-3b-0.1-ft-q4_k_m.gguf`.
3. Load the model in LM Studio.
4. Start the local server in LM Studio at `http://127.0.0.1:1234`.
5. Select the Orpheus backend in the Ultra-TTS web UI.

CLI example:

```bash
python gguf_orpheus.py --text "Hello, this is a test" --voice tara
```

Orpheus voices:

```text
tara, leah, jess, leo, dan, mia, zac, zoe
```

### Chatterbox Multilingual

Chatterbox is used for local multilingual generation, including Japanese workflows. It requires
its Python dependencies and model files to be available locally.

### Kokoro

Kokoro runs through a separate lightweight worker environment.

In this repository, Kokoro-specific dependencies are expected to live outside the main application environment when needed.

### Piper

Piper is a lightweight local-process backend. Download voice files into `models/piper/`:

```bash
python scripts/download_models.py --piper-basic
```

### Dia

Dia is dialogue-focused and expects English speaker-tagged dialogue. It runs in a separate
worker process because the model is heavy and backend failures should not take down the web app.

Download Dia files only when you actually want to test Dia:

```bash
python scripts/download_models.py --current-hf dia dia-dac
```

### MLX-Audio

MLX-Audio is recommended for Apple Silicon environments. It uses a separate `.venv-mlx` so its
MLX and transformer dependencies do not disturb the PyTorch, Piper, or LM Studio backends.

```bash
python -m venv .venv-mlx
.venv-mlx/bin/python -m pip install -r requirements-mlx.txt
.venv-mlx/bin/python -m unidic download
python scripts/download_models.py --mlx-basic
```

The configured MLX model IDs are:

- `mlx-chatterbox`
- `mlx-qwen3-tts`
- `mlx-qwen3-custom`
- `mlx-qwen3-voice-design`
- `mlx-kokoro`
- `mlx-dia`

## Long-form generation

Use the long-form tab for articles, lessons, and pasted long-form text.

Ultra-TTS splits text before calling a backend because local engines have different practical
limits. Current limits include:

- Orpheus: 600 characters per segment
- Chatterbox: backend-defined limit
- Kokoro: backend-defined limit
- Piper: backend-defined limit
- MLX models: model-defined limit

The generated WAV is written under `outputs/web/`. A sibling `*.manifest.json` records the
backend, voice, language, segment boundaries, and text used for each generated segment.

## Local files and ignored artifacts

Ultra-TTS keeps local artifacts inside the project when possible:

- `models/piper/` for Piper ONNX voice files
- `models/huggingface/` for direct Hugging Face repo snapshots downloaded by `scripts/download_models.py`
- `.cache/huggingface/` and `.cache/torch/` for library-managed caches
- `outputs/` for generated audio
- `logs/` for local runtime logs
- `.venv/`, `.venv-kokoro/`, and `.venv-mlx/` for local Python environments

The app sets `HF_HOME`, `HF_HUB_CACHE`, `HF_ASSETS_CACHE`, `HF_XET_CACHE`,
`TRANSFORMERS_CACHE`, `TORCH_HOME`, and `XDG_CACHE_HOME` at startup so Chatterbox, Kokoro,
Dia, SNAC, and MLX-Audio cache under this repository by default.

Generated audio, model files, logs, virtual environments, local caches, and large model artifacts are intentionally ignored by Git.

## Model licenses

Ultra-TTS itself is licensed under Apache-2.0.

This repository does not grant additional rights to third-party TTS models, model weights, voice files, datasets, or generated voices.

Users are responsible for checking and complying with the license terms of each model and
backend they download or use, including LM Studio models, Hugging Face models, Piper voices,
Kokoro, Chatterbox, Dia, and MLX-Audio models.

## Security and privacy

Ultra-TTS is designed to run local TTS workflows. Generated audio, logs, downloaded models,
caches, and virtual environments are intentionally excluded from Git.

Do not commit API keys, private model files, generated audio containing personal data, or unreleased vulnerability details.

Local file paths used for reference audio should be treated as private environment details
unless they are intentionally shared.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup expectations,
pull request guidance, and suggested first contributions.

Before opening a pull request, run:

```bash
python -m unittest discover -s tests
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned improvements around documentation, model setup
clarity, packaging, CI, and regression testing.

## License

Apache-2.0. See [LICENSE](LICENSE).
