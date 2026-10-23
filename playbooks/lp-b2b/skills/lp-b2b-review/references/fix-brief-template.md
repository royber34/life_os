# Fix brief template (review/round-N/fix-brief.md)

```
# Fix brief, round N (<page version>)
Goal: <one line from GOAL.md>. This brief ranks what to change so a cold visitor understands, believes and acts alone.

## Scoreboard
<output of scripts/scoreboard.py: one row per seat with overall, act, submit %, L1 to L10>
Comprehension: <per seat, correct or the gap>

## A. Fixes within the seller's decisions (ranked by effect on GOAL.md)
1. <section> | <current text or element> | <change> | <seats that asked, lint or designer tag>
...

## B. Gaps caused by the seller's decisions or by facts only the seller can supply
- <gap> | <what it caps: line and seats> | <placeholder that stays> | decision id or "needs the seller"
(Recorded, never re-raised as an open point.)

## C. Rejected findings
- <finding> | <reason: invents facts / adds a caveat / operational detail / never-on-the-page item / removes a locked element / reviewer misread, with source>

## D. Questions only the seller can answer
- <question> | <the default if the seller does not answer>
```

Before an item enters A, check its proposed wording against the page's own facts: prices, durations, option names, what each option includes. A fix that makes one option's price read as the page's only price, or promises what the cheapest option does not include, is wrong even when the finding behind it is right.

Sort rules:
- A finding that a page change within the seller's decisions can fix goes to A, even if only one seat raised it, when it touches comprehension (L1, L4, L8).
- A finding raised by one seat about taste goes to A only if the designer or a second seat agrees; otherwise C with "single-seat taste".
- Anything that would invent a customer, number, testimonial, logo or portrait goes to C.
- A missing real asset (portrait, screenshot, profile link, exact number) goes to B as "needs the seller".
- Requests for real proof (faces, names, profile links, real numbers, a client result) are never rejected under the sales-page standard: that standard bans caveats and operational detail, and real people make proof checkable. They go to B as "needs the seller".
