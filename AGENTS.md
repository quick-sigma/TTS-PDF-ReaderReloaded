# AGENTS.md — Coding Agent Instructions

## Project Overview

pdfreader-reborn is a PyQt6-based PDF reader built with a microkernel architecture.
Python 3.13, managed with [uv](https://docs.astral.sh/uv/).

## Build & Run Commands

```bash
uv sync                          # Install dependencies
uv run python main.py            # Run the application
uv run python main.py file.pdf   # Open a specific PDF
```

## Testing

Framework: **pytest** (configured in `pyproject.toml`).

```bash
uv run pytest                                      # all tests
uv run pytest tests/data/test_document.py           # single file
uv run pytest tests/data/test_document.py::TestPdfDocument::test_page_count  # single test
uv run pytest -v                                    # verbose
uv run pytest --tb=long                             # full tracebacks
```

Test files go in `tests/`, mirroring the `src/` layout (e.g., `tests/data/test_document.py`).
Shared fixtures are in `tests/conftest.py` — use `sample_pdf` and `icons_dir` fixtures.

## Linting & Formatting

Install ruff as a dev dependency, then run before finalizing changes:

```bash
uv add --dev ruff
uv run ruff check --fix .       # lint + auto-fix
uv run ruff format .            # format
```

## Type Checking

```bash
uv add --dev mypy
uv run mypy .
```

## Code Style

### Types

- Use Python 3.13 syntax: `list[str]`, `dict[str, int]`, `X | Y` (not `Optional`/`Union`).
- Add return type annotations to all public and private functions.
- Use `-> None` on `__init__` and void methods.

### Imports

Group: stdlib → third-party → local (blank line between groups), alphabetically sorted.

```python
from abc import ABC, abstractmethod
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QToolBar

from pdfreader_reborn.data.document import PdfDocument
```

No wildcard imports. Use absolute imports.

### Naming

| Element       | Convention           | Example              |
|---------------|----------------------|----------------------|
| Modules       | `snake_case`         | `pdf_parser.py`      |
| Classes       | `PascalCase`         | `PdfDocument`        |
| Functions     | `snake_case`         | `parse_page`         |
| Constants     | `UPPER_SNAKE_CASE`   | `STANDARD_ICON_SIZE` |
| Type aliases  | `PascalCase`         | `PageRenderer`       |
| Private       | `_leading_underscore`| `_cleanup_worker`    |

### Formatting

- Line length: 88 chars (ruff default).
- Double quotes for strings.
- Trailing commas in multi-line structures.
- f-strings over `.format()` or `%`.

### Docstrings

Google-style for public APIs. Skip for trivial private helpers.

```python
def render_page(self, index: int, zoom: float = 1.0) -> bytes:
    """Render a page and return raw PNG bytes.

    Args:
        index: Zero-based page index.
        zoom: Zoom factor for rendering.

    Returns:
        Raw PNG image bytes.
    """
```

### Error Handling

- Assign error message to `msg` variable, then raise:
  ```python
  msg = f"File not found: {path}"
  raise PdfLoadError(msg)
  ```
- Use `from exc` when re-raising: `raise PdfLoadError(msg) from exc`.
- Custom exceptions inherit from a project base (e.g., `PdfLoadError(Exception)`).
- Never silently swallow exceptions; use `contextlib.suppress()` only when intentional.

### PyQt6 Patterns

- Use `AppSignals` (central `QObject` with `pyqtSignal`) for inter-component communication.
- Keyboard shortcuts are managed by `KeyboardManager`, not set on `QAction` directly.
- Background work uses `QThread` with thread-safe `queue.Queue` (never busy-waiting).
- Use `__slots__` on data-heavy classes.
- Use `Protocol` for duck-typed interfaces, `ABC` for strict inheritance hierarchies.
- Use `dataclass` for plain data holders (e.g., `PageRenderTask`).

### Microkernel with pluggy

- `Kernel` owns the `pluggy.PluginManager` and dispatches hooks to registered plugins.
- Hook specifications live in `src/pdfreader_reborn/kernel/hooks.py` (use `@hookspec`).
- Plugins live in `src/pdfreader_reborn/plugins/`, implement hooks with `@hookimpl`.
- Plugins are registered in `main.py` via `kernel.register_plugin(plugin)`.
- To add a new toolbar button, create a plugin class, implement `provide_toolbar_buttons`, register it in `MainWindow._register_plugins`.

### General

- `pathlib.Path` over `os.path`.
- `logging` over `print` (except CLI entry points).
- `if __name__ == "__main__":` guard in `main.py`.
- Avoid global mutable state.

## Project Structure

```
pdfreader-reborn/
├── main.py                          # Entry point (MainWindow + main())
├── pyproject.toml                   # uv project config
├── src/
│   └── pdfreader_reborn/
│       ├── data/                    # Document model (PdfDocument, Page, FitzRenderer)
│       ├── kernel/                  # Microkernel (Kernel, hookspecs via pluggy)
│       ├── plugins/                 # Plugin implementations (OpenFilePlugin, ...)
│       └── ui/                      # Qt widgets (viewer, toolbar, signals, keyboard)
├── tests/
│   ├── conftest.py                  # Shared fixtures (sample_pdf, icons_dir)
│   ├── data/                        # Tests for data layer
│   └── ui/                          # Tests for UI layer
└── icons/                           # SVG/PNG toolbar icons
```

## Workflow

Write test → write module → run test → lint → finalize. Always run `uv run ruff check .` and `uv run ruff format .` before finishing.
