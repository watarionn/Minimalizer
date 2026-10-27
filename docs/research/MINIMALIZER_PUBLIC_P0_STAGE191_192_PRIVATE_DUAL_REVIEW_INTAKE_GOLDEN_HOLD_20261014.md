# MinimalizerPublic P0: Stages191–192 private dual-review intake (source-free status)

Date: 2026-10-14 JST
Scope: research-only on the existing PR #393 Draft branch. Public site, Local Minimalizer, and Stage135 preview are not changed.

## Review intake

- Reviewer A reportedly used iPhone, reviewer B reportedly used PC. Each submitted two private, untrusted original-frame draft JSON files for GC001 and Raden, 340x340. Different device platforms are acceptable because source pins, format, fullframe RLE lengths, classes, and original alpha eligibility are verified independently.
- All four inputs have passed structural / original-source pin validation against private owner-side originals; no source art, individual label arrays, image previews, A/B drafts, original-source RGBA, file credentials, email addresses, or reviewer identities are stored in this repository.
- Private, owner-only A and B submission copies are archived separately under the established `chatGPT及びCodex用 / MinimalizerPublic / StructuralRecovery_P0_20261010` hierarchy. A separate owner-only restricted folder holds the full comparison and visual adjudication package. Do not share it with either reviewer until independent review is complete and confidentiality rules permit.

## Coarse comparison only, no Golden

All figures below refer only to source-original fully opaque pixels; 115,152 per case. Comparisons are proposals, never certified ground truth.

| Case | A coverage | B coverage | Agreement of all source opaque | Untrusted class disputes | At least one abstention | Manual adjudication needed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GC001 | 99.14% | 99.04% | 93.86% (108,080 px) | 5,055 px | 2,017 px | 7,072 px |
| Raden | 99.81% | 99.90% | 80.30% (92,462 px) | 22,371 px | 319 px | 22,690 px |

- Among source pixels both review submissions explicitly classify as character parts rather than background, agreement is 93.19% for GC001 and 69.44% for Raden. Do not conflate these rates with classification accuracy.
- Raden's largest taxonomy disagreement is garment vs sleeve; GC001 has a smaller but meaningful garment/accessory distinction. Both require human source inspection, not majority vote, class-relabel heuristics, AI image generation, or synthetic ground-truth promotion.
- Source RGBA and both label arrays remain unchanged. Any reviewer corrections must be submitted as new versions, preserving originals.

## Gate status and follow-up

- Four submitted files: received and structurally accepted (not semantic certification).
- Authenticated two distinct human identities and genuine independent work: **not proven by software**; confirm out-of-band with the operator.
- Fully classified every source opaque pixel: **not yet**; A and B each have residual unreviewed source-opaque pixels.
- Manual dispute adjudication: **pending**.
- Historical Stage8 fullbody vertex limits, physical iPhone Safari acceptance, real rollback rehearsal: **still unresolved**.
- Golden: **HOLD**. PR #393: **Draft** and unmerged. Production release authority: **false**.

Next: manually adjudicate all disputed / abstained pixels using private original-art overlays, document class definitions for sleeve/garment/accessory/neckwear, collect corrected versioned labels if needed, and rerun private original-source audits before any Golden or deployment decision.
