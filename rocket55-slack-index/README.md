# Rocket55 Slack Export — Index & Analysis

**Source:** `Rocket55_Slack_export_Jan_1_2026__Jul_23_2026.zip`
**Coverage:** Jan 1 2026 → Jul 23 2026 (a handful of older threads from Aug–Dec 2025 survive in Canvas/List history)
**Size:** 242 channels · 317 users · 6,493 files · ~60,600 messages (≈43,200 written by people, ≈17,400 by bots/integrations)

---

## What this folder is

This is an **index** of the Slack export — a map that separates *signal* (client work, decisions, processes, where things live) from *noise* (bot alerts, social chatter, verification codes). It is meant to be read, not run. Nothing here modifies the original export.

> **Jargon check.** A *Slack export* is a set of JSON files — one file per channel per day — plus metadata files listing users and channels. Each message is a record with who said it, when, the text, and any thread replies. I wrote small Python scripts to read all 6,493 files, resolve the cryptic user IDs (like `UNF726GBA`) into real names, tally activity, and pull out links and keywords. The results are summarized in the documents below.

## Read in this order

| File | What it answers |
|---|---|
| **`00-executive-summary.md`** | The headline findings — signal vs. noise, and the answer to "where does everything get saved?" Start here. |
| **`operations-playbook.md`** | The deep dive you asked for: systems of record, contracts/SOWs, templates, repeatable processes, and how accounts are managed. |
| **`canvas-appendix.md`** | Primary-source contents of the client "Overview" Canvases, retrieved live from Slack (they were missing from the export). The standardized client template lives here. |
| **`collaboration.md`** | How the teams are structured and how they collaborate around each client. |
| **`clients.md`** | Roster of ~165 client accounts, sorted by activity, with channel names and engagement type. |
| **`channel-index.md`** | Every meaningful channel, grouped and classified, with people, storage links, and signal flags. |
| **`channel-index.csv`** | The same channel data as a spreadsheet you can sort/filter yourself. |

## How channels were classified

Rocket55 uses a **consistent channel naming convention**, which is itself a finding (see the playbook). The classifier keys off the suffix:

- `<client>-all` → full-service **account team** channel
- `<client>-web` / `-web-build` → **website build** project
- `<client>-admin` → **internal** account planning (client not present)
- `<client>-recurring` → **retainer** work
- `client_<name>_rocket55` → **shared** channel the client is actually in
- `<client>` (bare name) → smaller / single-discipline account
- `FC:...Overview` → **Canvas/overview docs** attached to a channel
- Everything else → internal ops, tooling, or social ("noise")

## Method & limitations

- Counts and links were extracted mechanically; the narrative was written after reading the highest-signal channels directly.
- **Canvas bodies were not in the export** (only titles/links). They were later **retrieved live via authorized read-only Slack access** and written up in `canvas-appendix.md` — this is the richest single source in the folder. List *history* (e.g. the Help-requests tracker) still requires a live token and is not fully reproduced.
- Message *files* (uploaded PDFs/images) are referenced by URL only; the binaries are not included.
- "Signal flags" (SOW, contract, template, etc.) are keyword hits — useful as a heat-map, not a precise count of real contracts.
