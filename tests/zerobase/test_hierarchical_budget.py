import pytest
from minimalizer_zerobase.production.macro_mass import build_macro_mass_plan
from minimalizer_zerobase.production.hierarchical_budget import allocate_hierarchical_macro_budget,HierarchicalBudgetError

def r(b): return {"authorized":True,"bbox":b,"confidence":.9}
def full():
 return build_macro_mass_plan({"head":r([40,5,20,20]),"hair":r([35,2,30,28]),"torso":r([35,25,30,35]),"left_arm":r([20,27,15,30]),"right_arm":r([65,27,15,30]),"lower_body":r([38,60,24,35]),"accessory":r([47,30,6,18])})
def test_core_before_identity_and_no_duplicate_budget_spam():
 b=allocate_hierarchical_macro_budget(full(),12); a={x.role:x.primitives for x in b.allocations}
 assert all(a[x]>=1 for x in ("head","torso","lower_body"))
 assert a["hair"]<=2
 assert sum(a.values())<=12
 assert a["left_arm"]==1 and a["right_arm"]==1 and a["accessory"]==1
def test_fails_without_readable_core():
 p=build_macro_mass_plan({"head":r([1,1,2,2]),"torso":r([1,3,2,3])})
 with pytest.raises(HierarchicalBudgetError): allocate_hierarchical_macro_budget(p,12)
