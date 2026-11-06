# Workstreams

One agent per workstream, in its own folder under `research/`. Each brief is: `agent-brief-common.md`, then the matching block here, then the target's modules from `targets.md`, the relevant `treg-plan.json` rows, the budget, and the cutoff.

Each writes the common set: `section.md` (2,500 to 5,000 words), `events.jsonl`, `claims.jsonl`, `calls.jsonl`, `progress.jsonl`, `raw/`.

Scale the word count down when the probe found little. A short honest section beats padding.

## W1 Timeline (`w1-timeline`)
**Question:** how did this company get here, in order?
Pre-history, founding, each phase, pivots with stated reasons, positioning changes, inflection points. Use the lane `inflection` only for moments that measurably changed the trajectory, and say how. Write phase spans (`kind:"span"`, lane `pivot`, title starting `Phase `).
**Items:** one per source family or phase.

## W2 Economics (`w2-economics`)
**Question:** how does money move, and what does a unit earn?
Pricing history, money flows with a worked example, cost basis, margin sources, fees and credits, what each customer type pays. Extra output: `pricing_history.jsonl`. Revenue triangulation is a joint item with W3: W2 owns the model, W3 the inputs. Every estimate shows assumptions and a range.
**Items:** one per plan, flow or estimate.

## W3 Traction (`w3-traction`)
**Question:** what is actually happening, measured?
Usage, customers, traffic, installs, stars, reviews, rank, search interest, follower series, whichever exist. Write series as `kind:"metric"`. Note when a figure is vendor-stated. Line up jumps against dated actions.
**Items:** one per metric source.

## W4 Legal and entity (`w4-legal`)
**Question:** who is it legally, and what exposes it?
Entities, registers, terms and privacy history, licences, resale or data rights, regulation, incidents and how they were disclosed, litigation, and a risk register table. State that this is research and not legal advice. Consumer targets add the claims and regulation items from `targets.md`.
**Items:** one per document or register.

## W5 Product and tech (`w5-product`)
**Question:** what is it made of, and how fast does it change?
Software targets: stack, architecture, surfaces, release cadence, incident technicals, engineering process. Cross-check data-vendor tech stack results against live response headers. Consumer targets use the product and claims module from `targets.md` instead.
**Items:** one per subsystem, product line or release period.

## W6 Team and funding (`w6-team`)
**Question:** who does the work, and who pays for it?
People, functions, tenure, headcount over time, founders' background, rounds, investors, public grants. Extra output: `people.jsonl`. Public-role facts only.
**Items:** one per person group or round.

## W7 Go-to-market (`w7-gtm`), wave 2
**Question:** how does it get customers, in time order, and what did each action move?
Every channel from the target's list, with the channel's posts, ads or pages as rows in `gtm_actions.jsonl`, with engagement and the date observed. Watch or read the best performers through their transcripts, and write what the formula is. Website, SEO, marketplaces, partners, pricing hooks, funnel and loops. Line up actions against W3's metrics, with lift figures only where before and after both exist.
Mark gaps: if a channel cannot be reached, it appears as "not reachable", which is different from "not used".
**Items:** one per channel or account.

## W8 Competitors (`w8-competitors`), wave 2
**Question:** who could take this business, who is it taking from, and who could partner with it?
1. Discovery from several directions: similar-company data, search results for the category, comparison pages, review-site alternatives, who the company names, who bids on its name.
2. Long list up to 50 in `landscape.jsonl`.
3. Pick the top 15 to 25 with reasons, and profile each on one schema in `profiles.jsonl`.
4. Nested subagents are allowed here: up to 4, one per competitor group, each with its own folder and the same limits.

Scores and threat ratings are judgement, so give the reason. Include substitutes: what customers do instead.
**Items:** one per player. At most 6 tool calls each, and save before starting the next.

## Choosing modules

The probe drops a workstream only when its surface does not exist, and the coverage report names the drop. Common cases:
- W5 tech is thin without code. Keep it short, or use the product module.
- W6 is executives only for a listed company.
- A very small company can merge W2 with W3.
