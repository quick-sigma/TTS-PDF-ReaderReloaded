# AGENTS.md - Coding Agent Instructions

## Project Overview

pdfreader-reborn is a Python 3.13 project managed with [uv](https://docs.astral.sh/uv/).
The project is in early stages. Follow the conventions below to maintain consistency.

## Build & Run Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py

# Run a module or script
uv run python -m <module_name>
```

## Testing

Test framework: **pytest** (add to deps when tests are written).

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_foo.py

# Run a single test by name
uv run pytest tests/test_foo.py::test_specific_thing

# Run with verbose output
uv run pytest -v

# Run with coverage (requires pytest-cov)
uv run pytest --cov
```

Place all tests in a `tests/` directory at the project root. Test files must be named `test_*.py`.

## Linting & Formatting

Use **ruff** for both linting and formatting (add as a dev dependency first):

```bash
# Add ruff as a dev dependency
uv add --dev ruff

# Lint and auto-fix
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type checking (if using mypy or pyright)
uv add --dev mypy
uv run mypy .
```

Always run `uv run ruff check .` and `uv run ruff format .` before finalizing changes.

## Type Checking

Use type hints everywhere. Python 3.13 supports modern syntax:

```python
# Use built-in generics (lowercase)
def process(items: list[str]) -> dict[str, int]: ...

# Use X | Y union syntax (not Optional or Union)
def maybe_get(key: str) -> str | None: ...
```

## Code Style Guidelines

### Imports
- Group imports: stdlib, then third-party, then local (one blank line between groups).
- Use absolute imports; avoid `from x import *`.
- Sort imports alphabetically within each group (ruff enforces this with `I` rules).

```python
import sys
from pathlib import Path

from some_library import Thing

from pdfreader_reborn.core import parser
```

### Naming Conventions
| Element       | Convention           | Example              |
|---------------|----------------------|----------------------|
| Modules       | `snake_case`         | `pdf_parser.py`      |
| Classes       | `PascalCase`         | `PdfDocument`        |
| Functions     | `snake_case`         | `parse_page`         |
| Constants     | `UPPER_SNAKE_CASE`   | `MAX_RETRIES`        |
| Type aliases  | `PascalCase`         | `PageContent`        |
| Private       | `_leading_underscore`| `_internal_helper`   |

### Formatting
- Line length: **88 characters** (ruff default).
- Use double quotes for strings (ruff default).
- Use trailing commas in multi-line structures.
- Prefer f-strings over `.format()` or `%` formatting.

### Functions & Classes
- Keep functions small and single-purpose.
- Use `dataclass` or `TypedDict` for structured data.
- Prefer composition over deep inheritance.
- Use `@override` decorator when overriding methods (Python 3.12+).

### Error Handling
- Raise specific exceptions; avoid bare `except:`.
- Use custom exception classes inheriting from a project base when appropriate.
- Log errors with context; don't silently swallow exceptions.
- Use `contextlib.suppress()` for intentional exception suppression.

### Docstrings
- Use Google-style docstrings for public APIs.
- Skip docstrings for trivial private helpers where the name is self-explanatory.

```python
def extract_text(page: Page, *, preserve_layout: bool = False) -> str:
    """Extract text content from a PDF page.

    Args:
        page: The PDF page to process.
        preserve_layout: If True, maintain whitespace structure.

    Returns:
        The extracted text as a string.
    """
```

### General Best Practices
- Use `pathlib.Path` over `os.path` for file paths.
- Prefer `logging` over `print` for non-CLI output.
- Use `if __name__ == "__main__":` guard in executable scripts.
- Avoid global mutable state.

## Project Structure (Target)

```
pdfreader-reborn/
├── pyproject.toml
├── main.py
├── src/
│   └── pdfreader_reborn/
│       ├── __init__.py
│       └── ...
├── tests/
│   ├── __init__.py
│   └── ...
└── AGENTS.md
```

If the project uses a `src/` layout, configure it in `pyproject.toml` with:
```toml
[tool.uv]
package = true

[tool.setuptools.packages.find]
where = ["src"]
```

### Environmet

To manage packages use uv.
Actual installed packages:
- PyQT6
- EdgeTTS
- pytest

# Brief: PDF Reader with Edge-TTS, PyQt6, and Microkernel Architecture

Here's the full brief for your agent:

---

```markdown
# PROJECT BRIEF: AdaptivePDF Reader

## 1. Overview

**AdaptivePDF** is a powerful, extensible PDF reader built with PyQt6 and Python,
designed around a microkernel architecture. The core is a minimal PDF rendering
engine; every other feature — text-to-speech (edge-tts), annotation tools,
plugin management, multi-toolbar UI — is a pluggable component loaded through
the microkernel. The goal is a reader that can transform into different tools
for different users (researchers, students, legal professionals, developers, etc.).

## 2. Technology Stack

- **Language**: Python 3.11+
- **UI Framework**: PyQt6 (QMainWindow, QDockWidget, QToolBar, QTabWidget)
- **PDF Engine**: PyMuPDF (fitz) for rendering, text extraction, and manipulation
- **Text-to-Speech**: edge-tts (Microsoft Edge TTS, async, multi-language)
- **Plugin System**: importlib + abstract base class registry
- **Architecture**: Microkernel pattern
- **Async**: asyncio integrated into Qt event loop via qasync

## 3. Microkernel Architecture

```
┌─────────────────────────────────────────────────────┐
│                   MICROKERNEL CORE                   │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ PDF Engine  │  │ Plugin       │  │ Event Bus  │  │
│  │ (PyMuPDF)   │  │ Loader/Reg.  │  │ (Signals)  │  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │           Component Interface (ABC)             │ │
│  │  - init(kernel)                                 │ │
│  │  - get_toolbar() -> QToolBar | None             │ │
│  │  - get_dock_widget() -> QDockWidget | None      │ │
│  │  - get_menu_entries() -> list[QAction]          │ │
│  │  - on_document_loaded(document)                 │ │
│  │  - on_page_changed(page_number)                 │ │
│  │  - shutdown()                                   │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────┼────────────────┐
          ▼            ▼                ▼
   ┌────────────┐ ┌──────────┐  ┌──────────────┐
   │ TTS Plugin │ │ Annotate │  │  Bookmark    │
   │ (edge-tts) │ │ Plugin   │  │  Plugin      │
   └────────────┘ └──────────┘  └──────────────┘
          ▼            ▼                ▼
   ┌────────────┐ ┌──────────┐  ┌──────────────┐
   │ Search     │ │ Export   │  │  User Profile│
   │ Plugin     │ │ Plugin   │  │  Plugin      │
   └────────────┘ └──────────┘  └──────────────┘
          ▼            ▼                ▼
   ┌────────────┐ ┌──────────┐  ┌──────────────┐
   │ OCR Plugin │ │ Compare  │  │  Custom...   │
   │ (optional) │ │ Plugin   │  │  (3rd party) │
   └────────────┘ └──────────┘  └──────────────┘
```

### 3.1 Kernel Responsibilities

The kernel handles ONLY:
- PDF document lifecycle (open, close, page navigation, zoom, rotate)
- Plugin discovery, loading, dependency resolution, lifecycle management
- Inter-component event bus (document_loaded, page_changed, selection_changed,
  annotation_added, tts_state_changed, etc.)
- MainWindow construction (dock areas, toolbar slots, menu bar assembly)
- Settings persistence (QSettings or JSON-based config)

### 3.2 Plugin Contract

Every plugin implements:

```python
class PluginInterface(ABC):
    name: str
    version: str
    description: str
    dependencies: list[str]  # other plugin names

    @abstractmethod
    def init(self, kernel: "MicroKernel") -> None: ...

    @abstractmethod
    def get_toolbar(self) -> QToolBar | None: ...

    @abstractmethod
    def get_dock_widgets(self) -> list[QDockWidget]: ...

    @abstractmethod
    def get_menu_actions(self) -> list[QAction]: ...

    @abstractmethod
    def on_event(self, event: str, data: dict) -> None: ...

    @abstractmethod
    def shutdown(self) -> None: ...
```

### 3.3 Plugin Discovery

Plugins are loaded from:
1. `plugins/builtins/` — shipped with the app
2. `plugins/community/` — user-installed
3. `~/.adaptivepdf/plugins/` — external

Each plugin folder contains:
```
plugin.json          # metadata, dependencies, entry point
__init__.py          # exports Plugin class
```

## 4. Interface Design — Multi-Toolbar Okular-Style Layout

### 4.1 Schematic Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  MENU BAR                                                                  ║
║  [File] [Edit] [View] [Tools] [Plugins] [Profiles] [Window] [Help]        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  TOOLBAR 1: Navigation                                                     ║
║  [◀ Pg] [Pg ▶] [Pg: ▼ 12 / 340 ▼]  [🔍-] [100% ▼] [🔍+]  [◰ Fit]      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  TOOLBAR 2: TTS Controls (Plugin)                                         ║
║  [▶ Read] [⏸ Pause] [⏹ Stop]  [🔊 ━━━●━━━]  Speed: [1.0x ▼]            ║
║  Voice: [en-US-AriaNeural ▼]  Lang: [Auto ▼]  [📖 Read Selection Only]   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  TOOLBAR 3: Annotation Tools (Plugin)                                     ║
║  [✎ Highlight] [🖍 Underline] [⊞ Stamp] [📝 Note] [📏 Measure]           ║
║  Color: [🟡🟢🔵🔴]  Opacity: [━━●━━]  [🗑 Delete] [↩ Undo]              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────┐  ┌──────────────────────────────────────┐  ┌──────────────┐  ║
║  │ SIDEBAR  │  │                                      │  │  RIGHT PANEL │  ║
║  │ (Dock)   │  │          PDF PAGE VIEWPORT           │  │  (Dock)      │  ║
║  │          │  │                                      │  │              │  ║
║  │ [📑 Pg]  │  │   ┌──────────────────────────────┐   │  │ [📋 Meta]    │  ║
║  │ Thumbnails│  │   │                              │   │  │  Title: ...  │  ║
║  │          │  │   │    Rendered PDF page with     │   │  │  Author: ... │  ║
║  │ ┌──────┐ │  │   │    zoom, pan, annotations    │   │  │  Pages: 340  │  ║
║  │ │ pg 1 │ │  │   │    overlaid                  │   │  │              │  ║
║  │ │ pg 2 │ │  │   │                              │   │  │ [🔍 Search]  │  ║
║  │ │ pg 3 │ │  │   │    Highlighted text with     │   │  │  results...  │  ║
║  │ │  ... │ │  │   │    TTS cursor tracking       │   │  │              │  ║
║  │ └──────┘ │  │   │                              │   │  │ [🔖 Bookmarks│  ║
║  │          │  │   └──────────────────────────────┘   │  │              │  ║
║  │ [🌳 TOC] │  │                                      │  │ [📝 Notes]   │  ║
║  │ Ch. 1    │  │  STATUS BAR                          │  │  list...     │  ║
║  │  § 1.1   │  │  [Page 12/340] [Zoom: 125%] [TTS:   │  │              │  ║
║  │  § 1.2   │  │  Reading...] [Annotations: 47]       │  │ [📊 Stats]   │  ║
║  │ Ch. 2    │  │                                      │  │  word count  │  ║
║  │  § 2.1   │  └──────────────────────────────────────┘  │  reading     │  ║
║  │          │                                             │  time est.   │  ║
║  └──────────┘                                             └──────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 4.2 Toolbar Docking Behavior

All toolbars are QToolBar instances with these properties:
- `setMovable(True)` — user can drag and rearrange
- `setFloatable(True)` — toolbars can float as independent windows
- Each toolbar belongs to a plugin; if plugin is unloaded, toolbar disappears
- Toolbars can be toggled via `View > Toolbars` menu
- Layout state saved/restored via `QMainWindow.saveState()` / `restoreState()`

### 4.3 Dock Widget Zones

| Zone        | Widgets                                              |
|-------------|------------------------------------------------------|
| Left Dock   | Page thumbnails, Table of Contents, Bookmarks tree   |
| Right Dock  | Metadata panel, Search results, Annotations list,    |
|             | Reading statistics, Plugin-specific panels            |
| Bottom Dock | TTS transcript/progress, Log console (dev mode)      |

Docks are tabbed (QTabWidget inside QDockWidget) so multiple panels
share the same zone. Users can undock, resize, and rearrange.

## 5. Core Features (Built-in Plugins)

### 5.1 PDF Engine (Kernel — not a plugin)

- Open / Save / Save As / Print
- Page navigation: first, prev, next, last, go-to-page
- Zoom: in, out, fit-width, fit-page, custom percentage
- Rotation: 0°, 90°, 180°, 270°
- Text selection and copy to clipboard
- Render to QImage via PyMuPDF → QPainter pipeline
- Continuous scroll mode and single-page mode
- Dark mode rendering (invert + tint)

### 5.2 TTS Plugin (edge-tts)

- Async TTS via edge-tts with qasync bridge
- Voice selection from all available edge-tts voices (filtered by language)
- Adjustable speed (0.5x – 3.0x), pitch, volume
- Sentence-level highlighting: tracks current sentence in viewport
- "Read selection" mode: reads only user-selected text
- "Read from page" mode: starts reading from current page
- Keyboard shortcuts: Play/Pause (F5), Stop (F6)
- Export audio to MP3 file (edge-tts supports this natively)

### 5.3 Annotation Plugin

- Highlight, underline, strikethrough, squiggly annotation tools
- Freehand drawing (ink annotations)
- Text notes (sticky notes anchored to position)
- Shape stamps (rectangle, circle, arrow, line)
- Color picker, opacity slider, line width control
- Annotations stored in PDF (standard PDF annotation objects)
- Annotation list panel with page jump on click

### 5.4 Search Plugin

- Full-text search across all pages
- Search with regex option
- Results highlighted in viewport with yellow markers
- Result list in right dock with page/context preview
- Find and replace (for editable text layers)

### 5.5 Bookmark Plugin

- Add/remove bookmarks to any page with custom names
- Bookmark tree organized by user-defined groups
- Import/export bookmarks as JSON

### 5.6 User Profile Plugin

- Profiles: "Student", "Researcher", "Legal", "Developer", "Accessibility"
- Each profile pre-configures which toolbars/docks are visible
- Profile saves: toolbar layout, default zoom, TTS settings, theme
- One-click profile switching from toolbar or menu

## 6. User Profiles — Transform the Reader

| Profile        | Active Toolbars          | Active Docks             | Theme   |
|----------------|--------------------------|--------------------------|---------|
| Student        | Nav + TTS + Annotations  | Thumbnails + Notes       | Light   |
| Researcher     | Nav + Search + Annotations| TOC + Search + Stats     | Dark    |
| Legal          | Nav + Annotations + Export| Thumbnails + Annotations | Neutral |
| Developer      | Nav + Search             | TOC + Log Console        | Dark    |
| Accessibility  | Nav + TTS (large icons)  | None (max viewport)      | High contrast |

## 7. Plugin Example — Full TTS Plugin Skeleton

```python
# plugins/builtins/tts_plugin/__init__.py

from PyQt6.QtWidgets import QToolBar, QDockWidget, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import edge_tts
import asyncio
from abc import ABC

class PluginInterface(ABC):
    name: str
    version: str
    description: str
    dependencies: list[str]
    def init(self, kernel): ...
    def get_toolbar(self) -> QToolBar | None: ...
    def get_dock_widgets(self) -> list[QDockWidget]: ...
    def get_menu_actions(self) -> list[QAction]: ...
    def on_event(self, event: str, data: dict): ...
    def shutdown(self): ...

class TTSPlugin(PluginInterface):
    name = "Text-to-Speech"
    version = "1.0.0"
    description = "Edge-TTS integration for reading PDFs aloud"
    dependencies = []

    def init(self, kernel):
        self.kernel = kernel
        self.current_voice = "en-US-AriaNeural"
        self.rate = "+0%"
        self._build_toolbar()
        self.kernel.event_bus.connect("selection_changed", self._on_selection)

    def _build_toolbar(self):
        self.toolbar = QToolBar("TTS Controls")
        self.toolbar.setObjectName("tts_toolbar")

        self.act_play = QAction("▶ Read", self.toolbar)
        self.act_play.triggered.connect(self._start_reading)
        self.act_pause = QAction("⏸ Pause", self.toolbar)
        self.act_stop = QAction("⏹ Stop", self.toolbar)
        self.act_stop.triggered.connect(self._stop_reading)

        self.toolbar.addAction(self.act_play)
        self.toolbar.addAction(self.act_pause)
        self.toolbar.addAction(self.act_stop)
        # ... voice selector combo, speed slider, etc.

    def get_toolbar(self):
        return self.toolbar

    def get_dock_widgets(self):
        return []  # Could add a transcript panel

    def get_menu_actions(self):
        return [self.act_play, self.act_pause, self.act_stop]

    def _on_selection(self, data):
        self.selected_text = data.get("text", "")

    async def _speak(self, text):
        communicate = edge_tts.Communicate(text, self.current_voice, rate=self.rate)
        # Stream audio via QMediaPlayer or pygame
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                self._play_audio_chunk(chunk["data"])

    def _start_reading(self):
        text = self.selected_text or self.kernel.get_page_text()
        asyncio.ensure_future(self._speak(text))

    def _stop_reading(self):
        self._cancel_speech = True

    def on_event(self, event, data):
        if event == "document_loaded":
            self.act_play.setEnabled(True)

    def shutdown(self):
        self._stop_reading()
```

## 8. Event Bus Design

```python
# kernel/event_bus.py

from PyQt6.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    """
    Central event bus. Plugins subscribe to events.
    Events are string-keyed. Data is always a dict.
    """
    _signals: dict[str, pyqtSignal] = {}

    def register(self, event_name: str):
        if event_name not in self._signals:
            self._signals[event_name] = pyqtSignal(dict)

    def emit(self, event_name: str, data: dict):
        if event_name in self._signals:
            self._signals[event_name].emit(data)

    def connect(self, event_name: str, callback):
        self.register(event_name)
        self._signals[event_name].connect(callback)

    def disconnect(self, event_name: str, callback):
        if event_name in self._signals:
            self._signals[event_name].disconnect(callback)
```

Standard events:
- `document_loaded` — {path, page_count, metadata}
- `document_closed` — {}
- `page_changed` — {page_number}
- `zoom_changed` — {zoom_factor}
- `selection_changed` — {text, rect}
- `annotation_added` — {type, page, data}
- `tts_started` — {page, voice}
- `tts_sentence` — {sentence_index, text, rect}
- `tts_finished` — {}
- `search_results` — {query, results: [{page, rect, context}]}
- `plugin_loaded` — {name, version}
- `plugin_unloaded` — {name}

## 9. Main Window Skeleton

```python
# kernel/main_window.py

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AdaptivePDF Reader")
        self.resize(1400, 900)

        self.kernel = MicroKernel(self)
        self._setup_dock_areas()
        self._load_plugins()
        self._restore_layout()

    def _setup_dock_areas(self):
        # Left dock — tabbed: Thumbnails | TOC | Bookmarks
        self.left_dock = QDockWidget("Navigation", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.left_tabs = QTabWidget()
        self.left_dock.setWidget(self.left_tabs)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # Right dock — tabbed: Meta | Search | Notes | Stats
        self.right_dock = QDockWidget("Panels", self)
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.right_tabs = QTabWidget()
        self.right_dock.setWidget(self.right_tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

        # Central viewport
        self.pdf_view = PDFViewport(self.kernel)
        self.setCentralWidget(self.pdf_view)

    def _load_plugins(self):
        for plugin in self.kernel.plugin_loader.load_all():
            toolbar = plugin.get_toolbar()
            if toolbar:
                self.addToolBar(toolbar)
            for dock in plugin.get_dock_widgets():
                self._register_dock(dock)
```

## 10. File Structure

```
adaptivepdf/
├── main.py                          # Entry point
├── kernel/
│   ├── __init__.py
│   ├── microkernel.py               # Core orchestrator
│   ├── main_window.py               # QMainWindow setup
│   ├── pdf_engine.py                # PyMuPDF wrapper
│   ├── viewport.py                  # Central PDF rendering widget
│   ├── event_bus.py                 # Inter-plugin communication
│   ├── plugin_loader.py             # Discovery, loading, lifecycle
│   ├── plugin_interface.py          # ABC for all plugins
│   ├── settings_manager.py          # QSettings wrapper
│   └── profile_manager.py           # User profile save/restore
├── plugins/
│   └── builtins/
│       ├── tts_plugin/
│       │   ├── __init__.py
│       │   ├── plugin.json
│       │   ├── tts_engine.py        # edge-tts async wrapper
│       │   ├── voice_selector.py    # Voice picker widget
│       │   └── toolbar.py           # TTS toolbar widget
│       ├── annotation_plugin/
│       │   ├── __init__.py
│       │   ├── plugin.json
│       │   ├── tools.py             # Highlight, note, draw tools
│       │   └── toolbar.py
│       ├── search_plugin/
│       │   ├── __init__.py
│       │   ├── plugin.json
│       │   ├── search_engine.py
│       │   └── results_panel.py
│       ├── bookmark_plugin/
│       │   ├── __init__.py
│       │   ├── plugin.json
│       │   └── bookmark_tree.py
│       ├── profile_plugin/
│       │   ├── __init__.py
│       │   ├── plugin.json
│       │   └── profiles/
│       │       ├── student.json
│       │       ├── researcher.json
│       │       ├── legal.json
│       │       ├── developer.json
│       │       └── accessibility.json
│       └── export_plugin/
│           ├── __init__.py
│           ├── plugin.json
│           └── export_dialog.py
├── resources/
│   ├── icons/
│   ├── themes/
│   │   ├── light.qss
│   │   ├── dark.qss
│   │   └── high_contrast.qss
│   └── fonts/
├── tests/
├── requirements.txt
└── README.md
```

## 11. Requirements

```
# requirements.txt
PyQt6>=6.6.0
PyMuPDF>=1.24.0
edge-tts>=6.1.0
qasync>=0.27.0
```

## 12. Implementation Priority

| Phase | Features                                              |
|-------|-------------------------------------------------------|
| 1     | Kernel + PDF engine + viewport + basic navigation     |
| 2     | Plugin loader + event bus + toolbar/dock integration  |
| 3     | TTS plugin (edge-tts) with sentence highlighting      |
| 4     | Annotation plugin (highlights, notes, shapes)         |
| 5     | Search plugin (full-text + regex)                     |
| 6     | Bookmark plugin + User profile plugin                 |
| 7     | Export plugin (annotations to PDF, TTS to MP3)        |
| 8     | Theme system + accessibility profile                  |
| 9     | Plugin marketplace / community plugin loading         |
| 10    | Polish, testing, packaging (PyInstaller)              |

## 13. Key Design Decisions

1. **PyMuPDF over pdf.js**: Native Python, no web engine overhead,
   direct QImage rendering, full annotation support in the PDF spec.

2. **edge-tts over pyttsx3**: Higher quality neural voices, 300+ voices
   in 40+ languages, no local voice engine installation needed.

3. **Microkernel over monolith**: Every feature can be disabled without
   breaking the core. Third-party plugins can add capabilities the
   original team never imagined.

4. **QMainWindow dock system over custom layout**: Native OS integration,
   saved layouts, multi-monitor support, accessible by default.

5. **Profiles over preferences**: Instead of 50 settings, users pick
   a profile and get a pre-configured experience. Power users can
   customize profiles in JSON.
```

---

The brief is ready to feed to your agent. The ASCII schematic gives a clear visual of the multi-toolbar layout with left/right docks and the central viewport. The microkernel contract, event bus, plugin skeleton, and file structure are all specified so your agent has a concrete blueprint to implement against.


## Workflow

- Write a test
- Write the module
- Test the module