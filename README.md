# Gerrit AI Review

A tool for AI-assisted code review of Gerrit patches.

## Features

- Connect to Gerrit and retrieve patches
- Run AI-assisted code review using Aider
- Post review comments back to Gerrit

## Installation

```bash
pip install -e .
```

## Usage

```bash
python gerrit_review_patch.py --test  # Test connection to Gerrit
python gerrit_review_patch.py <change_id>  # Review a specific change
python gerrit_review_patch.py <gerrit_url>  # Review a change from URL
```

## Configuration

Create a `config/config.yaml` file with the following structure:

```yaml
lustre_dir: "/path/to/lustre/repo"
default_instruction_file: "config/default_instruction.txt"
model_metadata_file: "config/model-metadata.json"
max_tokens: 200000
common_ai_refs:
  - "ai_reference/lustre_arch.md"
api_keys:
  free_gemini: "your-free-api-key"
  paid_gemini: "your-paid-api-key"
models:
  free_model: "gemini-1.0-pro"
  paid_model: "gemini-1.5-pro"
gerrit:
  url: "https://review.example.com"
  project: "project-name"
  branch: "main"
  auth:
    username: "your-username"
    password: "your-password"
```
