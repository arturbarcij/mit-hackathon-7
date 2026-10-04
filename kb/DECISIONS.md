# Decisions

Append only. Newest at the bottom. Agents do not reopen a decision here without the lead.

| # | When (CEST) | Decision | Why | Who |
|---|---|---|---|---|
| 1 | Sat 3 Oct, 20:00 | Sector: Annex B, Agriculture | Chosen by Arthur | Arthur |
| 2 | Sat 20:10 | One decision: act / wait / ask the officer about a leaf problem in coffee, with timing | Brief asks for one better decision; covers identify, time, and extension next step | Lead |
| 3 | Sat 20:10 | Reference geography: Kenya central highlands (Nyeri area) | Matches Noor's farm and languages; JMuBEN is Kenyan Arabica | Lead |
| 4 | Sat 20:10 | Languages: Swahili full, Kikuyu subset (machine, pending review), English | National + home language; Kikuyu answers the less-supported-language question | Lead |
| 5 | Sat 20:10 | Price reference out of core scope; Tier 3, non-AI | A lookup is not an AI job; honesty scores | Lead |
| 6 | Sat 20:10 | No runtime LLM. Fixed answer bank; generative AI only at build time (voice) | Offline rule, hallucination guardrail, checkable outputs | Lead |
| 7 | Sat 20:10 | Weekend capture protocol: 10 leaves photographed at the house on a plain page | Phone stays at the house; smartphone only at weekends; narrows domain gap | Lead |
| 8 | Sat 20:40 | Product name: Jani (working) | Swahili for leaf; short | Lead |
| 9 | Sat 20:50 | No agent framework now. Agents = markdown briefs in `kb/agents` + Claude Code agent files. LangGraph or a pipeline only if time is left after the MVP | Saves 2 to 8 hours; judges score the tool, not the build pipeline | Arthur |
| 10 | Sat 20:55 | Six builder agents first: research, ml, engine, ui, content-voice, docs. Reviewers (qa, redteam, judge) and pitch added later | MVP focus | Arthur |
| 11 | Sat 20:55 | Training on Arthur's laptop GPU; Kaggle as fallback | Cloud workspace has no GPU | Lead |
| 12 | Sat 20:55 | Gemini Pro as independent reviewer (translations, advice, videos); not in the product | Second model family catches different errors | Lead |
| 13 | Sat 21:00 | Repo lives in `MIT_Hackathon_7/app`; API keys in `app/backend/.env` (git-ignored) | Arthur's choice of layout | Arthur |
| 14 | Sat 21:00 | UI built in Lovable; engine (ML, offline, storage) built in Cursor; strict path ownership | Avoid sync overwrites | Lead |
| 15 | Sat 21:20 | GitHub repo `arturbarcij/mit-hackathon-7` is the top-level `MIT_Hackathon_7` folder (not `app/`); private until submission | Arthur created it that way | Arthur |
| 16 | Sat 21:25 | Bright Data MCP configured for Cursor and Claude Code on the laptop; research agent runs there (cloud session cannot reach Bright Data) | Egress limits in the cloud workspace | Lead |
| 17 | Sat 21:45 | No general agent framework. Instead a QA harness (`app/qa/`): deterministic checks for every requirement plus judge and red-team LLM reviews. Framework or LangGraph only if time remains after MVP | Scored criteria reward verified claims, not build tooling; harness costs ~90 min and guards the pass/fail gate | Arthur + Lead |
| 18 | Sat 22:30 | Research adopted: extension ratio 1:1,380 (MoALD 2025); no national yield-decline claim; women smartphone 42%; JMuBEN2 added to training data; MMS-TTS and NLLB flagged CC BY-NC | kb/research/EVIDENCE.md and DATASETS.md, primary sources | Lead |
| 19 | Sat 22:30 | Behind schedule by ~1 h. Run five lanes at once: ml (Cursor chat 1, GPU), engine (Cursor chat 2, background), ui (Lovable via Claude), content (Claude), docs skeletons (Claude sub-agent). No new agent types | Parallelism, not more roles, recovers time | Lead |
| 20 | Sat 22:45 | Add the cooperative outlier map ("is it me, or is it everyone?"): synthetic deliveries and plots (labelled), real Sentinel-2 NDVI and rainfall; reason codes, abstention; feeds an officer-approved SMS nudge to the leaf check. New geo agent, runs in Cursor on Windows (only machine with satellite access). Tier 1b; cut line 02:00 drops NDVI, keeps deliveries + rainfall | Directly answers Annex B's "not sure why"; uses the cooperative registry; closes the loop map to phone to officer | Arthur + Lead |
| 21 | Sat 23:00 | Two repos: mit-hackathon-7 (kb, ml, geo, qa, docs, backend, produced assets in app/) and jani-web (Lovable: UI + engine, live URL) cloned into web/. One-way asset sync app/ to web/ by app/backend/scripts/sync_to_web.py (engine owns it). Both public after submission; READMEs link each other | Lovable's GitHub sync creates its own repo and cannot push into a subfolder | Lead |
| 22 | Sat 23:40 | No JEV classifier: hosted and text-only, so it breaks the offline rule and the client_clean check and adds nothing over the fixed answer bank. OpenResearch deferred to after submission: Windows beta, worktrees carry neither uncommitted code nor git-ignored data, one GPU, and an agent loop would tune on the held-out sets. Instead the lead builds an overnight research harness in `app/ml/research/`: pre-registered jobs, a val-only selection rule, held-out sets scored once after the choice | Serves evidence (W3) without new tooling; protects the honest held-out claim | Arthur + Lead |
| 22 | Sun 4 Oct, 00:00 | Lead ports the non-ML engine (rules, season clock, answer cards, quality gate, JANI1 SMS) straight into the Lovable project; mock classifier becomes a transparent colour rule. Engine lane takes over ONNX inference and PWA. Source and tests in kb/lead/ | Engine lane blocked on GitHub sync; the live app showed invented translations and a non-contract SMS format | Lead (Claude) |
