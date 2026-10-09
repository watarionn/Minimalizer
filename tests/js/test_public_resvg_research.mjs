import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {Resvg,initWasm} from "../../web/static/vendor/resvg-wasm/index.mjs";
import {makeSourceSvg,compareRgba,auditShapes} from "../../web/static/public-resvg-research.mjs";

let pass=0;
function check(name,func){func();console.log("PASS",name);pass++;}
const outer={rgb:[10,20,30],rings:[[[1,1],[23,1],[23,23],[1,23]]]};
const hole={rgb:[130,90,40],rings:[[[1,1],[23,1],[23,23],[1,23]],
  [[5,5],[5,18],[18,18],[18,5]]]};
check("source SVG owner hole order and immutable colors",()=>{
 const before=JSON.stringify([outer,hole]);
 const source=makeSourceSvg([outer,hole],24,24);
 assert.equal(source.status,"ok");
 assert.equal(source.rings,3);
 assert.equal(source.seen,2);
 assert.ok(source.svg.includes('fill-rule="evenodd"'));
 assert.equal(JSON.stringify([outer,hole]),before);
});
check("invalid rings, dims and color fail closed",()=>{
 assert.equal(makeSourceSvg([outer],500,500).status,"invalid-input");
 assert.equal(makeSourceSvg([{rgb:[-1,0,0],polygon:[[0,0],[1,0],[1,1]]}],12,12).status,"invalid-shape");
 assert.equal(makeSourceSvg([{...outer,rings:[[[0,0],[3,0],[NaN,2]]]}],12,12).status,"invalid-ring");
});
check("cap whole owner without stripping holes",()=>{
 const s=makeSourceSvg(Array.from({length:12},()=>hole),24,24);
 assert.equal(s.status,"truncated");
 assert.equal(s.seen,8);
 assert.equal(s.rings,16);
});
check("raw RGBA transparent channel included and mismatch counted",()=>{
 const a=new Uint8ClampedArray([1,2,3,255,5,6,7,0]);
 const b=new Uint8ClampedArray(a);
 assert.equal(compareRgba(a,b).exactNativeParity,true);
 b[7]=10; b[0]=4;
 const diff=compareRgba(a,b);
 assert.equal(diff.differentPixels,2);
 assert.equal(diff.maxChannelDelta,10);
 assert.equal(diff.absoluteChannelDelta,13);
 assert.equal(compareRgba(a,[3,2,1]),null);
});
await initWasm(readFileSync(new URL("../../web/static/vendor/resvg-wasm/index_bg.wasm",import.meta.url)));
const testSvg=makeSourceSvg([hole],24,24).svg;
let rendered,renderer;
try {
 renderer=new Resvg(testSvg,{fitTo:{mode:"original"},font:{loadSystemFonts:false}});
 rendered=renderer.render();
 const png=rendered.asPng();
 assert.equal(renderer.width,24);
 assert.equal(renderer.height,24);
 assert.ok(png.length>50);
 assert.equal(Buffer.from(png).toString("hex",0,8),"89504e470d0a1a0a");
 pass++;console.log("PASS real pinned resvg WASM executes and returns PNG");
} finally {
 if(rendered?.free)rendered.free();
 if(renderer?.free)renderer.free();
}
const fail=await auditShapes([outer],24,24);
assert.equal(fail.status,"error"); // No browser Image, must fail closed.
assert.equal(fail.applied,false);
pass++;console.log("PASS unavailable browser canvas fails without application");
assert.equal(pass,6);
console.log("6 scenarios PASS");
