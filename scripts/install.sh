#!/bin/sh
# Installs the `tf` command (the factory launcher) on macOS and Linux. `tf install` then installs the factory
# in a project.
#
#   curl -fsSL <url of this file> | sh
#   sh scripts/install.sh                      # from a clone of the repository
#
# Variables (optional):
#   TF_REPO    factory repository (default https://github.com/dbqm45/tf.git; a private one needs git access)
#   TF_BIN     directory for the `tf` command (default ~/.local/bin)
#   TF_PYTHON  Python 3.9+ command (default python3, then python)
#   TF_GIT     git command (default git)
# See docs/setup.md. The script installs only the `tf` file in TF_BIN; it does not change PATH or shell profiles.
# ASCII only: the same messages must read correctly in any terminal encoding.
set -eu

REPO="${TF_REPO:-https://github.com/dbqm45/tf.git}"
BIN="${TF_BIN:-$HOME/.local/bin}"
GIT="${TF_GIT:-git}"

fail() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }

# Python 3.9+
PY=""
for c in ${TF_PYTHON:-python3 python}; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || fail "Python 3.9+ not found (tried: ${TF_PYTHON:-python3 python}). Install it: https://www.python.org/downloads/ (macOS: brew install python, Debian/Ubuntu: sudo apt install python3)."

# git
command -v "$GIT" >/dev/null 2>&1 || fail "git not found (${GIT}). Install it: https://git-scm.com/downloads (macOS: xcode-select --install or brew install git, Debian/Ubuntu: sudo apt install git)."

TMP="$(mktemp -d "${TMPDIR:-/tmp}/tf-install.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT INT TERM

printf '> Downloading the factory from %s\n' "$REPO"
"$GIT" clone -q --depth 1 "$REPO" "$TMP/tf" || fail "Could not download $REPO. A private repository needs git access (gh auth login, or an SSH key with TF_REPO=git@github.com:dbqm45/tf.git)."

PYTHONIOENCODING=utf-8 "$PY" "$TMP/tf/core/factory/tf.py" --install-launcher --repo "$REPO" --bin "$BIN" || fail "Installing the launcher failed."

case ":$PATH:" in
  *":$BIN:"*) ;;
  *) printf 'Note: add %s to PATH, e.g. in ~/.zshrc or ~/.bashrc:\n  export PATH="%s:$PATH"\n' "$BIN" "$BIN" ;;
esac
printf 'Done. In your project directory run: tf install\n'
