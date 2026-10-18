# -*- coding: utf-8 -*-
"""Systemd units must never depend on a binary the installer does not install.

Release 4.12.0 wrapped every unit's ExecStart in `infisical run --env=dev --`,
but the `infisical` CLI is never installed, so systemd refused each unit with
status=203/EXEC and a fresh install could never start. These tests pin the fix:
Infisical is only used when the CLI is really present and the checkout is
linked, and a unit whose ExecStart cannot run is repaired.
"""
import os
import re
import shutil
import stat
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASH = shutil.which("bash")

pytestmark = pytest.mark.skipif(BASH is None, reason="bash is required")


def _read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def helpers_from(name):
    """The shared shell helpers that build the ExecStart line, as sourced text."""
    text = _read(name)
    start = re.search(r"# -+\r?\n# How the services are started[^\r\n]*\r?\n", text)
    assert start, "%s: helper block missing" % name
    rest = text[start.end():]
    stop = re.search(r"\r?\n(?=fetch_project_code\(\) \{|# -+\r?\n# 1/7\.)", rest)
    assert stop, "%s: helper block is not closed" % name
    return rest[:stop.start()]


def run_bash(script, env=None, cwd=None):
    full_env = dict(os.environ)
    full_env.update(env or {})
    result = subprocess.run(
        [BASH, "-c", script],
        capture_output=True, text=True, env=full_env, cwd=cwd, timeout=60,
    )
    return result


def call_helper(name, body, env):
    script = "set -eu\n" + helpers_from(name) + "\n" + body
    result = run_bash(script, env=env)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


# --------------------------------------------------------------------------- #
# Static: the wrapper is never hardcoded into a unit
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name", ["install.sh", "manage.sh"])
def test_no_unit_starts_with_the_infisical_cli(name):
    text = _read(name)
    assert "ExecStart=infisical" not in text, (
        "%s writes a unit whose ExecStart needs the Infisical CLI; it is not "
        "installed on a fresh server (systemd fails with 203/EXEC)" % name
    )
    # Every ExecStart must come from the guard that checks the CLI first.
    assert text.count("ExecStart=$EXEC_START") >= 1, name
    assert 'EXEC_START="$(service_exec_start' in text, name


def test_both_scripts_build_the_start_command_the_same_way(tmp_path):
    """The installer and the menu must generate the identical ExecStart line.

    Upstream ships the same actions in both files, so a fix applied to only one
    of them would leave the other path broken again.
    """
    for name in ("install.sh", "manage.sh"):
        body = helpers_from(name)
        assert "infisical_available() {" in body, name
        assert "service_exec_start() {" in body, name
        assert "unit_missing_binary() {" in body, name

    env = {"INSTALL_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"}
    call = 'service_exec_start "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/main.py"'
    assert call_helper("install.sh", call, env) == call_helper("manage.sh", call, env)


def test_doctor_action_is_wired_into_the_menu():
    text = _read("manage.sh")
    assert "doctor() {" in text
    assert re.search(r"^\s*32\) doctor; pause ;;", text, re.M)
    assert "menu_item 32 menu_32" in text
    for key in re.findall(r"\$\(t (doctor_[a-z_]+)", text):
        assert 'MSG_EN[%s]="' % key in text, "missing English string for %s" % key
        assert 'MSG_FA[%s]="' % key in text, "missing Persian string for %s" % key


# --------------------------------------------------------------------------- #
# Behaviour of the guard that builds ExecStart
# --------------------------------------------------------------------------- #

def test_start_command_is_plain_python_without_the_cli(tmp_path):
    out = call_helper(
        "manage.sh",
        'service_exec_start "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/main.py"',
        {"INSTALL_DIR": str(tmp_path), "PATH": str(tmp_path) + ":/usr/bin:/bin"},
    )
    assert out == "%s/venv/bin/python3 %s/main.py" % (tmp_path, tmp_path)


