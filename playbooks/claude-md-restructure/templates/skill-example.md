---
# The `description` field is the most important line in a skill file.
# Claude Code uses it to decide WHEN to trigger the skill. Be explicit about
# trigger phrases and concrete situations — vague descriptions = missed triggers.
name: deploy-checklist
description: Pre-deployment verification checklist for the <PLACEHOLDER: service-name> service. Use when about to ship a release, deploying a change with database migrations, verifying CI status before going to production, or when the user says "ready to deploy", "ship it", "push to prod", or asks for a pre-deploy check. Walks through the steps in order and surfaces blockers.
---

# deploy-checklist

<!-- A skill is a procedure that loads ON DEMAND. Procedural content does NOT belong
     in CLAUDE.md — it belongs here. Each runbook should be small, verified, and
     have an attribution line so future-you knows where the source-of-truth lives. -->

## Pre-conditions
Before running this skill, confirm:
- Current branch is `main` (or the configured release branch).
- Working tree is clean (`git status` shows no uncommitted changes).
- CI is green on the latest commit (`gh run list -L 1`).
- The user has confirmed this is an intentional deploy, not exploration.

If any pre-condition fails, STOP and report which one. Do not proceed.

---

## Runbook 1: Standard deploy (no migrations)

**Use when:** the diff since last release touches only application code — no schema changes, no infra changes, no feature flags being flipped.

1. Verify the diff against the previous release tag:
   ```
   git diff <PLACEHOLDER: previous-tag>..HEAD --stat
   ```
   **Verify:** the file list matches what's expected. If anything in `infra/`, `migrations/`, or `flags/` shows up, abort this runbook and switch to Runbook 2.

2. Run the smoke test suite locally:
   ```
   <PLACEHOLDER: smoke-test-command>
   ```
   **Verify:** all tests pass. If any fail, STOP — do not deploy a red test.

3. Tag the release:
   ```
   git tag -s v<PLACEHOLDER: new-version> -m "Release v<PLACEHOLDER: new-version>"
   git push origin v<PLACEHOLDER: new-version>
   ```
   **Verify:** the tag appears on the remote.

4. Trigger the deploy workflow:
   ```
   gh workflow run deploy.yml -f tag=v<PLACEHOLDER: new-version>
   ```
   **Verify:** the workflow run starts and progresses past the build stage within 2 minutes.

5. After deploy completes, hit the health endpoint:
   ```
   curl -sf https://<PLACEHOLDER: service-host>/health
   ```
   **Verify:** returns 200 and the expected version string.

**Source:** `<PLACEHOLDER: docs/runbooks/deploy.md>` — keep this runbook in sync with that file.

---

## Runbook 2: Deploy with database migration

**Use when:** the diff touches `migrations/` or any schema-affecting file.

1. Run Runbook 1 steps 1-2 to verify the diff and tests.
2. Dry-run the migration against a snapshot of production:
   ```
   <PLACEHOLDER: migration-dry-run-command>
   ```
   **Verify:** the migration plan matches expectation. No unexpected DROPs.
3. Confirm with the user before continuing. Migrations are not auto-approved.
4. Continue with Runbook 1 steps 3-5.
5. After deploy, verify the schema change applied:
   ```
   <PLACEHOLDER: schema-check-command>
   ```
   **Verify:** the new column/table/index exists.

**Source:** `<PLACEHOLDER: docs/runbooks/deploy-with-migration.md>`.

---

## What does NOT belong in this skill
- **Architecture explanations.** Those live in `docs/architecture.md`.
- **General Claude Code behavior rules.** Those live in `~/.claude/CLAUDE.md`.
- **Project conventions** (branch naming, commit style). Those live in the project CLAUDE.md.
- **Incident response procedures.** Separate skill.
- **Anything that hasn't been verified against a real run.** If a step isn't tested, mark it `<UNVERIFIED>` so future-you knows to validate before trusting it.
