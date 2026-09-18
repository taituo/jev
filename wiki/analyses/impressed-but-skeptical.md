---
type: analysis
status: reviewed
created: 2026-09-18
updated: 2026-09-18
sources: [rfc6749]
tags: [audit, testing, limits]
---

# Impressed but skeptical

The first validation suite passed 12/12, yet review found fixture c021
labelled supported while its quote occurred outside the cited section.
The claim text was about access tokens, the quote
("specific scope, lifetime, and other access attributes") occurs in the
Introduction [rfc6749 §1], but the fixture cited [rfc6749 §1.4].

The old test only checked that a supported quote occurs anywhere in the
RFC file. That is weaker than the claim being audited, which asserts the
quote supports the specific cited section.

The corrected section-scoped invariant, checked against
`char_start`/`char_end` in `derived/sections.json`, is:

- supported and contradicted: the quote must occur in the cited section;
- real_standards_conflict: the quote must occur in at least one of the
  two cited sections;
- wrong_section: the quote must occur in the RFC but not in the cited
  section;
- fabricated_quote and unsupported: the quote must be absent from the
  cited section and from all six RFCs.

Lesson: a green test is evidence only when it measures the intended
claim. Section resolution is the intended claim here, so the test must
be section-scoped.

Limits: this is one caught error in a 40-item self-authored fixture set.
It shows the old test was too loose, not that the labels are now correct.
