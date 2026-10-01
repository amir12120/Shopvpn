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
    for name in ("README.md", "README.fa.md", "README.ru.md", "README.zh.md"):
        assert "shopvpn" in _read(name), f"{name} should document the shopvpn command"


def test_all_readmes_exist_in_both_languages():
    """English and Persian docs must both stay present."""
    for name in ("README.md", "README.fa.md", "INSTALL.md", "INSTALL.fa.md",
                 "README.ru.md", "README.zh.md"):
        assert os.path.isfile(os.path.join(ROOT, name)), f"{name} is missing"


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
    assert 'REPO_URL="https://github.com/amir12120/Shopvpn.git"' in text
    assert 'GITHUB_OWNER="amir12120"' in text
    # LibreTranslate is a multi-GB opt-in, never a silent download.
    assert "lt_heavy_prompt" in text
    assert 'SHOPVPN_INSTALL_LIBRETRANSLATE="$lt_env"' in text
    # The extra-language menu must survive merges of the upstream menu table.
    assert "install_translation_langs" in text
    assert "SHOPVPN_TRANSLATION_LANGS" in _read("setup_local_translation.sh")
