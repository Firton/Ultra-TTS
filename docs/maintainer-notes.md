# Maintainer notes

This document summarizes the current maintainer position of Ultra-TTS.

Ultra-TTS is an early open-source local browser GUI and CLI workspace for running
Japanese and multilingual TTS models.

The project is still early, so it should not be described as broadly adopted or
production-proven. Its current value is as a practical local TTS workflow for
developers, creators, educators, accessibility-focused users, and maintainers who
want to compare or run local TTS backends without relying only on cloud APIs.

## Project status and maintainer scope

Ultra-TTS is an early open-source project.

The current maintainer is responsible for the public Ultra-TTS repository structure,
local browser GUI workflow, CLI workflow, backend integration notes, documentation,
lightweight tests, release notes, issue triage, pull request review, and third-party
model/backend responsibility notes.

The repository history may include earlier code lineage or upstream work. The current
maintainer scope is the public Ultra-TTS workspace as maintained in this repository:
the packaging of local TTS workflows, documentation, launcher scripts, backend
integration notes, tests, and ongoing release/issue management.

The project should not be described as broadly adopted or production-proven. Its current
public value is as a practical local TTS workspace for Japanese and multilingual workflows,
backend comparison, long-form text splitting, and model responsibility documentation.

## Current maintainer responsibilities

The primary maintainer is responsible for:

- repository structure
- GUI and CLI workflow maintenance
- backend integration notes
- documentation
- lightweight tests
- release notes
- issue triage
- pull request review
- model/backend responsibility notes

## Current public evidence

Current public evidence includes:

- Apache-2.0 license
- README with quickstart and backend notes
- SECURITY.md
- CONTRIBUTING.md
- ROADMAP.md
- CHANGELOG.md
- CODEOWNERS
- GitHub Actions lightweight test workflow
- release history
- merged pull requests for OSS readiness work
- third-party model/backend responsibility notes

## Appropriate project description

Use this description when summarizing the project:

> Ultra-TTS is an early open-source local browser GUI and CLI workspace for running
> Japanese and multilingual TTS models locally.

Do not claim:

- broad adoption
- production usage
- external users
- download counts
- stars beyond what GitHub shows
- model redistribution rights not granted by upstream projects

## Possible maintainer automation use cases

Useful maintainer automation includes:

- pull request review assistance
- issue triage
- release-note drafting
- documentation synchronization
- backend setup documentation
- regression test generation
- Japanese text normalization tests
- long-form TTS segmentation tests

All generated changes should be reviewed by the maintainer and validated by CI before release.
