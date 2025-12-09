# Skills Overview

This workspace contains several independent skills. Each folder is a self-contained tool that can be enabled or composed as needed.

## airss
- Purpose: RSS/Atom ingestion pipeline with AI summarization and Notion sync.
- Highlights: monitors feeds, parses content (including Twitter/X), uploads images, and creates structured Notion pages with AI-generated summaries and categories.
- Entrypoint: `main.py`; configuration in `config.yaml`.

## article-extractor
- Purpose: Extracts and cleans full article text from source pages.
- Highlights: focuses on readability-friendly output for downstream processing or summarization.
- Docs: see `SKILL.md` for usage.

## prompt-rewriter
- Purpose: Utility skill for rewriting or refining prompts.
- Highlights: lightweight helper to post-process prompts before sending to models.
- Docs: see `SKILL.md`.

## VideoDownload
- Purpose: Download videos from supported platforms.
- Highlights: simple CLI skill; configuration via `pyproject.toml`.
- Docs: `README.md` and `SKILL.md` describe setup and usage.
