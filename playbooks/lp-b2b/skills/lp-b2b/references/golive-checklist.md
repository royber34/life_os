# Go-live checklist

Every line is something that broke on a real page. Mark each one done (with evidence), at deploy, or needs the user (with what) in `site/build-report.md`.

## Form and measurement
- [ ] The host's form handling is switched on and one test request through every step arrived (with detection off, test submissions silently return a 404).
- [ ] Only the first step's fields show at first render on a 375 px phone.
- [ ] The fields match what the follow-up needs; optional fields last.
- [ ] Notifications go to an inbox someone reads, with a clear subject.
- [ ] Requests land where the team works (a sheet or CRM), with the source.
- [ ] `page_version` set and raised per release; one form name per page version.
- [ ] Page-view analytics in place, so requests have a denominator.

## Link preview
- [ ] og title, description and a 1200x630 image with a `?v=` cache-buster; PNG favicons.
- [ ] The preview read cold, with no page around it ("they" in a preview had no referent once).
- [ ] Tested live in a chat app with a fresh `?v=` and in LinkedIn's Post Inspector.

## What gets published
- [ ] Only page files are public; README, notes and reviews return 404 (both real builds served their README publicly at first).
- [ ] The host's badge is off if it covers the mobile button.
- [ ] `noindex` (meta tag and X-Robots-Tag header) while the page is unlisted.
- [ ] Custom domain and www point at this project; HTTPS issued.

## Page integrity
- [ ] Light theme declared and checked on a dark-mode phone.
- [ ] The thanks page and any no-JavaScript fallback match the current copy, fonts and theme (one stale thanks page stayed live for ten versions).
- [ ] One number per claim across page, preview and image.
- [ ] `capture.py` and `check_page.py` report no warnings or FAILs.

## Legal (check your market; examples for Germany, Switzerland and the EU, based on secondary sources checked in October 2026, not legal advice)
- [ ] Germany: an Impressum per section 5 of the Digitale-Dienste-Gesetz (it replaced section 5 TMG on 14 May 2024 with the same content): name, postal address, email, a second fast contact route, register and VAT details where they exist.
- [ ] Switzerland: identity and contact address including email (UWG Art. 3 para. 1 lit. s).
- [ ] A privacy notice reachable from the form (GDPR Art. 13).
- [ ] No third-party request before consent: self-host web fonts (a Munich court ruled in January 2022 that loading Google Fonts from Google's servers without consent was unlawful); no tracking script without a consent step.
- [ ] Examples labelled as examples; guarantee terms stated plainly.

## Release
- [ ] Iterated on previews; one publish per approved release.
- [ ] A rollback point for the previous live version.
- [ ] The user's explicit yes for the publish, recorded in `STATE.md`.
