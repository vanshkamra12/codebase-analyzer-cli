# 🚀 Codebase Analyzer CLI

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org) [![Rich](https://img.shields.io/badge/Rich-Dashboard-brightgreen)](https://rich.readthedocs.io) [![AST](https://img.shields.io/badge/AST-Parsing-orange)](https://docs.python.org/3/library/ast.html)

Production-grade code intelligence for Python repositories. Analyzed Django (2,894 files):

| Metric | Result |
|--------|--------|
| Files | 2,894 |
| Functions | **31,602** |
| Classes | **10,893** |
| Call Edges | **182,896** |
| JSON Export | 15.4 MB |
| Avg Complexity | 2.04 |

![Demo](demo.gif)

**One-line install:**
```bash
pip install git+https://github.com/vanshkamra12/codebase-analyzer-cli.git && codebase-analyzer --help
```

---

## What it does

- Finds every `.py` file in a repo and parses it with Python's `ast` module
- Extracts functions, classes, and imports with file locations and line numbers
- Builds a call graph (what calls what, and how many times)
- Calculates McCabe cyclomatic complexity per function
- Shows a summary in the terminal using a Rich table
- Can export everything as JSON or a Markdown report

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

# skip directories like tests or migrations
codebase-analyzer ./myrepo --exclude tests migrations

# both outputs, no terminal summary
codebase-analyzer ./myrepo --export analysis.json --report report.md --quiet

# check version
codebase-analyzer --version
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
