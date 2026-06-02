#!/usr/bin/env python
"""
stylometry.py - deterministic style metrics for a corpus of LinkedIn posts.

Part of the linkedin-profile-tov-analyzer skill. Produces the OBJECTIVE layer
of a voice profile so the analysis is reproducible, not impressionistic. The
interpretive layers (stance, humour, signature phrases) are done by the model
reading the posts; this script handles only what can be counted.

Input (one of, auto-detected by extension):
  - a .txt file with posts separated by a line containing only --- (3+ dashes)
  - a .jsonl file with one object per line containing a "text" field
  - a LinkedIn data-export Shares.csv (auto-detects the commentary column)

Usage:
  python stylometry.py <path> [--out metrics.json]

Output: JSON to stdout (or to --out). Pure standard library. No network calls.
"""
import argparse
import csv
import json
import re
import sys
import statistics
from collections import Counter

# Emoji ranges (common pictographic + symbol blocks + variation selector).
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF"
    "️"
    "]"
)
WORD_RE = re.compile(r"[A-Za-z']+")
HASHTAG_RE = re.compile(r"#\w+")
SENT_SPLIT_RE = re.compile(r"[.!?]+(?:\s|$)")
CONTRACTION_RE = re.compile(r"\b\w+(?:n't|'re|'ve|'ll|'d|'m|'s)\b", re.IGNORECASE)

