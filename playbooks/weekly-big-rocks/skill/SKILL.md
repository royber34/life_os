---
name: weekly-big-rocks
description: Weekly planning routine. Reads what actually happened last week (email, calendar and any other connected sources), reconciles last week's plan, and picks 3 to 5 Big Rocks for the coming week, each tied to the user's north star, with a next action, a definition of done and a time block. Use when the user asks to plan their week, run a weekly review, pick their big rocks or set weekly priorities. Runs by hand or as a weekly scheduled task.
---

# Weekly Big Rocks

Once a week you read the evidence of the user's last week, check it against their north star, and hand back a short plan: **3 to 5 Big Rocks for the coming week, exactly one ranked #1.** The user runs their week from it.

The run is attended only if the user asked for it in this conversation; a scheduled run is unattended. When unattended, nobody is there to answer questions. Decide from the evidence and the rules below, and write uncertainty into the plan instead of guessing.

## What a good Big Rock is

- **Important over urgent** (Covey's Quadrant II). It moves something that matters, even when something else is louder this week.
- **Tied to the north star.** It serves a named goal, value or quarter focus in `north-star.md`. A rock that ties to nothing goes on the "Not this week" list.
- **A lead measure** (4DX). Something the user controls this week ("send 5 proposals"), never an outcome they can only watch ("close 2 deals").
- **Concrete.** A verb-first next action and a definition of done.
- **Scheduled.** A proposed time block (an implementation intention: when and where).

Three to five rocks, with one #1 picked by the Focusing Question from *The ONE Thing*: "What's the ONE Thing I can do such that by doing it everything else will be easier or unnecessary?" The #1 is the highest-leverage thing the user can act on this week. If the biggest opportunity waits on someone else, the #1 is the controllable move that advances it.

## Rules

1. **No fabrication.** A source that returns nothing is "no signal". A quiet week is a finding.
2. **Discussed is not done.** Tag every item as discussed / proposed / scheduled, or as agreed / done / happened. A meeting on the calendar with no notes may not have happened: say so.
3. **Negative claims need full evidence.** "You haven't sent / replied to / raised X" may only be stated after checking the sent folder and drafts of every sending channel you can reach, and after reading the full thread. For a channel you cannot reach, write "send status unverifiable". A note saying "sending now" is not evidence of a send either.
4. **Check freshness first.** Confirm each source is live and how old its newest data is. A stale or unreachable source is named at the top of the plan.
5. **Latest decision wins.** If a later signal reverses an earlier commitment, the earlier one is off. Flag the reversal.
6. **Read-only everywhere.** Never send, reply, draft, accept or delete on any channel. The only things you write are the plan file, `north-star.md` when the user answers the first-run questions, and, if the user set one up, a post to their own Slack channel.

Read `references/connector-gotchas.md` before gathering. It lists the ways each connector has produced wrong findings before.

## Files

Everything lives in `~/.claude/weekly-big-rocks/` (create it on first run):

- `north-star.md`: the user's goals, roles, values and quarter focus. Every rock ties back to it.
- `plan-YYYY-MM-DD.md`: one file per week, named by that week's Monday.

## Step 1: Orient

1. **Set the dates.** The coming week is the next Monday to Sunday; if today is Monday, it is this week.
2. **Read `north-star.md`.** If it still says "Last confirmed: YYYY-MM-DD", it is the blank template: treat it as missing.
   - Missing, and the user is present: ask the questions in `templates/north-star.md` one at a time, then write the file with today's date as "Last confirmed".
   - Missing, and running unattended: copy the template into place if absent, plan from the evidence alone, skip the north-star tie test (Step 3.3 and check 6), and put "Fill in your north star: ~/.claude/weekly-big-rocks/north-star.md" at the top of the plan.
   - "Last confirmed" older than 90 days: add one line at the top of the plan asking whether it is still true. Never edit it yourself.
3. **Read last week's plan:** the newest plan file dated before the coming Monday. On the first run there is none: skip reconciliation and say so.
4. **Check for a seed.** If the coming week's plan file already exists and starts with "# Big Rocks: week of", an earlier run wrote it: you will replace it. Otherwise the user wrote it: keep their text word for word under "## Your notes" at the top of the plan, and treat any rocks in it as pre-committed.

## Step 2: Gather

Use every source that is connected. Email and calendar are the core; the rest are optional:

- **Email:** the sent folder for the last 7 days first, then drafts, then inbox threads waiting on the user.
- **Calendar:** the last 7 days (what happened) and the next 7 days (fixed commitments). Estimate free focus hours, with a low-confidence flag if the calendar looks sparsely kept.
- **Notes:** the notes folder named in `north-star.md`, if any.
- **Meetings:** transcripts from the last 7 days. Read the full transcript of the 3 or 4 most decision-heavy meetings; use summaries for the rest and mark them summary-only.
- **Chat** (Slack, WhatsApp or similar): asks directed at the user, commitments they made. Skip social chatter.
- **Past Claude Code sessions:** the session logs under `~/.claude/projects/` changed in the last 7 days, if readable (otherwise skip and say so). They show work that is half-done. This source knows what is already drafted, which keeps next actions correctly sized.

If you can run subagents, give each source its own, in parallel. Each is read-only, spawns no further subagents, and returns the same contract:

- candidate rocks, open loops (waiting on the user or on someone else), and hard commitments (meetings, deadlines, promises)
- for each item: a one-line source citation and its discussed-or-done tag
- one freshness line: is the source live, and how old is its newest data

Sources return at very different speeds. Once most are back, start drafting, and fold in late ones before saving.

Then reconcile:

- **Deduplicate.** One commitment seen in email, a meeting and a note is one candidate with strong corroboration, not three.
- **Apply recency.** Later decisions override earlier ones.
- **Score last week.** Each rock: done / partial / slipped / dropped, with evidence. Carry forward what still matters.

## Step 3: Choose the rocks

1. List candidates per role from `north-star.md`, so the week is not accidentally all one role.
2. Sort them into urgent/important. Keep "urgent for someone else" out of the rocks.
3. Tie each survivor to a named line in `north-star.md`. Drop or demote the orphans.
4. Turn any outcome the user can't control this week into the lead action that drives it.
5. Cut to 3 to 5 rocks (aim for 3 or 4) and pick the #1.
6. Nest related tasks under their rock as one-line "also under this rock" items.
7. From what is left, keep up to about 6 genuinely important or time-sensitive items as **Also this week**, split into Need to (owed or time-sensitive) and Want to (self-directed).
8. Put tempting distractions on a **Not this week** list.
9. Give each rock a next action, a definition of done and a time block. Check that the blocked hours fit the free focus hours (if the estimate is low-confidence, use the typical focus hours from `north-star.md`, or 25 to 30). If it does not fit, cut.

Every item you surfaced ends up somewhere: a rock, nested, Also this week, Not this week, or consciously dropped.

## Step 4: Independent check

Hand the draft plan, the gathered evidence and `north-star.md` to a **separate reviewer subagent** with a fresh context and no write access. A check run in the same context tends to pass its own work. Starred checks must pass; at most two others may miss.

1. (*) 3 to 5 rocks, exactly one #1.
2. (*) Every claim cites a source. Nothing invented.
3. (*) Every "not sent / no reply" claim is backed by sent folder, drafts and a full-thread read, or marked unverifiable.
4. (*) Stale or unreachable sources are named at the top.
5. (*) Seeded text is kept word for word.
6. Every rock ties to a named line in `north-star.md`.
7. Every rock is a lead action with a next action, a definition of done and a time block.
8. Every surfaced item is placed.
9. Time-blocked hours fit capacity.
10. The #1 is obvious in 5 seconds and the rocks section reads in about a minute.

Revise and re-check up to 2 times. If it still fails, ship the best version and say at the top what fell short. If subagents are unavailable, run the checklist yourself and note that it was self-checked.

## Step 5: Save

1. **Re-read the plan file immediately before writing.** If the user seeded it, even while you were running, keep their text word for word under "## Your notes", never over it.
2. Save to `~/.claude/weekly-big-rocks/plan-YYYY-MM-DD.md` in the format below.
3. **Optional Slack post:** only if `north-star.md` names the user's own Slack channel. Post the plan from "Big Rocks" through "Capacity", under 4,900 characters, to that channel and nowhere else. If the send tool is not pre-approved on an unattended run, skip the post and say so in the plan.
4. If the user is present, show them the rocks and the path to the file.

## Plan format

```
# Big Rocks: week of {Mon DD} to {Sun DD}

{Only if needed: stale/unreachable sources, north star to fill in or re-confirm, checks that fell short.}

{Only if the user seeded this file: "## Your notes" with their text, word for word.}

**Last week:** {N of M rocks done}. {One honest line: what moved, what slipped, what carries over.}

## The Big Rocks
1. **{Rock #1}** (THE ONE THING)
   Why: {the north-star line it serves}. Next: {verb-first action}. Done = {criterion}. Block: {when/where}.
   Also under this rock: {related one-liners, if any}
2. **{Rock 2}**
   Why: ... Next: ... Done = ... Block: ...
{3 to 5 only if they earn a slot}

## Also this week
- Need to: {item + next action}
- Want to: {item + next action}

## Not this week
- {distraction to resist}

**Capacity:** ~{N} focus hours free, {M} hours blocked for rocks. {One realism line.}

---

## Last week, reconciled
{Each prior rock: done / partial / slipped / dropped, with evidence.}

## Evidence
{Per source: freshness line, then the items with citations and tags.}
```

Keep it as short as the week allows. A quiet week gets a short plan and says so.
