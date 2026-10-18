# Lane A L02 sleeve component evidence, 2026-10-18 (Run18)

**Research only: L02 HOLD / Golden HOLD / L03 NO_GO / production NO_GO.**

Canonical baseline main `4b1f6dc65a1b166966d88fdb24be013a5a480218`. The existing exploratory sleeve proposal uses 8-connected components and a color threshold of 30 tuned on H04/H06/H08. Diagonal-only sleeve contact can therefore be accepted as if it were a four-neighbor garment attachment. That is not independent owner evidence.

Run18 local source-free audit (not production) separates 8-connected sleeve components into four-neighbor seed contact, diagonal-only contact, and isolated. It reports source RGB boundary L1 without a tuned threshold, source partial alpha, candidate seed losses and non-class32 additions. A distinct postscore path partitions frozen candidate pixels by human-known outerwear, arm, hair, underlayer, other known negative and unknown; unknown/occluded unknown never become negatives. It neither produces a candidate mask nor promotes any owner.

Local Python 3.13.5 / NumPy 2.3.5 / OpenCV 4.13.0 synthetic tests: **190/190 PASS** (Run17 160 + Run18 30); ZIP re-extraction 190/190 PASS and 24-file SHA manifest match. These are **not** new signed-original inference, independent holdout, or CI evidence. Existing H04 arm FP 236px/hair FP 8px, H06 outerwear misses 2523px and H08 misses 4254px remain unresolved.

Source-free Run18 code/tests and SHA package are held separately pending safe GitHub integration and cloud read-after-write. Never commit user images, NPZ, private coordinates or masks. Do not change Lane B or Golden.

Next: review source-only code/test diff, run GitHub CI, validate signed frozen H04/H06/H08 and untouched-character predictions against independently authenticated pins, score human labels only after inference, preserve private evidence in the existing Drive folder, and retain HOLD until true semantic/Golden/iPhone acceptance.
