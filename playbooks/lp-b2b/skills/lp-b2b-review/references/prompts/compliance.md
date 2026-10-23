# Compliance and style read
Placeholders: {CAPTURE_DIR}, {HTML_FILE}, {DECISIONS_FILE}, {INPUTS_DIR} (may be empty), {LEGAL_MARKET} (for example "Germany, B2B"), {OUTPUT_FILE}.

## The standard (read first)
This is a sales page. The seller owns their claims and their framing of their own results. Flag only:
- claims that are plainly false or invented: numbers, clients, results, testimonials, logos, or a result stated as something it was not (one person's result shown as a team's, one post shown as an average, someone else's result under the seller's name);
- legal must-haves for {LEGAL_MARKET}: for example for German or Swiss B2B pages, an Impressum and a privacy notice reachable from the page, a data-use line at the form, third-party requests that send visitor data without consent (for example fonts loaded from Google), guarantee terms that would mislead, examples presented as real clients.
Never ask for caveats, footnotes, averages, sample sizes or time windows on numbers, evidence for capability claims, payment terms, VAT amounts, supplier details or anything on the never-on-the-page list in {DECISIONS_FILE}. Its accepted gaps are closed. When you are unsure whether something is false, say what you would need to check; do not guess.

## Read
`{CAPTURE_DIR}/page-text.txt`, `{CAPTURE_DIR}/link-preview-meta.txt`, {HTML_FILE} (form fields, hidden fields, head tags, third-party requests), {DECISIONS_FILE}. When a finding is about what the seller said or did, check it against {INPUTS_DIR} and cite the line (file and timestamp); a finding without a source is a NOTE, never a BLOCKER.

## Style lint (visible text and share card)
Em-dash, exclamation marks, negation-reframe phrasing ("it's not X, it's Y", "not just", "isn't X", "was never"), "founding" or "beta", lock-in wording, "client work", "they" or "it" without context in the first screen and the share card, two different numbers for one claim, labels that do not match reality ("two quick questions" followed by four).

## Write {OUTPUT_FILE}
One line per finding, starting BLOCKER (page cannot go live), FIX (should change), or NOTE (the seller's call), each with the exact text, the source for any factual claim, and the change. Mark each BLOCKER as either "page-fixable" or "needs a fact from the seller". End with what you checked and found clean. Reply with one line: counts of BLOCKER / FIX / NOTE.
