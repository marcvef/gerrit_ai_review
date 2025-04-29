# Gerrit AI Review

A tool for AI-assisted code review of Gerrit patches.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
# Lustre project directory
lustre_dir: "/path/to/lustre/repo"

# Aider configuration
aider:
  # Default instruction file
  default_instruction_file: "config/default_instruction.txt"

  # Common AI references to add to the context
  common_ai_refs:
    - "ai_reference/lustre_arch.md"

  # API keys
  api_keys:
    free_gemini: "your-free-api-key"
    paid_gemini: "your-paid-api-key"

  # Model settings
  models:
    free_model: "gemini-1.0-pro"
    paid_model: "gemini-1.5-pro"

  # Model metadata file path
  model_metadata_file: "config/model-metadata.json"

  # Token limits
  max_tokens: 200000
  map_tokens: 8192

  # Directories to ignore when adding files to context
  ignored_dirs:
    - "lustre/tests"

# Gerrit server settings
gerrit:
  # Gerrit server URL
  url: "https://review.example.com"

  # Project name
  project: "project-name"

  # Branch name
  branch: "main"

  # Authentication settings
  auth:
    username: "your-username"
    password: "your-password"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
