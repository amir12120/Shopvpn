# -*- coding: utf-8 -*-
"""Practical, dependency-free checks for more ShopVPN modules.

These extend tests/test_smoke.py so regressions in the shared helpers (text
escaping, DB text policy, the bot-text scanner and i18n runtime) are caught by
CI before they reach a server. Everything here runs without aiogram/FastAPI.
"""
import importlib

import pytest

import md_utils
import db_text_policy as dtp
import text_scanner
import settings_schema
import i18n


PURE_MODULES = [
    "jalali",
    "md_utils",
    "translation_quality",
    "db_text_policy",
    "text_scanner",
    "settings_schema",
    "i18n",
]


@pytest.mark.parametrize("name", PURE_MODULES)
def test_dependency_free_modules_import(name):
    assert importlib.import_module(name) is not None


# --------------------------------------------------------------------------- #
# md_utils: escaping that prevents Telegram entity parse errors
# --------------------------------------------------------------------------- #
def test_escape_html():
    assert md_utils.escape_html("<b>& 'x'</b>") == "&lt;b&gt;&amp; 'x'&lt;/b&gt;"
    assert md_utils.escape_html(None) == ""
    assert md_utils.escape_html(123) == "123"


@pytest.mark.parametrize("raw,expected", [
    ("a_b", r"a\_b"),
    ("a*b", r"a\*b"),
    ("a`b", r"a\`b"),
    ("a[b", r"a\[b"),
    (r"a\b", r"a\\b"),
    ("plain", "plain"),
])
def test_escape_md_escapes_special_chars(raw, expected):
    assert md_utils.escape_md(raw) == expected


def test_escape_md_none():
    assert md_utils.escape_md(None) == ""


# --------------------------------------------------------------------------- #
# db_text_policy: only system text is ever localized
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("table,column,kind", [
    ("products", "name", dtp.TextStorageKind.CUSTOM),
    ("products", "description", dtp.TextStorageKind.CUSTOM),
    ("users", "username", dtp.TextStorageKind.CUSTOM),
    ("bot_text_registry", "default_text", dtp.TextStorageKind.SYSTEM),
    ("products", "price", dtp.TextStorageKind.NEUTRAL),
])
def test_classify_text_field(table, column, kind):
    assert dtp.classify_text_field(table, column) is kind


def test_classify_setting():
    assert dtp.classify_setting("store_name") is dtp.TextStorageKind.CUSTOM
    assert dtp.classify_setting("msgtext__greeting") is dtp.TextStorageKind.SYSTEM
    assert dtp.classify_setting("panel_api_url") is dtp.TextStorageKind.NEUTRAL


def test_custom_db_text_is_never_translated():
    # Custom text must survive verbatim even for a non-Persian language.
    assert dtp.render_db_text("products", "name", "لینک <x> & y", "en") == "لینک <x> & y"
    assert dtp.render_custom_content(1234) == "1234"
    assert dtp.render_stored_setting("store_name", "My Shop", "en") == "My Shop"


def test_is_custom_text_field():
    assert dtp.is_custom_text_field("products", "name") is True
    assert dtp.is_custom_text_field("products", "price") is False


# --------------------------------------------------------------------------- #
# text_scanner: finds db.get_text(key, default) literals
# --------------------------------------------------------------------------- #
def test_scan_bot_texts(tmp_path):
    (tmp_path / "sample_module.py").write_text(
        'db.get_text("greeting", "سلام {name}")\n'
        'x = db.get_text("farewell", "خداحافظ")\n'
        'bad = f"nope {1}"\n'  # non-literal default must be ignored
        'db.get_text("greeting", "سلام دوباره")\n',  # duplicate key -> last wins
        encoding="utf-8",
    )
    found = {row["key"]: row for row in text_scanner.scan_bot_texts(str(tmp_path))}
    assert set(found) == {"greeting", "farewell"}
    assert found["greeting"]["default_text"] == "سلام دوباره"
    assert found["greeting"]["category"] == "sample_module"


def test_scan_bot_texts_missing_dir_is_empty(tmp_path):
    assert text_scanner.scan_bot_texts(str(tmp_path / "does-not-exist")) == []


# --------------------------------------------------------------------------- #
# i18n runtime
# --------------------------------------------------------------------------- #
def test_tr_persian_is_passthrough():
    assert i18n.tr("🛒 خرید کانفیگ", "fa") == "🛒 خرید کانفیگ"


def test_tr_english_uses_catalog():
    assert i18n.tr("🛒 خرید کانفیگ", "en") == "🛒 Buy configuration"


def test_language_context_roundtrip():
    token = i18n.set_language("en")
    try:
        assert i18n.get_language() == "en"
    finally:
        i18n.reset_language(token)
    assert i18n.get_language() == i18n.DEFAULT_LANGUAGE


def test_settings_schema_api_present():
    assert callable(settings_schema.sales_settings_cards)
