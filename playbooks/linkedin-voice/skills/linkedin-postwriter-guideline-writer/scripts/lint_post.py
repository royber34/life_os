#!/usr/bin/env python
"""
lint_post.py - advisory mechanical scan of a draft LinkedIn post against the
hard bans a Roy-style voice guideline encodes.

IMPORTANT: this is an ASSIST, not a judge. The regex heuristics (especially the
negation-reframe and em-dash checks) WILL produce false positives. A human, or
the drafting agent, makes the final call. Nothing here auto-rejects a post.

Usage:
  python lint_post.py <draft.txt> [--json] [--max-hashtags 3]
  type draft.txt | python lint_post.py -        (Windows stdin)
  cat draft.txt  | python lint_post.py -        (unix stdin)

Pure standard library. No network.
"""
import argparse
import json
import re
import sys

BUZZWORDS = [
    "delve", "leverage", "seamless", "robust", "elevate", "tapestry", "realm",
    "fast-paced", "it's worth noting", "it is worth noting", "let's dive in",
    "in conclusion", "in summary", "game-changer", "game changer",
    "supercharge", "testament to", "navigating the", "ever-evolving", "unlock the",
]

# Heuristic negation-reframe ("not X, it's Y") detectors. Fuzzy by design.
NEG_REFRAME = [
    re.compile(r"\b(it'?s|this is|that'?s)\s+not\b[^.?!]{0,80}[,.]?\s+(it'?s|it is|but|rather|instead)\b", re.I),
    re.compile(r"\b(isn'?t|wasn'?t|aren'?t|don'?t|doesn'?t)\b[^.?!]{0,80}[.?!]\s+(it'?s|it is|they'?re|that'?s)\b", re.I),
    re.compile(r"\bnot just\b[^.?!]{0,60}\bbut\b", re.I),
]


def check(text, max_hashtags=3):
    findings = []

    def add(severity, rule, message, snippet=""):
        findings.append({
            "severity": severity, "rule": rule,
            "message": message, "snippet": snippet[:140].replace("\n", " "),
        })

    # em-dash (the #1 tell; this guideline bans the character outright)
    em = text.count("—")
    if em:
        add("blocker", "em-dash",
            str(em) + " em-dash character(s). Use a spaced hyphen ' - ' instead.")

    # tilde approximation
    for m in re.finditer(r"~\s*\d", text):
        add("blocker", "tilde-approximation",
            "'~' used for approximation. Write 'about' / 'around' or the plain number.",
            text[max(0, m.start() - 20):m.start() + 20])

    # negation-reframe (heuristic)
    for rx in NEG_REFRAME:
        for m in rx.finditer(text):
            add("blocker", "negation-reframe",
                "Possible 'not X, it's Y' construction (the #1 AI tell). Rewrite as a direct positive claim. Heuristic, verify.",
                m.group(0))

    # links in body
    for m in re.finditer(r"https?://\S+", text):
        add("blocker", "link-in-body",
            "URL in the post body suppresses reach. Move it to the first comment or use a comment-to-send CTA.",
            m.group(0))

    # hashtags
    tags = re.findall(r"#\w+", text)
    if len(tags) > max_hashtags:
        add("flag", "hashtags",
            str(len(tags)) + " hashtags (guideline max " + str(max_hashtags) + ").",
            " ".join(tags))

    # exclamation marks
    ex = text.count("!")
    if ex:
        add("flag", "exclamation",
            str(ex) + " exclamation mark(s). Prefer emphasis via a fragment, not '!'.")

    # paragraph length > 2 sentences. Fragment-triads ("Positive EBITDA. Positive
    # cash flow. No outside funding.") are a deliberate rhythmic device, not bloat,
    # so only count "full" sentences (>= 6 words). A run of short fragments passes.
    FULL_SENTENCE_WORDS = 6
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    for i, p in enumerate(paras, 1):
        sents = [s for s in re.split(r"[.!?]+(?:\s|$)", p) if s.strip()]
        first = p.lstrip()[:1]
        is_bullet = first in ("-", "•", "💎", "*")
        full_sentences = sum(1 for s in sents if len(s.split()) >= FULL_SENTENCE_WORDS)
        if full_sentences > 2 and not is_bullet:
            add("flag", "paragraph-length",
                "Paragraph " + str(i) + " has " + str(full_sentences) +
                " full sentences (guideline max 2). Add a line break. (Short fragment-triads are exempt.)",
                p[:120])

    # buzzwords / AI-tell phrases
    low = text.lower()
    for b in BUZZWORDS:
        idx = low.find(b)
        if idx != -1:
            add("flag", "buzzword", "AI-tell phrase: '" + b + "'.",
                text[max(0, idx - 15):idx + len(b) + 15])

    return findings


def main():
    ap = argparse.ArgumentParser(
        description="Advisory lint of a draft LinkedIn post against guideline bans. Assist, not judge."
    )
    ap.add_argument("path", help="draft .txt file, or '-' for stdin")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--max-hashtags", type=int, default=3)
    args = ap.parse_args()

    try:
        text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    except FileNotFoundError:
        print("error: file not found: " + args.path)
        sys.exit(1)

    findings = check(text, args.max_hashtags)
    blockers = [f for f in findings if f["severity"] == "blocker"]
    flags = [f for f in findings if f["severity"] == "flag"]

    if args.json:
        print(json.dumps(
            {"findings": findings, "counts": {"blocker": len(blockers), "flag": len(flags)}},
            indent=2, ensure_ascii=False))
        return

    if not findings:
        print("PASS: no mechanical issues found.")
        print("(Voice match and hook quality still need human judgment - the lint only catches mechanics.)")
        return

    print("ADVISORY SCAN: " + str(len(blockers)) + " blocker(s), " + str(len(flags)) +
          " flag(s). Heuristic, verify each. Nothing here auto-rejects.\n")
    for f in findings:
        print("[" + f["severity"].upper() + "] " + f["rule"] + ": " + f["message"])
        if f["snippet"]:
            print("    > " + f["snippet"])
    print("\nReminder: the negation-reframe and em-dash checks can false-positive. Human judgment decides.")


if __name__ == "__main__":
    main()
