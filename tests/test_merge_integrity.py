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
    "python-bidi": "bidi",
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
    # --- upstream batch merged with the next release ---
    "audit_forwarder.py",
    "admin_channel_engage.py",
    "admin_channel_plan.py",
    "admin_channel_posts.py",
    "admin_post_brand.py",
    "channel_ai.py",
    "channel_post_scheduler.py",
    "channel_suggestions.py",
    "gift_card_ai.py",
    "gift_card_handlers.py",
    "gift_card_render.py",
    "gift_cards.py",
    "jarvis_guide.py",
    "leak_admin.py",
    "leak_index.py",
    "leak_scanner.py",
    "post_image.py",
    "price_display.py",
    "product_waitlist.py",
    "userbot.py",
    "userbot_admin.py",
    "db/gift_cards.py",
    "db/leak_store.py",
    "db/userbot_store.py",
    # --- upstream batch: competitive seasons, daily quiz, lootbox engagement,
    # --- smart leak/channel discovery ---
    "daily_quiz.py",
    "engagement.py",
    "engagement_handlers.py",
    "leak_discovery.py",
    "season_quiz_handlers.py",
    "seasons.py",
    "db/engagement.py",
    "db/seasons.py",
    # --- upstream batch: dedicated sub, web store, in-bot updater ---
    "dedicated_sub.py",
    "admin_dedicated_sub.py",
    "db/dedicated_sub.py",
    "sub_server/__init__.py",
    "sub_server/server.py",
    "web_auth.py",
    "web_store/__init__.py",
    "web_store/routes.py",
    "web_store/server.py",
    "updater.py",
    "admin_update.py",
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

    # Product waitlist (upstream 90fb055 batch, via origin/main).
    waitlist = (ROOT / "product_waitlist.py").read_text(encoding="utf-8")
    assert "async def notify_waitlist(" in waitlist
    assert "def bot_sender(" in waitlist
    catalog = (ROOT / "db/catalog.py").read_text(encoding="utf-8")
    for needle in ("def add_product_waitlist(", "def get_product_waitlist(", "def remove_product_waitlist("):
        assert needle in catalog, f"db/catalog.py lost {needle}"
    assert "CREATE TABLE IF NOT EXISTS product_waitlist" in (ROOT / "db/_base.py").read_text(encoding="utf-8")
    assert "db.add_product_waitlist" in handlers_user
    assert "product_waitlist.notify_waitlist" in handlers_admin
    assert "product_waitlist.notify_waitlist" in admin_panel
    assert "product_waitlist.notify_waitlist" in (ROOT / "miniapp/server.py").read_text(encoding="utf-8")



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



