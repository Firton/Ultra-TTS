# Demo

Ultra-TTS is a local browser GUI and CLI workspace for Japanese and multilingual TTS workflows.

This document describes what a reviewer or new user should be able to verify without
downloading every heavy backend.

## Web UI

The web UI is served locally by `web_app.py`.

```bash
python web_app.py --host 127.0.0.1 --port 8765 --open
```

Then open:

```text
http://127.0.0.1:8765
```

## Screenshot

A Web UI screenshot should be stored at:

```text
docs/images/ultra-tts-web-ui.png
```

The screenshot must not include:

- private file paths
- API keys
- personal generated text
- generated audio containing personal data
- private model names or local-only secrets

## Demo workflows

### 1. Single text generation

Use the web UI to enter a short sentence and select an available local backend.

This demonstrates the basic GUI workflow.

### 2. Multi-speaker script generation

Use a speaker-tagged script to verify that the UI can represent multi-speaker text before
backend generation.

This demonstrates the intended dialogue workflow.

### 3. Long-form text splitting

Use the long-form tab with a longer paragraph or article.

This demonstrates text segmentation before backend calls and manifest metadata next to
generated output.

## Audio samples

Audio samples should be added only when model and voice licenses allow redistribution.

For now, this repository does not commit generated audio samples.
