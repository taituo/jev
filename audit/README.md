# Audit harness (ROADMAP project 1)

Offline harness for the calibrated citation audit. No live call has been
made; `audit/responses/` holds no responses yet (live run pending review).

## Layout

```text
audit/
  state.py            build request state from fixtures + section slices
  questions.py        the four questions (single reviewable file)
  client.py           replay / live / Fake clients + cache format + hash check
  analyze.py          metrics from cached responses (stdlib only)
  run_audit.py        CLI entry point
  PREREGISTRATION.md  locked expectations (do not edit after live responses)
  responses/.gitkeep  placeholder; one <id>.json per fixture after a live run
  results.md / results.json   written by --replay once responses exist
```

Live path needs no third-party SDK: it POSTs stdlib-Urllib JSON to
`POST https://api.typesafe.ai/v1/systemone`
(`{"model": "jev-latest", "state": {...}, "questions": {...}}`).
Replay and analysis are stdlib-only.

## Replay (no key)

```sh
python3 audit/run_audit.py --replay
# or: python3 audit/run_audit.py   (replay is the default)
```

Verifies each cached response's request hash against the current
state+questions, fails loudly on drift, then writes `audit/results.md`
and `audit/results.json`.

## Later live run (reviewed task only)

Run from the repo root in a single command so the variable is not persisted:

```sh
TYPESAFE_API_KEY="$(cat <keyfile>)" python3 audit/run_audit.py --live
```

`<keyfile>` is a path outside the repo. The key is read from the
environment only, never printed, logged, stored, or committed. Cached
responses store the response body, model/version fields, token usage, the
request hash and a timestamp — never headers or auth material.

## Tests

```sh
python3 -m unittest discover -s tests -v
```