def test_new_upstream_features_stay_wired():
    """The merged upstream batch (userbot, leak scanner, gift cards, channel
    tools, payment-gate conditions): presence is not enough — each feature must
    stay reachable from a start-up task, handler, dispatcher or DB path, or it
    silently does nothing on a real server."""
    main_py = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "import userbot" in main_py
    assert "userbot.run(main_db, BOT_TOKEN)" in main_py
    assert "import leak_index" in main_py
    assert "leak_index.run(main_db)" in main_py

    # Gift cards hook both config-delivery paths and register their routers.
    assert "from gift_card_handlers import deliver_gift_order" in (ROOT / "config_delivery.py").read_text(encoding="utf-8")
    web = (ROOT / "admin_panel/config_delivery_web.py").read_text(encoding="utf-8")
    assert "gift_get_order" in web and "gift_mark_order_delivered" in web
    bot_manager = (ROOT / "bot_manager.py").read_text(encoding="utf-8")
    assert "from gift_card_handlers import create_gift_router" in bot_manager
    assert "from userbot_admin import create_userbot_router" in bot_manager
    assert "from leak_admin import create_leak_router" in bot_manager
    assert "from channel_post_scheduler import channel_post_loop" in bot_manager
    assert "from audit_forwarder import audit_forward_loop" in bot_manager
    handlers_user = (ROOT / "handlers_user.py").read_text(encoding="utf-8")
    assert "from gift_card_handlers import redeem_gift_for_message" in handlers_user

    # Payment-gate conditions: admin callback -> FSM state -> settings -> DB.
    handlers_admin = (ROOT / "handlers_admin.py").read_text(encoding="utf-8")
    assert 'F.data == "adm_pmgate"' in handlers_admin
    assert "AdminPmGate.waiting_value" in handlers_admin
    assert "from price_display import price_range" in handlers_admin
    assert "import product_waitlist" in handlers_admin
    states = (ROOT / "states.py").read_text(encoding="utf-8")
    assert "class AdminPmGate(StatesGroup):" in states

    # Channel tools must stay imported AND registered on the admin router —
    # an import without register() is a menu button that does nothing.
    for module in ("admin_channel_posts", "admin_channel_engage", "admin_channel_plan"):
        assert f"import {module}" in handlers_admin, f"{module} import disappeared"
        assert f"{module}.register(router, db, senior_admin_only, deny_mid)" in handlers_admin, (
            f"{module} is imported but no longer registered on the admin router"
        )
    assert "import channel_suggestions" in (ROOT / "channel_post_scheduler.py").read_text(encoding="utf-8")
    keyboards = (ROOT / "keyboards.py").read_text(encoding="utf-8")
    assert "from price_display import price_label_plain" in keyboards
    assert "def pm_gate_list_kb(" in keyboards
    assert "def admin_category_item_keys(" in keyboards
    assert "USER_SCREENS = {" in keyboards

    # Channel-post CRUD lives in the DB layer the scheduler claims from.
    db_system = (ROOT / "db/system.py").read_text(encoding="utf-8")
    assert "def create_channel_post(" in db_system
    assert "def claim_channel_post(" in db_system


def test_payment_method_gate_is_wired_end_to_end():
    """Per-gateway activation conditions (pm_gate) must stay reachable.

    The admin sets "after N purchases / N days" per gateway; until then the
    gateway is hidden in the bot and the mini app, so every edge of that chain
    has to keep existing or the setting silently does nothing.
    """
    db_payments = (ROOT / "db/payments.py").read_text(encoding="utf-8")
    for needle in (
        "def payment_gate_setting_keys(",
        "def get_payment_gate_settings(",
        "def payment_gate_passed(",
    ):
        assert needle in db_payments, f"db/payments.py lost {needle!r}"

    keyboards = (ROOT / "keyboards.py").read_text(encoding="utf-8")
    assert "def pm_gate_list_kb(" in keyboards
    assert "def pm_gate_method_kb(" in keyboards
    assert 'callback_data="adm_pmgate"' in keyboards or '"adm_pmgate"' in keyboards

    handlers_admin = (ROOT / "handlers_admin.py").read_text(encoding="utf-8")
    assert 'F.data == "adm_pmgate"' in handlers_admin
    assert "AdminPmGate.waiting_value" in handlers_admin
    assert "class AdminPmGate(StatesGroup):" in (ROOT / "states.py").read_text(encoding="utf-8")

    miniapp = (ROOT / "miniapp/server.py").read_text(encoding="utf-8")
    assert miniapp.count("db.payment_gate_passed(") >= 4


