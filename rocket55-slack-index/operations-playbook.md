# Operations Playbook — What the Slack Export Reveals

This is the deep dive: **where work and files live, how contracts/SOWs are handled, what templates exist, which processes repeat, and how accounts are managed.** Everything here is drawn from the messages; representative examples are cited as `[channel, date]`.

> **Update — Canvas contents now included.** The bodies of the client "Overview"/"Resources" Canvases (missing from the export) were retrieved live from Slack. They are primary-source evidence for almost everything below; see **`canvas-appendix.md`** for the full text and the standardized template anatomy. Findings from the Canvases are marked **[Canvas]**.

---

## 1. Systems of record — where things get saved

Rocket55 runs a **two-brain** model: **Accelo** holds the *work*, **Google Drive** holds the *documents*, and Slack points at both.

### Accelo — the delivery system of record
`rocket55.accelo.com` is by far the most-linked internal system (**1,124 links**). It is where **jobs, tasks, time, and retainers** live. The vocabulary is everywhere:
- "let's get a task in for me to build out ad groups… you're task is set up for the 13th" `[renew-all, 2026-01-07]`
- "I just put it in the retainer bucket" `[ic-system-all, 2026-07-23]`
- Links are always of the form `?action=view_job&id=####` — every deliverable is a numbered **job**.
- **Time logging is governed**: *"Accelo quirk — if you log your time against a client, that time is marked as non-billable. Here are the best practices…"* `[general, 2026-01-27]`.
- **OOO lives in Accelo too** and is mirrored to a Canvas: *"I update the canvas every Monday with the out-of-office messages I can see in Accelo"* `[general, 2026-01-19]`.

Highest Accelo activity (proxy for actively-tracked delivery): `frsecure` (61), `halco` (57), `prinsco` (54), `maryland_oncology_hematology` (46), `atwell` / `renew-all` (40 each), `metro-state-all` (38), `cpc-all` / `r55-internal-gougeon-brothers` (35).

### Google Drive / Docs / Sheets — the document store
~1,900 links. **Every client has a "client folder"** and it is the expected home for anything durable:
- Brand guides, keyword maps ("we have an existing keyword map in the folder" `[alumiplate-all]`), creative, meeting notes, coverage docs, strategy decks.
- The norm is to *copy external files into the folder* so nothing is lost: *"I had to create a new document since that was not shareable… I just copied it and saved it in the FRS folder"* `[frsecure, 2026-05-26]`.
- Google Meet auto-records to a Drive **"Meet Recordings"** folder `[general, 2026-02-17]`; Fireflies and Fathom also capture calls (`fireflies-recap-gems`).
- Recurring pain point: **assets are hard to find** — *"i can't find it in my inbox… dug for like 15 min"* `[cpc-all]`, *"I'm not finding it in the CPC client folder"* `[cpc-all, 2026-04-02]`, *"I don't see it in the creative drive"* `[idi-all]`.

### 1Password — the credential vault
All client logins live in **1Password** ("1Pass"): *"they're in 1pass!"* `[renew-all]`, *"I got credentials saved in 1Password for the live site"* `[brigade-hometown-exteriors-web]`. The team **migrated from LastPass** in 2025 (`help-1password`, `FC: Help requests tracker`) — a transition still surfacing edge cases (recovery keys, vault ownership).

### Slack Canvas / "Channel Overview" — the per-client quick reference **[Canvas]**
**Every active client has a pinned Canvas** — titled `<Client> Overview`, `Channel Overview`, `Resources`, or `Important Links` (~40 of them; full inventory in `canvas-appendix.md`). It is the single fastest-reference hub and follows a **standardized skeleton**: Team (named discipline owners) → Key Dates (Internal/Client Kickoff, Roadmap) → Client Assets → Key links grouped **ADMIN / GENERAL / PAID / SXO / RevOps / Social / Web** → an **Access checklist** (Ads, GA, LinkedIn, GTM, Search Console, Website) → Client Notes.
- *"it's saved in the channel overview! [Internal Sales Handoff]"* `[halco, 2026-01-12]`
- *"here's the 2026 budget. i also put it in the ispiri overview canvas"* `[ispiri-all]`
- **"Mission Control"** is a **cloned per-client tracker spreadsheet** — the identical tab `gid=1509272238` appears on Atwell, Ispiri, Toppan Merrill, Maryland Oncology, and Turn Style, i.e. a master template duplicated for each account.
- The template is **adapted for regulated clients** — Maryland Oncology's Canvas adds a **"HIPAA Compliance: Advertising & Data"** doc.

