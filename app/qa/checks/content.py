"""Answer bank and rule table integrity.

Guardrail G3 (avoid hallucinations): the app can only say things in answers.json.
Pass/fail P1: the catch-all rule must be ask_officer.
R4/R5: Swahili for every answer, Kikuyu for the core set.
"""
from __future__ import annotations

from pathlib import Path

from qa.common import Result, read_json

REQUIRED_IDS = [
    "how_to_pick_leaves", "how_to_photograph", "retake_blurry", "retake_dark", "not_a_leaf",
    "healthy_all", "rust_low", "rust_high_pre_rains", "rust_high_in_rains", "rust_high_dry",
    "cercospora", "phoma", "miner", "mixed_problems", "too_many_unsure", "ask_officer",
    "berries_out_of_scope", "other_crop",
    "consent_main", "consent_photos", "decision_act", "decision_wait", "decision_ask",
    "referral_ready", "language_name",
]
KIK_CORE = ["how_to_pick_leaves", "healthy_all", "rust_high_pre_rains", "too_many_unsure",
            "ask_officer", "decision_act", "decision_wait", "decision_ask"]
ALLOWED_CONDITIONS = {"dominant", "affected_gte", "affected_lte", "uncertain_gte",
                      "distinct_problems_gte", "window"}
ALLOWED_WINDOWS = {"pre_short_rains", "short_rains", "pre_long_rains", "long_rains", "dry"}
BANNED_WORDS = ["mancozeb", "chlorothalonil", "copper oxychloride 50", "ml per", "g per litre",
                "grams per", "litres per", "revolutionise", "empower", "seamless", "cutting-edge"]


def run(root: Path) -> list[Result]:
    out: list[Result] = []
    a_path = root / "src/content/answers.json"
    r_path = root / "src/content/rules.json"
    s_path = root / "src/content/season.json"
    if not a_path.exists():
        return [Result("content:answers", "skip", "src/content/answers.json missing")]

    answers = read_json(a_path)
    if isinstance(answers, dict):
        answers = list(answers.values())
    by_id = {a["id"]: a for a in answers if isinstance(a, dict) and "id" in a}

    # Required IDs
    missing = [i for i in REQUIRED_IDS if i not in by_id]
    out.append(Result("content:required_ids", "fail" if missing else "pass",
                      f"{len(missing)} required answer IDs missing" if missing else f"{len(by_id)} answers, all required IDs present",
                      missing))

    # Language coverage
    no_sw = [i for i, a in by_id.items() if not a.get("text", {}).get("sw")]
    no_en = [i for i, a in by_id.items() if not a.get("text", {}).get("en")]
    out.append(Result("content:swahili_text", "fail" if no_sw else "pass",
                      f"{len(no_sw)} answers lack Swahili text" if no_sw else "every answer has Swahili text", no_sw))
    out.append(Result("content:english_text", "fail" if no_en else "pass",
                      f"{len(no_en)} answers lack English text" if no_en else "every answer has English text", no_en))
    no_kik = [i for i in KIK_CORE if i in by_id and not by_id[i].get("text", {}).get("kik")]
    out.append(Result("content:kikuyu_core", "warn" if no_kik else "pass",
                      f"{len(no_kik)} of {len(KIK_CORE)} core answers lack Kikuyu text (Tier 2)" if no_kik else "all 8 core answers have Kikuyu text",
                      no_kik))

    # Length, sources, assumptions, banned words
    long_ones = [i for i, a in by_id.items() if len(a.get("text", {}).get("en", "")) > 220]
    out.append(Result("content:short_text", "warn" if long_ones else "pass",
                      f"{len(long_ones)} English texts over 220 chars (hard to listen to)" if long_ones else "all texts short enough to listen to",
                      long_ones))
    unsourced = [i for i, a in by_id.items()
                 if a.get("kind", "result") == "result" and not a.get("sources") and not a.get("assumption")]
    out.append(Result("content:sourced_results", "fail" if unsourced else "pass",
                      f"{len(unsourced)} result cards have no source and no assumption flag" if unsourced else "every result card is sourced or flagged as assumption",
                      unsourced))
    banned = []
    for i, a in by_id.items():
        blob = " ".join(str(v) for v in a.get("text", {}).values()).lower()
        for w in BANNED_WORDS:
            if w in blob:
                banned.append(f"{i}: '{w}'")
    out.append(Result("content:no_doses_or_marketing", "fail" if banned else "pass",
                      "found pesticide doses/brands or marketing words" if banned else "no doses, brands or marketing words",
                      banned))
    no_notsure = [i for i, a in by_id.items() if a.get("kind", "result") == "result" and a.get("severity") in ("act", "watch") and not a.get("not_sure")]
    out.append(Result("content:not_sure_line", "warn" if no_notsure else "pass",
                      f"{len(no_notsure)} act/watch cards lack a 'what we are not sure about' line" if no_notsure else "all act/watch cards say what they are unsure about",
                      no_notsure))

    # Rules
    if not r_path.exists():
        out.append(Result("content:rules", "skip", "src/content/rules.json missing"))
    else:
        rules = read_json(r_path)
        problems: list[str] = []
        if not rules or rules[-1].get("if") not in ({}, None) or rules[-1].get("then") != "ask_officer":
            problems.append("last rule must be {\"if\": {}, \"then\": \"ask_officer\"}")
        for n, r in enumerate(rules):
            cond = r.get("if", {})
            for k in cond:
                if k not in ALLOWED_CONDITIONS:
                    problems.append(f"rule {n}: unknown condition '{k}'")
            if "window" in cond and cond["window"] not in ALLOWED_WINDOWS:
                problems.append(f"rule {n}: unknown window '{cond['window']}'")
            if r.get("then") not in by_id:
                problems.append(f"rule {n}: target '{r.get('then')}' not in answers.json")
            if any(isinstance(v, (int, float)) for v in cond.values()) and not (r.get("assumption") or r.get("sources")):
                problems.append(f"rule {n}: numeric threshold without sources or assumption flag")
        out.append(Result("content:rules", "fail" if problems else "pass",
                          f"{len(problems)} rule problems" if problems else f"{len(rules)} rules valid, catch-all is ask_officer",
                          problems))

    # Season
    if not s_path.exists():
        out.append(Result("content:season", "skip", "src/content/season.json missing"))
    else:
        season = read_json(s_path)
        names = {w.get("name") for w in season.get("windows", [])}
        bad = sorted(names - ALLOWED_WINDOWS)
        has_src = bool(season.get("source") or season.get("sources"))
        status = "fail" if bad or not has_src else "pass"
        out.append(Result("content:season", status,
                          ("unknown windows: " + ", ".join(bad)) if bad else ("no source listed" if not has_src else f"{len(names)} windows, sourced"),
                          []))
    return out
