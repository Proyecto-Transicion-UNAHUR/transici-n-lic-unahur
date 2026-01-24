from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from transicion.models import (
    Subject2018A,
    Subject2018B,
    Subject2025,
    StudentSelection,
    CrActivity,
    CrActivityCompletion,
)
from transicion.rules_loader import load_rules

# --- configurable constants (document these in README) ---
CREDITS_TO_HOURS = 25  # fallback conversion if hours_hint is missing
PLAN2018_TOTAL_HOURS = 3520
PLAN2025_TOTAL_HOURS = 3200
ACA_TOTAL_REQUIRED = 30


def _subjects_2018_by_variant(db: Session, variant: str):
    if variant == "B":
        return {s.code: s for s in db.query(Subject2018B).all()}
    return {s.code: s for s in db.query(Subject2018A).all()}


def calc_hours_2018(db: Session, passed_2018_codes: set[str], variant: str) -> Tuple[int, int]:
    s2018 = _subjects_2018_by_variant(db, variant)
    got = 0
    for code in passed_2018_codes:
        subj = s2018.get(code)
        if not subj:
            continue
        got += (subj.hours_hint or (subj.credits * CREDITS_TO_HOURS))
    return got, PLAN2018_TOTAL_HOURS


def run_calc(db: Session, user_id: str, variant: str) -> Dict:
    """Core transition calculation.

    - Determines approved 2025 subjects based on mapping_rules*.yaml
    - Computes partial MERGE_Nto1 cases and ACA from partials
    - Adds ACA from CR activities (variant B) via CrActivityCompletion
    - Returns a dict ready for UI rendering and PDF export
    """
    variant = (variant or "A").upper()

    rules = load_rules(variant)
    s2025 = {s.code: s for s in db.query(Subject2025).all()}

    sel = (
        db.query(StudentSelection)
        .filter_by(user_id=user_id, variant=variant, passed=True)
        .all()
    )
    passed_2018 = {x.subject_code for x in sel}

    approved_2025: set[str] = set()
    partials: List[Dict] = []
    aca_from_subjects = 0

    for r in rules:
        if r.type == "DIRECT":
            if all(code in passed_2018 for code in r.src_2018_codes):
                approved_2025.update(r.dst_2025_codes)

        elif r.type == "SPLIT_1toN":
            if r.src_2018_codes and r.src_2018_codes[0] in passed_2018:
                approved_2025.update(r.dst_2025_codes)

        elif r.type == "MERGE_Nto1":
            have = [c for c in r.src_2018_codes if c in passed_2018]
            need = len(r.src_2018_codes)
            k = len(have)

            if need == 0:
                continue

            if k == need:
                approved_2025.update(r.dst_2025_codes)
            elif 1 <= k < need:
                per_unit = r.aca_on_partial or 0
                mode = r.aca_partial_mode or "per_source"

                if per_unit > 0:
                    partial_aca = per_unit if mode == "per_rule" else (k * per_unit)
                    aca_from_subjects += partial_aca

                    partials.append(
                        {
                            "dst": r.dst_2025_codes,
                            "have": have,
                            "missing": [c for c in r.src_2018_codes if c not in have],
                            "aca_granted": partial_aca,
                            "mode": mode,
                            "comment": r.comment,
                        }
                    )

        elif r.type == "ACA_ONLY":
            if any(code in passed_2018 for code in r.src_2018_codes):
                aca_from_subjects += int(r.aca_credits or 0)

    # --- ACA from CR activities (typically variant B) ---
    # (We do not block it for variant A in code; the UI can hide it.)
    extra_rows = (
        db.query(CrActivity)
        .join(CrActivityCompletion, CrActivity.code == CrActivityCompletion.activity_code)
        .filter(CrActivityCompletion.user_id == user_id)
        .filter(CrActivityCompletion.variant == variant)
        .filter(CrActivityCompletion.completed == True)
        .all()
    )
    aca_from_cr = sum(a.cre_value for a in extra_rows)

    aca_total = min(ACA_TOTAL_REQUIRED, aca_from_subjects + aca_from_cr)

    got_2025_hours = sum(s2025[c].hours_total for c in approved_2025 if c in s2025)
    hrs_2018_got, hrs_2018_total = calc_hours_2018(db, passed_2018, variant)

    return {
        "user_id": user_id,
        "variant": variant,
        "hrs_2018": {"got": hrs_2018_got, "total": hrs_2018_total},
        "hrs_2025": {"got": got_2025_hours, "total": PLAN2025_TOTAL_HOURS},
        "aca_credits": aca_total,
        "aca_required": ACA_TOTAL_REQUIRED,
        "aca_from_subjects": aca_from_subjects,
        "aca_from_cr": aca_from_cr,
        "equivalences_2025": [
            {
                "code": code,
                "name": s2025[code].name if code in s2025 else code,
                "hours_total": s2025[code].hours_total if code in s2025 else None,
            }
            for code in sorted(approved_2025)
        ],
        "partials": partials,
    }