def test_seasons_quiz_and_lootbox_stay_wired():
    """The seasons / daily-quiz / lootbox batch must stay reachable end to end.

    Presence is not wiring: a season loop that is never scheduled, a router
    that is imported but not included, or a lootbox order only the bot can
    approve all look perfectly healthy in a diff and do nothing on a server.
    """
    bot_manager = (ROOT / "bot_manager.py").read_text(encoding="utf-8")
    assert "import daily_quiz" in bot_manager
    assert "import seasons" in bot_manager
    assert "from season_quiz_handlers import create_season_quiz_router" in bot_manager
    assert "from engagement_handlers import create_engagement_router" in bot_manager
    assert "dp.include_router(create_season_quiz_router(db, is_main_bot=is_main_bot))" in bot_manager
    assert "dp.include_router(create_engagement_router(db, is_main_bot=is_main_bot))" in bot_manager
    assert "asyncio.create_task(seasons.season_loop(db, bot))" in bot_manager
    assert "asyncio.create_task(daily_quiz.quiz_loop(db, bot))" in bot_manager


    # Streak/points bookkeeping is triggered from the blocked-user touch path.
    blocked_user = (ROOT / "blocked_user.py").read_text(encoding="utf-8")
    assert "import engagement" in blocked_user
    assert 'engagement.schedule_touch(self.db, data["bot"], user.id)' in blocked_user

    # The mixins must ride on the Database class or their tables are unreachable.
    db_init = (ROOT / "db/__init__.py").read_text(encoding="utf-8")
    for needle in (
        "from .seasons import SeasonsMixin",
        "from .engagement import EngagementMixin",
        "    SeasonsMixin,",
        "    EngagementMixin,",
    ):
        assert needle in db_init, f"db/__init__.py lost {needle!r}"

    db_seasons = (ROOT / "db/seasons.py").read_text(encoding="utf-8")
    for needle in (
        "class SeasonsMixin",
        "def season_get_active(",
        "def season_standings(",
        "def season_user_stats(",
        "def badge_list(",
    ):
        assert needle in db_seasons, f"db/seasons.py lost {needle!r}"

    db_engagement = (ROOT / "db/engagement.py").read_text(encoding="utf-8")
    for needle in (
        "class EngagementMixin",
        "def approve_lootbox_order(",
        "def box_type_get(",
        "def box_type_allows_payment_method(",
    ):
        assert needle in db_engagement, f"db/engagement.py lost {needle!r}"

    seasons_py = (ROOT / "seasons.py").read_text(encoding="utf-8")
    for needle in ("def season_loop(", "def enabled(", "def mask_name(", "def prize_lines(",
                   "def fmt_local("):
        assert needle in seasons_py, f"seasons.py lost {needle!r}"

    daily_quiz = (ROOT / "daily_quiz.py").read_text(encoding="utf-8")
    assert "def quiz_loop(" in daily_quiz
    assert "def answer_quiz_for_message(" in daily_quiz
    assert "def schedule_touch(" in (ROOT / "engagement.py").read_text(encoding="utf-8")

    season_handlers = (ROOT / "season_quiz_handlers.py").read_text(encoding="utf-8")
    assert "def create_season_quiz_router(" in season_handlers
    assert "def show_season_for_message(" in season_handlers
    engagement_handlers = (ROOT / "engagement_handlers.py").read_text(encoding="utf-8")
    for needle in (
        "def create_engagement_router(",
        "def notify_lootbox_delivered(",
        "def show_lootbox_for_message(",
        "def show_progress_for_message(",
    ):
        assert needle in engagement_handlers, f"engagement_handlers.py lost {needle!r}"

    # Bot side: the account-hub entries and the lootbox payment-method gate.
    handlers_user = (ROOT / "handlers_user.py").read_text(encoding="utf-8")
    assert "from daily_quiz import answer_quiz_for_message" in handlers_user
    assert "from season_quiz_handlers import show_season_for_message" in handlers_user
    assert "from engagement_handlers import show_lootbox_for_message, show_progress_for_message" in handlers_user
    for action in ('"__open_season__"', '"__open_lootbox__"', '"__open_progress__"',
                   '"__quiz_answer__:"'):
        assert action in handlers_user, f"the account-hub entry {action} disappeared"
    assert "db.box_type_allows_payment_method" in handlers_user
    assert 'order["lootbox_type_id"]' in handlers_user

    # All three approval surfaces must keep telling the buyer about the boxes.
    handlers_admin = (ROOT / "handlers_admin.py").read_text(encoding="utf-8")
    assert "db.approve_lootbox_order" in handlers_admin
    assert "from engagement_handlers import notify_lootbox_delivered" in handlers_admin
    assert "kb.user_group_stats_kb" in handlers_admin
    payment_delivery = (ROOT / "payment_delivery.py").read_text(encoding="utf-8")
    assert 'if order["lootbox_type_id"]:' in payment_delivery
    assert "db.approve_lootbox_order(order_id)" in payment_delivery
    assert "notify_lootbox_delivered(" in payment_delivery
    assert '"lootbox_type_id" in keys and order["lootbox_type_id"]' in (
        ROOT / "extra_gateway_user.py").read_text(encoding="utf-8")

    # Schema, settings and ledger labels the feature needs to function at all.
    db_base = (ROOT / "db/_base.py").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS leak_candidates" in db_base
    assert "CREATE TABLE IF NOT EXISTS leak_queries" in db_base
    assert '("orders", "lootbox_type_id", "INTEGER")' in db_base
    db_constants = (ROOT / "db/constants.py").read_text(encoding="utf-8")
    assert '"acct_show_lootbox"' in db_constants
    assert '"acct_lootbox": {"label"' in db_constants
    assert '"acct_orders", "acct_tutorial", "acct_referral", "acct_wallet", "acct_lootbox"' in db_constants
    db_orders = (ROOT / "db/orders.py").read_text(encoding="utf-8")
    for needle in ('"season_prize"', '"lootbox_buy"', '"milestone_prize"'):
        assert needle in db_orders, f"db/orders.py lost {needle}"

    keyboards = (ROOT / "keyboards.py").read_text(encoding="utf-8")
    assert "def user_group_stats_kb(" in keyboards
    assert '"acct_lootbox": ("acct_show_lootbox", "lb_menu")' in keyboards
    assert '("adm_season_quiz"' in keyboards
    assert '("adm_engage"' in keyboards
    assert '"wal_progress"' in keyboards

    # Mini app: the season endpoint feeds the season card in the account page.
    miniapp = (ROOT / "miniapp/server.py").read_text(encoding="utf-8")
    assert '@app.get("/api/season")' in miniapp
    assert "season_logic.enabled(db)" in miniapp
    assert "db.season_standings(" in miniapp
    app_js = (ROOT / "miniapp/static/app.js").read_text(encoding="utf-8")
    assert "/api/season" in app_js
    assert "function seasonCard(" in app_js


