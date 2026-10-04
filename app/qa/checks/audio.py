"""Audio exists for every answer in Swahili (R4) and for the Kikuyu core (R5); total under budget."""
from __future__ import annotations

from pathlib import Path

from qa.common import Result, dir_size, human_bytes, read_json
from qa.checks.content import KIK_CORE

AUDIO_BUDGET = 4 * 1024 * 1024


def run(root: Path) -> list[Result]:
    a_path = root / "src/content/answers.json"
    audio = root / "public/audio"
    if not a_path.exists() or not audio.exists():
        return [Result("audio", "skip", "answers.json or public/audio missing")]
    answers = read_json(a_path)
    if isinstance(answers, dict):
        answers = list(answers.values())
    # Nudges are SMS text only (content-voice brief), so they need no audio.
    ids = [a["id"] for a in answers if "id" in a and a.get("kind") != "nudge"]

    out: list[Result] = []
    missing_sw = [i for i in ids if not (audio / "sw" / f"{i}.mp3").exists()]
    out.append(Result("audio:swahili", "fail" if missing_sw else "pass",
                      f"{len(missing_sw)} answers lack Swahili audio" if missing_sw else f"Swahili audio present for all {len(ids)} answers",
                      missing_sw))
    missing_kik = [i for i in KIK_CORE if i in ids and not (audio / "kik" / f"{i}.mp3").exists()]
    out.append(Result("audio:kikuyu_core", "warn" if missing_kik else "pass",
                      f"{len(missing_kik)} core answers lack Kikuyu audio (Tier 2)" if missing_kik else "Kikuyu audio present for the 8 core answers",
                      missing_kik))
    size = dir_size(audio, (".mp3", ".ogg", ".wav"))
    out.append(Result("audio:budget", "fail" if size > AUDIO_BUDGET else "pass",
                      f"audio total {human_bytes(size)} (budget {human_bytes(AUDIO_BUDGET)})"))
    man = audio / "manifest.json"
    out.append(Result("audio:manifest", "pass" if man.exists() else "warn",
                      "manifest.json present" if man.exists() else "manifest.json missing (engine, duration, text hash per clip)"))
    return out
