# Evaluation: Project 1 calibrated citation audit (live run)

Run date: 2026-09-19 (UTC).
Approved harness commit: `81ae6f1ccd2dfd8a1af4a782e54985881aa5aa8a`.
Model: returned `jev-1.13.0` for all 40 fixtures (requested `jev-latest`).
Cache completeness: 40/40 (`audit/responses/c001.json` through `c040.json`), each with fixture identity, current request hash, model/version fields, usage (`input_tokens`/`output_tokens`), and all four answers (`q1_relation`, `q2_verbatim`, `q3_beyond`, `q4_scope`).

No questions, labels, thresholds, or interpretations were retuned after observing responses.

## Headline set (36 single-section fixtures)

- Accuracy (Q1 vs expected map in `audit/PREREGISTRATION.md` §(a)): 88.9% (32/36).
- Defects flagged (`flagged = (Q1 verdict != supports)` per §(b)): 9/10 (detection rate 90.0%).
- Supported flagged (false flags): 0/26 (false-flag rate 0.0%).

Per class (n / correct / flagged):

- `supported` (26): 26 / 0.
- `contradicted` (3): 3 / 3.
- `fabricated_quote` (3): 2 / 3.
- `unsupported` (2): 1 / 2.
- `wrong_section` (2): 0 / 1.

Confusion (expected x predicted): supports 26/0/0; contradicts 0/3/0; says_nothing 1/3/3.

Confidence buckets (Choice, cutoff >= 0.9):

- `>= 0.9`: n=32, correct=30, precision 93.8%.
- `< 0.9`: n=4, correct=2, precision 50.0%.
- Precision gap: 43.8 percentage points, **INCONCLUSIVE** because the low bucket has fewer than 10 items (pre-registered small-bucket rule).

Triage (descriptive per §(c)): smallest threshold reaching >= 95% precision is 0.98 (precision 96.7%, coverage 83.3%, 30/36 accepted).

## Assessment against every pre-registered threshold (§(c)–(d))

1. Detection (>= 8/10 defects flagged): observed 9/10 — PASS.
2. False flags (<= 3/26 supported flagged): observed 0/26 — PASS.
3. Confidence separation (gap >= 15 points, INCONCLUSIVE if either bucket < 10): gap 43.8 points but low bucket n=4 — **INCONCLUSIVE**, which §(d) counts as a negative result.
4. Triage 95% precision leg (§(d)): a threshold (0.98) reaches 95% — no negative finding on this leg alone.

Negative-result rule (§(d)): INCONCLUSIVE confidence is an explicit negative-result condition. This run is therefore a **negative result**: confidence does not separate right from wrong answers under the pre-registered bucket rule. Per `ROADMAP.md` and §(d), further experiment work stops; no general performance claim is made. Published unchanged as a negative result.

## Noul sweeps (descriptive, no pass/fail)

Q2 near-verbatim and Q3 goes-beyond sweeps are reported as tables in `audit/results.md` / `audit/results.json` with no threshold line. Q3 at 0.9 isolates the 9 flagged headline items (9 positives, all flagged); Q2 positives are never flagged at any swept threshold.

## Real standards conflicts (descriptive, no threshold)

Four `real_standards_conflict` fixtures (c037–c040), judged against two sections each, have no expected verdict:

- c037: supports, 0.98 / q2 0.59 / q3 0.22 / fully.
- c038: supports, 0.80 / q2 0.45 / q3 0.33 / fully.
- c039: supports, 0.98 / q2 0.65 / q3 0.22 / fully.
- c040: supports, 0.85 / q2 0.73 / q3 0.45 / fully.

## Limits

Small (36 headline + 4 conflict), self-authored fixture set; a pass here would have been a method check motivating project 2, not general evidence. As a negative result, it stops the project per the pre-registered rule.

## Artifacts and replay

- Preregistration: `audit/PREREGISTRATION.md`.
- Generated results: `audit/results.md`, `audit/results.json`.
- Cached responses: `audit/responses/c001.json` through `c040.json`.
- Keyless replay (reproduces results byte-for-byte):

```sh
env -u TYPESAFE_API_KEY PYTHONDONTWRITEBYTECODE=1 python3 -B audit/run_audit.py --replay
```
