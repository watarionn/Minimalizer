# No-Face-Plate structural audit: correction to prior NO FACE OVERLAY claim (2026-10-08)

**Incident and disposition:** User correctly observed that Part Occlusion Ownership v1 still looked like a big skin-colored face covering bangs. **Prior statements saying "no face overlay" were misleading. The output remains NO-GO.** This audit does not change the production or previous archived images.

## Verified root cause

The full vector study's `assemble()` places `put(owner,skin,"subject","underlay")`. That fills **the entire source subject silhouette with a single skin RGB** before drawing hair and costume. The label `data-part="subject"` does not make it semantically innocent: the part is still an opaque skin-colored face plate, visible whenever foreground hair/clothes fail to cover it.

For actual GC001 source masks and the exact previously generated SVG, the reproducible audit measured:

- Opaque subject underlay covers source face: **4,808** pixels.
- Opaque subject underlay covers source hair footprint beneath its hair layer: **14,654** pixels.
- Intersection of the separate Phase04 face and hair masks: **0**. Therefore we must **not** falsely describe the issue as source face/hair masks literally overlapping. The real fault is the unnecessary underlying skin-colored subject polygon exposed through incomplete hair color paths.
- Outcome: `NO_GO_FACE_PLATE`, `do_not_promote=true`.

Auditor: `tools/research/audit_no_face_plate.py`. Output `chatGPT及びCodex用/Minimalizer/NoFacePlate_Gate_20261008/face_plate_audit.json`, Drive folder `1-poU5N6KyNMeo4rTEcJY796gNG5WFFQ3`. Unit regression in `tests/test_audit_no_face_plate.py`. **6 relevant tests PASS.**

## Revised non-negotiable design gates

- "No separate face path" **is not equivalent** to "no face overlay". Reject any opaque, face-colored subject-wide underlay as an implicit face plate, regardless of `data-part` label.
- Do not solve the issue by adding a face-sized skin ellipse/polygon, repainting the fringe or restoring unobservable pixels under eye/nose/mouth.
- For future complete character vector scene, construct original-part-owned geometry *directly*, including hair and clothing boundaries. Figure silhouette occupancy is an evaluation mask, not permission to fill all of it with facial skin color.
- The facial area whose underlay is not source-observable must remain unresolved or fail closed until a legitimate sparse-vector/no-detail background representation is established. A deliberately transparent demonstration is **not** a final usable image either.
- Continue preserving existing PartColorOwnership, PartOcclusionOwnership and FaceParts research outputs for audit; do not silently replace them or ship to MinimalizerLocal/Public.

Next execution should replace the skin-colored figure-wide base with part-specific source-color geometry and insist on side-by-side actual image visual proof. After that separately verify true hairstyle/color integrity and Golden quality.
