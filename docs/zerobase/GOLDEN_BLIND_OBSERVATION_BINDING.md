# Blind Semantic Observation / Mask Binding

Status: IMPLEMENTED / OBSERVER CAPABILITY HOLD

This layer converts observer evidence into Golden Comparison feature evidence and authorized semantic masks without manual labels or Golden images.

Binding is intentionally strict. A feature becomes present and receives an authorized mask only when exactly one observer record carries the manifest semantic_role and a valid bbox. Missing, unlabeled, ambiguous, or geometry-less observations become unknown and receive no mask.

Repository audit at this milestone found deterministic SLIC region evidence and existing part-binding infrastructure, but no real runtime currently assigns Golden Comparison semantic roles such as hair/necktie/accessory on arbitrary blind images. DINO/SAM remain observer contracts/research evidence rather than semantic authority. Therefore the sealed blind cases must remain HOLD rather than being manually labelled to force a pass.

Next engineering milestone: connect a real frozen semantic observer/hypothesis runtime, then feed its untouched outputs through this binding layer and the existing hard gates.
