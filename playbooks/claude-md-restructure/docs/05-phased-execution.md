# 05 — Phased execution

This is the operational core of the playbook. Seven phases, in order. Each phase has a verification gate before you move on. Skipping the gate is how you end up debugging the restructure instead of finishing it.

Each phase below follows the same template: goal, inputs, steps, verification gate, rollback, output. Read the whole phase before starting the steps in it — some steps depend on context that's later in the section.

---

## Phase 1 — Research pass

**Goal.** Before touching your own files, understand what other practitioners have already learned about `CLAUDE.md` structure, skill design, and the auto-loader. Calibrate against multiple sources, not one.

**Inputs.** A few hours of focused reading time. A way to capture notes (a scratchpad doc is fine).

**Steps.**

1. Read the official Claude Code documentation on `CLAUDE.md` files, skills, the auto-load hierarchy, and the agent SDK if it's referenced.
2. Find and read at least 3 first-party Anthropic sources that discuss `CLAUDE.md` design — engineering posts, talks, interviews with the team that built Claude Code. Note the specific tests and principles they articulate.
3. Find at least 3 high-signal community sources — practitioners who have actually restructured a bloated file and written about it. Avoid pure opinion posts; favour posts that show before/after.
4. Capture the points where sources disagree. Those are the decisions you'll need to make explicitly later.
5. Write a one-page summary of "here's what I think the rules are, and here's where I'm unsure." That document becomes the input to Phase 2.

**Verification gate.** You can answer, in your own words: what belongs in a global `CLAUDE.md`, what doesn't, why, and which of those answers you're confident in vs. taking on faith.

**Rollback.** None — this phase is read-only.

**Output.** A short principles document and a list of open questions. You'll use it to audit your existing setup.

---

## Phase 2 — Audit your existing setup

**Goal.** Inventory everything Claude Code currently loads on your behalf, and classify each block of content by the test from Phase 1.

**Inputs.** The principles document from Phase 1. Your live `~/.claude/CLAUDE.md` and any project-level `CLAUDE.md` files.

**Steps.**

1. List every file Claude Code loads at session start: the global `CLAUDE.md`, every project `CLAUDE.md` in trees you work in, every `CLAUDE.local.md`, every `MEMORY.md` under `~/.claude/projects/`.
2. For the global file specifically, break it into blocks (a block = a heading and its content, or a contiguous list under one bullet). Number them.
3. For each block, apply the "would removing this cause Claude to make mistakes?" test. Honest answers only — "it feels important" doesn't count.
4. Classify each block as one of:
   - **Keep in global** — a rule that affects every session and removing it causes mistakes.
   - **Move to a skill** — a procedure or runbook; Claude needs it sometimes, not always.
   - **Move to project `CLAUDE.md`** — context specific to one project tree.
   - **Move to README or docs** — reference content; humans need it, Claude doesn't need it pre-loaded.
   - **Delete** — duplicate, stale, or fails the test.
5. Watch for the triple-duplicate pattern: the same rule expressed once as a global bullet, once inside a project file, and once captured in auto-memory. All three load simultaneously into your context. Pick one home for it.

**Verification gate.** Every block in your current files has a classification. You can defend each classification by pointing to the test, not your intuition.

**Rollback.** None — this phase is also read-only. You're producing a plan, not editing files.

**Output.** A classification table: block → current location → target location → reason.

---

## Phase 3 — Backup with hash verification

See `04-backup-and-safety.md` for the full procedure. Don't skip it. The rest of this document assumes you've finished it.

**Verification gate.** You have a tested, hash-verified backup of every file that will be modified. You've actually run the restore script against a drifted file and watched it work.

**Output.** A date-stamped backup directory you trust.

---

## Phase 4 — Build skills for procedures

**Goal.** For every block classified "move to a skill" in Phase 2, produce a working skill. This is the largest phase by time spent.

**Inputs.** The classification table from Phase 2. Your backup from Phase 3.

**Steps.**

1. Group related runbooks. Don't make one skill per procedure — make one skill per coherent area of operation. A skill that handles "deploy, rollback, and incident response" for a service is more useful than three near-identical skills with overlapping triggers.
2. For each skill, write the frontmatter first. The frontmatter description is the single most important line in the file. It's how Claude decides whether to invoke the skill. Bad descriptions are the #1 reason skills never fire.
3. Write the body as a runbook with explicit structure:

   ```
   ---
   name: example-skill
   description: One paragraph that names the triggers (verbs and nouns a user would say), the inputs the skill expects, the outputs it produces, and when NOT to invoke it.
   ---

   # Skill name

   ## When to use this
   Concrete triggering scenarios. Bullet form.

   ## Pre-conditions
   What must already be true before running this.

   ## Runbook: <task name>
   1. Step. Concrete command or example.
   2. Step. Verification line ("you should see X").
   3. Step. ...

   ## Source
   "Captured from a real session on <date> where <what happened>" — not theoretical.

   ## What does NOT belong in this skill
   Adjacent things you might be tempted to handle here but shouldn't. Forces clarity about scope.
   ```

