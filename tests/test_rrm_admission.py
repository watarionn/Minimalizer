"""Minimalizer API RRM gate tests; no model imports or GPU work."""
from contextlib import contextmanager
from unittest.mock import patch
import os
import unittest

from local_worker.rrm_admission import (
    RRMAdmissionDenied,
    compute_slot,
)


class FakeUnavailable(Exception):
    def __init__(self, reason):
        self.reason = reason


class RRMAdmissionTests(unittest.TestCase):
    def test_off_is_backwards_compatible(self):
        with patch.dict(os.environ, {"MINIMALIZER_RRM_MODE": "off"}):
            with patch("local_worker.rrm_admission._guard_factory",
                       side_effect=AssertionError("must not import RLO")):
                with compute_slot("v2"):
                    pass

    def test_enforced_lease_surrounds_compute(self):
        order = []

        @contextmanager
        def fake_hold(project, label, kind):
            self.assertEqual((project, label, kind),
                             ("minimalizer", "local-worker:zerobase2", "cpu"))
            order.append("acquire")
            try:
                yield "ticket"
            finally:
                order.append("release")

        with patch.dict(os.environ, {"MINIMALIZER_RRM_MODE": "enforce"}):
            with patch("local_worker.rrm_admission._guard_factory",
                       return_value=(FakeUnavailable, fake_hold)):
                with compute_slot("zerobase2"):
                    order.append("compute")
        self.assertEqual(order, ["acquire", "compute", "release"])

    def test_busy_is_rejected_without_compute(self):
        @contextmanager
        def busy(*args, **kwargs):
            raise FakeUnavailable("heavy_slot_busy")
            yield

        with patch.dict(os.environ, {"MINIMALIZER_RRM_MODE": "enforce"}):
            with patch("local_worker.rrm_admission._guard_factory",
                       return_value=(FakeUnavailable, busy)):
                with self.assertRaises(RRMAdmissionDenied) as ctx:
                    with compute_slot("v2"):
                        self.fail("computation should not run")
        self.assertEqual(ctx.exception.reason, "heavy_slot_busy")

    def test_invalid_mode_fails_closed(self):
        with patch.dict(os.environ, {"MINIMALIZER_RRM_MODE": "unexpected"}):
            with self.assertRaises(RRMAdmissionDenied):
                with compute_slot("v2"):
                    self.fail("must not run")

    def test_exception_from_computation_is_not_converted(self):
        @contextmanager
        def fake_hold(*args, **kwargs):
            yield

        with patch.dict(os.environ, {"MINIMALIZER_RRM_MODE": "enforce"}):
            with patch("local_worker.rrm_admission._guard_factory",
                       return_value=(FakeUnavailable, fake_hold)):
                with self.assertRaisesRegex(ValueError, "quality-gate"):
                    with compute_slot("v2"):
                        raise ValueError("quality-gate")


if __name__ == "__main__":
    unittest.main()
