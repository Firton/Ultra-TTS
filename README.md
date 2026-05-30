# Ultra-TTS

Ultra-TTS is a local browser app and CLI workspace for experimenting with text-to-speech backends on Windows.

The current app supports:

- Orpheus through LM Studio's local OpenAI-compatible API
- Chatterbox Multilingual for local multilingual generation
- Kokoro through a separate lightweight local worker
- Dia as an experimental English dialogue backend
- Single-text and multi-speaker script generation

Generated audio, model files, logs, virtual environments, and local cache files are intentionally ignored by Git.

## Web App

Start the browser UI:

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

Dia is dialogue-focused and expects English speaker-tagged dialogue. It needs more VRAM than the current 6GB-class local GPU for practical quality, so the UI treats it as experimental.

## Local Files

Ignored by Git:

- `.venv/`
- `.venv-kokoro/`
- `logs/`
- `outputs/`
- audio outputs such as `*.wav`, `*.mp3`, `*.flac`
- downloaded model files such as `*.gguf`, `*.safetensors`, `*.ckpt`, `*.pt`, `*.onnx`

## License

Apache 2.0

