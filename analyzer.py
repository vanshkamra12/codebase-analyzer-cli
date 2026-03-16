#!/usr/bin/env python3

import ast
import os
import json
import argparse
import datetime
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()


class CodebaseAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.imports: List[Dict[str, Any]] = []
        self.call_graph: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.stats: Dict[str, Any] = {}
        self._errors: List[str] = []

    def analyze(self) -> None:
        console.print(Panel.fit(
            f"[bold]Codebase Analyzer[/bold]\n[dim]{self.repo_path}[/dim]",
            border_style="blue"
        ))

        py_files = list(self.repo_path.rglob("*.py"))
        console.print(f"\nFound [bold]{len(py_files)}[/bold] Python files\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Parsing...", total=len(py_files))
            for py_file in py_files:
                try:
                    self._parse_file(py_file)
                except SyntaxError as e:
                    self._errors.append(f"{py_file.name}: SyntaxError line {e.lineno}")
                except Exception as e:
                    self._errors.append(f"{py_file.name}: {str(e)[:80]}")
                progress.advance(task)

        if self._errors:
            console.print(f"\n[yellow]Skipped {len(self._errors)} file(s) with parse errors[/yellow]")

        self._compute_stats()
        console.print("\n[green]Done![/green]")

    def print_summary(self) -> None:
        table = Table(
            title="Analysis Results",
            show_header=True,
            header_style="bold",
            border_style="dim",
        )
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right")

        skip = {"top_modules"}
        for key, val in self.stats.items():
            if key in skip:
                continue
            if isinstance(val, float):
                display = f"{val:,.2f}"
            elif isinstance(val, int):
                display = f"{val:,}"
            else:
                display = str(val)
            table.add_row(key.replace("_", " ").title(), display)

        console.print(table)

        top_modules = self.stats.get("top_modules", {})
        if top_modules:
            console.print("\nTop imports:")
            for mod, count in top_modules.items():
                console.print(f"  {mod}: {count}")

        top_calls = sorted(self.call_graph.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        if top_calls:
            console.print("\nMost called functions:")
            for name, calls in top_calls:
                console.print(f"  {name}: {len(calls)} calls")

    def export_json(self, output_file: str) -> None:
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "repo_path": str(self.repo_path),
            "stats": self.stats,
            "functions": self.functions[:1000],
            "classes": self.classes[:500],
            "imports": self.imports[:2000],
            "call_graph": {k: v for k, v in list(self.call_graph.items())[:5000]},
            "parse_errors": self._errors,
        }

        out = Path(output_file)
        with out.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        size_mb = out.stat().st_size / (1024 * 1024)
        console.print(f"\nExported {size_mb:.2f} MB to {out}")

    def generate_report(self, output_file: str) -> None:
        top_modules = self.stats.get("top_modules", {})
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "# Codebase Analysis Report\n\n",
            f"**Repo:** `{self.repo_path}` — **Generated:** {now}\n\n",
            "## Summary\n\n",
        ]

        for key, val in self.stats.items():
            if key == "top_modules":
                continue
            if isinstance(val, float):
                formatted = f"{val:,.2f}"
            elif isinstance(val, int):
                formatted = f"{val:,}"
            else:
                formatted = str(val)
            lines.append(f"- **{key.replace('_', ' ').title()}:** {formatted}\n")

        lines.append("\n## Top Dependencies\n\n")
        for mod, count in top_modules.items():
            lines.append(f"- `{mod}`: {count} imports\n")

        lines.append("\n## Most Called Functions\n\n")
        top_calls = sorted(self.call_graph.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for name, calls in top_calls:
            lines.append(f"- `{name}`: {len(calls)} calls\n")

        lines.append("\n## Classes (by method count)\n\n")
        for cls in sorted(self.classes, key=lambda c: c["methods_count"], reverse=True)[:20]:
            lines.append(f"- `{cls['name']}` in `{cls['file']}` — {cls['methods_count']} methods\n")

        if self._errors:
            lines.append("\n## Parse Errors\n\n")
            for err in self._errors:
                lines.append(f"- {err}\n")

        out = Path(output_file)
        out.write_text("".join(lines), encoding="utf-8")
        console.print(f"\nReport saved to {out}")

    def _parse_file(self, file_path: Path) -> None:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(file_path))
        rel = str(file_path.relative_to(self.repo_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.classes.append({
                    "file": rel,
                    "name": node.name,
                    "line": node.lineno,
                    "methods_count": sum(
                        1 for n in node.body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ),
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions.append({
                    "file": rel,
                    "name": node.name,
                    "line": node.lineno,
                    "args_count": len(node.args.args),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "complexity": self._cyclomatic_complexity(node),
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append({
                        "module": alias.name,
                        "file": rel,
                        "is_relative": False,
                    })
            elif isinstance(node, ast.ImportFrom):
                self.imports.append({
                    "module": node.module or "",
                    "file": rel,
                    "is_relative": (node.level or 0) > 0,
                })

        self._extract_calls(tree, rel)

    def _cyclomatic_complexity(self, func_node: ast.AST) -> int:
        """McCabe cyclomatic complexity. Starts at 1, +1 per branch."""
        score = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With,
                                  ast.Assert, ast.ExceptHandler)):
                score += 1
            elif isinstance(node, ast.BoolOp):
                score += len(node.values) - 1
            elif isinstance(node, (ast.ListComp, ast.SetComp,
                                    ast.DictComp, ast.GeneratorExp)):
                score += 1
        return score

    def _extract_calls(self, tree: ast.AST, rel_path: str) -> None:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            else:
                continue
            self.call_graph[name].append({
                "caller_file": rel_path,
                "caller_line": getattr(node, "lineno", 0),
            })

    def _compute_stats(self) -> None:
        py_files = list(self.repo_path.rglob("*.py"))
        num_files = len(py_files)

        external = [
            imp["module"].split(".")[0]
            for imp in self.imports
            if imp["module"] and not imp["is_relative"]
        ]

        complexities = [f["complexity"] for f in self.functions]
        avg_cc = round(sum(complexities) / max(1, len(complexities)), 2)
        high_cc = sum(1 for c in complexities if c > 10)

        self.stats = {
            "total_files": num_files,
            "total_functions": len(self.functions),
            "total_classes": len(self.classes),
            "total_imports": len(self.imports),
            "call_edges": sum(len(v) for v in self.call_graph.values()),
            "unique_callee_names": len(self.call_graph),
            "avg_functions_per_file": round(len(self.functions) / max(1, num_files), 2),
            "avg_cyclomatic_complexity": avg_cc,
            "high_complexity_functions": high_cc,
            "top_modules": dict(Counter(external).most_common(5)),
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a Python codebase using AST parsing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  analyzer .                        # analyze current directory
  analyzer ./myrepo                 # analyze a specific repo
  analyzer ./myrepo --export out.json
  analyzer ./myrepo --report out.md
        """,
    )
    parser.add_argument("repo_path", nargs="?", default=".", help="path to repo (default: .)")
    parser.add_argument("--export", "-e", metavar="FILE", help="export results as JSON")
    parser.add_argument("--report", "-r", metavar="FILE", help="export results as Markdown")
    parser.add_argument("--quiet", "-q", action="store_true", help="skip summary output")

    args = parser.parse_args()

    repo = Path(args.repo_path)
    if not repo.exists():
        console.print(f"[red]Error: path not found: {args.repo_path}[/red]")
        sys.exit(1)

    analyzer = CodebaseAnalyzer(str(repo))
    analyzer.analyze()

    if not args.quiet:
        analyzer.print_summary()

    if args.export:
        analyzer.export_json(args.export)

    if args.report:
        analyzer.generate_report(args.report)


if __name__ == "__main__":
    main()
