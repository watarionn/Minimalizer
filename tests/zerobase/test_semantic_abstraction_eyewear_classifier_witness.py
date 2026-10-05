import pytest
from minimalizer_zerobase.semantic_abstraction.eyewear_classifier_witness import *
def test_contract_frozen(): assert MODEL_SIZE=="small" and MIN_PRESENT_PROBABILITY==.80
def test_threshold(): assert not bind_classifier_probability(.799).present and bind_classifier_probability(.80).present
def test_region_conditioned_result_is_not_independent(): assert not independent_from_region_proposal(bind_classifier_probability(.95),used_region_proposal=True)
def test_source_head_crop_can_be_independent(): assert independent_from_region_proposal(bind_classifier_probability(.95),used_region_proposal=False)
def test_invalid_probability_fails(): 
 with pytest.raises(ValueError):bind_classifier_probability(float("nan"))