POV = {
    "first_singular": {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'd", "i'll"},
    "first_plural": {"we", "us", "our", "ours", "ourselves", "we're", "we've"},
    "second": {"you", "your", "yours", "yourself", "you're", "you've"},
    "third": {"they", "them", "their", "theirs", "he", "she", "him", "her", "his"},
}

# Minimum words for a "real" sentence when flagging short/fragment style.
SHORT_SENTENCE_WORDS = 5


def read_posts(path):
    lower = path.lower()
    if lower.endswith(".csv"):
        return _read_csv(path)
    if lower.endswith(".jsonl"):
        return _read_jsonl(path)
    return _read_txt(path)


def _read_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            text = (obj.get("text") or obj.get("commentary") or "").strip()
            if text:
                out.append(text)
    return out


def _read_csv(path):
    posts = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        col = None
        for name in fields:
            if name and re.sub(r"\s+", "", name).lower() in (
                "sharecommentary", "commentary", "sharecomment", "text", "post"
            ):
                col = name
                break
        if col is None and fields:
            col = fields[-1]  # last column is the LinkedIn commentary in older exports
        for row in reader:
            text = (row.get(col) or "").strip()
            if text:
                posts.append(text)
    return posts


def _read_txt(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    chunks = re.split(r"(?m)^\s*-{3,}\s*$", raw)
    posts = [c.strip() for c in chunks if c.strip()]
    if len(posts) <= 1:
        # fallback: treat 3+ newline gaps as post separators
        alt = [b.strip() for b in re.split(r"\n\s*\n\s*\n", raw) if b.strip()]
        if len(alt) > len(posts):
            posts = alt
    return posts


def _sentences(text):
    return [s.strip() for s in SENT_SPLIT_RE.split(text) if s.strip()]


def _stat(values):
    if not values:
        return {"mean": 0, "stdev": 0, "min": 0, "max": 0}
    return {
        "mean": round(statistics.mean(values), 2),
        "stdev": round(statistics.pstdev(values), 2) if len(values) > 1 else 0,
        "min": min(values),
        "max": max(values),
    }


def _confidence_tier(n):
    if n >= 20:
        tier = "strong"
    elif n >= 8:
        tier = "moderate"
    else:
        tier = "low"
    notes = {
        "strong": "20+ posts: patterns are reliable.",
        "moderate": "8-19 posts: directional. Verify key traits against more posts where possible.",
        "low": "Under 8 posts: provisional only. Do not assert firm rules; gather more posts first.",
    }
    return {"n_posts": n, "tier": tier, "note": notes[tier]}


def analyze(posts):
    n = len(posts)
    if n == 0:
        return {"error": "no posts found in input"}

    all_words = []
    sent_lens = []
    post_chars = []
    post_lines = []
    para_lens = []
    first_lines = []
    pov_counts = Counter()
    punct = Counter()
    emoji_counter = Counter()
    hashtags = Counter()
    contraction_total = 0
    short_sentences = 0
    total_sentences = 0

    for text in posts:
        post_chars.append(len(text))
        lines = text.splitlines()
        post_lines.append(len([l for l in lines if l.strip()]))
        for l in lines:
            if l.strip():
                first_lines.append(l.strip())
                break
        for para in [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]:
            para_lens.append(len(_sentences(para)) or 1)
        sents = _sentences(text)
        total_sentences += len(sents)
        for s in sents:
            words = WORD_RE.findall(s)
            if words:
                sent_lens.append(len(words))
                if len(words) < SHORT_SENTENCE_WORDS:
                    short_sentences += 1
        words = [w.lower() for w in WORD_RE.findall(text)]
        all_words.extend(words)
        for w in words:
            for cat, members in POV.items():
                if w in members:
                    pov_counts[cat] += 1
        punct["em_dash"] += text.count("—")
        punct["en_dash"] += text.count("–")
        punct["hyphen"] += text.count("-")
        punct["ellipsis"] += text.count("…") + len(re.findall(r"\.\.\.", text))
        punct["exclamation"] += text.count("!")
        punct["question"] += text.count("?")
        punct["comma"] += text.count(",")
        punct["colon"] += text.count(":")
        punct["semicolon"] += text.count(";")
        punct["parens"] += text.count("(")
        for e in EMOJI_RE.findall(text):
            emoji_counter[e] += 1
        for h in HASHTAG_RE.findall(text):
            hashtags[h.lower()] += 1
        contraction_total += len(CONTRACTION_RE.findall(text))

    total_words = len(all_words)

    def per_1000(x):
        return round(x * 1000.0 / total_words, 2) if total_words else 0

    uniq = len(set(all_words))
    hapax = sum(1 for _, c in Counter(all_words).items() if c == 1)
    pov_total = sum(pov_counts.values()) or 1
    sent_stat = _stat(sent_lens)

    return {
        "corpus": {
            "n_posts": n,
            "total_words": total_words,
            "avg_words_per_post": round(total_words / n, 1),
            "avg_chars_per_post": round(sum(post_chars) / n, 1),
            "avg_lines_per_post": round(sum(post_lines) / n, 1),
        },
        "sentences": {
            "total": total_sentences,
            "words_per_sentence": sent_stat,
            "burstiness_stdev": sent_stat["stdev"],
            "pct_short_sentences_under_5w": round(
                100.0 * short_sentences / (len(sent_lens) or 1), 1
            ),
        },
        "paragraphs": {"sentences_per_paragraph": _stat(para_lens)},
        "lexical": {
            "type_token_ratio": round(uniq / total_words, 3) if total_words else 0,
            "hapax_rate": round(hapax / total_words, 3) if total_words else 0,
            "unique_words": uniq,
        },
        "point_of_view": {
            "first_singular_pct": round(100.0 * pov_counts["first_singular"] / pov_total, 1),
            "first_plural_pct": round(100.0 * pov_counts["first_plural"] / pov_total, 1),
            "second_pct": round(100.0 * pov_counts["second"] / pov_total, 1),
            "third_pct": round(100.0 * pov_counts["third"] / pov_total, 1),
            "raw_counts": dict(pov_counts),
        },
        "punctuation_per_1000_words": {k: per_1000(v) for k, v in punct.items()},
        "punctuation_raw": dict(punct),
        "emoji": {
            "total": sum(emoji_counter.values()),
            "per_post": round(sum(emoji_counter.values()) / n, 2),
            "top": emoji_counter.most_common(10),
        },
        "hashtags": {
            "total": sum(hashtags.values()),
            "avg_per_post": round(sum(hashtags.values()) / n, 2),
            "unique": hashtags.most_common(20),
        },
        "contractions": {
            "total": contraction_total,
            "per_1000_words": per_1000(contraction_total),
        },
        "hooks_first_lines": first_lines[:30],
        "confidence": _confidence_tier(n),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Deterministic stylometry for a LinkedIn post corpus."
    )
    ap.add_argument(
        "path",
        help="posts file: .txt (posts split by a line of ---), .jsonl, or LinkedIn Shares.csv",
    )
    ap.add_argument("--out", help="write JSON here instead of stdout")
    args = ap.parse_args()

    # Force UTF-8 stdout so emoji in the metrics do not crash on a Windows cp1252 console.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        posts = read_posts(args.path)
    except FileNotFoundError:
        print(json.dumps({"error": "file not found: " + args.path}))
        sys.exit(1)
    except Exception as e:  # surface, never swallow
        print(json.dumps({"error": "could not read input: " + str(e)}))
        sys.exit(1)

    result = analyze(posts)
    out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        n = result.get("corpus", {}).get("n_posts", "?")
        print("wrote " + args.out + " (" + str(n) + " posts)")
    else:
        print(out)


if __name__ == "__main__":
    main()
