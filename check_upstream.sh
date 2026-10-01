#!/usr/bin/env bash
# ============================================================================
# check_upstream.sh — compare this fork with the upstream project.
#
# Upstream: mehdirafatpanah/Shopvpn  (the original project this fork is based
# on). Run this any time to see whether the original source has changes that
# this fork does not have yet.
#
#   bash check_upstream.sh
#
# It only fetches and reports; it never changes your files. Review the listed
# commits/files and port only the changes that keep the lean, easy install and
# run behaviour of this fork.
#
# Environment knobs:
#   SHOPVPN_UPSTREAM_URL     override the upstream git URL
#   SHOPVPN_UPSTREAM_BRANCH  override the upstream branch (default: main)
# ============================================================================
set -euo pipefail

UPSTREAM_URL="${SHOPVPN_UPSTREAM_URL:-https://github.com/mehdirafatpanah/Shopvpn.git}"
UPSTREAM_BRANCH="${SHOPVPN_UPSTREAM_BRANCH:-main}"
REMOTE="upstream"

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "This is not a git checkout. Clone the repository first." >&2
    exit 1
fi

if git remote get-url "$REMOTE" >/dev/null 2>&1; then
    git remote set-url "$REMOTE" "$UPSTREAM_URL"
else
    git remote add "$REMOTE" "$UPSTREAM_URL"
fi

echo "🔎 Comparing this fork with upstream: $UPSTREAM_URL ($UPSTREAM_BRANCH)"
echo "Fetching upstream..."
git fetch --quiet "$REMOTE" "$UPSTREAM_BRANCH"

REF="$REMOTE/$UPSTREAM_BRANCH"
BEHIND="$(git rev-list --count "HEAD..$REF")"

echo "Upstream commits not in this fork: $BEHIND"
if [ "$BEHIND" = "0" ]; then
    echo "✅ This fork already contains every upstream change."
    exit 0
fi

echo ""
echo "New upstream commits:"
git log --oneline --no-merges "HEAD..$REF"

echo ""
echo "Files changed upstream (relative to the common base):"
git diff --stat "HEAD...$REF" || true

echo ""
echo "Review the list above and port only the changes that keep this fork's"
echo "easy, disk-lean install and run behaviour intact."
