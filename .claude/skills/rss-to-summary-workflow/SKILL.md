---
name: rss-to-summary-workflow
description: Orchestrate multi-skill workflows (e.g., run rss-article-saver then daily-article-summarizer) with ordered steps, per-step timing, and run logs. Use when Codex needs to run several skills in sequence and track durations.
---

# RSS To Summary Workflow

## Overview

Orchestrate skills by running named steps in sequence, measuring each step, and logging results for later analysis.

## Quick Start

Run from this skill directory:

```bash
python scripts/run_workflow.py --list
python scripts/run_workflow.py --workflow rss-to-summary
python scripts/run_workflow.py --dry-run --workflow rss-to-summary
```

## Configure Workflows

Edit `workflows.yaml` to add new workflows or adjust commands.

```yaml
skills:
  rss-article-saver:
    path: .claude/skills/rss-article-saver
    command: ["uv", "run", "--env-file", ".env", "python", "main.py"]
  daily-article-summarizer:
    path: .claude/skills/daily-article-summarizer
    command: ["uv", "run", "--env-file", ".env", "python", "main.py"]

workflows:
  rss-to-summary:
    steps:
      - skill: rss-article-saver
      - skill: daily-article-summarizer
```

Rules:
- `skills` defines reusable skill configs.
- `workflows.<name>.steps` lists steps in order.
- Each step references a `skill` key from `skills`.
- `timeout_seconds` is per step and optional. If omitted, no timeout is enforced.

## Logging

Each executed step appends a JSON line to:

`logs/workflow_runs.jsonl`

Fields include: workflow, step, start_time, end_time, duration_seconds, status, exit_code.

## Failure Behavior

If a step fails or times out, the runner stops and does not execute remaining steps.
