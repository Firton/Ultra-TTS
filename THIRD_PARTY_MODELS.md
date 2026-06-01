# Third-party models and backends

Ultra-TTS is an application and workflow repository for running local TTS backends.

Ultra-TTS itself is licensed under Apache-2.0, but this license does not automatically
apply to third-party models, model weights, voice files, datasets, generated voices,
or backend projects.

Users are responsible for checking and complying with each upstream license before
downloading, running, redistributing, or commercializing outputs.

## Backend and model responsibility matrix

| Backend / workflow | What Ultra-TTS provides | Typical upstream source | Required local files | License / usage notes | Redistribution notes | Status |
|---|---|---|---|---|---|---|
| LM Studio / Orpheus | Local OpenAI-compatible API workflow and Orpheus integration notes | LM Studio and Orpheus-compatible model providers | GGUF model file loaded in LM Studio | Check LM Studio terms and the selected model's license | Do not redistribute model files unless upstream permits it | Supported workflow |
| Chatterbox Multilingual | Local multilingual TTS backend integration | Chatterbox / Hugging Face model sources | Python dependencies and model files | Check upstream model and package licenses | Do not redistribute model weights unless upstream permits it | Supported workflow |
| Kokoro worker | Lightweight local worker workflow | Kokoro package/model sources | Worker environment, voice/model files | Check upstream package, model, and voice licenses | Do not redistribute voice/model files unless upstream permits it | Supported workflow |
| Piper | Local-process TTS backend using ONNX voice files | Piper and Piper voice repositories | ONNX voice files under `models/piper/` | Check each voice file's upstream license | Voice redistribution depends on the selected voice license | Supported workflow |
| Dia | Experimental dialogue backend | Dia model sources | Dia model and related files | Check upstream model license and usage terms | Do not redistribute model files unless upstream permits it | Experimental |
| MLX-Audio | Apple Silicon workflow for MLX-compatible TTS models | MLX-Audio and MLX community model repositories | MLX environment and model files | Check each model's upstream license | Redistribution depends on each model license | Supported workflow |

## Generated audio

Generated audio may be subject to the terms of the model, voice, dataset, or backend
used to create it.

Ultra-TTS does not grant additional rights to generated voices or outputs.

Before publishing generated samples, users should verify:

- the model license
- the voice license
- dataset restrictions, if any
- commercial-use restrictions
- attribution requirements
- redistribution restrictions

## Repository policy

This repository intentionally does not commit:

- model weights
- GGUF files
- ONNX voice files
- generated audio
- private reference voices
- logs
- local caches
- virtual environments

See `.gitignore` for the exact ignore rules.

## For contributors

When adding a new backend or model preset, include:

- upstream project name
- upstream URL
- required local files
- setup notes
- license notes
- redistribution notes
- whether the backend is stable, experimental, or documentation-only

Do not add model weights or generated audio to this repository without explicit maintainer
approval and verified redistribution rights.
