"""Research-only lossless M/L-to-H/V SVG path compaction; vertices unchanged."""
import re, hashlib, json, argparse
from pathlib import Path
from xml.etree import ElementTree as ET

NS="{http://www.w3.org/2000/svg}"
TOK=re.compile(r"([MLZ])|(-?\\d+(?:\\.\\d+)?)")
GRAMMAR=re.compile(r"(?:M-?\\d+ -?\\d+ ?(?:L-?\\d+ -?\\d+ ?)*Z)+")

def encode_path(d):
    if not GRAMMAR.fullmatch(d): raise ValueError("unverified path syntax")
    tokens=[a or b for a,b in TOK.findall(d)]
    result=[]; index=0; x=y=0; start=None; vertices=0
    while index<len(tokens):
        op=tokens[index];index+=1
        if op=="Z":
            if start is None: raise ValueError("no ring")
            result.append("Z");x,y=start;continue
        if op not in ("M","L") or index+1>=len(tokens): raise ValueError("malformed")
        a=int(tokens[index]);b=int(tokens[index+1]);index+=2;vertices+=1
        if op=="M": result.append(f"M{a} {b}");start=(a,b)
        elif b==y: result.append(f"H{a}")
        elif a==x: result.append(f"V{b}")
        else: result.append(f"L{a} {b}")
        x,y=a,b
    return " ".join(result),vertices

def compact(original,target):
    original=Path(original);target=Path(target)
    tree=ET.parse(original);root=tree.getroot()
    if root.tag!=NS+"svg": raise ValueError("invalid namespace")
    clips=root.findall(".//"+NS+"clipPath/"+NS+"path")
    shapes=len(root.findall(".//"+NS+"rect"))+len(clips)
    if shapes!=40 or len(clips)!=10: raise ValueError("wrong full-scene shape contract")
    before=after=verts=0
    for p in clips:
        d=p.get("d");value,n=encode_path(d)
        before+=len(d);after+=len(value);verts+=n;p.set("d",value)
    target.parent.mkdir(parents=True,exist_ok=True)
    tree.write(target,encoding="utf-8",xml_declaration=False)
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    return {"original":original.name,"originalSha256":sha(original),"compressedSha256":sha(target),
        "originalPathCharacters":before,"compressedPathCharacters":after,
        "retainedVertexCount":verts,"shapeCount":shapes,"production":"UNCHANGED",
        "stage8HistoricSourceBudget":"HOLD","fullSceneGolden":"HOLD"}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("sources",nargs="+");p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    report=[compact(f,a.out/Path(f).name) for f in a.sources]
    (a.out/"lossless_metrics.json").write_text(json.dumps(report,indent=2)+"\\n")
    print(json.dumps(report,indent=2))
