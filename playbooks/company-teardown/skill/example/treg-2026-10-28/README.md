# Example bundle

`bundle-sample.json` is a small bundle for trying the dashboard without running a teardown. It has 60 dated events, 30 go-to-market actions and two metric series (GitHub stars and PyPI downloads), taken from public sources up to 2026-10-28.

Every row is basis `fact` and confidence `high`. It holds no revenue or user estimates, no competitors or market rows, and no named people other than the publicly named founder. Legal and incident rows are left out. Nobody has verified it independently, so the page says "Not verified yet". The rows are a spread across the dates, so the timeline is incomplete by design: treat it as a demo and do not cite it.

The moves, insights, impact and connections sections are format examples, marked as such: they show the structure and make no claims about the company.

## Try it

From `skill/`:

```
python -I scripts/build_dashboard.py validate example/treg-2026-10-28
python -I scripts/build_dashboard.py build example/treg-2026-10-28
```

`build` writes `example/treg-2026-10-28/dashboard/index.html`, about 0.5 MB. Open it in a browser. The built file is not kept in the repo.
