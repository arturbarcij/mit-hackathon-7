# Video coverage of the PDF content items (a) to (e)

Owner: pitch. Status: draft from the scripts, Sat 3 Oct. Timestamps are planned (kb/pitch/VIDEO*.md). Replace with actual times after the takes are edited. Tick a box only when the item is both spoken or shown in the final file.

PDF source: Section 08 of the challenge brief (video of 2 to 5 minutes). Platform rule (MASTER_PROMPT 2.10): three videos, each MP4 or MOV, at most 60 seconds, at most 1 GB. Our three videos must jointly cover all five items.

## Coverage table

| Item | Video | Planned second | Spoken | Shown on screen | Done |
|---|---|---|---|---|---|
| (a) Problem statement, one sentence, with evidence | 1 | 0:08 to 0:33 | Spoken version of the sentence, "a 2021 review reports" | Written sentence slide at 0:20, source tags for MoALD 2025 and Agronomy 2021 | [ ] |
| (b) AI capability, why not a simpler tool, guardrails | 3 | 0:10 to 0:20 AI capability; 0:31 to 0:41 why not simpler; 0:41 to 0:49 guardrails | Yes, all three | Model size and latency, four crossed-out cards (SMS, spreadsheet, search, officer), guardrail list | [ ] |
| (b) support | 2 | 0:38 to 0:45 | "not sure, ask the officer" | Abstention screen | [ ] |
| (c) End-to-end demo | 2 | 0:00 to 0:55 | Yes | Airplane mode, language and consent, ten photos, plot summary, Swahili audio, Kikuyu clip, abstention, decision and pre-filled SMS, officer confirms | [ ] |
| (d) Where it sits in the user's day | 2 | 0:00 to 0:06 and 0:45 to 0:50 | "Saturday, at the house"; "I press send myself" | Timeline bar for Noor's week: Saturday morning, Saturday at the house, weekdays by SMS, officer visit | [ ] |
| (d) Tech stack | 3 | 0:49 to 0:55 | "React app, ONNX Runtime, Supabase. Saturday at the house; follow-up by SMS." | Stack list, repo tree, live URL | [ ] |
| (e) Our take on localising AI | 1 | 0:33 to 0:52 | Yes | Kikuyu and Swahili cards, World Bank quote tag | [ ] |

All five items have at least one spoken or shown instance. Weak point: (d) "where the tool sits in her day" is mostly shown (the timeline bar) with one spoken line at 0:00 in Video 2 and one in Video 3. If there is spare time in the edit, add one spoken sentence naming the weekday follow-up. The weekday SMS reminder is Tier 3 and simulated; if it is not built, drop that part of the bar and say nothing about it.

## Cross-check against the brief's wording

| Brief wording | Where |
|---|---|
| (a) "Because of this tool, [user] will [action] by [when] that they would otherwise [not do / do late / do worse]; we know because [evidence]" | PROBLEM_STATEMENT.md slot table |
| (b) "what the tool does with AI ... why a simpler tool (SMS, a spreadsheet, a search) would not do the same job. Mention the guardrails" | Video 3, three beats |
| (c) "prototype demo with clear user journey end to end" | Video 2 |
| (d) "where the tool sits in the user's day ... when they open it, what they do, what happens next. ... include tech stack details" | Video 2 timeline bar, Video 3 stack beat |
| (e) "what localizing AI development means to you" | Video 1 closing section |

## Flags

1. **Cooperative outlier map** ("is it me, or is it everyone?", MASTER_PROMPT 3.4 and 3.5). On Sat 23:35 STATUS.md has G1 to G4 `todo` and U2 `doing`. It is Tier 1b and must never block the farmer app. It is **not demoable tonight**. Plan: Video 2 shows the map only if G4 is `done` and it renders on the live URL at the 11:00 recording slot; Video 3 shows it in the diagram only if it runs. Deliveries and plots are synthetic and labelled; satellite and rainfall are real. If it is dropped, no PDF item is lost, because (a) to (e) do not depend on it.
2. **SMS to dashboard** is not automated (no gateway in MASTER_PROMPT 5.1). The officer's referral in Video 2 is a seeded record and is labelled "simulated".
3. **Kikuyu** is Tier 2. If no clip exists by the 09:30 cut, delete Video 2 beat 0:30 to 0:38 and keep (e) in Video 1 as "Swahili, with Kikuyu planned" only if that is true. Do not show Kikuyu that does not exist.
4. **Swahili review (L3)** is still `todo`. Keep the on-screen note until a reviewer signs off.

## Technical check (fill after export, with ffprobe)

Command per file: `ffprobe -v error -show_entries format=format_name,duration,size:stream=codec_name,width,height -of default=nw=1 video/<file>`

| File | Container | Duration (s) | Size (MB) | Resolution | Under 60 s | Under 1 GB | Burned-in captions |
|---|---|---|---|---|---|---|---|
| video/video1_team.mp4 | [PENDING: V1] | [PENDING: V1] | [PENDING: V1] | [PENDING: V1] | [ ] | [ ] | [ ] |
| video/video2_demo.mp4 | [PENDING: V1] | [PENDING: V1] | [PENDING: V1] | [PENDING: V1] | [ ] | [ ] | [ ] |
| video/video3_tech.mp4 | [PENDING: V1] | [PENDING: V1] | [PENDING: V1] | [PENDING: V1] | [ ] | [ ] | [ ] |

## Three-minute backup cut (if the platform takes one 2 to 5 minute video)

Order 1, 2, 3. Target about 2 minutes 45 s to 3 minutes. Planned positions: Video 1 at 0:00, Video 2 at about 0:55, Video 3 at about 1:50 (shift to match the real lengths).

```
printf "file 'video1_team.mp4'\nfile 'video2_demo.mp4'\nfile 'video3_tech.mp4'\n" > video/list.txt
ffmpeg -f concat -safe 0 -i video/list.txt -c copy video/jani_backup_3min.mp4
```

If `-c copy` fails because codec settings differ, re-encode:
`ffmpeg -f concat -safe 0 -i video/list.txt -c:v libx264 -crf 20 -c:a aac -b:a 160k -pix_fmt yuv420p video/jani_backup_3min.mp4`

The backup cut is not one of the three uploaded files. Do not commit anything under `video/` except this file.

## Captions
Burned-in English, from kb/pitch/CAPTIONS/video1.srt to video3.srt (drafts generated from the scripts by kb/pitch/make_srt.py; re-time against the real takes). Burn in with: `ffmpeg -i in.mp4 -vf "subtitles=captions.srt:force_style='FontSize=22,Outline=2'" -c:a copy out.mp4`. The drafts do not caption the app's own Swahili and Kikuyu audio; add the English text of the answer card on screen during those clips.
