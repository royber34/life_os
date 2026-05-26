# The CLAUDE.md Restructure Playbook

A methodology for shrinking a bloated Claude Code global memory file from a sprawling monolith down to a routed, fast, accurate system — without losing any operational content.

---

## The problem

If you've been using Claude Code for a few months, your global `~/.claude/CLAUDE.md` may have grown into a 500+ line document containing infrastructure docs, runbooks, agent architectures, bug logs, active task lists, an update history, conventions across every project you touch, and probably a few duplicated copies of "how to work with me" rules. If so, Claude Code performance is probably degrading on you and you might not have connected the dots.

Three things are happening simultaneously:

1. **Context rot is real and measured.** [Chroma Research (2025)](https://www.trychroma.com/research/context-rot) tested 18 frontier models. Claude Sonnet 4 and Opus 4 exhibit the *largest* gap between focused and full-prompt performance — they're more sensitive to irrelevant context than competitors, not less.
2. **Anthropic's own engineering team has named this anti-pattern.** The official best-practices guide warns: *"Bloated CLAUDE.md files cause Claude to ignore your actual instructions"* and calls out "the over-specified CLAUDE.md" as a common failure mode. Their documented target: **under 200 lines per CLAUDE.md file**.
3. **Boris Cherny's own published CLAUDE.md** (he created Claude Code) is ~100 lines / ~2,500 tokens. If yours is 5–10× larger, you're outside the documented best practice from the person who built the system.

The cost compounds: combined with MCP tool schemas (25–50k tokens for a typical setup), a 10k-token global CLAUDE.md consumes ~30% of a 200k context window before any actual work begins.

This playbook documents how to fix it — safely, without losing operational content, with verification at every step.

---

## Who this is useful for

You'll get value from this if any of these are true:

- Your global `~/.claude/CLAUDE.md` is more than ~300 lines.
- You've added content to it incrementally over months and never trimmed.
- Your Claude Code sessions feel slower, less accurate, or more likely to ignore specific rules you've set.
- You have multiple projects with their own CLAUDE.md files and aren't sure how they should relate.
- You have procedural runbooks (multi-step recipes) embedded in your CLAUDE.md that load on every session whether relevant or not.
- You want to fix this but are worried about losing the operational content you've accumulated.

This is **not** for you if:

- Your CLAUDE.md is already lean (~100 lines or less).
- You've only used Claude Code on one or two projects.
- You're looking for a one-size-fits-all template to copy. This is a *methodology*, not a template — the final file shape depends on your work.

---

## The eight principles

Every decision in the restructure traces back to one of these. They generalize across any CLAUDE.md setup:

1. **The "would removing this cause Claude to make mistakes?" test.** Apply it to every line. If no, cut it. (Boris Cherny's own articulated test.)
2. **State doesn't belong in CLAUDE.md.** Status trackers, task lists, changelogs, last-modified dates — out. They go in dedicated files or git history.
3. **Procedures don't belong in CLAUDE.md.** Multi-step recipes (five-plus steps, decision branches, verification points) become skills, which load on demand. CLAUDE.md keeps a one-line trigger.
4. **Reference content doesn't belong in CLAUDE.md.** Architecture documentation, API references, command cheatsheets — separate `.md` files or your project README. CLAUDE.md points at them.
5. **The global file is a router, not a content dump.** It orients new sessions and routes them to where the depth lives. Project-scoped CLAUDE.md files do the heavy lifting when you `cd` into their territory.
6. **Failure-log discipline.** When Claude makes a mistake you have to correct, codify it as a one-liner in the relevant CLAUDE.md immediately. Without this, files calcify and you'll be doing another restructure in 18 months.
7. **Hierarchy is the auto-loader's job, not the file's.** Claude Code walks up the directory tree from your cwd, loading every CLAUDE.md it finds. Global handles cross-project preferences; project files handle project-specific rules; nested files handle sub-component scope. Files don't need to explain this — Claude Code does.
8. **Skills > CLAUDE.md bullets for anything procedural.** Skills cost zero tokens until invoked. Putting a multi-step procedure inline in CLAUDE.md means every session pays for it, whether relevant or not.

---

## The methodology — seven phases

Don't skip the early ones. They're the reason the rest is safe.

### Phase 1 — Research pass (before you touch anything)

Spend an hour reading what authoritative sources actually say. Spawn parallel research agents or read manually:

- **Anthropic's official docs** — [best practices](https://code.claude.com/docs/en/best-practices), [memory](https://code.claude.com/docs/en/memory)
- **Boris Cherny's own CLAUDE.md** (via Charlie Hills' anatomy diagram on Substack) — what the creator of Claude Code actually uses
- **Context rot research** — [Chroma Research](https://www.trychroma.com/research/context-rot), [Liu et al. "Lost in the Middle"](https://aclanthology.org/2024.tacl-1.9/), [Anthropic engineering blog on context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- **Real-world CLAUDE.md exemplars** — Trail of Bits, Ory dockertest, Serial-Studio, PyTorch tutorials, Sourcegraph CodeScaleBench, the [josix/awesome-claude-md](https://github.com/josix/awesome-claude-md) curation

You're not looking for opinions. You're looking for explicit rules from authoritative sources you can point at when you cut content. This is the difference between confident cuts and second-guessing.

### Phase 2 — Audit your existing setup

Before changing anything, inventory:

- Your global `~/.claude/CLAUDE.md` — line count, byte count, section breakdown
- Every project-level CLAUDE.md across your filesystem (glob `**/CLAUDE.md`)
- Every auto-memory MEMORY.md under `~/.claude/projects/`
- Every CLAUDE.local.md anywhere
- What's already in your skills directory at `~/.claude/skills/`

For each CLAUDE.md, classify every section into:

- **KEEP** — cross-cutting rules Claude needs every session
- **MOVE** — project-specific content that belongs in a project file or a skill
- **DELETE** — state, changelogs, redundant lists, research notes that should not be in any CLAUDE.md

Identify duplicates between files. Look specifically for the "triple-duplicate" pattern — the same content in nested directories where multiple files load simultaneously when you `cd` deep into a project. This is a common hidden bloat source.

### Phase 3 — Backup with hash verification

Before any file change, take a hash-verified backup. Mirror the original paths in the backup directory and include a manifest with restore instructions.

```
~/.claude/backups/YYYY-MM-DD-pre-restructure/
├── MANIFEST.md                   ← Index + restore instructions
├── restore.ps1 (or restore.sh)   ← Idempotent restore script with SHA256 verification
└── files/
    └── <mirrored original path>/CLAUDE.md
```

Every backed-up file gets its SHA256 captured at backup time. The restore script verifies hashes before overwriting and prompts if the target has changed since backup. The whole backup is restorable with one command.

See `templates/restore.ps1` (or `restore.sh`) for a working implementation.

### Phase 4 — Build skills for procedures

For every multi-step procedure currently embedded in any CLAUDE.md, create a skill at `~/.claude/skills/<skill-name>/SKILL.md`. Each skill needs:

- A frontmatter `description` that names the trigger phrases reliably (the description is how Claude decides to invoke; bad descriptions = skill never fires)
- Step-by-step instructions with explicit verification at each step
- A "Source: <how I know this works>" line per procedure — distinguishes battle-tested from theoretical
- An explicit list of what does NOT belong in the skill (prevents scope creep)

See `templates/skill-SKILL.md` for the structure.

### Phase 5 — Move project content to project CLAUDE.mds

For each major project with substantial infrastructure context, create or update a project-level CLAUDE.md. These auto-load only when you `cd` into the project — they don't bloat unrelated sessions.

The pattern:

- **Project-level CLAUDE.md** = orientation + project-specific rules + cross-reference table pointing to deeper docs
- **ARCHITECTURE.md / README.md / docs/** in the project = the deep reference content
- **STATUS.md / PLANS.md** alongside = frequently-changing state (don't put this in CLAUDE.md)

If a project has substantial infrastructure docs (more than ~100 lines), consider creating a dedicated infra repo (`~/<your-infra-repo>/`) and git-initializing it so update history lives in commits instead of inside CLAUDE.md.

### Phase 6 — Stage the new global as `.proposed`

Don't swap the live file directly. Write your slim new global to `~/.claude/CLAUDE.md.proposed`. Verify:

- Every forward reference (skill name, project path) resolves to an existing target
- Section structure matches what you intended
- File parses cleanly
- Live file SHA256 unchanged during this step

Show yourself the diff. Read the proposed file fresh, end to end. Edit before swapping if anything's off. This is your last review point before the live change.

### Phase 7 — Atomic swap + live verification in a fresh session

The swap:

1. Take an extra safety snapshot: `Copy-Item live live.pre-swap-<timestamp>`
2. Move proposed to live: `Move-Item proposed live -Force`
3. Verify new live SHA256 matches what proposed was pre-swap
4. Confirm `.proposed` no longer exists

Then — and this is the verification you can't skip — **open a brand new Claude Code session** and run real prompts:

- *"What do you know about how I work?"* — should reflect the slim global accurately
- *"Help me push this code"* — should ask for explicit approval (if that's one of your hard rules)
- *"Draft a client follow-up email"* — should mention invoking your recipient-POV review skill
- `cd` into an unmodified project and ask about it — should load that project's CLAUDE.md correctly

If anything misbehaves, rollback is one command (the pre-swap snapshot from step 1). The Phase 3 master backup is the deeper fallback.

---

## Two techniques worth knowing

Less standard but proved high-leverage during the restructure:

### The AI-roleplay pressure test

After you have a draft, spawn a separate Claude agent and have it roleplay your inspiration (Boris Cherny, with his documented public positions as constraints — his published CLAUDE.md, his Latent Space podcast statements, the Anthropic best-practices guide he co-authored). Have it review your draft.

In practice this surfaced:

- Items that should have been cut but I'd kept
- Items I'd kept against the inspiration's general guidance that *should* stay (because they applied differently to the specific use case)
- One critical missing piece (the failure-log discipline rule) that came from the reviewer agent's read of Boris's own pattern

Cheaper than discovering these in production after the swap.

### Verify the AI's choices against what was actually agreed

Mid-restructure, an AI agent will follow the surface logic of recommendations and forget the disagreements that qualified them. At some point during the work, do a pass specifically asking the AI: *"What did I say in this conversation vs. what did I implement?"*

In one case mid-restructure, I had told the AI *"I disagree with merging these two bullets, slightly"* — then the AI merged them anyway in the next draft, because the surface logic was tempting. The drift check caught it.

This generalizes well beyond CLAUDE.md restructures. Any long AI-assisted work benefits from the explicit "what did I say vs. what did you do" pass.

---

## Where the file ends up — example result

| Metric | Before | After |
|---|---|---|
| Lines in global CLAUDE.md | ~540 | ~62 |
| Bytes | ~36,000 | ~6,500 |
| Tokens | ~10,000 | ~1,500 |
| Context window consumed by global at session start (200k window) | ~5% | ~0.75% |
| Sections | 14+ (sprawling) | 8 (focused) |
| Procedural content | Multiple embedded runbooks (~150 lines) | 0 lines — all moved to skills |
| State (task lists, changelogs) | ~100 lines | 0 lines — moved to dedicated files or git history |

| Where content moved | What went there |
|---|---|
| `~/<your-infra-repo>/CLAUDE.md` (new project-scoped repo) | Infrastructure architecture, known bugs, system configurations, deployment paths |
| `~/<each-project>/CLAUDE.md` | Project-specific conventions, stakeholders, file routing |
| `~/.claude/skills/<name>/SKILL.md` | Multi-step runbooks, recipient-review protocols, setup procedures |
| `~/.claude/projects/<project>/memory/MEMORY.md` (auto-memory) | Learned patterns Claude captured automatically |
| Git history | Update logs, dated changelogs |
| Deleted | Research notes, redundant lists, content already auto-discovered |

The slim global, at the high level, contains:

- Identity and posture (who the user is, how to engage with them)
- Working principles (the cross-cutting "how I work" rules)
- Environment (OS, shell, model preferences)
- Hard rules (cross-project, no-exceptions)
- A quality bar (what passes before output is surfaced)
- A few generalizable mistakes to avoid (the failure log applied at global scope)
- A routing section pointing at where project-specific context lives
- Long-form personal record locations (journals, auto-memory)

---

## What's in this repo

```
.
├── README.md                    ← This file
├── docs/
│   ├── 01-the-bloat-problem.md  ← Context rot, token math, citations
│   ├── 02-research-pass.md      ← How to do the research first
│   ├── 03-audit-your-setup.md   ← Detailed audit methodology
│   ├── 04-backup-and-safety.md  ← The pre-work that lets you proceed
│   ├── 05-phased-execution.md   ← Phase-by-phase walkthrough
│   └── 06-anti-patterns.md      ← Failures to expect and avoid
├── templates/
│   ├── global-CLAUDE.md         ← Anonymized template global
│   ├── project-CLAUDE.md        ← Project-scope pattern
│   ├── skill-SKILL.md           ← Skill template, description-first
│   ├── restore.ps1              ← Windows restore script
│   └── restore.sh               ← Unix restore script
└── examples/
    └── before-after.md          ← Anonymized before/after with numbers
```

---

## What this is NOT

- **Not a framework.** Don't call it a framework. It's a playbook for one specific kind of cleanup.
- **Not a one-size-fits-all template.** The methodology generalizes; the final file shape depends on your work.
- **Not novel research.** The principles are documented elsewhere — what's new is the end-to-end methodology and the safety discipline.
- **Not for everyone.** If your CLAUDE.md hasn't grown past ~150 lines, you don't need this.

---

## Sources

All sources cited throughout are public.

- [Anthropic — Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- [Anthropic — How Claude remembers your project (memory docs)](https://code.claude.com/docs/en/memory)
- [Anthropic engineering blog — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Boris Cherny on the Latent Space podcast](https://www.latent.space/p/claude-code)
- [Charlie Hills — Anatomy of Boris Cherny's CLAUDE.md](https://charliehills.substack.com/) (anatomy diagram)
- [Chroma Research — Context Rot (2025)](https://www.trychroma.com/research/context-rot)
- [Liu et al. — Lost in the Middle (TACL 2024)](https://aclanthology.org/2024.tacl-1.9/)
- [HumanLayer — Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [josix/awesome-claude-md](https://github.com/josix/awesome-claude-md) (curated examples)
- Real-world CLAUDE.md exemplars: [Trail of Bits](https://github.com/trailofbits/claude-code-config), [Ory dockertest](https://github.com/ory/dockertest), [Serial-Studio](https://github.com/Serial-Studio/Serial-Studio), [PyTorch tutorials](https://github.com/pytorch/tutorials), [Sourcegraph CodeScaleBench](https://github.com/sourcegraph/CodeScaleBench), [quayside](https://github.com/quayside-app/quayside)

---

## Contributing

If you run this methodology on your own setup, the most useful contribution is a PR with your anonymized before/after metrics — lines, bytes, tokens, what moved where. More datapoints = better pattern-matching for everyone.

---

## License

MIT.
