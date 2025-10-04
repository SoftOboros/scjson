#!/usr/bin/env bash
# Agent Name: ci-ruby-harness
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

set -uo pipefail

# Reference (SCION) and secondary (Ruby) commands can be overridden via env
REF_CMD=${REF_CMD:-"node tools/scion-runner/scion-trace.cjs"}
# Ensure secondary (Ruby) uses comparable normalization flags
SEC_CMD=${SEC_CMD:-"ruby/bin/scjson engine-trace --leaf-only --omit-delta --omit-transitions --ordering scion"}
EXTRA_FLAGS=${EXTRA_FLAGS:-"--leaf-only --omit-delta --omit-transitions --ordering scion"}

# Known-differences support (optionally loaded via --known)
declare -A KNOWN_DIFFS
KNOWN_FILE=""

load_known() {
  local file="$1"
  [[ -z "$file" ]] && return 0
  [[ -f "$file" ]] || die "Known-diffs file not found: $file"
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    # Format: <chart> [py-ref|ref-sec|any]
    local chart cat
    chart="$(echo "$line" | awk '{print $1}')"
    cat="$(echo "$line" | awk '{print $2}')"
    [[ -z "$cat" ]] && cat="any"
    KNOWN_DIFFS["$chart"]="$cat"
  done < "$file"
}

is_known_diff() {
  local chart="$1"; local code="$2"
  local cat="${KNOWN_DIFFS[$chart]:-}"
  if [[ -z "$cat" ]]; then
    return 1
  fi
  if [[ "$cat" == "any" ]]; then
    return 0
  fi
  if [[ "$code" -eq 1 && "$cat" == "py-ref" ]]; then
    return 0
  fi
  if [[ "$code" -eq 2 && "$cat" == "ref-sec" ]]; then
    return 0
  fi
  return 1
}

die() { echo "[ci-ruby-harness] $*" >&2; exit 1; }

find_events() {
  local chart="$1"
  local base="${chart%.*}"
  local candidate="${base}.events.jsonl"
  if [[ -f "$candidate" ]]; then
    echo "$candidate"
    return 0
  fi
  # Alternate naming in same dir (foo.scxml + foo.events.jsonl)
  local dir="$(dirname "$chart")"
  local stem="$(basename "$chart" | sed 's/\.[^.]*$//')"
  candidate="${dir}/${stem}.events.jsonl"
  if [[ -f "$candidate" ]]; then
    echo "$candidate"
    return 0
  fi
  die "No events file found for ${chart}"
}

run_one() {
  local chart="$1"
  local events
  events="$(find_events "$chart")"
  echo "[ci-ruby-harness] Comparing: $chart"
  set +e
  python py/exec_compare.py "$chart" \
    --events "$events" \
    --reference "$REF_CMD" \
    --secondary "$SEC_CMD" \
    $EXTRA_FLAGS
  local code=$?
  set -e
  if [[ $code -eq 0 ]]; then
    echo "[ci-ruby-harness] OK: $chart"
    PASS=$((PASS+1))
  elif [[ $code -eq 1 ]]; then
    if is_known_diff "$chart" 1; then
      echo "[ci-ruby-harness] KNOWN(py-ref): $chart"
      KNOWN_PY_REF=$((KNOWN_PY_REF+1))
    else
      echo "[ci-ruby-harness] FAIL(py-ref): $chart"
      FAIL_PY_REF=$((FAIL_PY_REF+1))
    fi
  elif [[ $code -eq 2 ]]; then
    if is_known_diff "$chart" 2; then
      echo "[ci-ruby-harness] KNOWN(ref-sec): $chart"
      KNOWN_REF_SEC=$((KNOWN_REF_SEC+1))
    else
      echo "[ci-ruby-harness] FAIL(ref-sec): $chart"
      FAIL_REF_SEC=$((FAIL_REF_SEC+1))
    fi
  else
    echo "[ci-ruby-harness] ERROR(code=$code): $chart"
    FAIL_OTHER=$((FAIL_OTHER+1))
  fi
}

main() {
  local list_file=""
  local charts=()
  PASS=0
  FAIL_PY_REF=0
  FAIL_REF_SEC=0
  FAIL_OTHER=0
  KNOWN_PY_REF=0
  KNOWN_REF_SEC=0

  # Parse optional --list/-f argument; remaining args are charts/globs
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --list|-f)
        shift
        list_file="${1:-}"
        [[ -z "$list_file" ]] && die "--list requires a file path"
        shift
        ;;
      --known)
        shift
        KNOWN_FILE="${1:-}"
        [[ -z "$KNOWN_FILE" ]] && die "--known requires a file path"
        shift
        ;;
      *)
        charts+=("$1")
        shift
        ;;
    esac
  done

  # Default known-diffs file when present (auto-load to keep CI green)
  if [[ -z "$KNOWN_FILE" && -f scripts/ci_ruby_known_diffs.txt ]]; then
    KNOWN_FILE="scripts/ci_ruby_known_diffs.txt"
  fi

  # Load known diffs if provided or defaulted
  if [[ -n "$KNOWN_FILE" ]]; then
    load_known "$KNOWN_FILE"
  fi

  # If a list file is provided, append its entries
  if [[ -n "$list_file" ]]; then
    [[ -f "$list_file" ]] || die "List file not found: $list_file"
    while IFS= read -r line; do
      # skip blanks and comments
      [[ -z "$line" || "$line" =~ ^# ]] && continue
      charts+=("$line")
    done < "$list_file"
  fi

  # If no charts specified, use defaults
  if [[ ${#charts[@]} -eq 0 ]]; then
    charts=(
      tests/exec/toggle.scxml
      tests/exec/membership.scxml
      tests/exec/invoke_inline.scxml
      tests/exec/parallel_invoke.scxml
      tests/exec/invoke_timer.scxml
      tests/exec/parallel_history_invoke.scxml
      tests/exec/history_reentry.scxml
    )
  fi

  # Expand globs and run
  for pattern in "${charts[@]}"; do
    # shellcheck disable=SC2086
    for chart in $pattern; do
      # Create a per-chart workdir to retain artifacts for inspection
      workdir="$(mktemp -d -t scjson-exec-XXXXXX)"
      export WORKDIR_OVERRIDE="$workdir"
      run_one "$chart"
      echo "[ci-ruby-harness] Artifacts: $workdir"
    done
  done

  echo "[ci-ruby-harness] Summary: OK=$PASS py-ref=$FAIL_PY_REF ref-sec=$FAIL_REF_SEC other=$FAIL_OTHER known(py-ref)=$KNOWN_PY_REF known(ref-sec)=$KNOWN_REF_SEC"
  if [[ $FAIL_PY_REF -gt 0 || $FAIL_REF_SEC -gt 0 || $FAIL_OTHER -gt 0 ]]; then
    exit 1
  fi
}

main "$@"
