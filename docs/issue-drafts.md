# Issue drafts

These are real maintainer roadmap issues that can be created manually on GitHub.

## 1. Add demo screenshot for the web UI

### Summary

Add a screenshot of the Ultra-TTS web UI to the README.

### Why

The project currently explains the local browser GUI in text, but a screenshot would make
the workflow easier to understand for new users and reviewers.

### Tasks

- Run the web UI locally
- Capture a clean screenshot without private paths or generated personal content
- Save it as `docs/images/ultra-tts-web-ui.png`
- Link it from README

## 2. Add third-party model and backend license notes

### Summary

Maintain a backend-by-backend table for upstream model and backend responsibility notes.

### Why

Ultra-TTS integrates multiple local TTS workflows. Users need to understand that the
repository license does not automatically grant rights to third-party model weights, voice
files, datasets, or generated voices.

### Tasks

- Review upstream docs for each backend
- Add upstream URLs
- Add license/usage notes where verified
- Leave unverified licenses as "check upstream license"
- Avoid redistributing model weights or generated audio

## 3. Add Japanese text normalization regression tests

### Summary

Add lightweight tests for Japanese text normalization and long-form segmentation behavior.

### Why

Japanese TTS quality depends on handling punctuation, numbers, symbols, mixed
Japanese/English text, and long-form segmentation reliably.

### Tasks

- Add tests for Japanese punctuation
- Add tests for mixed Japanese/English text
- Add tests for numbers and units
- Add tests that avoid empty segments
- Keep tests lightweight and independent of model downloads
