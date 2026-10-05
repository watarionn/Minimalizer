# SA7.19 Eyewear-Specific Classifier Candidate — 2026-10-06

Status: DEVELOPMENT SEPARATION PASS / HOLDOUT REQUIRED

Candidate: mantasu/glasses-detector v1.0.x, anyglasses small classifier. MIT licensed. Weight file is approximately 122 KB. It runs in an isolated Python 3.12 environment.

Input rule: source-derived head/upper-person crop only. A Grounding-DINO proposal must not be used if the result is to count as an independent observer.

Development corpus probabilities:
Positive:
- Friend-A 0.958145
- Kaela 0.998649
- Hyakuto Kyoko 0.853832

Negative:
- AZKi 0.212098
- Fauna 0.655266
- Flare 0.492656
- Gawr Gura 0.552498
- Mumei 0.412753
- Sopia 0.052529

Positive minimum 0.853832; negative maximum 0.655266.

The development gate is now frozen at probability >= 0.80. This threshold was selected after seeing the development corpus, so these nine images cannot be used as the final generalization proof.

Medium model was also tested without changing the crop and performed worse, including Friend-A 0.161 and strong false positives on Flare/Mumei. Medium is rejected.

Next: SA7.20 must use untouched, visually labeled high-resolution holdout variants selected before scoring. GC001 remains sealed.