### The website delivery stack
- **WordPress** (client sites) hosted on **Kinsta**; **SendGrid**/SMTP for transactional mail; **Gravity Forms** for form capture — e.g. launch checklist in `[amsoil-aerospace-web-build, 2026-03-12]`, SMTP/SendGrid setup in `[gerbig-web, 2026-03-16]`.
- **Figma** is the design surface and the **client handoff** point: *"within the Figma file > Handoff tab, Brigade has populated it with the sitemap…"* `[brigade-hometown-exteriors-web, 2026-06-04]`.

### Reporting & CRM
- **Looker / Data Studio** dashboards are the reporting deliverable ("build dashboard" jobs; "get them familiar with the looker" `[frsecure]`).
- **HubSpot** is the marketing-automation/CRM platform for many accounts; for internal sales ops the agency itself moved **Salesforce → HubSpot**, adopting **PandaDoc** (contracts) and keeping **QuickBooks** (invoicing) — see §2 and `temp-hubspot-implement`.

---

## 2. Contracts, SOWs & proposals

There is no single "contracts channel"; scoping happens **inside each account**, concentrated in `-web` (project scope) and `-admin` (account planning) channels.

- **SOW / scope** talk clusters in `mhub-web`, `ecowater-admin`, `big-blue-boxes-all`, `delta-dental-all`, `mmt-web`, `renew-all`, `anderson_manufacturing-web`, `cpc-all`.
- **Proposals** are frequent (162 keyword hits) — top: `prinsco-water-table-podcast`, `atwell`, `blaine-brothers`, `frsecure`, `polywater-all`, `sunrise-all`. Proposals are often PDFs saved to Drive: *"Atwell _ HubSpot Onboarding Proposal_LL.pdf"* `[atwell, 2026-07-23]`.
- **Pricing is an open, recurring judgment call**, not a fixed rate card: *"I've adjusted the proposal to only include phase 1… I'm not sure how much we should charge to make money on this project though"* `[atwell, 2026-07-14]`.
- **Proposal tooling is Proposify** for client-facing proposals (`rocket55.proposify.com`, on FRSecure and Work Smart IT overviews) **[Canvas]**; **PandaDoc** is being adopted for *internal sales-ops* documents, integrated with HubSpot, pending legal review: *"We're migrating to PandaDoc… Waiting on [name] to finish up work with our legal counsel"* `[temp-hubspot-implement, 2026-01-05]`.
- **Scope changes are tracked and communicated**: *"the scope is going down to $4k/month so we will be doing…"* `[ecowater-all, 2026-03-31]`. Budget/scope is the single most-discussed operational topic (799 keyword hits), heaviest in `metro-state-all`, `wagner-all`, `nura-clinics-and-cpi-all`, `tsr-injury-law`, `university-athlete20251210`, `toppan-web`, `ecowater-admin`.

**Where signed agreements live (gap closed by Canvas access):** executed contracts **are** archived — in the client's **Google Drive folder, linked from the overview Canvas**. The `security-studio` "Important Resources" Canvas lists a **Signed MSA** (Drive file) and **Signed SOW** (Google Doc) right at the top, alongside the Google folder, roadmap, and kickoff doc **[Canvas]**. The recurring risk isn't storage but *starting before signature* — e.g. CPC: *"SOW is shared, going to start work with the verbal agreement"* **[Canvas, Weekly Pod Meeting]**.

---

## 3. Templates — the reusable library

Templates are real and referenced by name (248 keyword hits):

