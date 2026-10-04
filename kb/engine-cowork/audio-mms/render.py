#!/usr/bin/env python3
"""Render a fallback audio bank for Jani with Meta MMS-TTS (VITS).

Usage:
    python3 render.py <path/to/answers.json> [--out DIR] [--langs sw,kik]
                      [--dry-run] [--force] [--hf-home DIR]

Swahili (sw):  facebook/mms-tts-swh for every answer with text.sw
Kikuyu  (kik): facebook/mms-tts-kik for every answer with text.kik

Both models are CC-BY-NC-4.0 (non-commercial). Output is a machine voice
pending native speaker review. The script never changes answers.json.

Outputs under --out (default: the directory of this script):
    <lang>/<id>.mp3          mono, 32 kbps, 16 kHz, libmp3lame
    manifest.json            one row per clip, see MANIFEST_FIELDS below
    _work/<lang>/<id>.wav    intermediate wav at the model rate (16 kHz)
    _work/spot_<lang>.mp3    3-clip concatenations for a listening check
    SPOTCHECK_<lang>.mp3     copy of the first spot check, for the team

Re-runs skip clips whose rendered text hash has not changed, unless
--force is given. --dry-run writes the manifest with text_rendered and
substitutions but renders no audio and needs no model download.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata

MODELS = {
    "sw": "facebook/mms-tts-swh",
    "kik": "facebook/mms-tts-kik",
}
LICENCE = "CC-BY-NC-4.0"
VOICE = "machine (MMS-TTS), pending native speaker review"
SEED = 42
MP3_BITRATE = "32k"
MP3_RATE = 16000

# MMS does not read digits. Map the digits that appear in the answer bank.
# Anything not in the table is left as a digit and flagged in the manifest.
NUMBER_WORDS = {
    "sw": {
        "1": "moja", "2": "mbili", "3": "tatu", "4": "nne", "5": "tano",
        "6": "sita", "7": "saba", "8": "nane", "9": "tisa", "10": "kumi",
    },
    "kik": {
        "10": "ikũmi",
    },
}

# Kikuyu tilde vowels. Used only if the tokenizer has no token for them.
TILDE_MAP = {"ĩ": "i", "ũ": "u", "Ĩ": "I", "Ũ": "U"}

# Duration per character outside this band usually means tokenizer trouble.
SPC_LOW, SPC_HIGH = 0.04, 0.20


def text_hash(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def replace_digits(text, lang):
    """Return (new_text, substitutions, unmapped_digits)."""
    subs, unmapped = [], []
    table = NUMBER_WORDS.get(lang, {})

    def repl(m):
        d = m.group(0)
        if d in table:
            subs.append({"from": d, "to": table[d], "reason": "digit_to_word"})
            return table[d]
        unmapped.append(d)
        return d

    return re.sub(r"\d+", repl, text), subs, unmapped


def map_tildes(text):
    subs = []
    out = []
    for ch in text:
        if ch in TILDE_MAP:
            out.append(TILDE_MAP[ch])
        else:
            out.append(ch)
    for k, v in TILDE_MAP.items():
        n = text.count(k)
        if n:
            subs.append({"from": k, "to": v, "count": n, "reason": "tilde_vowel_not_in_vocab"})
    return "".join(out), subs


def prepare_text(text, lang, tilde_strategy):
    """tilde_strategy: 'keep' or 'map'. Returns (rendered, subs, flags)."""
    rendered = unicodedata.normalize("NFC", text)
    rendered, subs, unmapped = replace_digits(rendered, lang)
    flags = []
    if unmapped:
        flags.append("unmapped_digits:" + ",".join(unmapped))
    if lang == "kik" and tilde_strategy == "map":
        rendered, tsubs = map_tildes(rendered)
        subs += tsubs
    return rendered, subs, flags


def ffmpeg_to_mp3(wav, mp3):
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-ar",
         str(MP3_RATE), "-c:a", "libmp3lame", "-b:a", MP3_BITRATE, mp3],
        check=True,
    )


def mp3_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return round(float(out), 3)


def audio_stats(wave, sr):
    """Peak level (dBFS) and silence ratio (frames under -40 dBFS)."""
    import numpy as np
    x = np.asarray(wave, dtype=np.float32)
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    peak_db = 20 * np.log10(peak) if peak > 0 else -120.0
    frame = int(sr * 0.02)
    n = x.size // frame
    if n == 0:
        return round(peak_db, 1), 1.0
    frames = x[: n * frame].reshape(n, frame)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    thr = 10 ** (-40 / 20)
    return round(peak_db, 1), round(float(np.mean(rms < thr)), 3)


def load_model(name):
    import torch
    from transformers import AutoTokenizer, VitsModel
    tok = AutoTokenizer.from_pretrained(name)
    model = VitsModel.from_pretrained(name)
    model.eval()
    return tok, model


def check_tilde_strategy(tok):
    """Return 'keep' if the kik tokenizer knows ĩ and ũ, else 'map'."""
    vocab = tok.get_vocab()
    known = all(c in vocab for c in ("ĩ", "ũ"))
    return ("keep" if known else "map"), sorted(vocab.keys())


def synth(tok, model, text, seed=SEED):
    import torch
    torch.manual_seed(seed)
    inputs = tok(text, return_tensors="pt")
    unk = tok.unk_token_id
    n_unk = int((inputs["input_ids"] == unk).sum()) if unk is not None else 0
    with torch.no_grad():
        out = model(**inputs).waveform[0]
    return out.numpy(), model.config.sampling_rate, n_unk


def write_wav(path, wave, sr):
    import numpy as np
    from scipy.io import wavfile
    x = np.clip(wave, -1.0, 1.0)
    wavfile.write(path, sr, (x * 32767).astype(np.int16))


def concat_mp3(files, out):
    lst = out + ".txt"
    with open(lst, "w") as f:
        for p in files:
            f.write("file '%s'\n" % os.path.abspath(p))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    os.remove(lst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answers")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--langs", default="sw,kik")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--hf-home", default=None)
    args = ap.parse_args()

    if args.hf_home:
        os.environ["HF_HOME"] = args.hf_home
    os.environ.setdefault("HF_HOME", os.path.join(args.out, "_work", "hf"))

    with open(args.answers, encoding="utf-8") as f:
        answers = json.load(f)
    langs = [l for l in args.langs.split(",") if l]
    work = os.path.join(args.out, "_work")
    os.makedirs(work, exist_ok=True)

    manifest_path = os.path.join(args.out, "manifest.json")
    old = {}
    if os.path.exists(manifest_path):
        try:
            for row in json.load(open(manifest_path, encoding="utf-8"))["clips"]:
                old[(row["lang"], row["id"])] = row
        except Exception:
            old = {}

    report = {"models": {}, "tokenizer": {}, "render_seconds": {}, "blocked": {}}
    clips = []
    t_all = time.time()

    for lang in langs:
        model_name = MODELS[lang]
        os.makedirs(os.path.join(args.out, lang), exist_ok=True)
        os.makedirs(os.path.join(work, lang), exist_ok=True)
        tilde_strategy = "keep"
        tok = model = None
        if not args.dry_run:
            try:
                t0 = time.time()
                tok, model = load_model(model_name)
                report["models"][lang] = {"name": model_name, "load_s": round(time.time() - t0, 1),
                                         "sampling_rate": model.config.sampling_rate}
            except Exception as e:  # network refusal or missing weights
                report["blocked"][lang] = "%s: %s" % (type(e).__name__, str(e)[:400])
                print("BLOCKED %s: %s" % (lang, report["blocked"][lang]), file=sys.stderr)
                args_dry_for_lang = True
            else:
                args_dry_for_lang = False
            if tok is not None:
                strat, vocab = check_tilde_strategy(tok)
                report["tokenizer"][lang] = {"vocab_size": len(vocab), "vocab": vocab,
                                             "has_tilde_vowels": strat == "keep"}
                if lang == "kik":
                    tilde_strategy = strat
                    report["tokenizer"][lang]["tilde_strategy"] = strat
        else:
            args_dry_for_lang = True

        t_lang = time.time()
        for a in answers:
            text = a.get("text", {}).get(lang)
            if not text:
                continue
            rendered, subs, flags = prepare_text(text, lang, tilde_strategy)
            h = text_hash(rendered)
            mp3 = os.path.join(args.out, lang, a["id"] + ".mp3")
            row = {
                "lang": lang, "id": a["id"], "file": "%s/%s.mp3" % (lang, a["id"]),
                "bytes": None, "duration_s": None, "chars": len(rendered),
                "s_per_char": None, "peak_dbfs": None, "silence_ratio": None,
                "text_rendered": rendered, "text_original": text,
                "text_hash": h, "substitutions": subs, "flags": flags,
                "model": model_name, "licence": LICENCE, "voice": VOICE, "seed": SEED,
                "status": "not_rendered",
            }
            if a.get("kind") == "nudge":
                row["flags"].append("nudge_is_sms_only_in_spec")

            prev = old.get((lang, a["id"]))
            if (prev and not args.force and prev.get("text_hash") == h
                    and prev.get("status") == "rendered" and os.path.exists(mp3)):
                prev["flags"] = row["flags"]
                clips.append(prev)
                continue

            if args_dry_for_lang:
                row["status"] = "dry_run" if args.dry_run else "blocked_no_model"
                clips.append(row)
                continue

            wave, sr, n_unk = synth(tok, model, rendered)
            wav = os.path.join(work, lang, a["id"] + ".wav")
            write_wav(wav, wave, sr)
            ffmpeg_to_mp3(wav, mp3)
            dur = round(len(wave) / sr, 3)
            peak, sil = audio_stats(wave, sr)
            row.update({
                "bytes": os.path.getsize(mp3), "duration_s": dur,
                "s_per_char": round(dur / max(1, len(rendered)), 4),
                "peak_dbfs": peak, "silence_ratio": sil, "unk_tokens": n_unk,
                "status": "rendered",
            })
            if row["s_per_char"] < SPC_LOW or row["s_per_char"] > SPC_HIGH:
                row["flags"].append("duration_per_char_outlier")
            if n_unk:
                row["flags"].append("unk_tokens:%d" % n_unk)
            clips.append(row)
            print("%s/%s %.2fs %dB" % (lang, a["id"], dur, row["bytes"]))
        report["render_seconds"][lang] = round(time.time() - t_lang, 1)

        done = [os.path.join(args.out, c["file"]) for c in clips
                if c["lang"] == lang and c["status"] == "rendered"]
        for i in range(0, min(len(done), 9), 3):
            group = done[i:i + 3]
            if len(group) < 2:
                break
            spot = os.path.join(work, "spot_%s%s.mp3" % (lang, "" if i == 0 else "_%d" % (i // 3)))
            concat_mp3(group, spot)
            if i == 0:
                shutil.copy(spot, os.path.join(args.out, "SPOTCHECK_%s.mp3" % lang))

    totals = {}
    for lang in langs:
        rows = [c for c in clips if c["lang"] == lang]
        totals[lang] = {
            "clips": len(rows),
            "rendered": sum(1 for c in rows if c["status"] == "rendered"),
            "bytes": sum(c["bytes"] or 0 for c in rows),
            "duration_s": round(sum(c["duration_s"] or 0 for c in rows), 1),
            "outliers": [c["id"] for c in rows if "duration_per_char_outlier" in c["flags"]],
        }
    totals["all_bytes"] = sum(v["bytes"] for k, v in totals.items() if isinstance(v, dict))
    totals["budget_bytes"] = 4 * 1024 * 1024
    report["render_seconds"]["total"] = round(time.time() - t_all, 1)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "answers_file": os.path.abspath(args.answers),
                   "licence": LICENCE, "voice": VOICE, "seed": SEED,
                   "mp3": {"bitrate": MP3_BITRATE, "rate_hz": MP3_RATE, "channels": 1},
                   "totals": totals, "report": report, "clips": clips},
                  f, ensure_ascii=False, indent=1)
    print(json.dumps(totals, indent=1))
    if report["blocked"]:
        print("BLOCKED:", json.dumps(report["blocked"], indent=1), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
