# codebase-analyzer

A CLI tool that parses Python repositories using AST and extracts functions, classes, imports, call graphs, and cyclomatic complexity. Built to run on real, large codebases.

![Demo](demo.gif)

---

## What it does

- Finds every `.py` file in a repo and parses it with Python's `ast` module
- Extracts functions, classes, and imports with file locations and line numbers
- Builds a call graph (what calls what, and how many times)
- Calculates McCabe cyclomatic complexity per function
- Shows a summary in the terminal using a Rich table
- Can export everything as JSON or a Markdown report

## Results on Django (2,894 files)

| Metric | Value |
|--------|-------|
| Functions | 31,602 |
| Classes | 10,893 |
| Call graph edges | 182,896 |
| High-complexity functions (CC > 10) | 434 |
| JSON export size | 15.4 MB |

---

## Installation

```bash
pip install .
```

Or in editable/dev mode:

```bash
pip install -e .
```

This registers the `codebase-analyzer` command globally.

---

## Usage

```bash
# analyze current directory
codebase-analyzer .

# analyze a specific repo
codebase-analyzer ./myrepo

# export JSON output
codebase-analyzer ./myrepo --export analysis.json

# generate a Markdown report
codebase-analyzer ./myrepo --report report.md

# both, no terminal output
codebase-analyzer ./myrepo --export analysis.json --report report.md --quiet
```

---

## JSON output format

```json
{
  "timestamp": "2026-03-16T20:08:23",
  "repo_path": "/path/to/repo",
  "stats": {
    "total_files": 2894,
    "total_functions": 31602,
    "avg_cyclomatic_complexity": 2.04,
    "high_complexity_functions": 434
  },
  "functions": [
    {
      "file": "django/db/models/base.py",
      "name": "save",
      "line": 740,
      "args_count": 3,
      "is_async": false,
      "complexity": 12
    }
  ],
  "classes": [...],
  "imports": [...],
  "call_graph": {
    "assertEqual": [{ "caller_file": "tests/test_basic.py", "caller_line": 42 }]
  }
}
```

---

## Requirements

- Python 3.8+
- `rich >= 13.0`

---

## License

MIT
