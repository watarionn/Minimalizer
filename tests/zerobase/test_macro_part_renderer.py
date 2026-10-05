import numpy as np
from minimalizer_zerobase.production.macro_part_renderer import render_macro_parts_svg
def test_renders_distinct_readable_macro_parts():
 rgb=np.full((100,60,3),255,np.uint8); masks={}
 for k,box,c in [("head",(20,5,40,25),(240,180,140)),("hair",(15,2,45,28),(220,80,20)),("torso",(17,25,43,60),(30,50,90)),("left_arm",(7,28,17,58),(30,50,90)),("right_arm",(43,28,53,58),(30,50,90)),("lower_body",(18,60,42,95),(40,45,70))]:
  x0,y0,x1,y1=box;m=np.zeros((100,60),bool);m[y0:y1,x0:x1]=1;masks[k]=m;rgb[m]=c
 svg=render_macro_parts_svg(rgb,masks,{k:1 for k in masks})
 assert "<ellipse" in svg and svg.count("<polygon")>=3 and svg.count("<rect")>=2
 assert "#dc5014" in svg
