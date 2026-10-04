from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any

VOLATILE={"generated_at","elapsed_ms","runtime_ms","path","source_path","output_path"}

def scrub(v:Any)->Any:
    if isinstance(v,dict): return {k:scrub(x) for k,x in sorted(v.items()) if k not in VOLATILE}
    if isinstance(v,list): return [scrub(x) for x in v]
    return v

def first_diff(a:Any,b:Any,path="$"):
    if type(a)!=type(b): return {"path":path,"old":a,"new":b,"reason":"type"}
    if isinstance(a,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:return {"path":f"{path}.{k}","old":a.get(k,"<missing>"),"new":b.get(k,"<missing>"),"reason":"key"}
            d=first_diff(a[k],b[k],f"{path}.{k}")
            if d:return d
        return None
    if isinstance(a,list):
        if len(a)!=len(b):return {"path":path,"old_len":len(a),"new_len":len(b),"reason":"length"}
        for i,(x,y) in enumerate(zip(a,b)):
            d=first_diff(x,y,f"{path}[{i}]")
            if d:return d
        return None
    return None if a==b else {"path":path,"old":a,"new":b,"reason":"value"}

def main():
    p=argparse.ArgumentParser();p.add_argument("old",type=Path);p.add_argument("new",type=Path);x=p.parse_args()
    a=scrub(json.loads(x.old.read_text(encoding="utf8")));b=scrub(json.loads(x.new.read_text(encoding="utf8")))
    d=first_diff(a,b);print(json.dumps({"equal":d is None,"first_diff":d},ensure_ascii=False,indent=2,default=str))
if __name__=="__main__":main()
