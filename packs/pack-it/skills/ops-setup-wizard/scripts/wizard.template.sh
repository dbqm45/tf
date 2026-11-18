#!/usr/bin/env bash
# Setup wizard — claude-team-factory template (skill ops-setup-wizard).
# Run by a HUMAN on their own computer. The agent writes only the stages below the ETAPY marker.
# The library above the marker is the same in every wizard — do not edit it by hand.
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env}"
TOTAL_STAGES=0          # the agent sets the number of stages
CURRENT_STAGE=0
START_TS=$(date +%s)
DONE=()
SKIPPED=()
MANUAL=()

if [ -t 1 ]; then B=$'\e[1m'; D=$'\e[2m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[0m'; else B=""; D=""; G=""; Y=""; R=""; fi

say()  { printf '%s\n' "$*"; }
step() { printf '  %s→%s %s\n' "$B" "$R" "$*"; }
warn() { printf '%s! %s%s\n' "$Y" "$*" "$R"; }

stage() {
  CURRENT_STAGE=$((CURRENT_STAGE + 1))
  if [ -t 1 ]; then clear; fi
  local elapsed=$(( $(date +%s) - START_TS )) left=""
  if [ "$CURRENT_STAGE" -gt 1 ]; then
    local per=$(( elapsed / (CURRENT_STAGE - 1) ))
    left=" · about $(( (per * (TOTAL_STAGES - CURRENT_STAGE + 1) + 59) / 60 )) min left"
  fi
  printf '%sStage %d/%d%s%s\n%s%s%s\n\n' "$D" "$CURRENT_STAGE" "$TOTAL_STAGES" "$left" "$R" "$B" "$1" "$R"
}

pause() { read -r -p "${D}Press Enter to continue…${R} " _ </dev/tty; }

confirm() {  # confirm "Question?" → 0 = yes
  local a; read -r -p "$1 [y/N] " a </dev/tty
  [[ "$a" =~ ^[tTyY] ]]
}

open_url() {
  say "  ${B}Open:${R} $1"
  if command -v wslview >/dev/null 2>&1; then wslview "$1" >/dev/null 2>&1 || true
  elif grep -qi microsoft /proc/version 2>/dev/null && command -v cmd.exe >/dev/null 2>&1; then cmd.exe /c start "" "$1" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1 && [ "$(uname)" = "Darwin" ]; then open "$1" || true
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$1" >/dev/null 2>&1 || true
  fi
}

env_get() {  # value from ENV_FILE (without quotes) or an empty string
  [ -f "$ENV_FILE" ] || return 0
  local line; line=$(grep -E "^$1=" "$ENV_FILE" | tail -n 1 || true)
  line=${line#*=}
  if [[ "$line" == \"*\" ]]; then
    line=${line:1:${#line}-2}; line=${line//\\\"/\"}; line=${line//\\\\/\\}
  fi
  printf '%s' "$line"
}

ask() {  # ask VARIABLE "Question" — defaults to the value from .env
  local def; def=$(env_get "$1"); local v
  read -r -p "  $2${def:+ [$def]}: " v </dev/tty
  printf -v "$1" '%s' "${v:-$def}"
}

ask_secret() {  # ask_secret VARIABLE "Question" — input without echo; Enter keeps the current value
  local def; def=$(env_get "$1"); local v
  read -r -s -p "  $2${def:+ [Enter = keep]}: " v </dev/tty; printf '\n'
  printf -v "$1" '%s' "${v:-$def}"
}

write_env() {  # write_env KEY value — appends or replaces (idempotent)
  local key=$1 val=$2 tmp
  if [[ ! "$val" =~ ^[A-Za-z0-9_./:@+-]*$ ]]; then val=${val//\\/\\\\}; val="\"${val//\"/\\\"}\""; fi
  touch "$ENV_FILE"; chmod 600 "$ENV_FILE" 2>/dev/null || true
  tmp=$(mktemp)
  grep -vE "^$key=" "$ENV_FILE" >"$tmp" || true
  printf '%s=%s\n' "$key" "$val" >>"$tmp"
  cat "$tmp" >"$ENV_FILE"; rm -f "$tmp"
  step "saved $key in $ENV_FILE"
}

gh_ok() { command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; }

set_secret() {  # set_secret NAME value — GitHub Actions secret (value via stdin, not in arguments)
  if gh_ok; then printf '%s' "$2" | gh secret set "$1" >/dev/null && step "set secret $1"
  else MANUAL+=("GitHub secret $1 (gh not logged in)"); warn "gh unavailable — set secret $1 manually"; fi
}

set_var() {  # set_var NAME value — GitHub Actions variable (plain)
  if gh_ok; then gh variable set "$1" --body "$2" >/dev/null && step "set variable $1"
  else MANUAL+=("GitHub variable $1"); warn "gh unavailable — set variable $1 manually"; fi
}

done_stage() { DONE+=("$1"); }
skip_stage() { SKIPPED+=("$1"); }

summary() {
  if [ -t 1 ]; then clear; fi
  say "${B}Summary${R}"
  local x
  for x in "${DONE[@]+"${DONE[@]}"}"; do say "  ${G}✓${R} $x"; done
  for x in "${SKIPPED[@]+"${SKIPPED[@]}"}"; do say "  ${Y}–${R} skipped: $x"; done
  for x in "${MANUAL[@]+"${MANUAL[@]}"}"; do say "  ${Y}!${R} to do manually: $x"; done
  say ""; say "Running it again fills in the saved values as defaults."
}

trap 'printf "\nInterrupted. Run it again — the saved values will be filled in.\n"' INT

### ETAPY ### — below, the agent writes the stages (example to be replaced)
TOTAL_STAGES=1

stage "Example: API key for service X"
step "Panel → Developers → API keys → Reveal test key → copy"
open_url "https://example.com/dashboard/api-keys"
ask_secret X_API_KEY "Paste the test key"
write_env X_API_KEY "$X_API_KEY"
if confirm "Does CI need this key too?"; then set_secret X_API_KEY "$X_API_KEY"; fi
done_stage "API key for service X"

summary
