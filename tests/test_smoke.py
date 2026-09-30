# -*- coding: utf-8 -*-
"""Pure-logic smoke tests for ShopVPN.

These run without aiogram/Telegram and are safe to run in CI on Ubuntu 22.04
(Python 3.10). They intentionally cover the modules that don't need a network
or a running bot, plus a regression test for the Esfand date bug.
"""
import datetime

import pytest

from jalali import gregorian_to_jalali, jalali_to_gregorian, to_jalali_str
import translation_quality as tq
import i18n


# --------------------------------------------------------------------------- #
# Jalali date conversion
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("g,expected", [
    ((2024, 2, 29), (1402, 12, 10)),   # regression: was 1402/12/346
    ((2024, 3, 19), (1402, 12, 29)),
    ((2024, 3, 20), (1403, 1, 1)),     # Nowruz 1403
    ((2026, 3, 20), (1404, 12, 29)),
    ((2026, 3, 21), (1405, 1, 1)),     # Nowruz 1405
    ((2026, 9, 30), (1405, 7, 8)),
    ((2000, 1, 1), (1378, 10, 11)),
])
def test_jalali_known_dates(g, expected):
    assert gregorian_to_jalali(*g) == expected


def test_jalali_roundtrip_every_day():
    """Every day from 1990 to 2040 must survive gregorian -> jalali -> gregorian."""
    d = datetime.date(1990, 1, 1)
    end = datetime.date(2040, 12, 31)
    day = datetime.timedelta(days=1)
    while d <= end:
        jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
        gy, gm, gd = jalali_to_gregorian(jy, jm, jd)
        assert (gy, gm, gd) == (d.year, d.month, d.day), d
        d += day


def test_jalali_month_is_always_valid():
    d = datetime.date(1990, 1, 1)
    end = datetime.date(2040, 12, 31)
    day = datetime.timedelta(days=1)
    while d <= end:
        jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
        assert 1 <= jm <= 12, (d, jm)
        assert 1 <= jd <= 31, (d, jd)
        d += day


def test_to_jalali_str_formats():
    assert to_jalali_str(datetime.date(2026, 9, 30)) == "1405/07/08"


# --------------------------------------------------------------------------- #
# Translation token protection
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("text", [
    "سلام {name} عزیز",
    "لینک: https://panel.example.com:2053/sub/ABC123xyz",
    "vless://uuid@host:443?type=tcp&security=tls#MyNode",
    "🛒 خرید کانفیگ",
    "مبلغ 150,000 تومان - کد: SHOP-9F3A",
    "config: 10.99.99.1:40001",
    "نه ۱۲۳ و %d و %s و $VAR",
    "Mixed English and فارسی together",
])
def test_translation_protect_restore_is_lossless(text):
    protected, mapping = tq.protect(text)
    assert tq.restore(protected, mapping) == text


def test_structural_tokens_detects_urls_and_placeholders():
    assert "https://x.io/p" in tq.structural_tokens("a https://x.io/p b")
    assert "{name}" in tq.structural_tokens("{name}")


def test_validate_rules():
    assert tq.validate("سلام دنیا", "سلام دنیا", "fa")[0] is True
    ok, reason = tq.validate("سلام دنیا", "", "fa")
    assert ok is False and reason == "empty_translation"
    ok, reason = tq.validate("لینک https://a.io/x", "لینک", "fa")
    assert ok is False and reason == "structural_token_mismatch"


# --------------------------------------------------------------------------- #
# i18n helpers
# --------------------------------------------------------------------------- #
def test_language_catalog_has_core_languages():
    for code in ("fa", "en", "tr", "ar"):
        assert code in i18n.LANGUAGE_CATALOG


@pytest.mark.parametrize("raw,expected", [
    ("fa", "fa"), ("fa-IR", "fa"), ("Persian", "fa"), ("prs", "fa"),
    ("en", "en"), ("en-US", "en"),
    ("tr", "tr"), ("ar", "ar"),
    ("", "fa"), (None, "fa"), ("!!", "fa"),
])
def test_normalize_language(raw, expected):
    assert i18n.normalize_language(raw) == expected


class _FakeDb:
    def __init__(self, rows):
        self._rows = rows

    def get_language(self, code):
        return self._rows.get(code)


class _BoomDb:
    def get_language(self, code):
        raise RuntimeError("db unavailable")


def test_is_language_enabled():
    db = _FakeDb({"fa": {"enabled": 1}, "en": {"enabled": 1}, "tr": {"enabled": 0}})
    assert i18n.is_language_enabled(db, "fa") is True
    assert i18n.is_language_enabled(db, "en") is True
    assert i18n.is_language_enabled(db, "tr") is False
    # A missing row means the language was never enabled.
    assert i18n.is_language_enabled(_FakeDb({}), "en") is False
    # If the DB itself fails, only the always-available core set is allowed.
    assert i18n.is_language_enabled(_BoomDb(), "en") is True
    assert i18n.is_language_enabled(_BoomDb(), "tr") is False
