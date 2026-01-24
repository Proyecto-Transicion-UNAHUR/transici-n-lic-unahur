from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import yaml

RuleType = Literal["DIRECT", "SPLIT_1toN", "MERGE_Nto1", "ACA_ONLY"]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@dataclass
class MappingRule:
    type: RuleType
    src_2018_codes: list[str] = field(default_factory=list)
    dst_2025_codes: list[str] = field(default_factory=list)

    # MERGE_Nto1 partials
    aca_on_partial: Optional[int] = None
    aca_partial_mode: Optional[Literal["per_source", "per_rule"]] = None

    # ACA_ONLY
    aca_credits: Optional[int] = None

    comment: Optional[str] = None


def _read_yaml(path: Path):
    if not path.exists():
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def load_rules(variant: str | None = None) -> list[MappingRule]:
    """Load mapping rules.

    Precedence:
      - mapping_rules_<variant>.yaml (if variant provided and file exists)
      - mapping_rules.yaml
    """
    if variant:
        cand = DATA_DIR / f"mapping_rules_{variant}.yaml"
        data = _read_yaml(cand) if cand.exists() else _read_yaml(DATA_DIR / "mapping_rules.yaml")
    else:
        data = _read_yaml(DATA_DIR / "mapping_rules.yaml")

    rules: list[MappingRule] = []
    for item in data:
        # default behavior for MERGE partials
        if item.get("type") == "MERGE_Nto1" and "aca_partial_mode" not in item:
            item["aca_partial_mode"] = "per_source"
        rules.append(MappingRule(**item))
    return rules
