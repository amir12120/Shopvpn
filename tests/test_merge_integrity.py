# -*- coding: utf-8 -*-
"""Regression tests for pulling upstream Shopvpn features into this fork.

Every upstream merge is a chance to (a) drop the fork's own install/runtime
fixes, or (b) pull in a module that imports a package the lean installer never
installs. Both would show up as a broken install/update on a customer server,
so they are pinned here.
"""
import ast
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {
    ".git",
    ".github",
    "__pycache__",
    "backups",
    "tests",
    "translation-venv",
    "venv",
}

# Packages that ship as dependencies of a declared requirement (fastapi pulls
# both pydantic and starlette), so they never need their own requirements line.
TRANSITIVE_DEPS = {"pydantic", "starlette"}

# dist-name -> import-name for the requirements that differ.
DIST_ALIASES = {
    "python-dotenv": "dotenv",
    "pillow": "PIL",
    "pyjwt": "jwt",
    "python-multipart": "multipart",
    "deep-translator": "deep_translator",
    "google-genai": "google",
}

# Modules added by upstream that the fork must keep shipping and wiring up.
UPSTREAM_FEATURE_MODULES = (
    "admin_campaign.py",
    "admin_help.py",
    "ai_admin.py",
    "ai_media.py",
    "ai_text.py",
    "bank_inquiry.py",
    "campaign_ai.py",
    "churn_prediction.py",
    "draft_stream.py",
    "extra_settings_schema.py",
    "db/orders.py",
)

# Upstream keeps re-uploading these with a module-level `from i18n import tr`
# on line 1, which pushes the `# -*- coding: utf-8 -*-` declaration out of the
# legal position. The fork moved the import below the docstring instead.
IMPORT_ORDER_FIXED_FILES = (
    "config_delivery.py",
    "force_join.py",
    "handlers_admin.py",
)


