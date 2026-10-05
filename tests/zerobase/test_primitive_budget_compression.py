def test_redundant_major_color_paint_layer_removed():
 src=open("minimalizer_zerobase/production/graph_macro_renderer.py",encoding="utf-8").read()
 assert "for mass,mrgb in major_color_masses" not in src
 assert "global_mass_regions" in src and "garment_panels" in src
