# Sync this fork with upstream (Shopvpn)

This file is the authoritative, reusable procedure for pulling new upstream work
into this fork **without breaking anything we changed ourselves**.

- fork: `https://github.com/amir12120/Shopvpn` (branch `main`)
- upstream: `https://github.com/mehdirafatpanah/Shopvpn`

## How to use this file

Give your coding agent (Freebuff, Codex, Cursor, Claude Code, ...) this one line:

> Read `SYNC_UPSTREAM.md` in the repo root and execute every step in it exactly.
> Start with Step 1 and show me the classification report; wait for my approval
> before merging anything.

Persian equivalent, if you prefer:

> فایل `SYNC_UPSTREAM.md` در ریشه‌ی ریپو را کامل بخوان و دقیقاً طبق همان اجرا کن؛
> اول گزارش مرحله‌ی ۱ را بده و قبل از merge منتظر تأیید من بمان.

The agent must read the whole file before touching anything. Everything below is
binding: if a step cannot be completed safely, the agent reports it instead of
guessing.

---

## 0. Environment and hard rules

- Repo root on this machine: `E:\Z\new shop\Shopvpn`, branch `main`.
- Helper Python: `PY="/e/Z/new shop/TEMp/shopvpn-venv/Scripts/python.exe"`.
  Prefix every Python/test command with `PYTHONUTF8=1`, otherwise Persian output
  crashes with a cp1252 error.
- Shell is Git Bash on Windows: bash syntax everywhere, never cmd.exe.
- `core.autocrlf=true`: the working tree is CRLF, repo blobs are LF. Never
  "fix" line endings and never include a line-ending-only diff.
- **Never execute `install.sh`, `manage.sh`, `update.sh`, `cleanup.sh`,
  `preflight.sh`, `setup_local_translation.sh`, or anything that touches
  systemd, apt, pip installs, or a live server.** Verify statically and with the
  test suite only.
- If `git status` is not clean at the start, stop and report. Never discard,
  stash, or overwrite changes you did not make.
- This is a released, user-installed product (v4.9.0+) running on Ubuntu 22.04
  with systemd, Argos/LibreTranslate offline translation and SQLite. A broken
  merge ships real damage to real servers. Be conservative and evidence-driven.

## 1. Investigate BEFORE changing anything

1. `git fetch upstream main`
2. `git log --oneline HEAD..upstream/main`
3. `git diff --stat HEAD...upstream/main`
4. Read the real upstream diffs for Python changes: `git diff HEAD...upstream/main -- '*.py'`
5. Write a short report classifying each upstream commit as one of:
   - `NEW PYTHON FEATURE`
   - `PYTHON BUGFIX`
   - `INSTALL / SCRIPT CHANGE` (reject)
   - `DOCS` (reject unless it documents a feature we take)
   - `CI` (reject)
6. State, before merging, which category you take and which you reject.
   Do not start the merge before presenting this plan.
7. If anything is ambiguous or destructive, ask. Do not improvise.

## 2. Protected files — the fork side ALWAYS wins

Upstream re-uploads its own older shell files on every merge. These never change:

- `install.sh`, `manage.sh`, `update.sh`, `preflight.sh`, `cleanup.sh`,
  `setup_local_translation.sh`, `check_upstream.sh`
  → **the install/update flow is never modified**
