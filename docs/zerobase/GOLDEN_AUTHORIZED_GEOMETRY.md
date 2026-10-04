# Authorized Geometry Fitting / Rendering

Status: IMPLEMENTED

This milestone consumes only an already-authorized G5 geometry plan plus explicitly authorized semantic masks. The fitter cannot add semantic parts, choose feature identity, change primitive count, or consume a Golden raster.

The current deterministic native fitting path converts the authorized grammar into primitive families already supported by the canonical SvgRenderer. A `vtracer` fitter label is accepted only under the same semantic/primitive contract; it does not gain semantic authority.

This is intentionally a contract-first fitting layer. Mask extraction remains upstream observer work. Missing, unauthorized, or extra masks fail closed.

Next: bind sealed blind source images to upstream semantic observation/masks, run baseline and authorized candidate with the same renderer, preserve artifacts, and evaluate G8 without changing frozen G2-G7 rules.
