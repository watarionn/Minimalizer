import pytest
from minimalizer_zerobase.production.macro_mass import build_macro_mass_plan,MacroMassPlanError

def row(bbox,confidence=.9):
    return {"authorized":True,"bbox":bbox,"confidence":confidence,"provenance":"synthetic"}

def test_builds_structural_parentage_without_case_specific_semantics():
    p=build_macro_mass_plan({"head":row([40,10,20,20]),"hair":row([35,5,30,30]),"torso":row([35,30,30,35]),"left_arm":row([20,32,15,30]),"right_arm":row([65,32,15,30]),"lower_body":row([38,65,24,30])})
    roles=[m.role for m in p.masses]
    assert roles==["head","hair","torso","left_arm","right_arm","lower_body"]
    assert next(m for m in p.masses if m.role=="hair").parent_id=="mass:head"
    assert next(m for m in p.masses if m.role=="lower_body").parent_id=="mass:torso"

def test_unknown_observer_role_cannot_directly_become_mass():
    with pytest.raises(MacroMassPlanError):
        build_macro_mass_plan({"face_skin":row([1,1,2,2])})