- everything under `.github/`
- everything under `tests/`
- `VERSION`
- `README.md`, `README.fa.md`, `INSTALL.md`, `INSTALL.fa.md` and any other docs
  (drop upstream's ru/zh READMEs; this project is fa/en only)
- `i18n_extra.py`, and `i18n.py` where it declares
  `SUPPORTED_LANGUAGES = ("fa", "en")` — never add a third language

Also: do not import upstream's donation / crypto-wallet lines.

## 3. Merge procedure

- `git merge --no-commit --no-ff upstream/main`
- Resolve conflicts deterministically in favour of the fork:
  `git checkout --ours install.sh manage.sh update.sh preflight.sh cleanup.sh setup_local_translation.sh check_upstream.sh VERSION README.md README.fa.md INSTALL.md INSTALL.fa.md i18n_extra.py`
  and restore `.github/` and `tests/` wholesale to the fork side.
- Accept upstream only for new/modified Python code (features, bug fixes).
- If upstream **deleted** a file the fork needs, do not delete it. Keep it and
  report the deletion.
- A new third-party dependency from upstream: add it to `requirements.txt`
  keeping the lean flags (`--no-cache-dir`, CPU torch index when relevant), and
  add an import assertion for it to the CI job's
  "Runtime project-module import (merged upstream features)" step. If the local
  venv cannot import it (for example `aiohttp` is missing locally), say so and
  let CI prove it instead of claiming success.
- No cosmetic reformatting, no import reordering, no "while I was here" edits.
  Keep every diff minimal and reviewable.

## 4. Pin new features in the integrity test

- Update `tests/test_merge_integrity.py`: append every newly added upstream
  module to `UPSTREAM_FEATURE_MODULES` and add **real wiring** assertions — the
  module must be imported and actually reachable from a handler / menu / DB
  path. File existence alone is not enough.
- If a new module is wired through a dispatcher or registry, find that edge and
  assert it too.

## 5. Fork improvements that MUST survive every merge

Verify each of these still holds after merging. They are already pinned in the
test suite; if one fails, fix the merge — never the test.

- `force_join.py`, `config_delivery.py`, `handlers_admin.py`: line 1 is
  `# -*- coding: utf-8 -*-`, with `from i18n import tr` **below** the docstring.
- `handlers_admin.py` contains `call.bot.send_message(uid, notification)`.
- `handlers_user.py` contains at least two `call.bot, db,` occurrences.
- `keyboards.py` contains exactly one `def blupal_settings_kb(`.
- `admin_panel/server.py` imports `is_language_enabled`.
- The `language_selected` migration exists.
- `setup_local_translation.sh` installs Argos models **as the service account**:
  `SERVICE_USER` resolved via `systemctl show -p User --value "$SERVICE_NAME"`
  plus `getent passwd`; `as_service_user` sets `HOME=$SERVICE_HOME` and unsets
  `XDG_DATA_HOME` / `XDG_CACHE_HOME` / `XDG_CONFIG_HOME`; the LibreTranslate
  unit sets `Environment=HOME=$SERVICE_HOME`. This is the fix that stopped
  `/root` from filling up with a duplicate copy of every model.
- `cleanup.sh` sweeps pip + Argos download caches for **all** relevant homes
  (caller, service account, `/root`) using `while IFS= read -r h` — a plain
  `for h in $LIST` breaks on paths containing spaces; it also removes stale
  `/tmp/{restore_,restore_full_,xui_restore_,qr_bg_,image_,media_}*` dirs and
  vacuums the journal with `journalctl --vacuum-size=` (`SHOPVPN_JOURNAL_MAX`,
  default 200M).
- `manage.sh` has `wait_for_service_ready()` / `restart_service_and_wait()`
  (three consecutive `systemctl is-active` polls, 30 s budget, prints journal
  lines on failure) and `update_bot()` runs in this order:
  fetch → pip → translation → cleanup.sh → restart-and-wait.
- `install.sh` writes the journald drop-in
  (`/etc/systemd/journald.conf.d/shopvpn-disk.conf`, `SystemMaxUse`,
  `SystemKeepFree=1G`, opt out with `SHOPVPN_SKIP_JOURNAL_LIMIT=1`) and has the
  `BOT_READY` readiness loop.

## 6. Quality gates — ALL must pass, never work around one

- `PYTHONUTF8=1 "$PY" -m pytest tests -q` (baseline: 96 passed)
- `PYTHONUTF8=1 "$PY" -m ruff check --select F821,F811,E9 .`
  (ruff ships in the helper venv; a bare `ruff` may be "command not found")
- `bash -n` on every `*.sh`, plus a scan for the shell-glue bug class:
  `grep -nE '^(fi|done|esac|else)[A-Za-z_"]' *.sh` must return nothing.
- `"$PY" -m compileall -q .`
- `"$PY" check_i18n_coverage.py` must **exit 0**. Every new uncovered Persian
  string needs an English entry in `i18n_extra.EXTRA_PHRASES` (write ZWNJ as
  `\u200c`). Never "fix" this by weakening the checker.
- The workflow YAML must still parse.
- Known traps to re-check after every merge: a doubled backslash, or a size
  regex that requires a trailing `B`, makes the journal-size parse print `-`.
- Never delete, skip, or weaken a test to get green. If a gate cannot run in
  this environment, report it as NOT RUN instead of claiming success.

## 7. Release

1. Bump `VERSION` (e.g. 4.9.1 → 4.10.0). The file is CRLF in the working copy —
   preserve that.
2. Commit message in English that explains **why** (which upstream commits and
   which features), not a restatement of the diff.
3. `git tag -a v<VERSION> -m "..."` and `git push origin main --tags`.
   Pushes sometimes do not land on the first attempt: retry with
   `timeout 200 git -c http.version=HTTP/1.1 push origin main`, then **prove** it
   landed via `git fetch origin main -q` and comparing `git rev-parse HEAD` with
   `git rev-parse origin/main`.
4. Create the GitHub release for that tag via the REST API
   (`Authorization: Bearer $PAT`, where `$PAT` comes from `git credential fill`
   — the long git PAT returns 401 on api.github.com).
5. Wait for CI: `Deploy Smoke Test` and `Cleanup Caches` must be green. Poll in
   short calls; a long poll can exceed the command timeout. If red, fix the
   cause, never suppress it.
6. Final check: `git status` clean, `VERSION` correct,
   `git rev-list --count HEAD..upstream/main` == 0.

## 8. Final report (short, factual)

- Which upstream commits/features came in, and what each one does.
- Which upstream changes were REJECTED and why.
- What was added to the tests and CI.
- Result of each quality gate, plus the CI run number/URL.
- Tag, release link, and confirmation that upstream behind == 0.
- Anything you could NOT do, stated plainly. Never invent success, never hide a
  failing check.
