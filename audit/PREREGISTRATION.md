# Pre-registration: Project 1 calibrated citation audit

Status: locked before any TypeSafe response exists. No file under
`audit/responses/` (other than `.gitkeep`) existed when this was written.

Method: one TypeSafe request per fixture over shared state
(`audit/state.py`, `audit/questions.py`), four questions per claim
(Q1 Choice relation, Q2 Noul near-verbatim, Q3 Noul goes-beyond,
Q4 Choice scope). Headline set: the 36 single-section fixtures
(26 `supported` + 10 planted defects). Analysis: `audit/analyze.py`.

## (a) Expected-verdict map (Q1)

| fixture label      | expected Q1 verdict |
| ---                | ---                 |
| `supported`        | `supports`          |
| `contradicted`     | `contradicts`       |
| `unsupported`      | `says_nothing`      |
| `wrong_section`    | `says_nothing`      |
| `fabricated_quote` | `says_nothing`      |

Ambiguity note, pre-stated: `fabricated_quote` is ambiguous in principle —
a model that detects an invented quote could arguably answer `contradicts`
(the claim asserts something false) rather than `says_nothing` (the section
does not address it). We pre-register `says_nothing` as the expected verdict
because the cited section contains no statement on the claim either way, and
we pre-state the accepted set: for `fabricated_quote`, `wrong_section` and
`unsupported`, the accepted (unflagged-against) set is exactly
{`says_nothing`}; any other Q1 verdict counts as a flag for threshold (b)
and as incorrect for accuracy. For `contradicted` the accepted set is
exactly {`contradicts`}; for `supported` exactly {`supports`}.

The 4 `real_standards_conflict` fixtures have no expected verdict and no
threshold: each such claim asserts a cross-RFC (7519 vs 8725) conflict and
is judged against two sections, so a single supports/contradicts label is
not well-defined. They are reported descriptively only.

## (b) Flag rule

`flagged = (Q1 verdict != supports)`.

A supported claim answered anything but `supports` is a false flag; a
planted defect answered anything but `supports` is detected.

## (c) Pass thresholds (all three must hold)

1. Detection: at least 8 of the 10 planted defects flagged.
2. False flags: at most 3 of the 26 supported claims flagged.
3. Confidence separation: Choice confidence bucketed at >= 0.9 vs < 0.9;
   the precision gap (high-bucket precision minus low-bucket precision)
   is at least 15 percentage points. The confidence result is INCONCLUSIVE
   if either bucket has fewer than 10 items.

Triage reporting (descriptive, not pass/fail): coverage at the smallest
confidence threshold reaching >= 95% precision, or the statement that no
threshold does. Noul Q2/Q3 threshold sweeps are reported as tables with no
pass/fail line.

## (d) What counts as a negative result

Any of these is a negative result and will be published as is, with the
same tables and committed artifacts: fewer than 8 of 10 defects flagged;
more than 3 of 26 supported flagged; confidence gap below 15 points (or
INCONCLUSIVE by the small-bucket rule); or no triage threshold reaching
95% precision. A negative result stops the project: per ROADMAP.md, if
confidence does not separate right from wrong answers, report the negative
result and stop. Fixture errors are fixed by explicit reviewed commits,
never by rewording questions until green.

## (e) Scope limit

The 36-item result alone will not be described as general evidence. The
fixture set is small and self-authored; a pass here is a method check that
motivates project 2 (evidence expansion), not a general performance claim.

## Change rule

Nothing in this file may be changed after live responses exist except by an
explicit reviewed commit that says why.
