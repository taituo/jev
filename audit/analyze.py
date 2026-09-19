#!/usr/bin/env python3
"""Analyze cached TypeSafe responses against the pre-registered expectations.

Headline metrics use the 36 single-section fixtures (26 supported + 10
planted defects). The 4 ``real_standards_conflict`` fixtures are reported
separately and descriptively, with no threshold, because each such claim
asserts a cross-RFC conflict judged against two sections.

Stdlib only. No network. No key.

Outputs: markdown tables (stdout and optionally a file) plus a
machine-readable JSON dict (see :func:`compute_metrics`).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import questions as Q

# Pre-registered expected-verdict map (see audit/PREREGISTRATION.md).
EXPECTED: dict[str, str] = {
    "supported": "supports",
    "contradicted": "contradicts",
    "unsupported": "says_nothing",
    "wrong_section": "says_nothing",
    "fabricated_quote": "says_nothing",
}

HEADLINE_LABELS = {"supported", "contradicted", "unsupported",
                   "wrong_section", "fabricated_quote"}
CONFLICT_LABEL = "real_standards_conflict"

Q1 = Q.Q1_ID
Q2 = Q.Q2_ID
Q3 = Q.Q3_ID
Q4 = Q.Q4_ID

HIGH_CONF = 0.9
NOUL_SWEEP = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
TRIAGE_PRECISION_TARGET = 0.95


def q1_of(cached: dict) -> tuple[str, float, dict]:
    ans = cached["response"]["answers"][Q1]
    return ans["choice"], float(ans["confidence"]), dict(ans["probabilities"])


def to_records(pairs: list[tuple[dict, dict]]) -> list[dict]:
    """Join (fixture, cached) pairs into analysis records."""
    records = []
    for fixture, cached in pairs:
        label = fixture["label"]
        verdict, conf, probs = q1_of(cached)
        answers = cached["response"]["answers"]
        records.append({
            "fixture_id": fixture["id"],
            "label": label,
            "expected": EXPECTED.get(label),
            "verdict": verdict,
            "correct": (verdict == EXPECTED.get(label)) if label in EXPECTED else None,
            "flagged": verdict != "supports",
            "confidence": conf,
            "probabilities": probs,
            "q2": float(answers[Q2]["noul"]) if Q2 in answers else None,
            "q3": float(answers[Q3]["noul"]) if Q3 in answers else None,
            "q4": answers[Q4]["choice"] if Q4 in answers else None,
            "usage": cached["response"].get("usage", {}),
        })
    return records


def confusion(records: list[dict]) -> dict[str, dict[str, int]]:
    cats = ["supports", "contradicts", "says_nothing"]
    matrix = {e: {p: 0 for p in cats} for e in cats}
    for rec in records:
        if rec["expected"] in cats and rec["verdict"] in cats:
            matrix[rec["expected"]][rec["verdict"]] += 1
    return matrix


def confidence_buckets(records: list[dict], cutoff: float = HIGH_CONF) -> dict:
    high = [r for r in records if r["confidence"] >= cutoff]
    low = [r for r in records if r["confidence"] < cutoff]
    def precision(rs: list[dict]):
        if not rs:
            return None
        return sum(1 for r in rs if r["correct"]) / len(rs)
    return {
        "cutoff": cutoff,
        "high": {"n": len(high), "precision": precision(high),
                 "correct": sum(1 for r in high if r["correct"])},
        "low": {"n": len(low), "precision": precision(low),
                "correct": sum(1 for r in low if r["correct"])},
        "gap_pp": ((precision(high) - precision(low)) * 100
                   if precision(high) is not None and precision(low) is not None
                   else None),
    }


def triage_curve(records: list[dict],
                 target: float = TRIAGE_PRECISION_TARGET) -> dict:
    """Coverage at the smallest confidence threshold reaching target precision.

    Thresholds swept over sorted unique confidences (plus 0.0). For each
    threshold t, accepted = confidence >= t; precision over accepted;
    coverage = accepted / total. The reported point is the smallest t with
    precision >= target (hence maximal coverage at target). If no threshold
    reaches the target, the curve states that none does.
    """
    if not records:
        return {"target": target, "threshold": None,
                "statement": "no records; no threshold evaluated"}
    thresholds = sorted({r["confidence"] for r in records} | {0.0})
    for thr in thresholds:
        accepted = [r for r in records if r["confidence"] >= thr]
        if not accepted:
            continue
        prec = sum(1 for r in accepted if r["correct"]) / len(accepted)
        if prec >= target:
            return {"target": target, "threshold": thr, "precision": prec,
                    "coverage": len(accepted) / len(records),
                    "accepted": len(accepted), "total": len(records)}
    return {"target": target, "threshold": None,
            "statement": f"no confidence threshold reaches "
                         f">={target:.0%} precision"}


def noul_sweep(records: list[dict], key: str,
               thresholds: list[float] = NOUL_SWEEP) -> list[dict]:
    """Sweep a Noul threshold: positives and agreement with the flag label.

    ``flagged`` (Q1 verdict != supports) is the reference standard: for Q3
    (claim goes beyond) a positive should coincide with flagged; for Q2
    (near-verbatim) a positive should coincide with not-flagged, so the
    table reports both agreements and lets the reader judge.
    """
    rows = []
    usable = [r for r in records if r.get(key) is not None]
    for thr in thresholds:
        pos = [r for r in usable if r[key] >= thr]
        agree_flag = sum(1 for r in pos if r["flagged"])
        agree_noflag = sum(1 for r in pos if not r["flagged"])
        rows.append({"threshold": thr, "n": len(usable),
                     "positives": len(pos),
                     "positives_flagged": agree_flag,
                     "positives_not_flagged": agree_noflag})
    return rows


def per_class(records: list[dict]) -> dict[str, dict]:
    table = {}
    for label in sorted({r["label"] for r in records}):
        rs = [r for r in records if r["label"] == label]
        table[label] = {
            "n": len(rs),
            "correct": sum(1 for r in rs if r["correct"]),
            "flagged": sum(1 for r in rs if r["flagged"]),
        }
    return table


def compute_metrics(records: list[dict]) -> dict:
    headline = [r for r in records if r["label"] in HEADLINE_LABELS]
    conflicts = [r for r in records if r["label"] == CONFLICT_LABEL]
    defects = [r for r in headline if r["label"] != "supported"]
    supported = [r for r in headline if r["label"] == "supported"]

    flagged_defects = sum(1 for r in defects if r["flagged"])
    flagged_supported = sum(1 for r in supported if r["flagged"])
    accuracy = (sum(1 for r in headline if r["correct"]) / len(headline)
                if headline else None)
    buckets = confidence_buckets(headline)
    triage = triage_curve(headline)
    return {
        "n_headline": len(headline),
        "n_supported": len(supported),
        "n_defects": len(defects),
        "n_conflicts": len(conflicts),
        "accuracy_headline": accuracy,
        "flagged_defects": flagged_defects,
        "flagged_supported": flagged_supported,
        "detection_rate": (flagged_defects / len(defects)) if defects else None,
        "false_flag_rate": (flagged_supported / len(supported)) if supported else None,
        "per_class": per_class(headline),
        "confusion": confusion(headline),
        "confidence_buckets": buckets,
        "triage": triage,
        "noul_q2_sweep": noul_sweep(headline, "q2"),
        "noul_q3_sweep": noul_sweep(headline, "q3"),
        "conflicts": [
            {"fixture_id": r["fixture_id"], "verdict": r["verdict"],
             "confidence": r["confidence"], "q2": r["q2"], "q3": r["q3"],
             "q4": r["q4"]} for r in conflicts
        ],
        "conflict_note": ("real_standards_conflict claims assert a cross-RFC "
                          "conflict judged against two sections; reported "
                          "descriptively with no threshold."),
    }


def _pct(value) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def render_markdown(metrics: dict) -> str:
    lines = ["# Citation audit results", ""]
    lines.append("Headline set: 36 single-section fixtures "
                 f"(n_supported={metrics['n_supported']}, "
                 f"n_defects={metrics['n_defects']}).")
    lines.append("")
    lines += ["## Overall",
              "",
              "| metric | value |",
              "| --- | --- |",
              f"| accuracy (Q1 vs expected) | {_pct(metrics['accuracy_headline'])} |",
              f"| defects flagged (Q1 != supports) | {metrics['flagged_defects']}/{metrics['n_defects']} |",
              f"| supported flagged | {metrics['flagged_supported']}/{metrics['n_supported']} |",
              f"| detection rate | {_pct(metrics['detection_rate'])} |",
              f"| false-flag rate | {_pct(metrics['false_flag_rate'])} |",
              ""]
    lines += ["## Per class", "",
              "| label | n | correct | flagged |",
              "| --- | --- | --- | --- |"]
    for label, row in metrics["per_class"].items():
        lines.append(f"| {label} | {row['n']} | {row['correct']} | {row['flagged']} |")
    lines.append("")
    lines += ["## Confusion matrix (expected x Q1 verdict)", "",
              "| expected \\ predicted | supports | contradicts | says_nothing |",
              "| --- | --- | --- | --- |"]
    for exp, row in metrics["confusion"].items():
        lines.append(f"| {exp} | {row['supports']} | {row['contradicts']} | {row['says_nothing']} |")
    lines.append("")
    buckets = metrics["confidence_buckets"]
    lines += ["## Choice confidence buckets", "",
              f"Cutoff: >={buckets['cutoff']}.",
              "",
              "| bucket | n | correct | precision |",
              "| --- | --- | --- | --- |",
              f"| >= {buckets['cutoff']} | {buckets['high']['n']} | {buckets['high']['correct']} | {_pct(buckets['high']['precision'])} |",
              f"| < {buckets['cutoff']} | {buckets['low']['n']} | {buckets['low']['correct']} | {_pct(buckets['low']['precision'])} |",
              ""]
    gap = buckets["gap_pp"]
    lines.append(f"Precision gap: {'n/a' if gap is None else f'{gap:.1f} percentage points'} "
                 f"(INCONCLUSIVE if either bucket has fewer than 10 items).")
    lines.append("")
    tri = metrics["triage"]
    lines += ["## Triage curve", ""]
    if tri.get("threshold") is None:
        lines.append(tri.get("statement", "no threshold reaches the target."))
    else:
        lines.append(f"Smallest threshold reaching >={tri['target']:.0%} precision: "
                     f"{tri['threshold']:.2f} "
                     f"(precision {tri['precision']:.1%}, coverage {tri['coverage']:.1%}, "
                     f"{tri['accepted']}/{tri['total']} accepted).")
    lines.append("")
    for key, title in (("noul_q2_sweep", "Q2 near-verbatim"), ("noul_q3_sweep", "Q3 goes-beyond")):
        lines += [f"## Noul threshold sweep ({title})", "",
                  "| threshold | n | positives | of which flagged | of which not flagged |",
                  "| --- | --- | --- | --- | --- |"]
        for row in metrics[key]:
            lines.append(f"| {row['threshold']:.1f} | {row['n']} | {row['positives']} | "
                         f"{row['positives_flagged']} | {row['positives_not_flagged']} |")
        lines.append("")
    lines += ["## Real standards conflicts (descriptive, no threshold)", "",
              metrics["conflict_note"], "",
              "| fixture | Q1 verdict | confidence | q2 | q3 | q4 |",
              "| --- | --- | --- | --- | --- | --- |"]
    for row in metrics["conflicts"]:
        lines.append(f"| {row['fixture_id']} | {row['verdict']} | {row['confidence']:.2f} | "
                     f"{row['q2']} | {row['q3']} | {row['q4']} |")
    lines.append("")
    return "\n".join(lines)


def write_results(metrics: dict, md_path: Path, json_path: Path) -> None:
    md_path.write_text(render_markdown(metrics), encoding="utf-8")
    json_path.write_text(json.dumps(metrics, indent=2, sort_keys=True),
                         encoding="utf-8")
