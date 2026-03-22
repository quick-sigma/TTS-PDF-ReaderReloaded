# PDF Reader Reborn

A modern, extensible PDF reader built with Python 3.13 and PyQt6.

## Features

- **PDF Viewing** — Continuous scroll with lazy page rendering
- **Zoom Controls** — Zoom in/out with toolbar buttons or keyboard
- **Keyboard Shortcuts** — Fast navigation without mouse
- **Extensible Architecture** — Plugin-ready microkernel design

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd pdfreader-reborn

# Install dependencies with uv
uv sync

# Run the application
uv run python main.py
```

## Usage

### Opening a PDF

```bash
# Open directly from command line
uv run python main.py document.pdf

# Or use the Open button / Ctrl+O shortcut
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file dialog |
| `Ctrl+=` | Zoom in |
| `Ctrl++` | Zoom in (alternative) |
| `Ctrl+-` | Zoom out |
| `Ctrl+W` | Close document |

### Toolbar

The navigation toolbar provides:
- **Open PDF** — Open file dialog
- **Zoom In** — Increase zoom by 25%
- **Zoom Out** — Decrease zoom by 25% (minimum 50%)

## Architecture

```
src/pdfreader_reborn/
├── data/
│   └── document.py      # Document adapter (ABC + PdfDocument)
├── ui/
│   ├── icon.py          # Icon system (SVG + PNG)
│   ├── button.py        # Toolbar elements (linked list)
│   ├── toolbar.py       # Toolbar abstraction
│   ├── viewer.py        # PDF viewer with lazy loading
│   ├── signals.py       # Application signals hub
│   └── keyboard.py      # Keyboard shortcut manager
└── logic/               # Business logic layer
```

### Signals

All UI actions are decoupled via signals:

```python
signals = AppSignals()
signals.zoom_in.connect(handler)
signals.zoom_out.connect(handler)
```

### Keyboard Manager

Keyboard shortcuts map to signals:

```python
km = KeyboardManager(signals)
# Ctrl+= → signals.zoom_in
# Ctrl+- → signals.zoom_out
```

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/ui/test_keyboard.py

# Run with verbose output
uv run pytest -v
```

## Development

### Commands

```bash
# Install dependencies
uv sync

# Run the app
uv run python main.py

# Run tests
uv run pytest

# Lint (if ruff is installed)
uv run ruff check .
uv run ruff format .
```

### Adding a New Keyboard Shortcut

1. Add signal to `ui/signals.py`
2. Bind key in `ui/keyboard.py`
3. Connect handler in `main.py`

## License

MIT