- **New-client onboarding template**: *"its just the template for new client onboarding, so if they do have it already, you can just mark complete"* `[blaine-brothers, 2026-02-04]`.
- **Discipline-specific onboarding**: a **social dashboard build is "part of our onboarding template"** `[frsecure, 2026-01-12]`; social onboarding task docs `[otto-sport, 2026-04-07]`.
- **Kickoff docs** are a standard artifact (628 keyword hits): *"just got through the MMT kickoff doc"* `[mmt-web, 2026-01-21]`; heaviest in `toppan-web`, `prinsco-water-table-podcast`, `university-athlete20251210`, `tsr-injury-law`, `halco`.
- **Reporting template / process doc**: *"shared a reporting process doc with you via email"* `[cpc-all, 2026-05-18]`; executive-summary reporting variant described in `[obviouslee-admin, 2026-04-02]`.
- **Coverage doc** (OOO handoff) is a reused spreadsheet template linked from the OOO channel `[pm-am-resourcing, 2026-01-15]`.
- **Playbooks** (strategy deliverables, sometimes client- or partner-authored): social media playbooks for IDI and EcoWater (the latter from partner "Bald") `[idi-all]`, `[ecowater-all, 2026-03-11]`.

The heaviest "template" channel is `university-athlete20251210` (81 hits) — this looks like an email/asset-template–heavy engagement.

**The standardized artifact set [Canvas].** Beyond keyword hits, the Canvases reveal a consistent, reused library of per-client documents: **Mission Control** tracker (cloned template), **Internal Sales Handoff / Handoff Brief**, **Marketing Plan Blueprint**, **Discovery + Kickoff Call Agenda**, **Kickoff Deck** (Beautiful.ai), **Keyword Map**, **GBP Assessment**, **Technical SXO/Indexability Assessment**, **Reporting Dashboard** (Looker), **Ongoing Agenda/Notes** (Notion), **Asset Tracker**, **Campaign Plan** (Paid), **RevOps Technical Roadmap**, **Social Media Framework + Calendar**, and for web: **Web Project Brief / Timeline (TomsPlanner) / Questionnaire**. Account-ops templates: the **client Scorecard**, **OOO Coverage Plan**, and **Transition List** (see §4–§5).

---

## 4. Repeatable processes

Process language shows up 425 times; the clearest repeatable playbooks:

1. **Sales → delivery handoff.** An **"Internal Sales Handoff"** doc is saved to the client's channel overview at kickoff `[halco, 2026-01-12]`.
2. **Client onboarding.** Templated, multi-discipline (analytics dashboard build, access collection, month-1/month-2 task planning, kickoff doc). See the `onboarding` evidence across `frsecure`, `graco`, `otto-sport`, `atwell` (HubSpot onboarding as a productized offering).
3. **Monthly reporting.** Standardized around Looker/Data Studio with a defined structure (data page + insights/executive summary), reused across accounts `[obviouslee-admin, 2026-04-02]`.
4. **Resourcing / capacity planning.** Kerri Graber (Lead Web PM) posts a **weekly resourcing status report** for dev — later expanded to **design, content, and UX** — with named availability and "dev hold times." Teams book hours against individuals (*"I hold 5 hours a week for Toppan on Zac"*) `[pm-am-resourcing, 2026-01-16 / 2026-02-02]`.
5. **OOO coverage.** Every OOO gets a **coverage doc** (spreadsheet) with a notes column for the covering PM; the OOO Canvas is refreshed weekly from Accelo `[pm-am-resourcing]`, `[general]`.
6. **Time-logging hygiene.** Documented best-practices to avoid time landing as non-billable `[general, 2026-01-27]`.
7. **Website launch process.** A repeatable launch sequence (SendGrid From-email verification, Gravity Forms fallback, credentials to 1Password) `[amsoil-aerospace-web-build]`, `[brigade-hometown-exteriors-web]`.
8. **Internal system migration (its own project).** `temp-hubspot-implement` documents R55 moving sales ops off Salesforce onto HubSpot — integration shutoff, flat-file/data-loader migration, exclusion rules, PandaDoc for docs, Zoom scheduler, brand/segmentation cleanup. A good template for how they run a platform migration.
9. **Weekly pod cadence on EOS/Traction [Canvas].** The industrial-manufacturing pod's **"Weekly Pod Meeting"** Canvas is a classic EOS Level‑10 agenda: **Scorecard** review → **Issues list (IDS: Identify, Discuss, Solve)** → **at-risk/health flags** (clients trending red on budget/scope/satisfaction/churn) → strategy discussions → **growth/upsell**. Clients also get individual **weekly scorecards** (e.g. Thern: goal / this-week / 4-wk avg / miss-streak / 🟢🟡🔴 per metric).
10. **Emerging: Claude Projects as a per-project knowledge base [Canvas].** A PM notes rolling out, "across all projects," a project-specific Claude Project connected to email, Slack, and Fathom to house all project knowledge for recaps, status drafts, and search `[mmt-web "Latest Status Report"]`.

