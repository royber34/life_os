# Company Teardown: reverse-engineer any company into one checked, interactive page

A Claude Code skill that takes a company name and produces a sourced research archive plus one self-contained HTML page. The page opens on an overview, then what to do: the moves, opportunities, and what's working and what isn't. Behind that sit a dated timeline, go-to-market insights with campaign impact, an AI section (a GEO audit plus inferred AI use), competition with 10-year charts against rivals, and a deep dive. Agents do the research in parallel, independent agents check it, and the page tells you how far to trust it.

I built this after reverse-engineering [treg](https://treg.to) by hand with Claude. The result was good, and the audit of how it got made was humbling. Five of the six main sections only existed because I asked for them after seeing earlier output. Agents went silent for hours and nobody noticed until I asked. (The cause turned out to be my laptop going into standby: the system log matched both long hangs to the minute.) About 2% of the rows were checked, all hand-picked, so the true error rate was unknown. Claude never saw the page it built, so I did the QA. This playbook is what I'd set up from the start next time.

I then ran it on a consumer watch brand's US business. The facts held up, and I still wasn't happy with the result: it was a lot of information with no useful presentation. So it went through several rounds: a stage for moves, a deeper pass on what has worked by channel, angle, offer and format, a before-and-after study of campaigns, and a review panel of a CEO, CFO, CMO, head of sales and data analyst, all played by agents. Those changes are now built in. Sharing what's worked so far in case it helps.

**Fastest way** (in the Code tab of the Claude desktop app, or Claude Code): start a session in a new folder and paste:

> *Install the skill at https://github.com/royber34/life_os/tree/main/playbooks/company-teardown and use it to do a teardown of [company].*

---

## How it works

Claude stops for your yes at each gate.

| Stage | What happens | You approve |
|---|---|---|
| Intake | Ten questions with defaults: what decision this informs, scope, depth, budget, stop rule | The brief |
| Probe | Checks what the company exposes, picks research modules, says how deep this can go, shows ten real sample rows, estimates cost | Modules and cost |
| Research | Up to eight parallel workstreams: timeline, economics, traction, legal, product, team, go-to-market, competitors | Coverage and gaps |
| Verify | Fresh agents check claims against sources without seeing the writer's reasoning | Sees the error rate |
| Synthesis | A performance pass on what has worked, then moves, overview, so what, go-to-market, competition, deep dive, a one-page memo and a red-team review | The moves, memo and so what |
| Present | Builds the page, tests it in a real browser, reads its own screenshots, then runs a review panel by role | The page |
| Close | Archive for future agents, cost report, how to refresh | |

There's also a probe-only mode, which tells you cheaply what a full run would find, and a refresh mode for updating an earlier run.

## What makes it different from "research this company"

- **It checks what's knowable first.** A company with a public repo gives you pivots with stated reasons. A private consumer brand gives you ads and reviews, and thin economics. The probe tells you which before you spend.
- **It measures its own error rate.** Every claim the conclusions rest on is checked, plus a random sample of at least 100 others. The page shows a label and a range. One wrong row in 40 checks still allows a true rate up to 13%, so the range matters more than the point estimate.
- **It survives a dead session.** All state is on disk, each item is saved before the next starts, and a watcher tells a stuck agent from a shared outage.
- **It sees its own output.** A script opens the page, clicks every tab, compares counts with the data and takes screenshots.
- **It tells you what to do.** The moves sit right after the overview, each with evidence, a decision rule, a test and what happens if it's wrong. Weak evidence blocks a claim of fact, and doesn't block a cheap, labelled test.
- **It gives a marketing and sales team something to use.** By channel, angle, offer, format, product, timing, audience and sales route: what's working, what isn't, where the openings are, and when to stop.
- **It shows the long view against rivals.** Search, Wikipedia, Reddit and YouTube history, up to 10 years, on one time axis, with charts and brands added or removed by clicking. Reddit counts are adjusted for forum growth and checked by reading titles by hand.
- **It measures campaigns honestly.** Each is compared with the weeks before, the same weeks a year earlier and the same weeks at rivals, and it says how large an effect the data could even see.
- **It says what would make it better.** It lists the connections, such as ad accounts, CRM and order data, that would turn public signals into measured results.
- **It ends with action:** the cheapest real-world test of the conclusion, and who to call with what questions. Nobody gets contacted by the run.

## Target types

| Type | Depth to expect | Weak spot |
|---|---|---|
| Public repo (dev tools, open source) | 500 to 1,500 dated rows | Revenue stays an estimate |
| Private, no repo | 100 to 400 rows | Economics are mostly inference |
| Listed company | Several hundred, mostly primary sources | Needs narrowing to one unit or question |
| Consumer brand | 150 to 500 rows, strong on ads and reviews | Sales, margin and retail performance |

You can also scope a run to one brand or market. These ranges are guides. The public repo range comes from a hand-built version. One full consumer run produced about 850 checked claims, plus about 1,000 metric points.

## How far it's been tested

- **One full run,** on a consumer brand, including the deeper passes and the review panel. Many of its fixes were made along the way, and are now in the playbook.
- **One smaller cold-start test,** on a software company from the written instructions alone: research on two workstreams, moves, insights, a campaign study and the page, with the checks self-marked. It found real problems, which are fixed. It didn't exercise background agents, independent verifiers or the review panel on that target.
- **Automated:** 101 pipeline tests, plus browser checks on each built page.
- **AI section:** the GEO audit and AI-use workstreams have run once, on the consumer brand. Their counts and claims were checked in full by fresh verifiers.

So expect a consumer run to work as described. Expect other company types to work, with more judgement along the way. A full run on a second company hasn't been done yet.

## What it costs

From one full consumer run, so treat these as rough:
- **Paid data:** USD 1.53 for the main research, against a default cap of USD 5, and about USD 5 in all once the deeper passes, the AI section and the rivals history were added.
- **Work:** many hours of agent time, with model usage the real cost, and it is large. That run's total went well past the 3 to 4 active hours first planned. Use probe-only first if you're unsure.
- **You:** a review at each of the five gates.

---

## Quick start

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/company-teardown/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/company-teardown/install.ps1 | iex
```

Start a new session, then ask: *"do a company teardown of [company]"*.

**Needs:** Python 3. For the page's render test, Playwright too (`pip install playwright`, then `playwright install chromium`). Without it the page still builds, and you check the tabs yourself.

**Better with:** [treg](https://treg.to) connected as an MCP, for X, YouTube captions, SEO, ad libraries, reviews, enrichment and marketplaces at a small per-call price. Without it, the run uses free sources and web search, and social, SEO and ads get thinner.

## The page

One HTML file with everything inlined, so it works offline and you can email it. See a small example by building `skill/example/treg-2026-10-28/`, which holds a trimmed public-facts sample.

## What's in this folder

```
.
├── README.md
├── install.sh, install.ps1
├── tests/                      Tests for the pipeline scripts (not installed)
└── skill/
    ├── SKILL.md                Stages, gates, rules, resume
    ├── references/             One guide per stage, plus schemas and style
    ├── scripts/                watch, merge_events, ledger, campaign_impact, build_dashboard, render_test, cost_report
    ├── template/               The page: HTML, CSS, JS, pinned d3
    └── example/                A trimmed public-facts sample
```

## Limits

- **Accurate to sources is the most it can claim.** A source can be wrong, a vendor's number can be marketing, and evidence that was never found doesn't show up in any error rate.
- **Public research has a ceiling.** Customers, former staff and partners know things no web page does. The run tells you who to ask, and asking is up to you.
- **Public signals aren't sales.** Engagement, ratings, search and ad run length are proxies, and the page labels them. Campaign studies can miss smaller effects.
- **Review panels are agents playing a role,** not real executives. They catch a lot, and they don't replace asking real people.
- **Scores, moves and threat ratings are judgement,** and labelled that way.
- **Not legal or investment advice.**
- **Respect the sources.** Check that your use of any data vendor fits its terms, and don't publish paid data or personal details from a run folder.
- **Keep the computer awake.** A closed lid or standby freezes the agents. The skill asks for a keep-awake where the app offers one, but it can't stop a closed lid.

## License

MIT (see the repository root). `skill/template/d3.v7.min.js` is d3, under its own ISC licence in `d3.LICENSE.txt`.
