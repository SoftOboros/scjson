#!/usr/bin/env bash
# Agent Name: ci-ruby-harness
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

set -euo pipefail

# Reference (SCION) and secondary (Ruby) commands can be overridden via env
REF_CMD=${REF_CMD:-"node tools/scion-runner/scion-trace.cjs"}
SEC_CMD=${SEC_CMD:-"ruby/bin/scjson engine-trace --omit-delta"}
EXTRA_FLAGS=${EXTRA_FLAGS:-"--leaf-only --omit-delta"}

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
  python py/exec_compare.py "$chart" \
    --events "$events" \
    --reference "$REF_CMD" \
    --secondary "$SEC_CMD" \
    $EXTRA_FLAGS
}

main() {
  if [[ $# -gt 0 ]]; then
    for chart in "$@"; do
      run_one "$chart"
    done
    return 0
  fi

  # Default focused suite
  charts=(
    tests/exec/toggle.scxml
    tests/exec/membership.scxml
    tests/exec/invoke_inline.scxml
    tests/exec/parallel_invoke.scxml
    tests/exec/invoke_timer.scxml
    tests/exec/parallel_history_invoke.scxml
    tests/exec/history_reentry.scxml
  )
  for chart in "${charts[@]}"; do
    run_one "$chart"
  done
}

main "$@"

