"""I18n helpers for pdfreader-reborn.

Usage::

    from pdfreader_reborn.strings import t, set_locale

    set_locale("es")
    print(t("menu.file"))          # → "Archivo"
    set_locale("en")
    print(t("menu.file"))          # → "File"
    print(t("viewer.page_loading", page=3))  # → "Page 3 — loading…"
"""

from pdfreader_reborn.strings.strings import STRINGS

_DEFAULT_LOCALE = "es"
_locale: str = _DEFAULT_LOCALE
_listeners: list = []


def t(key: str, **kwargs: object) -> str:
    """Translate a string key to the current locale.

    Args:
        key: The string identifier (e.g. ``"menu.file"``).
        **kwargs: Optional format parameters for the string.

    Returns:
        The translated string, or the key itself if not found.
    """
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_locale, entry.get(_DEFAULT_LOCALE, key))
    if kwargs:
        return text.format(**kwargs)
    return text


def set_locale(lang: str) -> None:
    """Set the active locale and notify listeners.

    Args:
        lang: Locale code (``"es"``, ``"en"``, …).
    """
    global _locale
    _locale = lang
    for fn in _listeners:
        fn()


def get_locale() -> str:
    """Return the currently active locale code."""
    return _locale


def on_locale_changed(fn) -> None:  # noqa: ANN001
    """Register a callback invoked whenever the locale changes.

    Args:
        fn: A zero-argument callable.
    """
    _listeners.append(fn)


def get_supported_locales() -> dict[str, str]:
    """Return a mapping of locale code to display name.

    Returns:
        Dict like ``{"es": "Español", "en": "English"}``.
    """
    result: dict[str, str] = {}
    entry = STRINGS.get("lang.es", {})
    for loc in entry:
        result[loc] = entry[loc]
    return result
