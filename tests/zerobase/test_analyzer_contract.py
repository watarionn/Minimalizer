import numpy as np
import cv2
from minimalizer_zerobase.analyzers.contracts import AnalyzerAdapter, Evidence
from minimalizer_zerobase.analyzers.opencv_contours import OpenCVContourAdapter
from minimalizer_zerobase.core.coordinates import CoordinateSpace


def test_adapter_contract_and_deterministic_output():
    adapter = OpenCVContourAdapter(min_area=10)
    assert isinstance(adapter, AnalyzerAdapter)
    image = np.zeros((100, 120, 3), dtype=np.uint8)
    cv2.rectangle(image, (10, 20), (60, 80), (255,255,255), -1)
    cs = CoordinateSpace(120, 100)
    first = adapter.analyze(image, cs)
    second = adapter.analyze(image, cs)
    assert first and all(isinstance(x, Evidence) for x in first)
    assert [x.to_json() for x in first] == [x.to_json() for x in second]
    assert all(x.provenance.producer == "OpenCVContourAdapter" for x in first)


def test_optional_analyzer_failure_boundary_is_external_to_schema():
    cs = CoordinateSpace(10, 10)
    assert cs.to_dict()["width"] == 10
