"""Check the fixed answer bank and the rule table.

answers.json on main is an object keyed by id. This script also accepts the
older list shape. It does not fetch another branch.

    python app/backend/scripts/validate_content.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "app" / "src" / "content"

ALLOWED_KEYS = {
    "id",
    "kind",
    "severity",
    "text",
    "not_sure",
    "sources",
    "assumption",
    "translation_status",
    "reviewed_by",
}
SEVERITY = {"ok", "watch", "act", "ask"}
RULE_KEYS = {
    "dominant",
    "affected_gte",
    "affected_lte",
    "uncertain_gte",
    "uncertain_lte",
    "distinct_problems_gte",
    "window",
}
BRANDS = [
    "Ridomil",
    "Nordox",
    "Kocide",
    "Funguran",
    "Cuprocaffaro",
    "Bayleton",
    "Amistar",
    "Score",
    "Cupravit",
    "Champion",
    "Daconil",
    "Folicur",
    "Alto",
    "Tilt",
    "Actara",
    "Karate",
    "Duduthrin",
]


def load_answers(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        rows = []
        for key, item in data.items():
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row.setdefault("id", key)
            rows.append(row)
        return rows
    if isinstance(data, list):
        return data
    raise SystemExit("answers.json must be an object keyed by id, or a list")


def main() -> int:
    answers = load_answers(CONTENT / "answers.json")
    rules = json.loads((CONTENT / "rules.json").read_text(encoding="utf-8"))
    errors: list[str] = []

    ids = [a["id"] for a in answers]
    bank = {a["id"]: a for a in answers}
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")

    for rule in rules:
        if rule["then"] not in bank:
            errors.append("rule target missing: " + rule["then"])
        bad = set(rule["if"]) - RULE_KEYS
        if bad:
            errors.append(f"unknown condition key {bad}")
    if rules[-1]["if"] != {} or rules[-1]["then"] != "ask_officer":
        errors.append("last rule is not the ask_officer catch-all")

    for card in answers:
        extra = set(card) - ALLOWED_KEYS
        if extra:
            errors.append(f"{card['id']}: unexpected keys {extra}")
        for lang in ("en", "sw"):
            if not card["text"].get(lang, "").strip():
                errors.append(f"{card['id']}: missing text.{lang}")
        if card["severity"] not in SEVERITY:
            errors.append(f"{card['id']}: bad severity")
        if card["kind"] == "result":
            note = card.get("not_sure") or {}
            if not note.get("en") or not note.get("sw"):
                errors.append(f"{card['id']}: result card without en+sw not_sure")
        if "[placeholder]" in json.dumps(card):
            errors.append(f"{card['id']}: placeholder text left")
        for source in card["sources"]:
            if source.startswith("GUIDANCE#"):
                continue
            if re.fullmatch(r"S\d+", source):
                continue
            errors.append(f"{card['id']}: unknown source {source}")

    blob = json.dumps(answers, ensure_ascii=False)
    rules_blob = json.dumps(rules, ensure_ascii=False)
    doses = re.findall(r"\d+(?:[.,]\d+)?\s*(?:ml|g|kg|l|litres?|grams?|%)\b", blob, re.I)
    if doses:
        errors.append(f"dose-like strings: {doses}")
    for brand in BRANDS:
        if re.search(r"\b" + brand + r"\b", blob, re.I):
            errors.append("brand name: " + brand)
    if "\u2014" in blob or "\u2013" in blob or "\u2014" in rules_blob or "\u2013" in rules_blob:
        errors.append("em or en dash present")

    print(f"cards={len(answers)} rules={len(rules)}")
    if errors:
        print("FAIL")
        for error in errors:
            print(" -", error)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
