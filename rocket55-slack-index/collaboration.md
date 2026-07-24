# Team Collaboration — How Rocket55 Works Around Each Client

This pass looks at *how well the teams collaborate*, using message patterns, who connects whom, and the recurring friction points.

## The dominant working pattern: "turn it into a task"

The healthiest signal in the whole export is how consistently conversation converts into tracked work. Threads don't trail off — they resolve into an **Accelo job with an owner and a due date**:

> "let's get a task in for me to build out ad groups for branded… you're task is set up for the 13th!" — `renew-all`
> "Please post your work as a note in your task and tag me/Devon/Morgan so we know it's ready for QA" — `renew-all`

This gives most client channels a clean rhythm: **decision → task → QA tag → done**, with the Account Director or PM as the throughline.

## Who the connectors are

Top message volume comes from **coordination roles**, not individual contributors — which is what a well-run agency should look like:

| Person | Role | ~Msgs |
|---|---|--:|
| Rachel Gunderson | Account Director | 2,770 |
| Kerri Graber | Lead Web Project Manager | 2,207 |
| Emma Noriega | Senior Digital Project Manager | 1,983 |
| Kaitlyn Benson | Account lead (team owner) | 1,837 |
| Zac Forsman | VP of Web | 1,650 |
| Kate Berstene | Account/PM | 1,643 |
| Evan Wilberg | Sr. Client Success Manager | 1,020 |

PMs and ADs are the busiest nodes; VP of Web (Zac) is a booked, shared dev resource that teams schedule against.

## How channels are structured per client

Rocket55's naming convention encodes the collaboration model:

- **`-all`** — the cross-functional **account team** (paid, SEO/SXO, social, content, analytics + PM/AD). This is where strategy and status live.
- **`-web`** — a **project team** for a website build, PM-led, with design/dev/content/UX and Figma handoffs.
- **`-admin`** — **R55-only** back-of-house planning (scope, pricing, internal handoffs) — the client is *not* here.
- **`client_<name>_rocket55`** — a **shared** channel the client (or partner agency) is actually in; tone shifts to client-facing.
- **`FC:...Overview`** — the pinned **Canvas** each account uses as its reference hub.

Bigger accounts run several of these at once (e.g., Toppan Merrill, EcoWater, iSpiri, MMT, FRSecure, TSR Injury Law all span multiple channels — see `clients.md`), and the `-web` + `-all` pair is the most common two-channel shape.

## Cross-functional handoffs that work well

- **Sales → delivery**: an "Internal Sales Handoff" doc is saved into the channel overview at kickoff (`halco`).
- **Design → dev**: Figma "Handoff" tab is the agreed boundary (`brigade-hometown-exteriors-web`).
- **Strategy → execution**: strategists produce playbooks/keyword maps into the client folder; PMs task the work; QA is explicit.
- **Resourcing**: the weekly dev/design/content/UX availability report (`pm-am-resourcing`) lets PMs place work against real capacity instead of guessing — a genuinely mature practice.

## Recurring friction points (where collaboration strains)

1. **Finding assets / creative.** The most common complaint. "can't find it in the client folder," "I don't see it in the creative drive," "dug for like 15 min." Drive is the store, but findability depends on folder discipline — and it slips (`cpc-all`, `idi-all`, `ecowater-all`).
2. **Access & credentials.** Frequent waiting on WordPress/LinkedIn/hosting access; helped by 1Password but the LastPass→1Password migration left gaps (`frsecure`, `renew-all`, `help-1password`).
3. **Scope & pricing on add-on work.** Teams openly wrestle with what to charge and what's in/out of retainer ("not sure how much we should charge to make money," "I just put it in the retainer bucket"). Scope-down conversations are handled well; new-scope pricing is more ad hoc (`atwell`, `ecowater-all`, `metro-state-all`).
4. **Continuity through turnover.** Several departures/transitions in the window (Ellie, Ben Lohrding) are absorbed via the master account list + transition tracker — the process exists, but reassignment is a visible lift each time (`pm-am-resourcing`, `general`).
5. **Client-owned tooling sprawl.** Some accounts work inside the client's own Asana/Jira/SharePoint/Notion, so context lives partly outside R55's systems (`client_streamsong_rocket55` on Asana; SharePoint on Atwell/Metro State).

## Collaboration health by engagement type

- **Full-service `-all` accounts**: highest collaboration density and cleanest task discipline; ADs actively QA and close loops.
- **Web builds `-web`**: strongest process maturity (resourcing, staging reviews, launch checklists, Figma handoffs).
- **Single-channel accounts**: leaner; more likely to rely on one owner, so continuity risk is higher if that person is out.
- **Shared `client_*` channels**: lower internal chatter (as expected) — internal coordination shifts to the `-admin`/`-all` twin.

## Net assessment

Collaboration is **disciplined and system-anchored**: work is tracked in Accelo, documents are centralized in Drive, capacity is planned weekly, and account ownership is explicit. The improvement opportunities are **operational hygiene**, not culture — tighten Drive folder structure and asset naming, close the last credential-migration gaps, and standardize add-on/scope pricing so it's less of a per-thread judgment call.
