# Citation audit results

Headline set: 36 single-section fixtures (n_supported=26, n_defects=10).

## Overall

| metric | value |
| --- | --- |
| accuracy (Q1 vs expected) | 88.9% |
| defects flagged (Q1 != supports) | 9/10 |
| supported flagged | 0/26 |
| detection rate | 90.0% |
| false-flag rate | 0.0% |

## Per class

| label | n | correct | flagged |
| --- | --- | --- | --- |
| contradicted | 3 | 3 | 3 |
| fabricated_quote | 3 | 2 | 3 |
| supported | 26 | 26 | 0 |
| unsupported | 2 | 1 | 2 |
| wrong_section | 2 | 0 | 1 |

## Confusion matrix (expected x Q1 verdict)

| expected \ predicted | supports | contradicts | says_nothing |
| --- | --- | --- | --- |
| supports | 26 | 0 | 0 |
| contradicts | 0 | 3 | 0 |
| says_nothing | 1 | 3 | 3 |

## Choice confidence buckets

Cutoff: >=0.9.

| bucket | n | correct | precision |
| --- | --- | --- | --- |
| >= 0.9 | 32 | 30 | 93.8% |
| < 0.9 | 4 | 2 | 50.0% |

Precision gap: 43.8 percentage points (INCONCLUSIVE if either bucket has fewer than 10 items).

## Triage curve

Smallest threshold reaching >=95% precision: 0.98 (precision 96.7%, coverage 83.3%, 30/36 accepted).

## Noul threshold sweep (Q2 near-verbatim)

| threshold | n | positives | of which flagged | of which not flagged |
| --- | --- | --- | --- | --- |
| 0.1 | 36 | 26 | 0 | 26 |
| 0.2 | 36 | 26 | 0 | 26 |
| 0.3 | 36 | 26 | 0 | 26 |
| 0.4 | 36 | 26 | 0 | 26 |
| 0.5 | 36 | 26 | 0 | 26 |
| 0.6 | 36 | 24 | 0 | 24 |
| 0.7 | 36 | 23 | 0 | 23 |
| 0.8 | 36 | 20 | 0 | 20 |
| 0.9 | 36 | 8 | 0 | 8 |

## Noul threshold sweep (Q3 goes-beyond)

| threshold | n | positives | of which flagged | of which not flagged |
| --- | --- | --- | --- | --- |
| 0.1 | 36 | 27 | 9 | 18 |
| 0.2 | 36 | 16 | 9 | 7 |
| 0.3 | 36 | 13 | 9 | 4 |
| 0.4 | 36 | 11 | 9 | 2 |
| 0.5 | 36 | 11 | 9 | 2 |
| 0.6 | 36 | 11 | 9 | 2 |
| 0.7 | 36 | 10 | 9 | 1 |
| 0.8 | 36 | 10 | 9 | 1 |
| 0.9 | 36 | 9 | 9 | 0 |

## Real standards conflicts (descriptive, no threshold)

real_standards_conflict claims assert a cross-RFC conflict judged against two sections; reported descriptively with no threshold.

| fixture | Q1 verdict | confidence | q2 | q3 | q4 |
| --- | --- | --- | --- | --- | --- |
| c037 | supports | 0.98 | 0.59 | 0.22 | fully |
| c038 | supports | 0.80 | 0.45 | 0.33 | fully |
| c039 | supports | 0.98 | 0.65 | 0.22 | fully |
| c040 | supports | 0.85 | 0.73 | 0.45 | fully |
