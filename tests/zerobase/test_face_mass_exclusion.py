def test_renderer_excludes_head_from_internal_mass_recomposition():
 src=open("minimalizer_zerobase/production/graph_macro_renderer.py",encoding="utf-8").read()
 line=next(x for x in src.splitlines() if "global_parts=" in x)
 assert '"head"' not in line
 line=next(x for x in src.splitlines() if 'for role in ("lower_body","torso","major_clothing"' in x)
 assert '"head"' not in line