4. **The description-first principle.** Imagine a user phrasing their need in five different ways. Does your description match at least three of them? If not, rewrite it. Include synonyms, alternate verbs, the noun forms ("debug X" / "X is broken" / "fix X").
5. **The "source" attribution rule.** Every runbook step should be traceable to a real session where you ran it, not theoretical text you wrote because it sounded right. Theoretical runbooks rot — they read fine but fail in execution because nobody ever ran them end-to-end.
6. **The "what does NOT belong" footer.** This is the rule that prevents skills from sprawling. When you add a new runbook later, you ask "does this violate the NOT-belong list?" before adding.
7. Test each skill in a separate Claude Code session by phrasing the trigger five different ways. If it doesn't fire on three of them, the description needs work.

**Verification gate.** Every "move to skill" block from Phase 2 is implemented in a skill. Every skill fires on at least three phrasings of its trigger.

**Rollback.** Skills are additive — if a skill is broken, delete the skill file. The global `CLAUDE.md` you'll write in Phase 6 references skill names; if a skill doesn't exist when the new global goes live, the pre-flight check in Phase 6 will catch it.

**Output.** A populated `~/.claude/skills/` directory. A list of skill names you'll reference from the new global.

---

## Phase 5 — Move project content to project CLAUDE.mds

**Goal.** For every block classified "move to project `CLAUDE.md`" in Phase 2, place it in the right project tree so the auto-loader picks it up only when you're working in that project.

**Inputs.** The classification table from Phase 2. The directory layout of your projects.

**Steps.**

1. Understand the auto-load mechanism. Claude Code walks up the current working directory tree at session start and loads any `CLAUDE.md` it finds along the way. A project `CLAUDE.md` at `~/projects/foo/CLAUDE.md` loads only when your cwd is inside `~/projects/foo/`. The global `~/.claude/CLAUDE.md` always loads.
2. This is why moving project-specific content out of the global file is free wins: it shrinks every session's context, and the content reappears exactly when you need it.
3. Place project content. For each "move to project" block, identify the right project directory and write or extend the `CLAUDE.md` at its root.
4. Separate concerns within the project. A project `CLAUDE.md` should hold:
   - Orientation (what is this project, what state is it in).
   - Project-scoped rules (conventions specific to this tree).
   - Pointers to other docs in the project.

   It should NOT hold:
   - **Architecture detail.** Put that in `ARCHITECTURE.md` in the project. Claude reads it on demand, doesn't load it every session.
   - **Frequently-changing state.** Put plans in `PLANS.md`, status in `STATUS.md`, todos in `TODO.md`. Those churn — keep them out of the auto-loaded file.
   - **Reference content.** Put long reference text in the project README or `docs/`. Link to it from `CLAUDE.md`.
5. The shape of a good project `CLAUDE.md`: a few hundred words of orientation and rules, plus pointers. Anything longer is a smell.

**Verification gate.** Open a session inside the project tree. The project's `CLAUDE.md` loaded. Open a session outside the project tree. It did not.

**Rollback.** Project `CLAUDE.md` files are local to the project — if one is broken, revert it from backup and the global is unaffected.

**Output.** Project `CLAUDE.md` files in the right places, holding the right content. The "move to project" column of your classification table is fully consumed.

---

## Phase 6 — Stage the new global as `.proposed`

**Goal.** Draft the new global file as a sibling to the live one, without touching the live file. Verify everything it references actually exists.

**Inputs.** The classification table. The skills built in Phase 4. The project files placed in Phase 5.

**Steps.**

1. Write the new global to `~/.claude/CLAUDE.md.proposed`. The live file is untouched.
2. Treat the global file as a router. Its job is to:
   - State the cross-cutting rules that apply to every session.
   - Point Claude to the skills and project files that hold the depth.
   - NOT contain procedures, NOT contain reference content, NOT contain state.
3. Run a **forward-reference pre-flight check.** Every skill name and every project path mentioned in `CLAUDE.md.proposed` must resolve to an existing target. Write a small script that:
   - Extracts all skill references from the proposed file.
   - Confirms each one exists in `~/.claude/skills/`.
   - Extracts all project paths.
   - Confirms each one resolves to a real directory containing a `CLAUDE.md`.
   - Fails loudly if any reference is unresolved.
