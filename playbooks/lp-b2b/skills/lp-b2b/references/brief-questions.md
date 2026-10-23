# The key questions (stage 1)

Ask only what the inputs don't already answer: at most seven questions, in two or three rounds, plain words, each with a default the user can accept with "yes". If more is unknown, use defaults and list them. When a default cannot apply (no prices given, no story to tell), leave a visible placeholder such as `[MISSING: prices]`: placeholders don't block the wireframe, but they block going live.

| # | Question | Why it matters | Default if the user doesn't know |
|---|---|---|---|
| 1 | **What is the one thing a visitor should do on the page, and what happens after?** (order, request a start, book a call, sign up, join a waitlist) | The page has one job; every section serves it | A request form; "we reply within one working day" |
| 2 | **What do you sell, in one sentence, and to whom?** (role, company type and size, market) | The first screen has to say both in seconds | Draft the sentence from the inputs and ask for a yes |
| 3 | **How do visitors arrive?** (cold LinkedIn message, email, forwarded by a colleague, ads, your network) and on what device | Sets the tone, the link preview and how much they know already | Cold, from a link, on a phone |
| 4 | **What are the options and prices?** What is included, over how long, what does the buyer do themselves? | Visitors need what, how long and how much before they choose | Three options, the middle one recommended, price and duration on each; with no prices given, `[MISSING: prices]` |
| 5 | **What risk reversal can you carry?** (money back on a defined result, nothing binding until you confirm, a paid first step, a free first session) | The risk line under the button moves more visitors than any other line | "Nothing is binding until we confirm your start" |
| 6 | **What proof do you have?** Your own results with real numbers (and what each number is), clients who agreed in writing to be named, photos of the people behind it, screenshots, profile links | Belief is the hardest part; only real proof moves it | The people behind it, with names and roles; no client names without written consent; `[MISSING: proof]` for the rest |
| 7 | **Anything else fixed?** Brand and domain, language and currency, the legal market, rules for your profession about what you may claim or call yourself, where it will be hosted, words you never use, anything that must never be on the page | These shape the build and keep reviewers from re-opening closed topics | One page in the buyers' language and currency, a static host with a form (for example Netlify), no tracking |

After the answers, also decide the build size and write it into the brief: one static HTML page, unless at least two of these hold: several language or segment versions share the same content, a price calculator, a generated document such as an order PDF, many automated edits that need checks. A small page in one file can be changed in minutes; a template engine with tests turns every structural change into a project.