def test_leak_discovery_stays_wired():
    """Upstream's smart channel discovery must keep its crawler, store and admin UI."""
    leak_discovery = (ROOT / "leak_discovery.py").read_text(encoding="utf-8")
    for needle in ("class Discovery", "def message_text(", "def collect_refs(", "KEY_ENABLED"):
        assert needle in leak_discovery, f"leak_discovery.py lost {needle!r}"

    leak_scanner = (ROOT / "leak_scanner.py").read_text(encoding="utf-8")
    assert "import leak_discovery as ld" in leak_scanner
    assert "def install_realtime(" in leak_scanner
    assert "async def run_dedicated(" in leak_scanner
    assert "ld.Discovery(" in leak_scanner
    assert "events.MessageEdited" in leak_scanner  # edited posts are re-scanned

    main_py = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "import leak_scanner" in main_py
    assert "leak_scanner.run_dedicated(main_db, BOT_TOKEN)" in main_py

    db_leak_store = (ROOT / "db/leak_store.py").read_text(encoding="utf-8")
    for needle in (
        "def upsert_leak_candidate(",
        "def ensure_leak_queries(",
        "def list_prunable_leak_channels(",
        "def record_leak_query_run(",
    ):
        assert needle in db_leak_store, f"db/leak_store.py lost {needle!r}"

    leak_admin = (ROOT / "leak_admin.py").read_text(encoding="utf-8")
    assert "import leak_discovery as ld" in leak_admin
    assert '"adm_leak_d"' in leak_admin
    assert "ld.KEY_ENABLED" in leak_admin  # the discovery settings menu

    # Review callbacks must survive the report-group ownership check.
    report_router = (ROOT / "report_router.py").read_text(encoding="utf-8")
    assert '"lk:rot:", "lk:warn:", "lk:ign:",' in report_router
    assert '"adm_user_configs:",' in report_router


