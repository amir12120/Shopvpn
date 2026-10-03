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
