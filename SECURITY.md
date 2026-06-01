# Security Policy

## Reporting a Vulnerability

If you find a security issue in Ultra-TTS, please do not disclose it publicly before
it is reviewed.

Open an issue only for non-sensitive reports. For sensitive vulnerability details,
use a private communication channel if one is listed in the maintainer profile.

## Scope

Ultra-TTS is a local TTS GUI and CLI workspace. Security-sensitive areas include:

- local file handling
- model and backend configuration
- generated audio output paths
- launcher scripts
- web UI request handling
- environment variables and local cache paths

## Do not include

Please do not include the following in public issues or pull requests:

- API keys
- access tokens
- private model files
- generated audio containing personal information
- unreleased vulnerability details
- local machine paths that reveal private information

## Maintainer response

The maintainer will review security reports, assess impact, and publish fixes or
mitigations when appropriate.
