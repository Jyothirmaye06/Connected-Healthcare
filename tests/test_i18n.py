"""
Unit tests for multilingual internationalization (i18n) module.
"""

import pytest
from src.i18n import t, get_available_languages, TRANSLATIONS, AVAILABLE_LANGUAGES


def test_available_languages():
    langs = get_available_languages()
    assert "en" in langs
    assert "te" in langs
    assert "hi" in langs


def test_all_keys_have_translations():
    for key, lang_dict in TRANSLATIONS.items():
        assert "en" in lang_dict, f"Missing English for key: {key}"
        assert "te" in lang_dict, f"Missing Telugu for key: {key}"
        assert "hi" in lang_dict, f"Missing Hindi for key: {key}"
        assert len(lang_dict["en"].strip()) > 0
        assert len(lang_dict["te"].strip()) > 0
        assert len(lang_dict["hi"].strip()) > 0


def test_interpolation():
    msg_en = t("summary_normal", lang="en", hospital="Apollo", location="Chittoor", crowd=40, wait=50)
    assert "Apollo" in msg_en
    assert "40 people" in msg_en

    msg_te = t("summary_normal", lang="te", hospital="Apollo", location="Chittoor", crowd=40, wait=50)
    assert "Apollo" in msg_te
    assert "40" in msg_te

    msg_hi = t("summary_normal", lang="hi", hospital="Apollo", location="Chittoor", crowd=40, wait=50)
    assert "Apollo" in msg_hi
    assert "40" in msg_hi


def test_fallback():
    # Unknown key returns key
    assert t("completely_unknown_key", lang="en") == "completely_unknown_key"
    # Unknown lang falls back to English
    assert t("app_title", lang="fr") == TRANSLATIONS["app_title"]["en"]
