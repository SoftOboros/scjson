#!/usr/bin/env bash
# Agent Name: ruby-engine-wrapper
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

set -euo pipefail

# Parse args, capture input path and strip --xml (we will pre-convert if needed)
args=()
input=""
skip_next=0
for ((i=1; i<=$#; i++)); do
  arg="${!i}"
  if [[ $skip_next -eq 1 ]]; then
    skip_next=0
    continue
  fi
  case "$arg" in
    -I|--input)
      # capture next value as input
      j=$((i+1))
      input="${!j:-}"
      args+=("$arg")
      args+=("__INPUT_PLACEHOLDER__")
      skip_next=1
      ;;
    --xml)
      # drop
      ;;
    *)
      args+=("$arg")
      ;;
  esac
done

if [[ -z "$input" ]]; then
  echo "[ruby-engine-wrapper] Missing --input/-I path" >&2
  exit 2
fi

resolved_input="$input"
tmpfile=""
if [[ "$input" != *.scjson ]]; then
  # Pre-convert SCXML to scjson via Python CLI
  workdir="$(mktemp -d -t rbwrap-XXXXXX)"
  trap 'rm -rf "$workdir"' EXIT
  tmpfile="$workdir/converted.scjson"
  if ! python -m scjson.cli json "$input" -o "$tmpfile" >/dev/null 2>&1; then
    # Fallback to invoking the CLI script directly within the repo
    if ! python py/scjson/cli.py json "$input" -o "$tmpfile" >/dev/null 2>&1; then
      echo "[ruby-engine-wrapper] Python conversion failed for $input" >&2
      exit 3
    fi
  fi
  resolved_input="$tmpfile"
fi

# Replace placeholder with resolved input
final_args=()
for a in "${args[@]}"; do
  if [[ "$a" == "__INPUT_PLACEHOLDER__" ]]; then
    final_args+=("$resolved_input")
  else
    final_args+=("$a")
  fi
done

exec ruby/bin/scjson engine-trace "${final_args[@]}"
