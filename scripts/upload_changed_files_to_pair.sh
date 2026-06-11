#!/usr/bin/env bash
set -euo pipefail

REMOTE_USER="ratchev"
REMOTE_HOST="ratchev.pairserver.com"
REMOTE_ROOT="public_html"
KEY_FILE="${HOME}/.ssh/id_ed25519_pair_ratchev"

usage() {
  cat <<'USAGE'
Usage:
  scripts/upload_changed_files_to_pair.sh [--changed|--restaurants|--all]

Modes:
  --changed      Upload modified, staged, and untracked files under public/ (default).
  --restaurants  Upload the restaurant page, assets, and data JSON.
  --all          Upload every tracked file under public/.

Environment overrides:
  PAIR_REMOTE_USER, PAIR_REMOTE_HOST, PAIR_REMOTE_ROOT, PAIR_KEY_FILE
USAGE
}

REMOTE_USER="${PAIR_REMOTE_USER:-$REMOTE_USER}"
REMOTE_HOST="${PAIR_REMOTE_HOST:-$REMOTE_HOST}"
REMOTE_ROOT="${PAIR_REMOTE_ROOT:-$REMOTE_ROOT}"
KEY_FILE="${PAIR_KEY_FILE:-$KEY_FILE}"

mode="changed"
if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi

if [[ $# -eq 1 ]]; then
  case "$1" in
    --changed) mode="changed" ;;
    --restaurants) mode="restaurants" ;;
    --all) mode="all" ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Missing SSH key: $KEY_FILE" >&2
  exit 1
fi

is_safe_public_file() {
  local path="$1"
  [[ "$path" == public/* ]] || return 1
  [[ -f "$path" ]] || return 1
  [[ "$path" != public/WEBALIZER_REPORTS/* ]] || return 1
  [[ "$path" != public/ratchev.pairserver.com/* ]] || return 1
  [[ "$path" != *.env ]] || return 1
}

quote_sftp_path() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '"%s"' "$value"
}

append_file() {
  local path="$1"
  if is_safe_public_file "$path"; then
    files+=("$path")
  else
    skipped+=("$path")
  fi
}

files=()
skipped=()

case "$mode" in
  restaurants)
    append_file "public/restaurants.html"
    append_file "public/assets/js/restaurants.js"
    append_file "public/assets/css/site.css"
    append_file "public/data/restaurants.json"
    ;;
  all)
    while IFS= read -r -d '' path; do
      append_file "$path"
    done < <(git ls-files -z -- public)
    ;;
  changed)
    while IFS= read -r -d '' path; do
      append_file "$path"
    done < <(
      {
        git diff --name-only -z --diff-filter=ACMRT HEAD -- public
        git ls-files --others --exclude-standard -z -- public
      } | sort -zu
    )
    ;;
esac

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No uploadable public files found for mode: $mode"
  if [[ ${#skipped[@]} -gt 0 ]]; then
    printf 'Skipped:\n'
    printf '  %s\n' "${skipped[@]}"
  fi
  exit 0
fi

batch_file="$(mktemp "${TMPDIR:-/tmp}/pair-upload.XXXXXX.sftp")"
trap 'rm -f "$batch_file"' EXIT

{
  printf 'cd %s\n' "$(quote_sftp_path "$REMOTE_ROOT")"

  dirs=()
  for path in "${files[@]}"; do
    remote_path="${path#public/}"
    remote_dir="$(dirname "$remote_path")"
    if [[ "$remote_dir" != "." ]]; then
      current=""
      IFS='/' read -r -a parts <<< "$remote_dir"
      for part in "${parts[@]}"; do
        current="${current:+$current/}$part"
        dirs+=("$current")
      done
    fi
  done

  if [[ ${#dirs[@]} -gt 0 ]]; then
    printf '%s\n' "${dirs[@]}" | sort -u | while IFS= read -r dir; do
      printf -- '-mkdir %s\n' "$(quote_sftp_path "$dir")"
    done
  fi

  for path in "${files[@]}"; do
    remote_path="${path#public/}"
    printf 'put %s %s\n' "$(quote_sftp_path "$path")" "$(quote_sftp_path "$remote_path")"
  done
  printf 'bye\n'
} > "$batch_file"

echo "Uploading ${#files[@]} file(s) to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_ROOT}"
printf '  %s\n' "${files[@]}"

sftp \
  -i "$KEY_FILE" \
  -o PreferredAuthentications=publickey \
  -b "$batch_file" \
  "${REMOTE_USER}@${REMOTE_HOST}"

if [[ ${#skipped[@]} -gt 0 ]]; then
  printf 'Skipped:\n'
  printf '  %s\n' "${skipped[@]}"
fi
