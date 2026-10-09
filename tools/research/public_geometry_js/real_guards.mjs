// Candidate-only gate: no silently discarded islands, holes, or source pixels.
// Never grants production deployment, only preliminary per-role eligibility.
export function wholeSignedRoleGate(part, paper) {
  if (!part || !paper) throw new Error("missing source role evidence");
  for (const name of ["components","maskHoleCount","signedPixels","componentPixels"]) {
    if (!Number.isSafeInteger(part[name]) || part[name] < 0) throw new Error("invalid signed metric: "+name);
  }
  if (!/^[a-f0-9]{64}$/i.test(part.mask_sha256 || "")) throw new Error("unsigned original mask");
  if (part.signedPixels < 1 || part.componentPixels > part.signedPixels) throw new Error("invalid signed pixels");
  const complete = part.components === 1 && part.maskHoleCount === 0 &&
    part.componentPixels === part.signedPixels;
  const faithful = paper.accepted === true && paper.addedPixels === 0 &&
    paper.missingPixels === 0 && paper.protectedPreserved === true;
  const reason = !complete ? "INCOMPLETE_TOPOLOGY" :
    !faithful ? "PAPER_SOURCE_MASK_MISMATCH" : "PRELIMINARY_ONLY";
  return Object.freeze({complete, faithful, accepted: complete && faithful,
    reason, productionEligible: false});
}
