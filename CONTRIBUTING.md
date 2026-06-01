# Contributing

Contributions are welcome.

Ultra-TTS is an early open-source project focused on local Japanese and multilingual TTS
workflows.

## Good first contributions

Good first contributions include:

- improving setup documentation
- adding backend-specific examples
- improving Japanese text normalization
- adding tests for long-form text segmentation
- improving error messages
- documenting model/backend requirements
- improving Windows, macOS, and Linux launch instructions

## Before opening a pull request

Please make sure that:

- the change is clearly described
- generated audio, models, logs, caches, and virtual environments are not committed
- local machine-specific paths are not committed
- relevant lightweight tests are added or updated
- `python -m unittest discover -s tests` passes

## Large changes

Please open an issue before large changes such as:

- adding a new backend
- changing long-form segmentation behavior
- changing output directory behavior
- changing launcher behavior
- adding packaging or distribution workflows

## AI-assisted contributions

AI-assisted contributions are allowed, but all changes must be reviewed by a human maintainer
before release.

Tests and documentation must be checked before merging.
