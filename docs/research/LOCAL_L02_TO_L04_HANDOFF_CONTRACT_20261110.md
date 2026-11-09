# L02 to L04 handoff contract

The A-to-B handoff is a read-only, source-free audit boundary. It accepts no
candidate until H04, H06, and H08 each provide the same signed source, Stage8
JSON, and expanded SVG triple with matching SHA-256 values.

`tools/research/audit_l02_to_l04_handoff.py` additionally requires source-only
inference, `unknown_pixels_treated_as_negative=false`, exact source owner and
silhouette flags, a passing Chromium alpha replay, and a formal L04 budget
PASS. Missing H04, a mismatched triple, or either budget/formal HOLD leaves the
handoff ineligible. It does not alter B's cap policy or promote a candidate.

The audit is deliberately separate from Phase4 and Phase5. Phase4 must have a
candidate-specific independent receipt first; the exact candidate must then
pass the pinned Phase5 structural replay; only then may the resulting Stage8
triple be evaluated by this L04 boundary. Golden, release, rollback, and
production remain separate gates.
