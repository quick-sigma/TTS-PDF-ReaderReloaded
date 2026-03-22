"""All user-facing strings, keyed by string ID.

Each key maps to a dict of locale → translated text.  The default
locale is ``"es"`` (Spanish).  New locales are added by simply
extending every inner dict.
"""

STRINGS: dict[str, dict[str, str]] = {
    # ── Window ───────────────────────────────────────────────
    "app.title": {
        "es": "PDF Reader Reborn",
        "en": "PDF Reader Reborn",
    },
    # ── Menu bar ─────────────────────────────────────────────
    "menu.file": {
        "es": "Archivo",
        "en": "File",
    },
    "menu.file.open": {
        "es": "Abrir archivo…",
        "en": "Open file…",
    },
    "menu.file.close": {
        "es": "Cerrar",
        "en": "Close",
    },
    "menu.file.exit": {
        "es": "Salir",
        "en": "Exit",
    },
    "menu.view": {
        "es": "Vista",
        "en": "View",
    },
    "menu.view.zoom_in": {
        "es": "Acercar",
        "en": "Zoom in",
    },
    "menu.view.zoom_out": {
        "es": "Alejar",
        "en": "Zoom out",
    },
    "menu.settings": {
        "es": "Ajustes",
        "en": "Settings",
    },
    "menu.settings.language": {
        "es": "Idioma",
        "en": "Language",
    },
    "lang.es": {
        "es": "Español",
        "en": "Spanish",
    },
    "lang.en": {
        "es": "Inglés",
        "en": "English",
    },
    # ── Toolbar ──────────────────────────────────────────────
    "toolbar.open.label": {
        "es": "Abrir PDF",
        "en": "Open PDF",
    },
    "toolbar.open.tooltip": {
        "es": "Abrir archivo PDF (Ctrl+O)",
        "en": "Open PDF file (Ctrl+O)",
    },
    "toolbar.zoom_in.label": {
        "es": "Acercar",
        "en": "Zoom In",
    },
    "toolbar.zoom_in.tooltip": {
        "es": "Acercar (Ctrl+=)",
        "en": "Zoom in (Ctrl+=)",
    },
    "toolbar.zoom_out.label": {
        "es": "Alejar",
        "en": "Zoom Out",
    },
    "toolbar.zoom_out.tooltip": {
        "es": "Alejar (Ctrl+-)",
        "en": "Zoom out (Ctrl+-)",
    },
    "toolbar.navigation.name": {
        "es": "Navegación",
        "en": "Navigation",
    },
    # ── File dialog ──────────────────────────────────────────
    "dialog.open.title": {
        "es": "Abrir PDF",
        "en": "Open PDF",
    },
    "dialog.open.filter": {
        "es": "Archivos PDF (*.pdf);;Todos los archivos (*)",
        "en": "PDF Files (*.pdf);;All Files (*)",
    },
    # ── Viewer ───────────────────────────────────────────────
    "viewer.page_loading": {
        "es": "Página {page} — cargando…",
        "en": "Page {page} — loading…",
    },
}