4. Hash the proposed file. Record the hash. You'll re-check it in Phase 7 to confirm nothing was modified between staging and swap.
5. Read the proposed file end-to-end one more time. Treat it as a stranger would. Does any line need context that isn't there?

**Verification gate.** The proposed file exists. The pre-flight check passes with zero unresolved references. The hash is recorded.

**Rollback.** Delete `CLAUDE.md.proposed`. The live file is untouched. No harm done.

**Output.** `~/.claude/CLAUDE.md.proposed`, a recorded hash, a clean pre-flight report.

---

## Phase 7 — Atomic swap and live verification

**Goal.** Replace the live global file with the proposed one in a single atomic operation, then verify in a fresh session that the new file does what you expect.

**Inputs.** The proposed file and its recorded hash from Phase 6.

**Steps.**

1. Take the pre-swap snapshot (see `04-backup-and-safety.md`):

   ```powershell
   Copy-Item "$HOME\.claude\CLAUDE.md" "$HOME\.claude\CLAUDE.md.pre-swap-$(Get-Date -Format yyyyMMdd-HHmmss)"
   ```

2. Re-hash `CLAUDE.md.proposed`. Confirm it matches the hash recorded at the end of Phase 6. If it differs, something modified the file between staging and now — stop and investigate before swapping.
3. Atomic swap. Use `Move-Item` (PowerShell) or `mv` (bash) — both are atomic within a single filesystem, so there's no moment where the live path is missing.

   ```powershell
   Move-Item "$HOME\.claude\CLAUDE.md.proposed" "$HOME\.claude\CLAUDE.md" -Force
   ```

   ```bash
   mv ~/.claude/CLAUDE.md.proposed ~/.claude/CLAUDE.md
   ```

4. Hash the new live file. Confirm it matches the proposed-file hash from before the swap.
5. **Open a fresh Claude Code session.** Not the one you've been working in — that one has the old file already loaded in context and will mask problems. Start a new session.
6. Run the verification prompts. Have a small list ready before the swap. Examples:
   - "What's our backup discipline before a destructive change?" — should reference the snapshot pattern from your new global.
   - "How do you handle <a procedure that's now in a skill>?" — should invoke the skill, not recite the procedure inline.
   - "What environment am I on and what shell quirks matter?" — should match your global's environment block.
7. If any verification prompt fails, you have two options: edit the live file forward (the small-fix path), or roll back to the pre-swap snapshot (the I-was-wrong path).

**Verification gate.** A fresh session loads the new global, answers verification prompts correctly, and invokes skills when expected.

**Rollback.** `Move-Item` the pre-swap snapshot back over the live file. One command. Done.

**Output.** A new live global file. A pre-swap snapshot you can keep for a week or so before deleting. Confidence that the system actually works.

---

## Two techniques worth knowing

These don't fit neatly into a single phase but they raise the quality of the work meaningfully.

### 1. The AI-roleplay pressure test

After you've drafted the proposed file but before the swap, spawn a separate Claude agent and have it roleplay your inspiration — for example, a known practitioner whose documented positions you've been drawing from. Give the roleplay agent their public writing as context, then ask it to critique your draft from that practitioner's perspective.

What this typically catches:

- Bullets that sound right but contradict a principle from your source.
- "Defensible" content that doesn't actually pass the underlying test.
- Phrasing that's too vague — the inspiration would have stated it more sharply.
- Sections that exist because you didn't have the courage to cut them.

The roleplay critique is harsher than your own re-read. Use it.

### 2. Verify AI's choices against agreed positions

Halfway through a long restructure, the AI agent helping you will start following the surface logic of its earlier recommendations and forget the qualifications you added. You said "yes to skills, but only if related runbooks group together" — three steps later, it'll be proposing one skill per runbook because the surface logic is "use skills."

Periodically do a "what did I say vs. what did you implement" pass:

1. Pull up the original ask and the qualifications you've added since.
2. Look at the current state of the proposed file and the skills.
3. List every place where the implementation drifted from the agreed position.
4. Fix the drift.

Do this at least once between Phase 4 and Phase 6. The drift is invisible until you look for it.

---

## What you have at the end of Phase 7

- A global `CLAUDE.md` that acts as a router, not a content dump.
- A populated skills directory holding procedures.
- Project-level `CLAUDE.md` files holding project-specific orientation and rules.
- A backup and a snapshot.
- Verification that the new system works in a fresh session.

You're now in maintenance mode. See `06-anti-patterns.md` for what tends to go wrong from here.
