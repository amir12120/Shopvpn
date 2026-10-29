# -*- coding: utf-8 -*-
"""Checks for the installer/CLI scripts shipped with this fork.

These are pure text checks: they run without a server and catch regressions in
the one-command install flow (English-only output, the `shopvpn` CLI command,
automatic menu opening) before they reach a real machine.
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Any Arabic-script code point: install/update output must stay English.
ARA_FA = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def _read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


@pytest.mark.parametrize("name", ["install.sh", "update.sh", "preflight.sh",
                                  "cleanup.sh", "setup_local_translation.sh"])
def test_install_scripts_have_no_persian(name):
    assert not ARA_FA.search(_read(name)), f"{name} must not contain Persian text"


def test_install_is_one_command():
    """install.sh installs prerequisites, the bot, the CLI and opens the menu."""
    text = _read("install.sh")
    assert "apt-get install" in text                     # prerequisites
    assert "setup_local_translation.sh" in text          # bot install steps
    assert "shopvpn" in text                             # CLI command name
    assert "/usr/local/bin" in text                      # where the CLI goes
    assert "manage.sh" in text                           # the menu that opens
    assert "SHOPVPN_SKIP_MENU" in text                   # opt-out for CI
    assert "-t 0" in text                                # only open on a terminal


def test_install_creates_shopvpn_launcher():
    """The launcher must exec the installed manage.sh and be installed 0755."""
    text = _read("install.sh")
    assert "exec bash" in text
    assert "install -m 0755" in text
    assert 'CLI_NAME="shopvpn"' in text


def test_install_scripts_pass_reading():
    for name in ("install.sh", "update.sh", "check_upstream.sh"):
        assert os.path.getsize(os.path.join(ROOT, name)) > 0


def test_english_install_guide_exists():
    guide = _read("INSTALL.md")
    assert "install.sh" in guide
    assert "shopvpn" in guide
    assert not ARA_FA.search(guide), "INSTALL.md must be English-only"


def test_readmes_mention_shopvpn_command():
    for name in ("README.md", "README.fa.md"):
        assert "shopvpn" in _read(name), f"{name} should document the shopvpn command"


def test_only_english_and_persian_docs_ship():
    """The fork supports fa/en only; stale ru/zh readmes must not come back."""
    for name in ("README.md", "README.fa.md", "INSTALL.md", "INSTALL.fa.md"):
        assert os.path.isfile(os.path.join(ROOT, name)), f"{name} is missing"
    for name in ("README.ru.md", "README.zh.md"):
        assert not os.path.exists(os.path.join(ROOT, name)), f"{name} must stay removed"


def test_persian_docs_stay_persian():
    for name in ("README.fa.md", "INSTALL.fa.md"):
        assert ARA_FA.search(_read(name)), f"{name} should contain Persian text"


def test_check_upstream_helper_targets_upstream():
    text = _read("check_upstream.sh")
    assert "mehdirafatpanah/Shopvpn" in text


def test_manage_cli_defaults_to_english():
    text = _read("manage.sh")
    assert 'APP_LANG="en"' in text


def test_disk_lean_installs_survive_upstream_merges():
    """The disk fixes must be present in both install paths (manage.sh + install.sh).

    Upstream ships the same actions in the CLI and in the one-command installer,
    so a merge that only keeps one of them would silently bring the multi-GB
    CUDA torch wheel and pip's download cache back.
    """
    for name in ("manage.sh", "install.sh"):
        text = _read(name)
        assert "--index-url https://download.pytorch.org/whl/cpu" in text, name
        assert "--no-cache-dir" in text, name
    setup = _read("setup_local_translation.sh")
    assert "PIP_NO_CACHE_DIR=1" in setup
    assert "SHOPVPN_INSTALL_LIBRETRANSLATE" in setup


def test_manage_keeps_fork_repo_and_optional_heavy_fallback():
    text = _read("manage.sh")
    assert 'REPO_URL="https://github.com/amir12120/shopvpn-amir.git"' in text
    assert 'GITHUB_REPO="shopvpn-amir"' in text
    assert 'GITHUB_OWNER="amir12120"' in text
    # LibreTranslate is a multi-GB opt-in, never a silent download.
    assert "lt_heavy_prompt" in text
    assert 'SHOPVPN_INSTALL_LIBRETRANSLATE="$lt_env"' in text
    # The extra-language menu must survive merges of the upstream menu table.
    assert "install_translation_langs" in text
    assert "SHOPVPN_TRANSLATION_LANGS" in _read("setup_local_translation.sh")


def _update_bot_body():
    text = _read("manage.sh")
    start = text.index("update_bot() {")
    return text[start:text.index("\n}\n", start)]


def test_update_runs_every_step_including_disk_cleanup():
    """Apart from prerequisites, an update repeats everything an install does."""
    body = _update_bot_body()
    assert "fetch_project_code" in body                       # newest code
    assert "PIP_REQS" in body                                # dependencies
    assert "setup_local_translation.sh" in body               # translation runtime
    assert "cleanup.sh" in body, "update must free disk like the install does"
    assert 'restart_service_and_wait "$SERVICE_NAME"' in body


def test_translation_failure_is_a_warning_not_a_dead_bot():
    """A failed model refresh must not print "the bot did not start".

    The update summary used to treat every optional step failure as fatal, so a
    translation error printed the install_failed message even after step 5 had
    confirmed the bot was up. Keep the two states separate.
    """
    body = _update_bot_body()
    assert 'setup_local_translation.sh' in body
    assert '|| warned=1' in body
    assert 'failed=1' not in body.split("setup_local_translation.sh")[1].split("\n")[0]
    final = body.split("draw_rule")[-1]
    assert 'systemctl is-active --quiet "$SERVICE_NAME"' in final
    assert 'translation_update_warning' in final
    assert 'update_incomplete' in final


def test_translation_setup_cannot_exit_silently():
    """The old `set -e` + `grep` combination exited before writing anything.

    A missing SHOPVPN_TRANSLATION_LANGS key made grep return 1, which killed the
    script under `set -e`. The run then showed only a red cross, with no output,
    and never saved the key for the next update.
    """
    text = _read("setup_local_translation.sh")
    assert re.search(r"^set -uo pipefail$", text, re.M)
    assert not re.search(r"^set -euo pipefail$", text, re.M)
    assert "sed -n 's/^SHOPVPN_TRANSLATION_LANGS=//p'" in text
    assert "SHOPVPN_TRANSLATION_LANGS=%s" in text
    assert "FAILED=1" in text
    assert "exit \"$FAILED\"" in text


def test_no_restart_is_trusted_after_a_fixed_sleep():
    """`systemctl restart && sleep 2` is not a health check.

    Every ShopVPN unit runs with Restart=always, so a service that dies on
    import still answers "active" right after the restart. Restarts must go
    through the readiness helper, which polls until the unit stays up.
    """
    text = _read("manage.sh")
    assert "wait_for_service_ready()" in text
    assert "restart_service_and_wait()" in text
    assert not re.search(r"systemctl restart [^\n]*&&\s*sleep", text), (
        "a restart step must wait for readiness instead of a fixed sleep"
    )


def test_install_waits_until_the_bot_really_came_up():
    text = _read("install.sh")
    assert "BOT_READY" in text
    assert "cleanup.sh" in text
    assert "journalctl" in text, "a failed start must show what went wrong"


def test_cleanup_sweeps_every_home_the_journal_and_abandoned_tmp_dirs():
    """The disk fillers this fork exists for.

    Caches live in the HOME of whoever ran the command (the management menu
    under root) *and* in the HOME of the account the systemd unit runs as, so
    both have to be swept. Rotated journal files and the restore/QR temp dirs
    the bot abandoned grow without anyone noticing.
    """
    text = _read("cleanup.sh")
    assert "pip cache purge" in text
    assert "systemctl show -p User --value" in text, "the service account's cache must be swept too"
    assert "IFS= read -r h" in text, "home paths must be read line by line (they may contain spaces)"
    assert "journalctl --vacuum-size" in text and "SHOPVPN_JOURNAL_MAX" in text
    assert "-mtime +1" in text and "restore_" in text
    assert "$INSTALL_DIR/backups" in text, "the report should show what the backups cost"


def test_translation_models_install_into_the_bots_own_home():
    """The model install must follow the bot's account, not the caller's.

    Argos keeps installed models under the HOME of the running account, so
    running argospm as root while the unit runs as somebody else downloads a
    second full copy (a few hundred MB) and still leaves the bot without its
    models. HOME must therefore follow the unit, and any inherited XDG_*
    override must be dropped, because an empty XDG_* makes Argos resolve to a
    relative path.
    """
    text = _read("setup_local_translation.sh")
    assert 'systemctl show -p User --value "$SERVICE_NAME"' in text
    assert 'as_service_user "$VENV_DIR/bin/argospm" install' in text
    assert 'as_service_user "$VENV_DIR/bin/argospm" update' in text
    assert "-u XDG_DATA_HOME" in text


def test_installer_caps_the_system_journal():
    text = _read("install.sh")
    assert "journald.conf.d/shopvpn-disk.conf" in text
    assert "SystemMaxUse=" in text
    assert "SHOPVPN_SKIP_JOURNAL_LIMIT" in text, "the cap must stay opt-out"
