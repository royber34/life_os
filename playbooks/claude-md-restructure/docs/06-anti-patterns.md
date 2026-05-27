# 06 — Anti-patterns

The failure modes you should expect, organized by the phase that produces them. Each one names the mistake, the symptom that gives it away, and the right way to do it instead.

If you've read the previous docs and you're tempted to skip this one because "you wouldn't make these mistakes" — that's the first anti-pattern.

---

## Pre-restructure

### "I'll just delete some stuff"

The mistake: skipping the audit, the backup, and the staging — going straight to editing the live global file because you "know what's bloated."

Symptom: things break a few sessions later in ways you can't trace. You can't tell whether the breakage is from a deletion (which one?) or unrelated drift. No backup means no rollback.

Right way: every change goes through the seven-phase workflow even when it feels excessive. The phases are slow precisely because they make the failures visible while they're still cheap.

### "Let me add one more thing"

The mistake: the file grew because every time something went wrong, you added a rule to prevent recurrence. There was no rule for what should *not* be in the file, so the file only grew.

Symptom: a 600-line global file where most lines are reactive — added in response to a single incident, never re-examined.

Right way: pair "add a rule" with "what does this rule replace, or what test does it have to pass to stay?" If you can't answer, the rule doesn't go in.

---

## Research pass

### Treating opinion as authority

The mistake: citing blog posts and conference talks as if they were documentation, without distinguishing first-party (the people who built the tool) from third-party (practitioners with experience) from random-party (anyone with an audience).

Symptom: your principles document is built on three blog posts that contradict each other, and you didn't notice.

Right way: separate sources by tier. First-party docs and engineering posts set the rules. Practitioner posts inform interpretation. Opinion posts inform sentiment, not design.

### Under-research

The mistake: reading only the official docs and stopping there. Official docs say what's *possible*; they rarely say what tends to go wrong in practice.

Symptom: your plan is theoretically clean but doesn't survive contact with your actual file.

Right way: balance first-party docs with at least three accounts from practitioners who have done the restructure. Look specifically for posts that show the before-and-after.

---

## Audit

### Classifying based on "feels important"

The mistake: keeping bullets because they feel core to your work, without running the actual test ("would removing this cause Claude to make mistakes?").

Symptom: the new global is shorter than the old one but still bloated. You couldn't bring yourself to cut anything that "matters to your work" even though most of it was procedural and belonged in a skill.

Right way: the test is binary. If you can't construct a concrete mistake Claude would make without the bullet, the bullet goes. "It's nice to have it loaded" doesn't count.

### Missing the triple-duplicate pattern

The mistake: not noticing that the same rule appears in three places — once as a global bullet, once inside a project `CLAUDE.md`, and once captured in auto-memory.

Symptom: every session loads the same rule three times. Claude doesn't behave better because of it, but your context bill goes up.

Right way: during the audit, search every loaded file for each rule. Pick one home for it — usually the most specific one (project file > global) — and delete the others.

---

## Backup

### Backing up without verification

The mistake: copying files into a backup directory without hashing them, on the assumption that copy worked.

Symptom: when you restore from backup six weeks later, one file is silently truncated or corrupted. You don't notice for another week.

Right way: hash everything at backup time. Hash again at restore time. Compare. The whole point of a backup is the integrity guarantee, not the existence of a copy.

### Backing up but not testing restore

The mistake: writing the restore script, never running it, and assuming it works because the syntax looks right.

Symptom: the day you need to restore, the script fails on an edge case you didn't anticipate — a path with a space, a missing parent directory, a prompt that hangs because it's running non-interactively.

Right way: test the restore against a drifted file before you start the restructure. See `04-backup-and-safety.md`.

---

## Skill design

### Vague descriptions

The mistake: writing a skill description that's accurate but not invocable. "Helps with deployment" — Claude has no way to map a user's actual phrasing ("ship the new version", "deploy to staging", "push the build") onto that.

Symptom: you wrote a great skill, the runbook is solid, and it never fires because no user phrasing matches the description.

Right way: in the description, name the triggers in the words a user would actually use. List synonyms. Test by phrasing the same need five different ways and confirming the skill fires on at least three.

### Skills that are too narrow

The mistake: making one skill per runbook. You end up with seven skills covering the same area, with overlapping triggers — Claude picks the wrong one, or doesn't pick any because the descriptions blur together.

