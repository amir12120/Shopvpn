# -*- coding: utf-8 -*-
"""`sp update` must run the real update pipeline and tell the truth about it.

These tests run the shipped `sp` script and the real `manage.sh` inside a
throwaway install. `git`, `sudo`, `systemctl`, `journalctl`, `sleep` and `curl`
are stubs on PATH, so no server, network, systemd or real package install is
touched. They prove the shortcut really walks the documented pipeline in order,
and that its exit status is non-zero when the bot does not come back up — the
property that makes `sp update && ...` safe in a deploy script.
"""
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASH = shutil.which("bash")

pytestmark = pytest.mark.skipif(BASH is None, reason="bash is required")

STUBS = {
    "git": '#!/usr/bin/env bash\necho "git $*" >> "$SP_TEST_LOG"\nexit 0\n',
    "sudo": '#!/usr/bin/env bash\necho "sudo $*" >> "$SP_TEST_LOG"\nexec "$@"\n',
    "systemctl": (
        '#!/usr/bin/env bash\n'
        'echo "systemctl $*" >> "$SP_TEST_LOG"\n'
        'case "$1" in\n'
        '  list-units) exit 0 ;;\n'
        '  is-active) exit "${SP_TEST_ACTIVE:-0}" ;;\n'
        'esac\n'
        'exit 0\n'
    ),
    "journalctl": '#!/usr/bin/env bash\nexit 0\n',
    "sleep": '#!/usr/bin/env bash\nexit 0\n',
    "curl": '#!/usr/bin/env bash\nexit 1\n',
}


def _write(path, text, executable=False):
    path.write_text(text, encoding="utf-8")
    os.chmod(path, 0o755 if executable else 0o644)
    return path


def _install(tmp_path):
    install = tmp_path / "install"
    (install / "venv" / "bin").mkdir(parents=True)
    (install / ".git").mkdir()
    _write(install / "main.py", "print('stub')\n")
    _write(install / "VERSION", "9.9.9\n")
    _write(
        install / "venv" / "bin" / "activate",
        'pip() { echo "pip $*" >> "$SP_TEST_LOG"; }\ndeactivate() { :; }\n',
    )
    _write(
        install / "setup_local_translation.sh",
        '#!/usr/bin/env bash\necho "translation" >> "$SP_TEST_LOG"\n',
        executable=True,
    )
    _write(
        install / "cleanup.sh",
        '#!/usr/bin/env bash\necho "cleanup" >> "$SP_TEST_LOG"\n',
        executable=True,
    )
    # The shipped scripts, not copies of their logic.
    for name in ("manage.sh", "sp"):
        shutil.copy(os.path.join(ROOT, name), install / name)
    return install


@pytest.fixture()
def sandbox(tmp_path):
    install = _install(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in STUBS.items():
        _write(bin_dir / name, body, executable=True)

    home = tmp_path / "home"
    home.mkdir()

    env = dict(os.environ)
    env.update({
        "HOME": str(home),
        "PATH": str(bin_dir) + os.pathsep + env.get("PATH", ""),
        "SP_TEST_LOG": str(tmp_path / "log"),
        "SP_TEST_ACTIVE": "0",
        "SHOPVPN_DIR": str(install),
        "PYTHONUTF8": "1",
    })
    return install, tmp_path / "log", env


def _run(sandbox, args, active="0"):
    install, log, env = sandbox
    env = dict(env)
    env["SP_TEST_ACTIVE"] = active
    if log.exists():
        log.unlink()
    return subprocess.run(
        [BASH, str(install / "sp"), *args],
        cwd=str(install),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _lines(log):
    if not log.exists():
        return []
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line]


def _index(lines, prefix):
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            return i
    raise AssertionError("%r never ran; log was %r" % (prefix, lines))


def test_sp_update_runs_the_whole_pipeline_in_order(sandbox):
    result = _run(sandbox, ["update"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Bot updated." in result.stdout

    lines = _lines(sandbox[1])
    fetch = _index(lines, "git -C ")
    torch = _index(lines, "pip install")                       # CPU torch first
    reqs = max(i for i, line in enumerate(lines) if line.startswith("pip install"))
    assert torch < reqs, lines
    translation = _index(lines, "translation")
    cleanup = _index(lines, "cleanup")
    restart = _index(lines, "systemctl restart v2raybot")

    assert fetch < reqs < translation < cleanup < restart, lines
    # The readiness check, not just `systemctl restart`, decides success.
    polls = [i for i, line in enumerate(lines)
             if line == "systemctl is-active --quiet v2raybot"]
    assert len(polls) >= 3, lines
    assert min(polls) > restart, lines


def test_sp_update_fails_when_the_bot_does_not_stay_up(sandbox):
    result = _run(sandbox, ["update"], active="3")
    assert result.returncode == 1
    assert "did not stay up" in result.stdout + result.stderr


def test_sp_update_refuses_when_nothing_is_installed(tmp_path):
    env = dict(os.environ)
    env["SHOPVPN_DIR"] = str(tmp_path / "missing")
    result = subprocess.run(
        [BASH, os.path.join(ROOT, "sp"), "update"],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 1
    assert "not installed" in result.stderr


def test_sp_version_help_and_unknown_commands(sandbox):
    version = _run(sandbox, ["version"])
    assert version.returncode == 0
    assert "9.9.9" in version.stdout

    help_text = _run(sandbox, ["help"])
    assert help_text.returncode == 0
    assert "sp update" in help_text.stdout

    unknown = _run(sandbox, ["frobnicate"])
    assert unknown.returncode == 2
    assert "Unknown command" in unknown.stderr


def test_install_sh_installs_both_cli_names():
    with open(os.path.join(ROOT, "install.sh"), encoding="utf-8") as fh:
        text = fh.read()
    assert 'for cli in "$CLI_NAME" sp; do' in text
    assert '"/usr/local/bin/$cli"' in text
    assert 'export SHOPVPN_DIR="\\$INSTALL_DIR"' in text
    assert "sp update" in text


@pytest.mark.parametrize("name", ["README.md", "README.fa.md", "INSTALL.md"])
def test_the_short_command_is_documented(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        assert "sp update" in fh.read(), name


def test_sp_stays_syntactically_valid():
    result = subprocess.run(
        [BASH, "-n", os.path.join(ROOT, "sp")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert os.path.getsize(os.path.join(ROOT, "sp")) > 0