def test_rejected_upstream_paths_stay_out():
    """Upstream re-uploads its own install scripts, docs and a root-level test on
    every push. Those were rejected on purpose, so they must not creep back in."""
    assert not (ROOT / "test_leak_discovery.py").exists(), "upstream's root test came back"
    assert not (ROOT / "_.gitignore.txt").exists(), "upstream's gitignore dump came back"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Config Leak Detection & Smart Discovery" not in readme, (
        "an upstream README section replaced the fork's documentation"
    )

    manage = (ROOT / "manage.sh").read_text(encoding="utf-8")
    assert "telegram_accounts_menu()" not in manage, "upstream's manage.sh menu came back"
    extra = (ROOT / "manage_extra_cli.sh").read_text(encoding="utf-8")
    assert "setup_web_store()" in extra
    assert "setup_dedicated_sub()" in extra
    assert "telegram_accounts_menu()" not in extra
    assert "menu_item 33 menu_33" in manage
    assert "manage_extra_cli.sh" in manage
    assert "32) doctor; pause ;;" in manage
    # …while the fork's own service helpers are still there.
    assert "wait_for_service_ready()" in manage
    assert "restart_service_and_wait()" in manage

    # Telegram session files hold live credentials and must never be committable.
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "userbot_session.json" in gitignore
    assert "leak_session.json" in gitignore


def test_dedicated_sub_web_store_and_updater_stay_wired():
    """Dedicated subscription, website auth/store, and updater must stay reachable."""
    handlers_admin = (ROOT / "handlers_admin.py").read_text(encoding="utf-8")
    assert "import admin_dedicated_sub" in handlers_admin
    assert "import admin_update" in handlers_admin
    assert "admin_dedicated_sub.register(router, db, senior_admin_only, deny_mid, replace_admin_view)" in handlers_admin
    assert "admin_update.register(router, db, senior_admin_only, deny_mid, replace_admin_view)" in handlers_admin

    handlers_user = (ROOT / "handlers_user.py").read_text(encoding="utf-8")
    assert "import web_auth" in handlers_user
    assert "import dedicated_sub" in handlers_user
    assert "web_auth.confirm_login" in handlers_user
    assert "dedicated_sub.dedicated_link_for_upstream" in handlers_user

    bot_manager = (ROOT / "bot_manager.py").read_text(encoding="utf-8")
    assert "import updater" in bot_manager
    assert "updater.check_loop(bot, db)" in bot_manager

    config_delivery = (ROOT / "config_delivery.py").read_text(encoding="utf-8")
    assert "import dedicated_sub" in config_delivery
    assert "dedicated_sub.dedicated_link_for_upstream" in config_delivery

    db_init = (ROOT / "db/__init__.py").read_text(encoding="utf-8")
    assert "from .dedicated_sub import DedicatedSubMixin" in db_init

    miniapp = (ROOT / "miniapp/server.py").read_text(encoding="utf-8")
    assert "import web_auth" in miniapp
    assert "import dedicated_sub" in miniapp
    assert "web_auth.session_user" in miniapp

    admin_panel = (ROOT / "admin_panel/server.py").read_text(encoding="utf-8")
    assert "import dedicated_sub as ds" in admin_panel
    assert "api_web_store_preview_url" in admin_panel

    sub_server = (ROOT / "sub_server/server.py").read_text(encoding="utf-8")
    assert "import dedicated_sub as ds" in sub_server
    web_store = (ROOT / "web_store/server.py").read_text(encoding="utf-8")
    assert "from web_store.routes import router as web_router" in web_store

    updater_src = (ROOT / "updater.py").read_text(encoding="utf-8")
    assert 'FORK_GITHUB_OWNER = "amir12120"' in updater_src
    assert 'UPSTREAM_GITHUB_OWNER = "mehdirafatpanah"' in updater_src
    assert 'os.getenv("SHOPVPN_UPDATE_OWNER", "mehdirafatpanah")' not in updater_src
    assert 'raw.githubusercontent.com/{REPO_OWNER}' in updater_src
