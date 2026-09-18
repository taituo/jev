# Roadmap for taituo/jev

This repository is the long-term home for several small Jev experiments.
The Audited Wiki at the repo root is project 1. Future experiments become
clearly named sibling directories only when warranted; nothing is scaffolded
in advance.

## A. What Audited Wiki is now

- Six RFC sources: 7519, 7515, 7516, 6749, 6750, 8725.
- Section-addressable sources with pinned SHA-256 checksums
  (`raw/sources/`, `derived/sections.json`).
- A small wiki with section citations (`wiki/`).
- 40 frozen labelled fixtures (`fixtures/claims.jsonl`): 26 supported,
  10 planted defects, 4 real RFC 8725 vs 7519 conflicts.
- Stdlib deterministic tests (`tests/`).
- No Jev calls yet.

The fixture set is small and self-authored. It is a starting point for
method checks, not evidence of general performance.

## B. The repair cycle

Quote checks are section-scoped against `char_start`/`char_end` in
`derived/sections.json`:

- supported and contradicted quotes must occur in the cited section;
- real-standards-conflict quotes must occur in at least one of the two
  cited sections;
- wrong-section quotes must occur in the RFC but not in the cited section;
- fabricated-quote and unsupported quotes must be absent from the cited
  section and from all six RFCs.

Review found fixture c021 labelled supported while its quote occurred in
RFC 6749 §1 but was cited as §1.4. The citation was corrected to §1.
`LICENSE` is MIT for original code and wiki prose only; the RFC texts in
`raw/sources/` remain under IETF Trust terms.

Lesson and limits are recorded in
[wiki/analyses/impressed-but-skeptical.md](wiki/analyses/impressed-but-skeptical.md):
a green suite is evidence only when it measures the intended claim.

## C. Guiding principle

A passing result on a small fixture is not accepted as evidence.

Each project must state, before running, its success thresholds and what
would count as a negative result. Negative results are published alongside
positive ones, with the same tables and artifacts.

## D. Sequenced projects

### 1. Calibrated citation audit

- Question: can Jev judge whether a cited section supports a claim, with
  usable confidence?
- Jev primitives: Choice (supports / contradicts / says nothing) plus
  speculative Noul questions per claim in one request over shared state.
- Inputs: the 40 frozen fixtures with cited section text.
- Baseline: the deterministic quote-placement checks already in `tests/`.
- Smallest useful slice: all 40 fixtures, one request pattern, cached raw
  responses.
- Measurable outcome: per-class detection, false-flag rate, and a triage
  curve (coverage at >=95% precision); Choice confidence bucketed at
  >=0.9 vs <0.9.
- Success evidence: pre-stated precision/coverage thresholds met on the
  frozen set, with raw responses committed so replay needs no key.
- Stop/repair policy: if confidence does not separate right from wrong
  answers, report the negative result and stop; fixture errors are fixed
  by explicit reviewed commits, not by rewording questions until green.

### 2. Evidence expansion

- Question: do the project 1 findings hold on a larger, harder fixture set?
- Jev primitives: same as project 1.
- Inputs: roughly 120 fixtures within the RFC family, including near-miss
  modal-verb changes, partly covered claims, adjacent-section support, and
  at least 12 real cross-RFC conflicts; plus a second license-clean family
  in a different register (for example HTTP semantics or TLS 1.3), reported
  separately.
- Baseline: project 1 results on the original 40.
- Smallest useful slice: the enlarged RFC-family set with at least 10 cases
  per defect class and an independent spot-check sample before freezing.
- Measurable outcome: same metrics as project 1, per family.
- Success evidence: thresholds stated in advance are met on both families
  or the shortfall is published.
- Stop/repair policy: if the spot check finds systematic label problems,
  freeze is delayed until a focused repair lands.

### 3. RAG/index gate or reranker evaluation

- Question: can Jev select the right page or section and abstain when the
  answer is absent?
- Jev primitives: Choice over page/section IDs plus one Noul question
  ("is the answer present here at all").
- Inputs: labelled queries over the wiki, including unanswerable ones.
- Baseline: a plain lexical/BM25-style ranker.
- Smallest useful slice: one query set with unanswerable cases included.
- Measurable outcome: top-k accuracy and an unanswerable-detection
  threshold sweep.
- Success evidence: pre-stated top-k and abstention trade-offs beaten or
  the miss reported.
- Stop/repair policy: if the baseline ties or wins, publish that and stop.

### 4. State-size sensitivity

- Question: does accuracy degrade as unrelated context grows?
- Jev primitives: same as project 1.
- Inputs: the same fixtures with the cited section alone, section plus
  page, plus 3 and 10 unrelated sections.
- Baseline: cited-section-alone accuracy.
- Smallest useful slice: all four context sizes on the frozen set.
- Measurable outcome: accuracy versus input tokens per size.
- Success evidence: a valid result is "no degradation at these sizes",
  stated with the measured deltas.
- Stop/repair policy: if larger states break parsing or replay, fix the
  harness first; do not reinterpret the metric.

### 5. Controlled comparison variants

- Question: how stable are the results to small method changes?
- Jev primitives: same as the project being varied.
- Inputs: the fixtures and queries of the relevant earlier project.
- Baseline: the earlier project's locked configuration.
- Smallest useful slice: question-phrasing variants, batched versus
  one-question-per-request stability, and an optional generative-model
  JSON baseline, each varying one thing at a time.
- Measurable outcome: delta tables against the locked baseline.
- Success evidence: pre-stated stability bounds hold or the deviation is
  published.
- Stop/repair policy: one variable per comparison; a failed variant is a
  finding, not a reason to re-tune mid-run.

### 6. Concise eval/observations reports for each project

- Question: what was actually observed?
- Jev primitives: none new; this project writes up projects 1–5.
- Inputs: cached responses, metric tables, and review notes.
- Baseline: the pre-stated thresholds of each project.
- Smallest useful slice: one short results page per project.
- Measurable outcome: tables, raw-probability artifacts, and an explicit
  limitations list per project.
- Success evidence: a reader can reproduce the tables from the committed
  artifacts.
- Stop/repair policy: missing artifacts block the report; gaps are listed
  rather than filled by memory.

## E. Public-repo boundaries

May be committed:

- code, tests, and documentation;
- hand-authored fixtures and their reviewed corrections;
- cached API responses stripped of any credentials;
- results pages with tables and raw-probability artifacts.

May not be committed:

- keys or other credentials;
- chat exports, runbooks, or private notes;
- text that is not redistributable under the repository terms.

API keys, when a future project needs them, are only ever read from an
environment variable and never written, logged, or committed. Replay mode
must work with no key, using the committed cached responses.

## F. Global stop/repair policy

- Failing tests or secret-scan hits block any push.
- A review finding produces one focused repair before anything new.
- A broken fixture label is fixed by an explicit reviewed commit, never
  silently.
- If an experiment result contradicts a pre-stated expectation, it is
  reported as is.

## G. Status

| Project | State |
| --- | --- |
| Audited Wiki (repo root) | done |
| Repair cycle (section-scoped checks, c021, LICENSE, analysis) | done |
| 1. Calibrated citation audit | next |
| 2. Evidence expansion | planned |
| 3. RAG/index gate or reranker evaluation | planned |
| 4. State-size sensitivity | planned |
| 5. Controlled comparison variants | planned |
| 6. Eval/observations reports | planned |
