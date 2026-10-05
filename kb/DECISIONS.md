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
| 13 | Sat 21:00 | Repo lives in `MIT_Hackathon_7`; the product lives in `app/` | Arthur's choice of layout | Arthur |
| 14 | Sat 21:00 | UI built in Lovable; engine (ML, offline, storage) built in Cursor; strict path ownership | Avoid sync overwrites | Lead |
| 15 | Sun 4 Oct, 10:40 | Review agents run through `app/backend/agent_framework`. They check the app concurrently and do not generate the product. Decision 9 still stands for a build pipeline. | Arthur asked for a concurrent check of the whole app before the freeze. | Lead |
| 16 | Sun 4 Oct, 11:00 | The same runner now orchestrates the roster as an audit DAG: research, ml, engine, ui, content, docs, then qa, redteam, and judge. A seat starts only after the seats it depends on have finished. Every seat reports gaps and does not edit owned product paths. Decision 9 still blocks a pipeline that writes the app. Decision 15 still stands: this runner checks and does not generate the product. | The freeze check needs dependency order, and builder seats must stay audits. | Lead |
