# Introduction

`sync2txt` is a script designed to automatically aggregate source code files from a specified directory into a single text file in a target directory. This facilitates providing the entire project code as context to large language models (e.g., LLM/LLMtxt). The script supports automatic directory monitoring for real-time updates to the aggregated document, as well as manual execution for one-time generation.

[中文](README-ZH.md) English
---

# Use Cases

You can specify the target file as a directory in Google Drive, allowing the project code to be aggregated into Google Drive for easy use with Gemini.

## Key Features

- **Multi-file Type Support**: Aggregates `.py`, `.ts`, `.tsx`, `.js`, `.json`, `.md`, and other common code and text files.
- **Smart Ignore**:
  - Automatically applies `.gitignore` rules.
  - Supports custom `IGNORE_PATTERNS`.
  - Excludes binary files, images, and other irrelevant content.
- **Directory Structure Export**: Generates a clean tree-like directory structure (including ignored markers).
- **Flexible Configuration**:
  - Supports YAML configuration files.
  - Command-line parameter overrides.
- **Advanced Filtering**:
  - Filters by file size (`--max-size`).
  - Filters by modification time (`--since-days`).
- **Detailed Logging**: Multi-level logging for debugging.

## Usage

### Install Dependencies

```bash
# Main dependencies
pip install -r requirements.txt
# Test dependencies (optional)
pip install -r requirements-test.txt
```

### Configuration

#### 1. Configuration File (YAML)

```yaml
MONITORED_CODE_DIR: /path/to/code
OUTPUT_DOCUMENT_PATH: /path/to/output.txt
CODE_FILE_PATTERNS: 
  - '*.py'
  - '*.md'
IGNORE_PATTERNS:
  - node_modules
ENABLE_AUTOMATIC_MONITORING: true
DEBOUNCE_TIME: 2.0
```

#### 2. Command-Line Arguments

| Argument | Description | Example |
|------|------|------|
| `-s/--src` | Source code directory | `-s ./src` |
| `-o/--out` | Output file path | `-o output.txt` |
| `-c/--config` | Configuration file path | `-c config.yaml` |
| `--max-size` | Maximum file size (MB) | `--max-size 2` |
| `--since-days` | Days since last modification | `--since-days 7` |

### Run Examples

```bash
# Basic usage
python3 sync2txt.py -s ./project -o output.txt

# Use config file + filter large files
python3 sync2txt.py -c config.yaml --max-size 1.5

# Sync only recently modified files
python3 sync2txt.py -s ./src -o out.txt --since-days 3
```

## Testing (Pending)

```bash
# Run tests
pytest --cov=.

# Generate test coverage report
pytest --cov=. --cov-report=html
```

## Output Format Example

```
--- Project Code Context (Manual Run @ 2023-11-15 10:00:00) ---

Included Files (2):
- main.py
- utils/helper.py

--- File: main.py ---

import utils

if __name__ == "__main__":
    print("Hello")

--- File: utils/helper.py ---

def help():
    return "Help message"

--- Directory Structure ---
project/
├── main.py
└── utils/
    └── helper.py
```

## Development Guide

### Code Structure

- `sync2txt.py`: Main program.
- `directory_tree.py`: Directory tree generation module.
- `tests/`: Unit tests.

### Extension Suggestions

1. Add support for more file types.
2. Implement incremental update mode.
3. Support remote storage for output.

## License

MIT License