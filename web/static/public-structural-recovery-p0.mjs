// Research-only source-signed part recovery. Not imported by the Public route.
// A mask is an independent, signed observation, NEVER inferred from color alone.
export const VERSION = "public-structural-recovery-p0-part-paint-v1";
const LIMIT_PIXELS = 400 * 400;

function requireRgba(value, n, label) {
  if (!(value instanceof Uint8Array || value instanceof Uint8ClampedArray)
      || value.length !== n * 4) throw new TypeError(label + ": invalid RGBA");
}
function requireMask(value, n, label) {
  if (!(value instanceof Uint8Array || value instanceof Uint8ClampedArray)
      || value.length !== n) throw new TypeError(label + ": invalid signed mask");
  let count=0;
  for (const v of value) {
    if (v !== 0 && v !== 255) throw new TypeError(label + ": nonbinary signed mask");
    if (v) count++;
  }
  if (!count) throw new TypeError(label + ": empty signed mask");
  return count;
}
// Pick a real source pixel, not a synthesized mean or an external palette entry.
// The dominant 5-bit RGB cell is robust to tiny highlights/eyelashes and outliers.
function signedMedoid(source, indices) {
  if(!indices.length)throw new TypeError("empty owner tile");
  const bins=new Map();
  for(const i of indices){
    const o=i*4, r=source[o],g=source[o+1],b=source[o+2];
    const key=(r>>3)*1024+(g>>3)*32+(b>>3);
    let bin=bins.get(key);
    if(!bin){bin={n:0,sum:[0,0,0],first:i,indices:[]};bins.set(key,bin);}
    bin.n++;bin.sum[0]+=r;bin.sum[1]+=g;bin.sum[2]+=b;bin.indices.push(i);
  }
  let best=null,bestKey=Infinity;
  for(const [key,bin] of bins){
    if(!best || bin.n>best.n || (bin.n===best.n&&key<bestKey)){
      best=bin;bestKey=key;
    }
  }
  let pixel=best.first,score=Infinity;
  for(const i of best.indices){
    const o=i*4;
    const dr=source[o]*best.n-best.sum[0];
    const dg=source[o+1]*best.n-best.sum[1];
    const db=source[o+2]*best.n-best.sum[2];
    const distance=dr*dr+dg*dg+db*db;
    if(distance<score){score=distance;pixel=i;}
  }
  const o=pixel*4;
  return [source[o],source[o+1],source[o+2]];
}
function distanceSq(source, offset, c) {
  const dr=source[offset]-c[0],dg=source[offset+1]-c[1],db=source[offset+2]-c[2];
  return dr*dr+dg*dg+db*db;
}
function paint(mask,source,output,width,height,colorBudget,flatFace) {
  const positions=[];
  for(let i=0;i<width*height;i++)if(mask[i])positions.push(i);
  if(!positions.length)throw new TypeError("empty supported owner");
  if(flatFace){
    const rgb=signedMedoid(source,positions);
    for(const i of positions){const o=i*4;
      output[o]=rgb[0];output[o+1]=rgb[1];output[o+2]=rgb[2];}
    return {pixels:positions.length,paletteColors:1};
  }
  // Independent per-source-part palette. Do not share colors or geometry
  // across clothing/arm boundaries; seed with prevalent observed RGB bins.
  const bins=new Map();
  for(const i of positions){const o=i*4;
    const key=(source[o]>>3)*1024+(source[o+1]>>3)*32+(source[o+2]>>3);
    bins.set(key,(bins.get(key)||0)+1);
  }
  const ranked=[...bins].sort((a,b)=>b[1]-a[1]||a[0]-b[0]);
  const centers=[];
  for(const [key] of ranked){
    const c=[((key>>10)&31)*8+4,((key>>5)&31)*8+4,(key&31)*8+4];
    if(!centers.some(v=>{const dr=c[0]-v[0],dg=c[1]-v[1],db=c[2]-v[2];
      return dr*dr+dg*dg+db*db<=1024;}))centers.push(c);
    if(centers.length>=colorBudget)break;
  }
  const labels=new Uint8Array(width*height);
  for(let iter=0;iter<8;iter++){
    const counts=new Uint32Array(centers.length);
    const sums=centers.map(()=>[0,0,0]);
    for(const i of positions){const o=i*4;
      let best=0,score=Infinity;
      for(let k=0;k<centers.length;k++){
        const d=distanceSq(source,o,centers[k]);
        if(d<score){score=d;best=k;}
      }
      labels[i]=best;counts[best]++;
      sums[best][0]+=source[o];sums[best][1]+=source[o+1];sums[best][2]+=source[o+2];
    }
    for(let k=0;k<centers.length;k++)if(counts[k]){
      const mean=sums[k].map(v=>v/counts[k]);
      let score=Infinity,chosen=positions[0];
      for(const i of positions)if(labels[i]===k){
        const d=distanceSq(source,i*4,mean);
        if(d<score){score=d;chosen=i;}
      }
      centers[k]=[source[chosen*4],source[chosen*4+1],source[chosen*4+2]];
    }
  }
  // Neighbourhood vote only inside each signed owner. Avoid grid-tile seams.
  const smooth=new Uint8Array(labels);
  const present=new Uint8Array(mask.length);
  for(const i of positions)present[i]=1;
  for(const i of positions){
    const x=i%width,y=Math.floor(i/width),votes=new Uint16Array(centers.length);
    for(let yy=Math.max(0,y-2);yy<=Math.min(height-1,y+2);yy++)
      for(let xx=Math.max(0,x-2);xx<=Math.min(width-1,x+2);xx++){
        const j=yy*width+xx;if(present[j])votes[labels[j]]++;
      }
    let winner=labels[i],best=votes[winner];
    for(let k=0;k<votes.length;k++)if(votes[k]>best){best=votes[k];winner=k;}
    smooth[i]=winner;
  }
  // Colors are exact source RGB samples snapped above; masks remain untouched.
  for(const i of positions){const o=i*4,c=centers[smooth[i]];
    output[o]=c[0];output[o+1]=c[1];output[o+2]=c[2];}
  return {pixels:positions.length,paletteColors:centers.length};
}
export function recoverSignedParts({width,height,sourceRgba,baselineRgba,
  faceMask,parts,colorsPerPart=5}) {
  if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||
    width*height>LIMIT_PIXELS) throw new TypeError("invalid dimensions");
  const n=width*height;
  requireRgba(sourceRgba,n,"source");requireRgba(baselineRgba,n,"baseline");
  if(!Number.isInteger(colorsPerPart)||colorsPerPart<1||colorsPerPart>8)
    throw new TypeError("invalid per-part color budget");
  if(!Array.isArray(parts)||parts.length<1||parts.length>8)
    throw new TypeError("missing signed source parts");
  requireMask(faceMask,n,"face");
  const seen=new Uint8Array(n);
  for(let i=0;i<n;i++)if(faceMask[i])seen[i]=1;
  const ids=new Set();
  const verified=[];
  for(const part of parts){
    if(!part||typeof part.id!=="string"||!/^[a-z][a-z0-9-]{0,39}$/.test(part.id)||
      part.id==="face"||ids.has(part.id))throw new TypeError("invalid part ID");
    ids.add(part.id);
    const count=requireMask(part.mask,n,part.id);
    for(let i=0;i<n;i++)if(part.mask[i]){
      if(seen[i])throw new TypeError("overlapping signed owners");
      seen[i]=1;
    }
    verified.push({id:part.id,mask:part.mask,count});
  }
  // Signed masks may include source-antialias fringe or transparent pixels.
  // Never invent color at such pixels; preserve the original baseline there.
  for(let i=0;i<n;i++)if(faceMask[i]&&sourceRgba[i*4+3]!==255)
    throw new TypeError("face source alpha not opaque");
  for(const part of verified){
    part.effective=new Uint8Array(n);
    part.unsupportedPixels=0;
    for(let i=0;i<n;i++)if(part.mask[i]){
      if(sourceRgba[i*4+3]===255)part.effective[i]=255;
      else part.unsupportedPixels++;
    }
    if(part.unsupportedPixels===part.count)
      throw new TypeError("no source-backed owner pixels");
  }
  const output=new Uint8ClampedArray(baselineRgba);
  const regions=[];
  for(const part of verified){
    regions.push({id:part.id,unsupportedAlphaPixels:part.unsupportedPixels,
      ...paint(part.effective,sourceRgba,output,width,height,colorsPerPart,false)});
  }
  const face=paint(faceMask,sourceRgba,output,width,height,1,true);
  let changes=0;
  for(let i=0;i<n;i++){
    const o=i*4;
    if(output[o+3]!==baselineRgba[o+3])throw new Error("alpha violation");
    if(!seen[i] && (output[o]!==baselineRgba[o]||output[o+1]!==baselineRgba[o+1]
      ||output[o+2]!==baselineRgba[o+2]))throw new Error("outside owner violation");
    if(output[o]!==baselineRgba[o]||output[o+1]!==baselineRgba[o+1]||
       output[o+2]!==baselineRgba[o+2])changes++;
  }
  return {rgba:output,audit:Object.freeze({version:VERSION,appliedToProduction:false,
    changedPixels:changes,facePixels:face.pixels,facePaletteColors:face.paletteColors,
    parts:regions,totalPartPixels:regions.reduce((a,r)=>a+r.pixels,0),
    noOutsideOwnerChanges:true,sourceObservedColorsOnly:true})};
}
