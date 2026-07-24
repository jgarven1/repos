# Executive Summary

Rocket55 is a full-service digital marketing agency (paid media, SEO/"SXO", social, content, analytics, and website builds) running a large book of business — **~165 distinct client accounts** are visible in this seven-month window. Slack is where the *coordination* happens, but Slack is **not** the system of record. The real work lives in **Accelo** (jobs/tasks/time) and **Google Drive** (documents), with Slack acting as the connective tissue between them.

## Signal vs. noise at a glance

| Bucket | Channels | Human msgs | Keep? |
|---|--:|--:|---|
| Client account teams (`-all`) | 55 | 11,165 | **Signal** |
| Client website builds (`-web`) | 46 | 9,835 | **Signal** |
| Client single-channel accounts | 69 | 14,843 | **Signal** |
| Client shared/admin/HubSpot/retainer | 12 | 1,218 | **Signal** |
| Client overview docs (`FC:`) | 27 | 155 | **Signal (pointers)** |
| Prospect / upsell | 4 | 22 | **Signal (thin)** |
| Internal ops, tooling & social | 56 | 5,521 | **Mixed** |

**~37,000 of ~43,000 human messages (≈85%) are client-related.** The noise is concentrated and easy to strip: `1password-alerts`, `1password-notifications`, `verification-codes`, `anomaly-detections`, `alerts-implementation`, and `integration_logs` are almost entirely automated (they account for most of the 17,400 bot messages). Social channels (`water-cooler`, `random`, `book-club`, `foodies`, `music`, `movie-mondays`, sports, `catscatsandmorecats`, etc.) are genuine but non-operational.

A small set of **internal channels is high-signal for *process*** rather than for any one client: `general` (announcements, policy, Accelo best-practices), `pm-am-resourcing` (capacity planning), `r55_out-of-office` + the OOO Canvas, and `temp-hubspot-implement` (the agency migrating its *own* sales stack).

## Where everything gets saved (the short version)

| System | Role | Evidence strength |
|---|---|---|
| **Accelo** (`rocket55.accelo.com`) | **System of record for delivery** — jobs, tasks, time tracking, retainer buckets, OOO. 1,124 links. | Very strong |
| **Google Drive / Docs / Sheets** | **Document store** — every client has a "client folder"; brand guides, keyword maps, meeting notes, strategy decks, coverage docs. ~1,900 links. | Very strong |
| **Figma** | Design & dev **handoff** for web builds. 297 links. | Strong |
| **1Password** ("1Pass") | **Credential vault** for all client logins (migrated *from* LastPass mid-2025). | Strong |
| **Slack Canvas / "Channel Overview"** | Per-client **quick-reference hub** pinned to the channel (budgets, sales handoff, links, notes). | Strong |
| **HubSpot** (+ **PandaDoc**, **QuickBooks**) | Marketing automation/CRM for clients; PandaDoc for internal sales-ops docs; QuickBooks for invoicing. | Strong (client MA work) |
| **Proposify** | Client-facing **proposals** (`rocket55.proposify.com`). | Strong |
| **Notion** (`rocket55.notion.site`) | Ongoing client notes / status. | Strong |
| **WordPress** + **Kinsta** (hosting), **SendGrid** (email), **Gravity Forms** | The website delivery stack. | Strong |
| **Looker / (Google) Data Studio** | Client **reporting** dashboards. | Strong |
| **Fathom** (+ Fireflies) | Meeting/call **recordings & summaries**, linked from client Canvases. | Strong |
| **Beautiful.ai / Gamma / Canva** | Client-facing decks & recaps. | Moderate |
| **TomsPlanner** (web timelines), **Canto** (client DAM), **Asana**, **Trello**, **Jira**, **SharePoint** | Web-project or client-*owned* systems used on specific accounts. | Situational |

## The five things you asked about

1. **Where things get saved** → Accelo (work) + Google Drive "client folders" (docs) + 1Password (logins) + a standardized Slack Canvas per client. Playbook §1; template anatomy in `canvas-appendix.md`.
2. **Contracts / SOWs** → **Signed MSAs and SOWs live in the client's Google Drive folder, linked from the overview Canvas.** Proposals run through **Proposify** (client-facing) and **PandaDoc** (internal sales ops). Scoping/pricing debates are frequent ("not sure how much we should charge to make money on this project"). Playbook §2.
3. **Templates** → A real, standardized library: the **client-overview Canvas template**, a cloned **"Mission Control"** tracker, **onboarding/access checklist**, **kickoff & discovery agendas**, **keyword maps**, **reporting dashboards**, **social framework**, **scorecards**, **coverage docs**. Playbook §3, appendix.
4. **Repeatable processes** → Sales→delivery handoff, client onboarding, monthly reporting, resourcing/capacity planning, OOO coverage, time-logging, and an **EOS/Traction "Weekly Pod Meeting"** (scorecard + IDS issues + health flags). Playbook §4.
5. **Account management** → A **pod/team model** under Account Directors, tracked against a **"master account list,"** with a formal **Transition List** SOP and per-client **weekly scorecards**/health flags. Playbook §5, `collaboration.md`, appendix.

## Team collaboration — headline

Collaboration is **strong and disciplined**. The dominant pattern is *"turn this into a task"* — conversations consistently resolve into Accelo jobs with owners and due dates rather than trailing off. Web builds run through a **PM-led resourcing pipeline** (Kerri Graber posts weekly dev/design/content/UX availability). The busiest connectors are **Account Directors and Project Managers** (Rachel Gunderson, Kerri Graber, Emma Noriega, Kaitlyn Benson), which is what you'd hope to see. Friction points that recur: **finding creative/assets** ("can't find it in the client folder"), **access/credentials**, and **scope/pricing** on add-on work. See `collaboration.md`.
