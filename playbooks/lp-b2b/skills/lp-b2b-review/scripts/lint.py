"""Style lint for B2B sales page text, under the default house rules (edit RULES to change them).

Usage: python -I lint.py <text-or-markdown-file> [more files]
Advisory: prints every hit with its line number and a count per rule, always exits 0.
"""
import re
import sys
import pathlib

RULES = [
    ("em-dash", re.compile(chr(0x2014))),
    ("exclamation mark", re.compile(r"(?<!<)!(?!-|important|=)")),
    ("negation reframe", re.compile(r"\b(it'?s not|this isn'?t|that isn'?t|isn'?t just|not just|not only|was never|were never|is never about|the hard part (was|is) never)\b", re.I)),
    ("starting-out word", re.compile(r"\b(founding (members?|spots?|prices?|clients?|customers?|cohort|offer|rates?)|beta|early access|pilot customers?)\b", re.I)),
    ("lock-in word", re.compile(r"\b(locked( in)?|minimum term|lock-in|binding for|commit(ted)? for \d+)\b", re.I)),
    ("confidentiality scare", re.compile(r"\bclient work\b", re.I)),
    ("generic SaaS phrase", re.compile(r"\b(get started for free|powered by ai|join thousands|learn more|unlock|seamless(ly)?|revolutioni[sz]e|supercharge|game[- ]chang\w*|cutting[- ]edge|next[- ]level|leverage the power)\b", re.I)),
    ("hedge on a number", re.compile(r"\b(on average|average of|best of (the )?(first )?\w+ posts?|one person'?s results?|results may vary)\b", re.I)),
]


def lint(path: pathlib.Path) -> dict:
    counts = {name: 0 for name, _ in RULES}
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for name, rx in RULES:
            for m in rx.finditer(line):
                counts[name] += 1
                start = max(0, m.start() - 40)
                print(f"{path.name}:{i}: {name}: ...{line[start:m.end() + 40].strip()}...")
    return counts


if __name__ == "__main__":
    total = {name: 0 for name, _ in RULES}
    for arg in sys.argv[1:]:
        for name, c in lint(pathlib.Path(arg)).items():
            total[name] += c
    print("summary: " + ", ".join(f"{k} {v}" for k, v in total.items()))
