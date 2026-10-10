import assert from 'node:assert/strict';
import { recoverSignedParts, VERSION } from '../../web/static/public-structural-recovery-p0.mjs';
const W=10,H=10,N=W*H;
const src=new Uint8ClampedArray(N*4);
const base=new Uint8ClampedArray(N*4);
const face=new Uint8Array(N),left=new Uint8Array(N),right=new Uint8Array(N);
for(let y=0;y<H;y++)for(let x=0;x<W;x++){
  const i=y*W+x,o=i*4;
  src[o]=200;src[o+1]=180;src[o+2]=170;src[o+3]=255;
  base[o]=9;base[o+1]=10;base[o+2]=11;base[o+3]=255;
  if(x>=4&&x<=5&&y>=2&&y<=5) face[i]=255;
  if(x>=1&&x<=2&&y>=5&&y<=8){left[i]=255;src[o]=20;src[o+1]=30;src[o+2]=150;}
  if(x>=7&&x<=8&&y>=5&&y<=8){right[i]=255;src[o]=80;src[o+1]=140;src[o+2]=45;}
  if(face[i] && y===4){src[o]=0;src[o+1]=0;src[o+2]=0;}
}
const inputs=()=>({width:W,height:H,sourceRgba:src,baselineRgba:base,
 faceMask:face,parts:[{id:'left-arm',mask:left},{id:'right-arm',mask:right}]});
let passed=0;
function check(name, fn){fn();console.log('PASS',name);passed++;}
const run=()=>recoverSignedParts(inputs());
check('source-signed two arms plus face are protected',()=>{
 const r=run();assert.equal(r.audit.parts.length,2);assert.equal(r.audit.facePixels,8);
 assert.equal(r.audit.parts[0].pixels,8);assert.equal(r.audit.parts[1].pixels,8);
 assert.equal(r.audit.appliedToProduction,false);
 assert.equal(r.audit.noOutsideOwnerChanges,true);
 assert.equal(r.audit.sourceObservedColorsOnly,true);
 assert.equal(r.rgba.length,base.length);
 assert.match(VERSION,/structural-recovery-p0/);
});
check('outside signed owners and all alpha bitwise unchanged',()=>{
 const r=run().rgba;
 for(let i=0;i<N;i++){
  const o=i*4;assert.equal(r[o+3],base[o+3]);
  if(!(face[i]||left[i]||right[i]))assert.deepEqual([...r.subarray(o,o+4)],[...base.subarray(o,o+4)]);
 }
});
check('all applied part colors appear verbatim in own original pixels',()=>{
 const r=run().rgba;
 for(const mask of [left,right]){
  const colors=new Set([...mask].flatMap((v,i)=>v?[[...src.subarray(i*4,i*4+3)].join(',')]:[]));
  for(let i=0;i<N;i++)if(mask[i])assert(colors.has([...r.subarray(i*4,i*4+3)].join(',')));
 }
});
check('no source-eye or mouth-like high frequency face pixels',()=>{
 const r=run().rgba;let c=null;
 for(let i=0;i<N;i++)if(face[i]){const rgb=[...r.subarray(i*4,i*4+3)];
 if(!c)c=rgb;assert.deepEqual(rgb,c);assert.notDeepEqual(rgb,[0,0,0]);}
});
check('strict two-run reproducibility and read-only inputs',()=>{
 const s=new Uint8ClampedArray(src),b=new Uint8ClampedArray(base),f=new Uint8Array(face);
 const first=run();const second=run();assert.deepEqual(first.rgba,second.rgba);
 assert.deepEqual(first.audit,second.audit);assert.deepEqual(src,s);assert.deepEqual(base,b);assert.deepEqual(face,f);
});
check('reject nonbinary and empty owner masks',()=>{
 const p=inputs();p.parts[0].mask=Uint8Array.from(left);p.parts[0].mask[51]=127;
 assert.throws(()=>recoverSignedParts(p),/nonbinary/);
 const p2=inputs();p2.faceMask=new Uint8Array(N);assert.throws(()=>recoverSignedParts(p2),/empty/);
});
check('reject overlaps, duplicate IDs and signed face part IDs',()=>{
 const p=inputs();p.parts[1].mask=Uint8Array.from(right);p.parts[1].mask[51]=255;
 assert.throws(()=>recoverSignedParts(p),/overlapping/);
 const p2=inputs();p2.parts[1].id='left-arm';assert.throws(()=>recoverSignedParts(p2),/part ID/);
 const p3=inputs();p3.parts[1].id='face';assert.throws(()=>recoverSignedParts(p3),/part ID/);
});
check('reject unsupported dimensions, malformed buffers and color budgets',()=>{
 assert.throws(()=>recoverSignedParts({...inputs(),width:401,height:401}),/dimensions/);
 assert.throws(()=>recoverSignedParts({...inputs(),sourceRgba:new Uint8ClampedArray(5)}),/source/);
 assert.throws(()=>recoverSignedParts({...inputs(),colorsPerPart:0}),/budget/);
});
check('opaque source face mandatory; arm alpha fringe preserved',()=>{
 const p=inputs();p.sourceRgba=Uint8ClampedArray.from(src);p.sourceRgba[face.findIndex(v=>v)*4+3]=127;
 assert.throws(()=>recoverSignedParts(p),/face source alpha/);
 const p2=inputs();p2.sourceRgba=Uint8ClampedArray.from(src);
 const fringe=left.findIndex(v=>v);p2.sourceRgba[fringe*4+3]=0;
 const r=recoverSignedParts(p2);assert.equal(r.audit.parts[0].unsupportedAlphaPixels,1);
 assert.deepEqual([...r.rgba.subarray(fringe*4,fringe*4+4)],[...base.subarray(fringe*4,fringe*4+4)]);
});
check('negative control: parts cannot be guessed from pixels without signed masks',()=>{
 const p=inputs();delete p.parts;assert.throws(()=>recoverSignedParts(p),/missing signed/);
});
console.log('TOTAL',passed,'PASS');
