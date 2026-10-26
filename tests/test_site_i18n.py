from src.site_i18n import SITE_TRANSLATIONS, site_t, translate_guidance


def test_site_translations_cover_all_languages():
    for key, translations in SITE_TRANSLATIONS.items():
        assert len(translations) == 3, key
        assert all(value.strip() for value in translations), key
        assert site_t(key, "en") == translations[0]
        assert site_t(key, "te") == translations[1]
        assert site_t(key, "hi") == translations[2]


def test_guidance_translation_only_applies_to_known_seeded_copy():
    known = "High body temperature, chills, weakness or body aches"
    assert translate_guidance("Fever", "symptoms", known, "te") != known
    changed = "Changed source copy"
    assert translate_guidance("Fever", "symptoms", changed, "te") == changed
