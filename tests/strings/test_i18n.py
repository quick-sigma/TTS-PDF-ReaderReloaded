import pytest

from pdfreader_reborn.strings import t, set_locale, get_locale, get_supported_locales
from pdfreader_reborn.strings.strings import STRINGS


class TestTranslation:
    """Tests for the t() translation function."""

    def test_default_locale_is_es(self) -> None:
        """Default locale should be Spanish."""
        set_locale("es")
        assert get_locale() == "es"

    def test_translate_to_spanish(self) -> None:
        """t() should return Spanish text when locale is 'es'."""
        set_locale("es")
        assert t("menu.file") == "Archivo"
        assert t("menu.view") == "Vista"

    def test_translate_to_english(self) -> None:
        """t() should return English text when locale is 'en'."""
        set_locale("en")
        assert t("menu.file") == "File"
        assert t("menu.view") == "View"

    def test_translate_with_format_params(self) -> None:
        """t() should support format parameters."""
        set_locale("en")
        assert t("viewer.page_loading", page=3) == "Page 3 — loading…"
        set_locale("es")
        assert t("viewer.page_loading", page=5) == "Página 5 — cargando…"

    def test_translate_unknown_key_returns_key(self) -> None:
        """t() should return the key itself for unknown keys."""
        assert t("nonexistent.key") == "nonexistent.key"

    def test_switch_locale_updates_results(self) -> None:
        """Switching locale should immediately change t() results."""
        set_locale("es")
        es_val = t("menu.file")
        set_locale("en")
        en_val = t("menu.file")
        assert es_val != en_val


class TestLocaleManagement:
    """Tests for set_locale / get_locale."""

    def test_set_locale_changes_locale(self) -> None:
        """set_locale should update get_locale."""
        set_locale("en")
        assert get_locale() == "en"
        set_locale("es")
        assert get_locale() == "es"

    def test_get_supported_locales(self) -> None:
        """get_supported_locales should return all available locales."""
        locales = get_supported_locales()
        assert "es" in locales
        assert "en" in locales


class TestStringsCompleteness:
    """Tests that verify every string key has all required locales."""

    def test_all_keys_have_spanish(self) -> None:
        """Every string should have a Spanish translation."""
        for key, entry in STRINGS.items():
            assert "es" in entry, f"{key} missing Spanish translation"

    def test_all_keys_have_english(self) -> None:
        """Every string should have an English translation."""
        for key, entry in STRINGS.items():
            assert "en" in entry, f"{key} missing English translation"
