#!/usr/bin/env bash
# Zephirum Verify — action step.
# Runs every matched .zeph file through zephirum-q; a file passes when
# the decision core returns a valid receipt (DECIDED / zero-unit). Any
# structural error, runtime fault or (optionally) UNKNOWN fails the job
# with the named reason. No output is fabricated (§12).
set -u
pass=0; fail=0; unknown=0; out_scope=0
failed_files=()

for pattern in ${ZEPHIRUM_FILES:-"examples/**/*.zeph katas/*.zeph"}; do
  # expand glob relative to workspace (bash globbing)
  matches=$(compgen -G "$pattern" 2>/dev/null || true)
  for f in $matches; do
    [ -f "$f" ] || continue
    out=$(zephirum-q "$f" --json 2>&1); rc=$?
    # classify the receipt honestly: DECIDED*, UNKNOWN, OUT_OF_SCOPE
    # (plugin §12 refusal with a named reason — a valid answer, not an
    # error), or STRUCTURAL_ERROR (crash / no parseable receipt)
    status=$(printf '%s' "$out" | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    print("STRUCTURAL_ERROR"); sys.exit()
if d.get("routed") is False:
    print("OUT_OF_SCOPE"); sys.exit()
print(d.get("status","NO_STATUS"))' 2>/dev/null || echo STRUCTURAL_ERROR)
    if [ $rc -ne 0 ] && [ "$status" != "OUT_OF_SCOPE" ] || [ "$status" = "STRUCTURAL_ERROR" ] || [ "$status" = "NO_STATUS" ]; then
      fail=$((fail+1)); failed_files+=("$f")
      echo "::error file=$f::zephirum-q failed — $status"
      printf '%s\n' "$out" | head -5
    elif [ "$status" = "UNKNOWN" ]; then
      unknown=$((unknown+1))
      if [ "${ZEPHIRUM_FAIL_UNKNOWN:-false}" = "true" ]; then
        fail=$((fail+1)); failed_files+=("$f")
        echo "::error file=$f::verdict UNKNOWN and fail-on-unknown is set"
      else
        echo "::warning file=$f::verdict UNKNOWN (evidence insufficient) — counted, not failed"
      fi
    elif [ "$status" = "OUT_OF_SCOPE" ]; then
      out_scope=$((out_scope+1))
      reason=$(printf '%s' "$out" | python3 -c '
import json,sys
d=json.load(sys.stdin); print(d.get("reason","?"))' 2>/dev/null || echo "?")
      echo "::warning file=$f::out of plugin scope (§12 honest refusal) — $reason"
    else
      pass=$((pass+1))
      echo "OK  $f — $status"
    fi
  done
done

echo ""
echo "ZEPHIRUM VERIFY: $pass decided, $out_scope out-of-scope (honest refusals), $unknown unknown, $fail failed"
if [ $fail -gt 0 ]; then
  echo "failed: ${failed_files[*]}"
  exit 1
fi
exit 0