def _iter_project_python_files():
    for path in sorted(ROOT.rglob("*.py")):
        parts = set(path.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        yield path


def _declared_requirement_modules():
    modules = set()
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[<>=!\[;]", line)[0].strip().lower()
        modules.add(DIST_ALIASES.get(name, name.replace("-", "_")))
    return modules


def _local_importable_names():
    names = set()
    for path in ROOT.rglob("*.py"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        names.add(path.stem)
        if path.parent != ROOT:
            names.add(path.parent.name)
    return names


def _module_level_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                yield node.module.split(".")[0]


def test_upstream_feature_modules_still_shipped_and_wired():
    """The merged upstream modules must exist and stay reachable from the bot."""
    for relative in UPSTREAM_FEATURE_MODULES:
        path = ROOT / relative
        assert path.is_file(), f"{relative} disappeared from the fork"
        assert path.stat().st_size > 0, f"{relative} is empty"

    # Wired into the running bot / admin panel, not just sitting in the tree.
    assert "from churn_prediction import churn_offer_loop" in (ROOT / "bot_manager.py").read_text(encoding="utf-8")
    handlers_admin = (ROOT / "handlers_admin.py").read_text(encoding="utf-8")
    for module in ("admin_campaign", "admin_help", "ai_admin", "ai_media"):
        assert f"import {module}" in handlers_admin, f"{module} is no longer wired into the admin handlers"
    handlers_user = (ROOT / "handlers_user.py").read_text(encoding="utf-8")
    assert "import ai_media" in handlers_user
    assert "from draft_stream import DraftStreamer" in handlers_user

    # Bank inquiry backs the fake-receipt checks, extra settings back both web panels.
    assert "import bank_inquiry" in (ROOT / "receipt_ai_check.py").read_text(encoding="utf-8")
    admin_panel = (ROOT / "admin_panel/server.py").read_text(encoding="utf-8")
    assert "import extra_settings_schema" in admin_panel
    assert "extra_settings_schema" in (ROOT / "miniapp/server.py").read_text(encoding="utf-8")


def test_card_number_gate_is_wired_end_to_end():
    """The card-number display condition (upstream 91961c5/5a14239/63e9939) must
    stay wired: admin UI -> FSM state -> settings -> DB gate -> bot and miniapp.
    Without any of these edges the feature would silently do nothing, because
    both settings default to 0 (= no restriction)."""
    db_payments = (ROOT / "db/payments.py").read_text(encoding="utf-8")
    for needle in (
        'CARD_GATE_METHODS = ("card", "card_auto")',
        "def get_card_gate_settings(",
        "def card_gate_passed(",
        "def card_method_blocked_for_user(",
    ):
        assert needle in db_payments, f"db/payments.py lost {needle!r}"

    # Both settings exist and default to "off", so no existing install changes.
    db_constants = (ROOT / "db/constants.py").read_text(encoding="utf-8")
    assert '"card_gate_min_purchases": "0"' in db_constants
    assert '"card_gate_min_days": "0"' in db_constants

    # Admin entry point: button -> keyboard -> FSM state -> handler.
    keyboards = (ROOT / "keyboards.py").read_text(encoding="utf-8")
    assert "def card_gate_kb(" in keyboards
    assert 'callback_data="adm_cardgate"' in keyboards
    assert "adm_cardgate_edit:card_gate_min_purchases" in keyboards
    assert "adm_cardgate_edit:card_gate_min_days" in keyboards
    # The user-facing keyboard must consult the gate for the given user.
    assert "user_id: int = None" in keyboards
    assert "db.card_method_blocked_for_user(user_id, method_key)" in keyboards

    handlers_admin = (ROOT / "handlers_admin.py").read_text(encoding="utf-8")
    assert 'F.data == "adm_cardgate"' in handlers_admin
    assert 'F.data.startswith("adm_cardgate_edit:")' in handlers_admin
    assert "AdminCardGate.waiting_value" in handlers_admin
    assert "card_gate_setting" in handlers_admin  # admin action is logged

    states = (ROOT / "states.py").read_text(encoding="utf-8")
    assert "class AdminCardGate(StatesGroup):" in states

    # Bot side: both the order and the wallet-topup error paths check the gate,
    # and the renewal entry points re-check it before showing the card.
    handlers_user = (ROOT / "handlers_user.py").read_text(encoding="utf-8")
    assert handlers_user.count("db.card_method_blocked_for_user") >= 4, (
        "the card gate is no longer enforced on the bot payment paths"
    )
    assert '_order_payment_method_error(order, "card")' in handlers_user
    assert '_order_payment_method_error(order, "card_auto")' in handlers_user
    assert '_wallet_topup_method_error(amount, "card", call.from_user.id)' in handlers_user
    assert '_wallet_topup_method_error(amount, "card_auto", call.from_user.id)' in handlers_user

    # Mini app side: the card number must be withheld from the API response.
    miniapp = (ROOT / "miniapp/server.py").read_text(encoding="utf-8")
    assert "def _card_info(" in miniapp
    assert "if not db.card_gate_passed(user_id):" in miniapp
    assert '"card_number": None, "card_holder": None' in miniapp
    assert miniapp.count("**_card_info(db, tg_id)") >= 4, (
        "a miniapp endpoint still returns the raw card number"
    )
    assert "db.card_gate_passed(tg_id)" in miniapp  # card_to_card_enabled flag


def test_telegram_caption_limit_and_nginx_upload_budget_survive_merges():
    """Telegram rejects captions over 1024 chars, and nginx rejects bodies over
    1 MB - both were merged from upstream and must not be lost together."""
    admin_panel = (ROOT / "admin_panel/server.py").read_text(encoding="utf-8")
    assert "if len(text) > 1024:" in admin_panel
    assert 'media_type not in ("photo", "voice")' in admin_panel

    app_js = (ROOT / "admin_panel/static/app.js").read_text(encoding="utf-8")
    assert "res.status === 413" in app_js
    assert "client_max_body_size" in app_js

    # Every nginx server block we generate must accept large uploads, otherwise
    # the 413 message above is all the user ever sees.
    install = (ROOT / "install.sh").read_text(encoding="utf-8")
    manage = (ROOT / "manage.sh").read_text(encoding="utf-8")
    assert install.count("client_max_body_size 100m;") == 1
    assert manage.count("client_max_body_size 100m;") == manage.count("server_name $DOMAIN;"), (
        "a manage.sh nginx server block is missing the upload limit"
    )
    for script, text in (("install.sh", install), ("manage.sh", manage)):
        assert text.count("proxy_read_timeout 600s;") == text.count("client_max_body_size 100m;"), (
            f"{script}: upload limit and read timeout are out of sync"
        )


@pytest.mark.parametrize("relative", IMPORT_ORDER_FIXED_FILES)
def test_coding_declaration_stays_on_the_first_line(relative):
    """A PEP 263 coding line only counts on line 1 or 2 — keep it there."""
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].startswith("# -*- coding: utf-8 -*-"), (
        f"{relative}: the coding declaration is no longer the first line"
    )
    for index, line in enumerate(lines):
        if line.startswith("from i18n import tr"):
            assert index > 1, f"{relative}: `from i18n import tr` back on the coding lines"
            break


def test_language_selection_migration_survives_upstream_merges():
    """New users are asked for fa/en once; existing users are never re-asked."""
    assert "ALTER TABLE users ADD COLUMN language_selected" in (ROOT / "db/_base.py").read_text(encoding="utf-8")
    assert "def is_user_language_selected" in (ROOT / "db/users.py").read_text(encoding="utf-8")
    assert "is_user_language_selected" in (ROOT / "force_join.py").read_text(encoding="utf-8")


def test_module_level_imports_are_declared():
    """Nothing imported at module level may be missing from a lean install.

    Imports inside functions are allowed to be optional (they are wrapped in
    try/except or only run for an explicitly enabled feature).
    """
    declared = _declared_requirement_modules()
    stdlib = set(sys.stdlib_module_names)
    local = _local_importable_names()

    undeclared = {}
    for path in _iter_project_python_files():
        for root in _module_level_imports(path):
            if root in stdlib or root in declared or root in local or root in TRANSITIVE_DEPS:
                continue
            undeclared.setdefault(root, []).append(str(path.relative_to(ROOT)))

    assert not undeclared, (
        "module-level imports that requirements.txt does not install: "
        + ", ".join(f"{mod} ({files[0]})" for mod, files in sorted(undeclared.items()))
    )


@pytest.mark.parametrize("relative,needle", [
    ("jalali.py", "Esfand (month 12)"),
    ("admin_panel/server.py", "is_language_enabled, LANGUAGE_CATALOG"),
    ("handlers_admin.py", "call.bot.send_message(uid, notification)"),
    ("cleanup_loop.py", "async def _notify_user(bot: Bot, db, user_id: int"),
])
def test_fork_runtime_fixes_survive_upstream_merges(relative, needle):
    """Fixes that upstream keeps re-introducing as bugs must not be lost."""
    assert needle in (ROOT / relative).read_text(encoding="utf-8")


def test_fork_runtime_fixes_survive_upstream_merges_multi():
    keyboards = (ROOT / "keyboards.py").read_text(encoding="utf-8")
    assert keyboards.count("def blupal_settings_kb(") == 1, "duplicate keyboard definition came back"

    handlers_user = (ROOT / "handlers_user.py").read_text(encoding="utf-8")
    assert handlers_user.count("call.bot, db,") >= 2, "undefined `bot` came back in the config-delete alerts"


def test_lean_install_flags_survive_upstream_merges():
    """Upstream's plain `pip install -r requirements.txt` must not sneak back in."""
    for script in ("manage.sh", "install.sh", "update.sh"):
        text = (ROOT / script).read_text(encoding="utf-8")
        assert "--no-cache-dir" in text or "PIP_NO_CACHE_DIR=1" in text, (
            f"{script} lost the disk-lean pip flag"
        )
    # CPU-only torch keeps the venv around 1.3 GB instead of pulling the CUDA build.
    assert "download.pytorch.org/whl/cpu" in (ROOT / "manage.sh").read_text(encoding="utf-8")
