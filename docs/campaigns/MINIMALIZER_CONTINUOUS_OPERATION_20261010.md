# Minimalizer Continuous Campaign Operator Contract (2026-10-10)

**User problem:** The repeated command `次の工程を完了させて` was required far too often. A campaign is a sustained **goal**, not one assistant turn per tiny experiment.

## Mode

**Continuous campaign goal:** C08, with original visual and release gates intact. Read latest GitHub main, canonical `CMP-20261009-SA1060-TO-PRODUCTION.json`, latest handoff and Issue #321 on every restart. **Once the user says to proceed, treat it as permission for multiple safe engineering iterations and independent branches until an actual dependency or runtime limit.** Do not finish solely because one experiment, test, PR, or substage concluded.

For each execution, repeat as far as the available run permits:

1. **Reconcile source of truth:** Latest main/PRs, tracker and private Drive lineage. Avoid stale handoff.
2. **Select a batch of executable work, not merely one check box:** current C02b3 semantic owner/arm-hair-clothing diagnosis and separately executable C03 original Stage8 source-ring research; prepare C04 Approved-18/78 and human-Golden review materials without forging the actual review.
3. **Goal → Produce → Verify → Review → Ship → Preserve → Next:** For each cohesive engineering change, source-lock, run focused + independent tests, compare rendered images where appropriate, publish sanitized code+quantitative evidence to GitHub PR and private source/boards to approved Drive, merge only when defensible and confirm readback.
4. **Automatically continue** to the next unblocked subtask in the *same* execution. Do not ask for user instruction at each microstage. If a candidate fails, reject it with metrics, investigate a different hypothesis or parallel runnable item, not a repetitive HOLD report.
5. **Checkpoint on interruption:** Write a compact GitHub handoff that states actual merge SHAs, human/production holds, next executable command(s), private Drive verified links, missing saves, and any failures. The next scheduled run resumes there. A finished artifact does not imply continuous human-like background thinking.

## Only legitimate stop / user-input conditions

- **Authentic human visual Golden signoff** is required: the assistant can generate signed comparisons and propose a recommendation, not write `human_approved=true` on behalf of the user.
- **Source Stage8 budget** must be genuinely solved or an explicit *versioned* policy change approved; compact rendered-SVG cap is not a substitute for immutable original Stage8 cap.
- **Production cutover** requires the formal C05/C06 release gates, known-good rollback verification, and owner authorization; the assistant must not deploy to bypass HOLD.
- **iPhone real-device acceptance** is not inventable from desktop Chromium results. Until confirmed, C07/C08 cannot be called complete.
- Runtime/tool/quota/security/environment hard failure with no safe independent alternative; document precise blocker. Do not circumvent a refusal or repeatedly retry a protected action.

## Explicit failure handling

- `C02b1` pose-only attempt: original right wrist confidence below 0.60; do **not** silently lower threshold.
- `C02b2` color-only attempt: owner fragmentation and source-edge deletion; do **not** interpret 533 same-RGB pixels as a complete semantic truth.
- C02b2 private artifact upload had partial expiry; do **not** mark archive complete until every file is re-uploaded and read back.
- Source and signed artifacts immutable, default eyes/nose/mouth/brows OFF, no visible generated content/raster SVG embedding.
- Use GitHub/Drive official tools first. RDC only if artifact cannot be retrieved or computation cannot be performed by official paths, with minimal calls.
- Numeric synthetic PASS does **not** replace real Chrome visual or human signoff; cache and SHA provenance required.

## Communication policy

- **Do not request** `次の工程を完了させて` after each experiment, patch, PR or microstage.
- Report consolidated **durable milestones**, a true external approval question, or a precise unavoidable blocker. Avoid asking whether to continue when previous C08 authorization is already explicit.
- For a long interactive execution, give progress about every 20 seconds, then continue working instead of ending at a milestone.
- The scheduled ChatGPT automation is a **periodic re-entry**, currently at most hourly. It is not equivalent to an uninterrupted always-on code process. Do not imply constant work between runs.
- No new GitHub Actions workflow: respect repo `AGENTS.md` prohibition. If a persistent process is later required, design it independently with an explicit deployment/operational decision.

## Campaign snapshot

As of initial adoption: **C01 COMPLETE; C02 IN_PROGRESS (next C02b3), C03 and C04 HOLD, C05–C08 BLOCKED; production unchanged and release not authorized.** Reference Issue #321 and immutable campaign tracker for evolving truth. This snapshot is not a status promotion.

**Definition of outcome:** The user does not have to manually be the scheduler. The engineering system moves through safe stages, accurately preserves rejected attempts, and asks for human action only where it is truly indispensable.
