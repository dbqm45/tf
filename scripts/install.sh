#!/bin/sh
# Instaluje komendę `tf` (launcher fabryki) na macOS i Linuksie. Fabrykę w projekcie instaluje potem `tf install`.
#
#   curl -fsSL <adres tego pliku> | sh
#   sh scripts/install.sh                      # z klonu repozytorium
#
# Zmienne (opcjonalne):
#   TF_REPO    repozytorium fabryki (domyślnie https://github.com/dbqm45/tf.git; prywatne wymaga dostępu w gicie)
#   TF_BIN     katalog na komendę `tf` (domyślnie ~/.local/bin)
#   TF_PYTHON  polecenie Pythona 3.9+ (domyślnie python3, potem python)
#   TF_GIT     polecenie gita (domyślnie git)
# Opis: docs/setup.md. Skrypt niczego nie instaluje poza plikiem `tf` w TF_BIN; nie zmienia PATH ani profilu powłoki.
set -eu

REPO="${TF_REPO:-https://github.com/dbqm45/tf.git}"
BIN="${TF_BIN:-$HOME/.local/bin}"
GIT="${TF_GIT:-git}"

fail() { printf '✗ %s\n' "$1" >&2; exit 1; }

# Python 3.9+
PY=""
for c in ${TF_PYTHON:-python3 python}; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || fail "Brak Pythona 3.9+ (sprawdzono: ${TF_PYTHON:-python3 python}). Zainstaluj go: https://www.python.org/downloads/ (macOS: brew install python, Debian/Ubuntu: sudo apt install python3)."

# git
command -v "$GIT" >/dev/null 2>&1 || fail "Brak gita (${GIT}). Zainstaluj go: https://git-scm.com/downloads (macOS: xcode-select --install albo brew install git, Debian/Ubuntu: sudo apt install git)."

TMP="$(mktemp -d "${TMPDIR:-/tmp}/tf-install.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT INT TERM

printf '→ Pobieram fabrykę z %s\n' "$REPO"
"$GIT" clone -q --depth 1 "$REPO" "$TMP/tf" || fail "Nie udało się pobrać $REPO. Prywatne repozytorium wymaga dostępu w gicie (gh auth login albo klucz SSH, wtedy TF_REPO=git@github.com:dbqm45/tf.git)."

"$PY" "$TMP/tf/core/factory/tf.py" --install-launcher --repo "$REPO" --bin "$BIN" || fail "Instalacja launchera nie powiodła się."

case ":$PATH:" in
  *":$BIN:"*) ;;
  *) printf 'ℹ Dodaj %s do PATH, np. w ~/.zshrc albo ~/.bashrc:\n  export PATH="%s:$PATH"\n' "$BIN" "$BIN" ;;
esac
printf '✓ Gotowe. W katalogu projektu: tf install\n'