Symptom: a skills directory full of single-runbook skills with names like `deploy-staging`, `deploy-prod`, `rollback-staging`, `rollback-prod`, `check-deploy-status`.

Right way: group related runbooks into one skill. `release-ops` holds deploy, rollback, and status-check runbooks for both environments. The description fires on any of those triggers, and the body picks the right runbook based on context.

---

## Project CLAUDE.md

### Duplicating workflow rules from the global

The mistake: pasting cross-cutting rules from the global file into every project `CLAUDE.md` "for redundancy."

Symptom: every session loads each rule twice — once from global, once from project. The duplication doesn't help Claude (the second copy is ignored or, worse, conflicts subtly) but it does add noise.

Right way: project files hold project-specific content only. Cross-cutting rules live in the global, full stop.

### Reference content in CLAUDE.md instead of project README

The mistake: putting long-form reference material — architecture explanations, glossaries, full API descriptions — inside the project `CLAUDE.md`.

Symptom: project `CLAUDE.md` is several thousand words. Every session that enters the project tree loads the whole thing, even sessions that don't need it.

Right way: `CLAUDE.md` is orientation and rules. Reference goes in the project README or `docs/`. Link from `CLAUDE.md` so Claude can read on demand.

### Skipping the failure-log discipline

The mistake: the project file was written once at the start of the restructure and never updated, even as you correct Claude on the same project-specific issue for the fifth time.

Symptom: the same mistake recurs in the project every few weeks. You re-explain it every time.

Right way: when you correct Claude on something that'll likely recur in this project, add a line to the project `CLAUDE.md` immediately. That's the only way the file stays useful.

---

## Swap

### Swapping without a pre-swap snapshot

The mistake: skipping the pre-swap snapshot because you "already have a master backup."

Symptom: the swap goes wrong, and rolling back means digging through the master backup, finding the right file, running the restore script. Five minutes of stress when it should be one command.

Right way: take the pre-swap snapshot. It's one extra `Copy-Item`. It will save you exactly the day you need it.

### Not testing in a fresh session

The mistake: verifying the new global in the same session you've been working in for the last hour, where the old file is already loaded in context.

Symptom: verification passes. You declare success. The next morning, every fresh session is broken because the new file has a problem the old in-memory context was masking.

Right way: open a brand-new session for verification. Run the verification prompts there.

### Ignoring auto-memory drift

The mistake: the new global file is clean and minimal, but auto-memory still contains rules from when the global was bloated — some of which now contradict the new global.

Symptom: Claude behaves inconsistently — it follows the new global most of the time, but occasionally cites an auto-memory rule that contradicts it.

Right way: review auto-memory files after the swap. Prune anything that's now duplicated or contradicted by the new global.

---

## Post-restructure

### The file calcifies

The mistake: treating the restructure as a one-shot project. After it ships, the file stops being maintained.

Symptom: six months later, the file is bloated again. Same problem, same restructure needed.

Right way: failure-log discipline as a permanent practice. Every correction that'll likely recur prompts a question — "should this go in the global, a project file, or stay as a one-off?" Most go in a project file or get absorbed into an existing skill. A few belong in the global.

### Assuming the work is "done"

The mistake: post-swap, you stop running the test on new additions. New bullets get added without asking "would removing this cause Claude to make mistakes?"

Symptom: the file regrows. Every new bullet was added for a real reason at the time, none of which would pass the test on second look.

Right way: the test isn't only for the restructure. It's the gate for every future addition.

### Promoting auto-memory rules to global without thinking

The mistake: an auto-memory rule looks generally useful, so you promote it to the global file. You skip the test because "it was already there."

Symptom: the global file accumulates promoted rules that pass the "feels important" filter but not the actual test.

Right way: when promoting from auto-memory to global, the rule has to pass the test the same as any other candidate. Most auto-memory rules belong in a project file or a skill, not the global.

---

## The meta-pattern

Every anti-pattern above shares a shape: a step was skipped because it felt unnecessary in the moment, and the cost of skipping it became visible only later. The phases and tests in this playbook exist to make the cost visible *now*, when it's still cheap to fix.

If you find yourself thinking "this step is overkill for my situation," that's worth a pause. Sometimes you're right and the step is genuinely unnecessary for what you're doing. More often, you're about to produce one of the symptoms above.