---

## 5. Account management structure

- **Pod / team model under Account Directors.** New hires are announced into named teams — "joining Kaitlyn's team as a Client Success Coordinator," "Sr. Client Success Manager," and an Account Director for **"Consumer Lifestyle"** reporting to Devon `[general]`. Explicit **PODs** exist (`industrial-manufacturing-pod-4`, `-pod-5`, "POD 3," `Weekly Pod Meeting`).
- **Roles seen:** Account Director, (Sr.) Client Success Manager, Client Success Coordinator, Lead/Sr. Web Project Manager, (Sr.) Digital Project Manager, VP of Web, strategists (SEO/SXO, Paid, Social, Content, UX), designers, developers, Director of SEO & AI Search (new hire, Jul 2026), Director of Content & Strategic Initiatives.
- **Master account list** is the ownership source of truth — used to reassign a departing employee's accounts: *"can we make sure all of Ellie's tasks are reassigned today based on the master account list?"* `[pm-am-resourcing, 2026-01-15]`.
- **Formal client transitions [Canvas].** The **"Transition List (who do I need to meet with)"** Canvas is the handoff SOP: for each incoming owner (Evan, Emma, Kiley, Zander, Nick) it lists the outgoing owner to meet and each client to transition, with checkboxes. Accounts move deliberately (e.g., NAMSA transitioning Emma → Evan `[namsa-all, 2026-01-20]`; a "client transition tracker" spreadsheet `[cpc-all, 2026-05-18]`). Live account moves are tracked in the pod meeting (Rayus → PM Jason; C2 → PM Rachel / CSM Trey; MN Oncology off-boarding).
- **Client health & staffing flags [Canvas].** The pod meeting explicitly surfaces coverage risk ("Aaron's coverage of Kiley accounts is an orange flag"; "concerned on Prinsco coverage — should Evan be interim paid strategist?") and relationship risk (CPC "extremely strained").
- **Business reviews.** Periodic account business reviews (YoY performance) with client leadership, e.g. `[nura-clinics-and-cpi-all, 2026-04-23]`.
- **Partner / white-label relationships.** R55 works alongside other agencies: **obviouslee** (`team-sds-obviouslee`, `obviouslee-admin`, "obviouslee process doc"), **Bald** (creative/social playbooks for EcoWater), **OM Digital** (Bark). The `client_*_rocket55` channels (Bark, Sewing Down South, Streamsong) are shared channels where the client/partner is present.

---

## 6. Quick "noise" filter (safe to de-prioritize)

Automated / non-operational channels: `1password-alerts`, `1password-notifications`, `verification-codes`, `anomaly-detections`, `alerts-implementation`, `integration_logs`, plus social/interest channels (`water-cooler`, `random`, `book-club`, `foodies`, `music`, `movie-mondays`, `catscatsandmorecats`, `dogsdogsandmoredogs`, `f1`, `timberwolves`, `soccer-realfootball-fansunite`, `halloween`, `festa-della-repubblica`, `thrift_finds`, `intense`, `aftersun`, `nirvana66`, `hp-nerds`, `pride-full`). Keep `general`, `pm-am-resourcing`, `r55_out-of-office`, and `temp-hubspot-implement` — those carry process signal.
