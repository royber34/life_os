# Ingestion: getting a person's LinkedIn posts in

The default is for Claude to collect the posts from the user's own logged-in browser session. LinkedIn has no public posts API and blocks third-party scrapers (HTTP 999), so the reliable, low-friction path is to read what the user can already see in their own session. The official data export is offered as an optional upgrade when the browser capture is thin or the user wants the most complete read.

Always report how many posts were attempted, captured, and used (see the bottom of this file).

## Primary: Claude collects from the user's own logged-in browser session

Using a connected browser tool (for example Claude-in-Chrome) on the user's own authenticated LinkedIn session:

1. Navigate to the user's activity feed: `https://www.linkedin.com/in/<handle>/recent-activity/all/` (Posts filter).
2. Read the rendered posts with the page-text tool. The feed is **virtualized**: only a handful of posts render as real text at a time, and older ones unmount as you scroll. So:
   - Scroll the feed down incrementally and read again to pick up more posts.
   - Click **"Show more results"** at the bottom to load further batches.
   - De-duplicate by post text as you accumulate.
3. **Reposts:** capture only the user's own commentary line, not the reposted body (that is someone else's writing and would pollute the voice profile).
4. **Known limits to expect and work around (do not silently ignore):**
   - Tall image posts mean each scroll only advances a post or two.
   - Many activity entries are **"Boost"-only stubs that never hydrate into readable text**: skip them.
   - Some older posts are **deleted**: skip them.
   - Net result: you will often capture fewer posts than the 12 target. That is acceptable. Capture every post that renders as real text, then report the real count.

This is the user's own data in the user's own session, user-initiated. Note for the user: automated reading of a session sits in a grey zone under LinkedIn's User Agreement; keep it to their own profile, their own session, low volume. Never point a third-party scraper at LinkedIn.

## Optional reliability upgrade: the official data export

Recommend this when the browser capture comes back thin (under ~8 posts) or the user wants the most complete, reliable read. It returns the full post history.

1. Settings & Privacy -> Data privacy -> **Download my data**.
2. Click **Request new archive** (the file picker with the Posts/Shares option only appears here, not on the default screen).
3. Either tick the **Posts / Shares** file (emailed in minutes) or choose the larger full archive (up to 24 hours).
4. Note: LinkedIn **rate-limits archive requests to roughly one per 2 hours**, so if a recent archive was already requested, the picker is locked until the cooldown clears.
5. Download the ZIP. The relevant file is `Shares.csv` (post text, dates, URLs, visibility; no engagement metrics). Feed it straight to `scripts/stylometry.py`.

## Alternative: manual copy-paste

If neither path is convenient, the user can copy their posts from their activity feed into a `.txt` file, one post per block separated by a line containing only `---`. Useful when they want to hand-pick specific (for example high-performing) posts.

## Not allowed: third-party scrapers / unofficial APIs

LinkedIn returns HTTP 999 to non-browser agents and bans accounts for scraping (User Agreement section 8.2). The hiQ v. LinkedIn ruling only limited one federal hacking claim over public data; hiQ still lost on breach of contract. Off the table for a shareable skill.

## Required reporting

Whatever method is used, record and report three numbers:
- **Attempted:** how many posts/activity entries were found or listed.
- **Captured:** how many rendered as usable text and were collected.
- **Used:** how many went into the analysis (after dropping reposts' borrowed bodies, empty stubs, duplicates).

Then state the confidence tier that the "used" count implies (under 8 = low, 8-19 = moderate, 20+ = strong). Never present results without these numbers.
