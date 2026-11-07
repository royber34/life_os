# Review panel

Run this after S5 builds the page and before G4. Earlier checks ask whether facts match sources. This one asks whether senior readers would use the page.

On the first consumer run, facts had been checked and red-teamed, and the panel still scored usefulness 6, foundedness 5.5 and ease of reading about 5 out of 10. It found the page read as homework, buried its best finding, and had a chart that moved scores across a quadrant line.

## Who reads

Fresh agents in parallel, one per role, each blind to the others and to your view of the page. Choose the roles to fit the reader. The default is CEO, CFO, CMO, head of sales and data analyst. For a software target, swap CMO for the head of product or sales. Say plainly in your report that these are agents playing a role, not real executives.

Give each one the page through its screenshots, in reading order, plus `09-moves.md`. Give the CFO the economics section and the ledger. Give the analyst the ledger, verdicts, corrections and report, and have them test by doing: check a stated random draw of citations, say which rows the error rate covers, and assess each chart.

## Plain-reader test

Before the role panel, run two fresh readers one after the other on the moves and the AI findings, with citations stripped and no background. Ask each to score every item for clarity from 1 to 5, quote the words that lost them, and list figures with no basis and reasons that don't follow. Fix what they find, and check each rewording against its source. Also give a cold reader screenshots of each tab's top, and for each panel ask what was counted and what they take away. Their answers show misreadings that scores miss. A role panel praises a page that a plain reader can't follow, so this runs first. On the first run, it found ten of 25 moves unclear after a panel-approved rewrite.

## The brief

> You are the [role] of a [kind of company]. Someone outside hands you a page about the business, built only from public sources. Review it cold. Judge how useful the insights are for your decisions, how well founded they seem and where you'd stop believing, and how easy it is, structurally and visually, to see the points. Be blunt, praise only what earns it, and name the exact spot for each point.
>
> Write `verify/cold-eye-<role>.md`, saving within your first 10 tool calls. Sections: Skim (5 seconds), Mid-depth (1 to 2 minutes), Deepest (3 to 5 minutes), Scores out of 10 on usefulness, foundedness and ease of reading, Would act on first, Would ignore or cut, Top five fixes. Stop at 25 tool calls. Your final reply holds the whole review.

## Using the result

Report them all to the user in their own terms before changing anything, unless the user has said to go straight to fixes. Check their specific claims against the files first, and say which you accept and which you don't.

When applying fixes, **make the page stronger, and don't overcorrect**:

- Lose nothing. A cut from the main view moves to an expanded view, and a replaced chart keeps its information.
- Before and after, compare citations, numbers and move titles by script, and account for every difference.
- Readers often ask for less text. Answer that with better order and folding, while keeping the evidence one click away.
- Reviewers may ask for owners, deadlines and instructions. Keep the page descriptive, as `references/moves.md` sets out, and offer specifics as identified areas.
- Reviewers may contradict each other, or ask to remove what the user asked for. The user's request wins.
