#!/usr/bin/env python3
"""Run the calibrated citation audit (ROADMAP project 1).

Modes:
  --replay (default)  Verify cached responses in audit/responses/ against the
                      current state+questions; fail loudly on drift; then
                      write analysis to audit/results.md + audit/results.json.
                      Needs no key.
  --live              Fetch one response per fixture from the TypeSafe API and
                      cache it. Requires TYPESAFE_API_KEY in the environment;
                      refuses with a clear error when unset. Never prints,
                      logs or stores the key or request headers.

Examples:
  python3 audit/run_audit.py --replay
  TYPESAFE_API_KEY="$(cat <keyfile>)" python3 audit/run_audit.py --live

Stdlib only. No key is read, printed or stored except from the environment
in --live mode for the Authorization header of that process.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit import analyze as A
from audit import client as C
from audit import state as S

RESULTS_MD = ROOT / "audit" / "results.md"
RESULTS_JSON = ROOT / "audit" / "results.json"


def cmd_replay() -> int:
    fixtures = S.load_fixtures()
    try:
        pairs = C.replay_all(fixtures)
    except FileNotFoundError as exc:
        print(f"replay: no cached response yet ({exc.filename}); "
              f"nothing to analyze. Live run pending review.")
        return 2
    records = A.to_records(pairs)
    metrics = A.compute_metrics(records)
    A.write_results(metrics, RESULTS_MD, RESULTS_JSON)
    print(A.render_markdown(metrics))
    print(f"wrote {RESULTS_MD} and {RESULTS_JSON}")
    return 0


def cmd_live() -> int:
    fixtures = S.load_fixtures()
    try:
        paths = C.live_all(fixtures)
    except C.LiveRefusedError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    for path in paths:
        print(f"cached {path}")
    return cmd_replay()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Citation audit runner")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--replay", action="store_true",
                       help="verify cache and analyze (default, no key)")
    group.add_argument("--live", action="store_true",
                       help="fetch live responses (needs TYPESAFE_API_KEY)")
    args = parser.parse_args(argv)
    if args.live:
        return cmd_live()
    return cmd_replay()


if __name__ == "__main__":
    raise SystemExit(main())