def test_start_command_uses_infisical_only_when_cli_and_link_exist(tmp_path):
    work = tmp_path / "bot"
    work.mkdir()
    bindir = tmp_path / "bin"
    bindir.mkdir()
    env = {"INSTALL_DIR": str(work), "PATH": "%s:/usr/bin:/bin" % bindir}
    call = 'service_exec_start "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/main.py"'

    # linked checkout, but no CLI -> plain python
    (work / ".infisical.json").write_text("{}", encoding="utf-8")
    out = call_helper("manage.sh", call, env)
    assert not out.startswith("infisical"), out

    # CLI and link -> wrapped
    cli = bindir / "infisical"
    cli.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    cli.chmod(cli.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    out = call_helper("manage.sh", call, env)
    assert out.startswith("infisical run --env=dev -- "), out
    assert out.endswith("/venv/bin/python3 %s/main.py" % work), out

    # opt-out wins even with the CLI present
    env["SHOPVPN_USE_INFISICAL"] = "0"
    out = call_helper("manage.sh", call, env)
    assert out == "%s/venv/bin/python3 %s/main.py" % (work, work), out


def _fake_sudo(bindir):
    """A `sudo` that just runs the command, so repairs can be tested unprivileged."""
    sudo = bindir / "sudo"
    sudo.write_text('#!/bin/sh\nexec "$@"\n', encoding="utf-8")
    sudo.chmod(0o755)


def _fake_python(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


def test_a_broken_unit_is_detected_and_repaired(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _fake_sudo(bindir)
    _fake_python(tmp_path / "venv" / "bin" / "python3")

    unit = tmp_path / "v2raybot.service"
    unit.write_text(
        "[Unit]\nDescription=V2Ray Telegram Sales Bot\n\n[Service]\n"
        "WorkingDirectory=%s\n"
        "ExecStart=infisical run --env=dev -- %s/venv/bin/python3 %s/main.py\n"
        "Restart=always\n\n[Install]\nWantedBy=multi-user.target\n"
        % (tmp_path, tmp_path, tmp_path),
        encoding="utf-8",
    )
    env = {"INSTALL_DIR": str(tmp_path), "PATH": "%s:/usr/bin:/bin" % bindir}

    missing = call_helper("manage.sh", 'unit_missing_binary "$UNIT"', dict(env, UNIT=str(unit)))
    assert missing == "infisical"

    env2 = dict(env, UNIT=str(unit), FALLBACK="%s/venv/bin/python3 %s/main.py" % (tmp_path, tmp_path))
    result = call_helper(
        "manage.sh",
        'if repair_unit_execstart "$UNIT" "$FALLBACK"; then echo REPAIRED; else echo FAILED; fi',
        env2,
    )
    assert result.splitlines()[-1] == "REPAIRED", result
    assert result.splitlines()[0] == "fixed", result

    text = unit.read_text(encoding="utf-8")
    assert re.search(r"^ExecStart=%s/venv/bin/python3 %s/main\.py$" % (re.escape(str(tmp_path)), re.escape(str(tmp_path))), text, re.M), text
    assert "Restart=always" in text, "the repair must not touch the rest of the unit"
    # the repaired unit is now runnable
    missing = call_helper("manage.sh", 'unit_missing_binary "$UNIT"', dict(env, UNIT=str(unit)))
    assert missing == ""


def test_repair_refuses_a_unit_it_cannot_make_runnable(tmp_path):
    """A unit pointing at a missing interpreter must not be "repaired" silently."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _fake_sudo(bindir)
    unit = tmp_path / "v2raybot.service"
    original = "[Service]\nExecStart=%s/venv/bin/python3 %s/main.py\n" % (tmp_path, tmp_path)
    unit.write_text(original, encoding="utf-8")

    result = call_helper(
        "manage.sh",
        'if repair_unit_execstart "$UNIT" "$FALLBACK"; then echo REPAIRED; else echo FAILED; fi',
        {"INSTALL_DIR": str(tmp_path), "PATH": "%s:/usr/bin:/bin" % bindir,
         "UNIT": str(unit), "FALLBACK": "%s/venv/bin/python3 %s/main.py" % (tmp_path, tmp_path)},
    )
    assert result.splitlines()[-1] == "FAILED", result
    assert unit.read_text(encoding="utf-8") == original, "a failed repair must change nothing"


def test_install_sh_writes_a_unit_systemd_can_execute(tmp_path):
    """End-to-end: the snippet install.sh runs must leave a runnable unit.

    This is the exact regression of 4.12.0, tested through the real installer
    code (with /etc/systemd redirected and sudo/systemctl stubbed) rather than
    through a copy of it.
    """
    install_dir = tmp_path / "v2ray_bot"
    unit_dir = tmp_path / "units"
    bindir = tmp_path / "bin"
    unit_dir.mkdir()
    bindir.mkdir()
    _fake_sudo(bindir)
    stub = bindir / "systemctl"
    stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stub.chmod(0o755)
    _fake_python(install_dir / "venv" / "bin" / "python3")
    (install_dir / "main.py").write_text('print("main")\n', encoding="utf-8")
    (install_dir / ".env").write_text("BOT_TOKEN=1:2\nOWNER_ID=1\n", encoding="utf-8")

    text = _read("install.sh")
    start = text.index('SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"')
    end = text.index('sudo systemctl enable "$SERVICE_NAME" > /dev/null 2>&1')
    snippet = text[start:end].replace("/etc/systemd/system", unit_dir.as_posix()).replace("\r", "")

    script = "\n".join([
        "set -euo pipefail",
        helpers_from("install.sh"),
        snippet,
    ])
    env = {
        "INSTALL_DIR": install_dir.as_posix(),
        "SERVICE_NAME": "v2raybot",
        "TOTAL_STEPS": "7",
        "PATH": "%s:/usr/bin:/bin" % bindir.as_posix(),
    }
    result = run_bash(script, env=env)
    assert result.returncode == 0, result.stdout + result.stderr

    unit = unit_dir / "v2raybot.service"
    assert unit.is_file(), "the installer did not write a unit"
    content = unit.read_text(encoding="utf-8")
    expected = "ExecStart=%s/venv/bin/python3 %s/main.py" % (install_dir.as_posix(), install_dir.as_posix())
    assert expected in content, content
    assert "ExecStart=infisical" not in content, content

    missing = call_helper(
        "install.sh", 'unit_missing_binary "$UNIT"', dict(env, UNIT=unit.as_posix())
    )
    assert missing == "", "the generated unit cannot be executed: %s" % missing


def test_unit_missing_binary_reports_a_missing_interpreter(tmp_path):
    unit = tmp_path / "v2raybot.service"
    unit.write_text(
        "[Service]\nExecStart=%s/venv/bin/python3 %s/main.py\n" % (tmp_path, tmp_path),
        encoding="utf-8",
    )
    env = {"INSTALL_DIR": str(tmp_path), "PATH": "/usr/bin:/bin", "UNIT": str(unit)}
    missing = call_helper("manage.sh", 'unit_missing_binary "$UNIT"', env)
    assert missing == "%s/venv/bin/python3" % tmp_path
