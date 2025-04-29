# Gerrit AI Review

A tool for AI-assisted code review of Gerrit patches.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Connect to Gerrit and retrieve patches
- Run AI-assisted code review using Aider
  - Runs three separate reviews
    - Generic review
    - Style check review
    - Static analysis review
- Post review comments back to Gerrit

## Installation

(Disclaimer: setup.py is not functional yet. pip -e has not been tested yet. Only manual installation instructions are provided for now.)

```bash
# Clone the repository
git clone https://github.com/marcvef/gerrit_ai_review
cd gerrit_ai_review

# Set up Python virtual environment (Aider requires Python 3.9-3.12)
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply necessary patches to Aider (must be in virtual environment)
./patch_aider_api.sh

# Configure the tool
cp config/config.yaml config/my_config.yaml
# Edit config/config.yaml to add your API keys and customize settings

# Optional: Clone or update your Lustre codebase
# git clone https://github.com/lustre/lustre-release /path/to/lustre/repo
# Important: Set the correct path to your Lustre repository in config.yaml
# Note: The tool will clean the Lustre codebase before running reviews
```

## Usage
(Disclaimer: The assumption is that the python scripts are running from the root directory of the repository. Testing pending for other pwds.)

This software allows two modes of operation:

1. **AI only** Run the AI reviewer only
- Usage:
```bash
$ python ai_review.py -h
usage: ai_review.py [-h] [--yes] [-o OUTPUT] [-i INSTRUCTION] [-c CONFIG] [--aider | --augment] [-f | -p] [--max-files MAX_FILES] [--max-tokens MAX_TOKENS] [-v] [--generic-review] [--style-review] [--static-analysis-review]

Run AI-assisted code review with different backends

options:
  -h, --help            show this help message and exit
  --yes                 Skip confirmation prompt
  -o OUTPUT, --output OUTPUT
                        Output file to write the response to
  -i INSTRUCTION, --instruction INSTRUCTION
                        File containing the instruction for the AI
  -c CONFIG, --config CONFIG
                        Path to configuration file
  --aider               Use Aider as the backend (default)
  --augment             Use Augment as the backend
  -f, --free-model      Use the free model (default)
  -p, --paid-model      Use the paid model
  --max-files MAX_FILES
                        Maximum number of most-changed files to add to context (default: 3)
  --max-tokens MAX_TOKENS
                        Maximum number of tokens allowed in context (default: 200,000)
  -v, --verbose         Print verbose output, including command results

Review types (if none specified, all will be run):
  --generic-review      Run generic review
  --style-review        Run style check review
  --static-analysis-review
                        Run static analysis review
```
- Example run with paid model and style review only:
```bash
$ python ai_review.py -p -c <your-config-file> --style-review
```

2. **AI + Gerrit** Run the AI reviewer and post the results to Gerrit
- Usage: 
```bash
$ python gerrit_review_patch.py -h
usage: gerrit_review_patch.py [-h] [-c CONFIG] [--test] [-s] [--yes] [-v] [--generic-review] [--style-review] [--static-analysis-review] [change_id]

Connect to Gerrit and review patches

positional arguments:
  change_id             Change ID, number, or Gerrit URL to retrieve and review

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to configuration file
  --test                Test the connection to Gerrit
  -s, --skip-gerrit-review
                        Run AI review but skip posting the results to Gerrit
  --yes                 Skip confirmation prompts
  -v, --verbose         Print verbose output, including command results

Review types (if none specified, all will be run):
  --generic-review      Run generic review
  --style-review        Run style check review
  --static-analysis-review
                        Run static analysis review
```

- Test connection with Gerrit:
```bash
$ python gerrit_review_patch.py -c <your-config-file> --test
```
- Review a specific patch and post the results to Gerrit. `--yes` skips confirmation prompt for each AI review:
```bash
python gerrit_review_patch.py --config <your-config-file> https://review.whamcloud.com/c/fs/lustre-release/+/<id>/ --yes
```

Note, when no review type is set, all three reviews will be run in sequence and posted to Gerrit - each review type is posted as a separate comment.

## Token information
Token configurations for `gerrit_review_patch.py` should be done in the config file. The following config fields have an impact on token usage and can be modified to reduce the number of tokens used for each API call. This is particularly important when using the free model:
- `common_ai_refs` are used in the generic review (around 3.5K tokens)
- `style_check_ai_refs` are used in the style check review (around 18K tokens)
- `static_analysis_ai_refs` are used in the static analysis review (around 5K tokens)
- `max_tokens` is the maximum number of tokens allowed in the context (default: 200,000). `gerrit_review_patch.py` tries to fit within that context window by reducing the number of source files added to the context automatically. `max_files` is the maximum number of files to add to the context.
- `map_tokens` is the number of tokens allowed for the repository map (default: 8192).
- `max_files` is the maximum number of files to add to the context from a given commit (default: 5).

Further CLI options to make using free models more easily usable are planned.

## Configuration

Create a `config/config.yaml` file with the following structure:

```yaml
# Lustre project directory
lustre_dir: "/path/to/lustre/repo"

# Aider configuration
aider:
  # Default instruction file. Use either instructions or instructions_short. Feel free to modify the instructions.
  generic_instruction_file: "config/instructions/generic.txt"
  style_check_instruction_file: "config/instructions/style_check.txt"
  static_analysis_instruction_file: "config/instructions/static_analysis.txt"

  # Common AI references to add to the context
  common_ai_refs:
    - "ai_reference/lustre_arch.md"
  
  style_check_ai_refs:
    - "ai_reference/lustre_code_style.md"
    - "ai_reference/linux_code_style.md"

  static_analysis_ai_refs:
    - "ai_reference/static_analysis.md"

  # API keys
  api_keys:
    free_gemini: "your-free-api-key"
    paid_gemini: "your-paid-api-key"

  # Model settings (currently only gemini supported)
  models:
    free_model: "gemini-1.0-pro"
    paid_model: "gemini-1.5-pro"

  # Model metadata file path
  model_metadata_file: "config/model-metadata.json"

  # Token limits
  max_tokens: 200000
  map_tokens: 8192

  # Maximum number of files to add to context from a given commit
  max_files: 5

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
