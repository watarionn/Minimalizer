# Structural Guidance Track - Checkpoint SG-1 Production Closure

Date: 2026-09-20
Status: CLOSED

## Scope
SG-1 covers the first production integration of structural guidance into Minimalizer 2.0:
- RTMLib structural guidance
- DeepLSD line guidance
- pose-aware line gate v2
- Region Merge integration
- exact-binding 18 and Approved-78 validation
- production deployment verification

## Fixed candidate
- pose-aware line gate floor: 0.20
- pose weight: 0.06
- line strength: 0.35

## Validation
- exact-binding 18 invariant failures: 0/18
- Approved-78 invariant failures: 0/78
- integration tests after latest-main rebase: 57/57 passed
- GitHub Actions PR CI #104: success
- full-suite audit before merge: 563 passed, 2 pre-existing missing-fixture failures (tests/assets/false_face_phase85.png)

## Delivery
- PR #33: V2: integrate pose and line guidance
- merged to main
- merge commit: 34230c9f916395d5d389f04a0de8d30fc2235c93
- Railway production service: minimalizer-web
- production deployment: d06e7e6f-4560-4ee9-a3b4-669c7101d571
- deployment status: SUCCESS
- deployed commit: 34230c9f916395d5d389f04a0de8d30fc2235c93

## Production smoke
- GET /health: 200 OK
- GET /api/v2/info: 200 OK
- POST /api/v2/minimalize with Approved-78 input: 200 OK
- response content type: image/png
- PNG signature verified
- sample response size: 4501 bytes

## Closure
Checkpoint SG-1 Production Closure is complete.
Further structural-guidance quality work belongs to SG-2 and should be treated as a separate checkpoint/workstream.
