import pytest
from minimalizer_zerobase.semantic_abstraction.eyewear_hires_corpus import *
H="a"*64
def test_freeze_requires_visual_hires_basis_and_both_roles():
 r=freeze_hires_corpus((HiresCorpusEntry("p",H,"positive","manual_visual_hires"),HiresCorpusEntry("n","b"*64,"negative","manual_visual_hires")))
 assert len(r["corpus_sha256"])==64 and r["version"]=="sa7.16-v1"
def test_order_invariant():
 a=HiresCorpusEntry("a",H,"positive","manual_visual_hires");b=HiresCorpusEntry("b","b"*64,"negative","manual_visual_hires")
 assert freeze_hires_corpus((a,b))["corpus_sha256"]==freeze_hires_corpus((b,a))["corpus_sha256"]
def test_rejects_unverified_label():
 with pytest.raises(ValueError):freeze_hires_corpus((HiresCorpusEntry("p",H,"positive","thumbnail_guess"),HiresCorpusEntry("n","b"*64,"negative","manual_visual_hires")))
