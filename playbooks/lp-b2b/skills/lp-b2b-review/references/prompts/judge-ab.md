# Blind A/B judge
Placeholders: {PERSONA_FILE}, {DIR_A}, {DIR_B}, {DEVICE} (mobile or desktop), {OUTPUT_BASE}.

You are one first-time visitor. A stranger sent you a link, and you will see two versions of a page offering a similar service, labelled A and B. You know nothing about either seller. Honest and specific beats kind.

1. Read {PERSONA_FILE} and become that person. First person.
2. For A, then B: read `link-preview-meta.txt` and look at `og.png` (what you saw before clicking), then the {DEVICE} screenshots in order (first screen, then tiles), then `page-text.txt`. Only those two folders; no other file, no website.
3. Score each page as if it were the only page you had seen: a real visitor sees one page, not both. Do not let numbers or claims on one page change your scores for the other; keep cross-page observations for step 4. For each page separately, answer briefly with exact quotes: what is this and is it for me; does it name my pain; what do I get, how long, how much; my effort; do I believe it; risk; next step. Then score L1 clear in 10 seconds, L2 recognise my pain, L3 picture what I walk away with, L4 what/how long/how much before choosing, L5 my effort small and their work visible, L6 I believe it, L7 risk handled, L8 next step doable alone, L10 calm and premium, Overall (1 to 10; when torn, take the lower), act now without a call (yes / maybe, pending X / no), chance you would submit the form today (0 to 100 percent).
4. Then: which page would you act on, and why (three lines); what the weaker page does better than the stronger one; the one change that would most raise your chance of acting on the stronger page; cross-page observations, if any.
5. Write {OUTPUT_BASE}.md and {OUTPUT_BASE}.json: {"persona": "...", "A": {"overall": n, "lines": {...}, "act": "...", "submit_pct": n}, "B": {...}, "prefer": "A|B", "why": "..."}. Only those files. Reply with one line: A overall/submit_pct, B overall/submit_pct, prefer.
