# -*- coding: utf-8 -*-
"""The admin-panel switch that turns the whole reseller section on or off.

The state/text logic lives in ``reseller_section.py``, which deliberately has
no aiogram dependency, so these tests run on CI where Telegram is not installed.
The menu/handler tests are source-level wiring checks for the same reason.
"""
from pathlib import Path

import i18n
import reseller_section


class FakeDB:
    def __init__(self, **settings):
        self.settings = settings

    def get_setting(self, key, default=""):
        return self.settings.get(key, default)


ROOT = Path(__file__).resolve().parents[1]


def test_section_is_on_by_default_and_off_only_for_the_zero_value():
    assert reseller_section.is_enabled(FakeDB()) is True
    assert reseller_section.is_enabled(FakeDB(reseller_section_enabled="1")) is True
    assert reseller_section.is_enabled(FakeDB(reseller_section_enabled="0")) is False
    # A malformed/empty value must not lock the bot out of the feature.
    assert reseller_section.is_enabled(FakeDB(reseller_section_enabled="")) is True


def test_toggle_label_follows_the_state():
    on = reseller_section.toggle_label(FakeDB(reseller_section_enabled="1"))
    off = reseller_section.toggle_label(FakeDB(reseller_section_enabled="0"))
    assert "خاموش کردن" in on
    assert "روشن کردن" in off


def test_status_text_reports_the_state():
    on = reseller_section.status_text(FakeDB(reseller_section_enabled="1"))
    off = reseller_section.status_text(FakeDB(reseller_section_enabled="0"))
    assert "🟢 روشن" in on
    assert "🔴 خاموش" in off
    assert "مدیریت نماینده‌های فعلی" in on


def test_toggle_messages_describe_the_change():
    assert "خاموش شد" in reseller_section.toggle_message(True)
    assert "روشن شد" in reseller_section.toggle_message(False)


def test_new_strings_have_english_translations():
    for text in (
        reseller_section.blocked_text(),
        reseller_section.toggle_label(FakeDB(reseller_section_enabled="0")),
        reseller_section.toggle_message(True),
        reseller_section.toggle_message(False),
    ):
        translated = i18n.tr(text, "en")
        assert translated and translated != text, text


def test_keyboards_hide_every_reseller_entry_when_the_section_is_off():
    source = (ROOT / "keyboards.py").read_text(encoding="utf-8")
    # One gate is shared by the tiers/request/commission/panel builders.
    assert "section_on = reseller_section_enabled(db)" in source
    assert source.count("not section_on") >= 3
    assert 'if not is_reseller or not section_on:' in source
    # The toggle is injected into the resellers category independently of the
    # custom item ordering, so it cannot be reordered out of reach.
    assert 'if cat_key == "resellers" and is_main_bot:' in source
    assert "reseller_section.TOGGLE_CALLBACK" in source or \
        '"adm_reseller_section_toggle"' in source


def test_handlers_are_wired_to_the_setting():
    admin = (ROOT / "handlers_admin.py").read_text(encoding="utf-8")
    user = (ROOT / "handlers_user.py").read_text(encoding="utf-8")
    assert "reseller_section.TOGGLE_CALLBACK" in admin
    assert "db.set_setting, kb.RESELLER_SECTION_SETTING" in admin
    # panel open, stats, fixed product, new config, tiers menu, rt callback,
    # and the request flow all refuse to work while the section is off.
    assert user.count("kb.reseller_section_enabled(db)") >= 7


def test_default_setting_is_registered():
    constants = (ROOT / "db" / "constants.py").read_text(encoding="utf-8")
    assert '"reseller_section_enabled": "1"' in constants
