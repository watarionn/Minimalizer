/* V25 research-only connected source-color region proposals. No synthesis or model calls. */
(function(root) {
"use strict";
function propose(built,palette,rgba,width,height,options) {
  const cfg=Object.assign({maxGroupPixels:256,minGroupPixels:4,minGainSquared:2500,
    maxDepth:6,maxSeeds:16,lowerYFraction:0.33,minDonorPixels:150,
    minRecipientPixels:150},options||{});
  const area=width*height,labels=built.componentIds;
  if(!Number.isInteger(width)||!Number.isInteger(height)||area!==labels.length
    ||rgba.length!==4*area||!Array.isArray(built.components)
    ||!palette||!Array.isArray(palette.colors)
    ||!Number.isInteger(cfg.maxGroupPixels)||cfg.maxGroupPixels<2||cfg.maxGroupPixels>400
    ||!Number.isInteger(cfg.minGroupPixels)||cfg.minGroupPixels<2
    ||cfg.minGroupPixels>cfg.maxGroupPixels
    ||!Number.isInteger(cfg.maxDepth)||cfg.maxDepth<1||cfg.maxDepth>8
    ||!Number.isInteger(cfg.maxSeeds)||cfg.maxSeeds<1||cfg.maxSeeds>32
    ||!Number.isFinite(cfg.minGainSquared)||cfg.minGainSquared<0
    ||!Number.isFinite(cfg.lowerYFraction)||cfg.lowerYFraction<0
    ||cfg.lowerYFraction>1)throw Error("Invalid V25 group bounds");
  const neighbors=i=>{
    const x=i%width,y=Math.floor(i/width);
    return [x>0?i-1:-1,x+1<width?i+1:-1,
      y>0?i-width:-1,y+1<height?i+width:-1].filter(j=>j>=0);
  };
  const sq=(i,c)=>{
    const p=4*i;
    return (rgba[p]-c[0])**2+(rgba[p+1]-c[1])**2+(rgba[p+2]-c[2])**2;
  };
  const sizes=built.components.map(c=>c.count),seeds=[];
  const minY=Math.floor(height*cfg.lowerYFraction);
  for(let y=minY;y<height;y++)for(let x=0;x<width;x++){
    const i=y*width+x,donor=labels[i];
    if(donor<0||sizes[donor]<cfg.minDonorPixels||!palette.colors[donor])continue;
    const recipients=new Set(neighbors(i).map(j=>labels[j]));
    recipients.delete(donor);
    for(const recipient of recipients) {
      if(recipient<0||sizes[recipient]<cfg.minRecipientPixels
        ||!palette.colors[recipient])continue;
      const gain=sq(i,palette.colors[donor])-sq(i,palette.colors[recipient]);
      if(gain>=cfg.minGainSquared)seeds.push({pixel:i,donor,recipient,gain});
    }
  }
  seeds.sort((a,b)=>b.gain-a.gain||a.pixel-b.pixel||
    a.donor-b.donor||a.recipient-b.recipient);
  let considered=0,topologyRejected=0,smallRejected=0;
  for(const seed of seeds.slice(0,cfg.maxSeeds)){
    considered++;
    const {donor,recipient}=seed;
    const seen=new Set([seed.pixel]),q=[{pixel:seed.pixel,depth:0}];
    let sourceGain=seed.gain;
    for(let head=0;head<q.length&&q.length<cfg.maxGroupPixels;head++){
      const {pixel,depth}=q[head];
      if(depth>=cfg.maxDepth)continue;
      for(const j of neighbors(pixel)) {
        if(q.length>=cfg.maxGroupPixels)break;
        if(seen.has(j)||labels[j]!==donor||Math.floor(j/width)<minY)continue;
        const gain=sq(j,palette.colors[donor])-sq(j,palette.colors[recipient]);
        if(gain<cfg.minGainSquared)continue;
        seen.add(j);q.push({pixel:j,depth:depth+1});sourceGain+=gain;
      }
    }
    if(q.length<cfg.minGroupPixels){smallRejected++;continue;}
    if(sizes[donor]-seen.size<cfg.minDonorPixels){topologyRejected++;continue;}
    const first=built.components[donor].pixels.find(i=>!seen.has(i));
    if(first===undefined){topologyRejected++;continue;}
    // Full 4-connected donor proof: a removed bridge cannot split a sleeve.
    const visited=new Set([first]),flood=[first];
    for(let head=0;head<flood.length;head++)for(const j of neighbors(flood[head])){
      if(labels[j]!==donor||seen.has(j)||visited.has(j))continue;
      visited.add(j);flood.push(j);
    }
    if(visited.size!==sizes[donor]-seen.size){topologyRejected++;continue;}
    // Source boundary seed joins recipient; only original labels and colors exist.
    const next=new Int32Array(labels);
    for(const i of seen)next[i]=recipient;
    const components=built.components.map(c=>({...c,pixels:[],
      count:0,minX:width,minY:height,maxX:0,maxY:0,borderTouches:0}));
    for(let i=0;i<area;i++){
      const c=components[next[i]];
      if(!c)throw Error("V25 invalid component index");
      const x=i%width,y=Math.floor(i/width);
      c.pixels.push(i);c.count++;
      c.minX=Math.min(c.minX,x);c.maxX=Math.max(c.maxX,x);
      c.minY=Math.min(c.minY,y);c.maxY=Math.max(c.maxY,y);
      if(x===0||y===0||x===width-1||y===height-1)c.borderTouches++;
    }
    if(components.some(c=>c.count===0))throw Error("V25 erased region");
    return {built:{components,componentIds:next},metrics:{
      candidates:seeds.length,groups:1,movedPixels:seen.size,
      sourceRgbErrorReduction:sourceGain,seed:seed.pixel,donor,recipient,
      considered,topologyRejected,smallRejected,pixels:[...seen].sort((a,b)=>a-b)
    }};
  }
  return {built,metrics:{candidates:seeds.length,groups:0,movedPixels:0,
    sourceRgbErrorReduction:0,seed:null,donor:null,recipient:null,
    considered,topologyRejected,smallRejected,pixels:[]}};
}
function compareSource(rgba,baselineShapes,candidateShapes,width,height) {
  const raster=root.MinimalizerOpenCvRaster;
  if(!raster||typeof raster.renderShapesRgba!=="function")
    return {pass:false,reason:"raster_missing",changedPixels:0,improvement:0};
  const before=raster.renderShapesRgba(baselineShapes,width,height,1,1,2);
  const after=raster.renderShapesRgba(candidateShapes,width,height,1,1,2);
  if(before.length!==4*width*height||before.length!==after.length)
    return {pass:false,reason:"invalid_raster",changedPixels:0,improvement:0};
  let improvement=0,changedPixels=0;
  for(let p=0;p<before.length;p+=4){
    if(before[p]===after[p]&&before[p+1]===after[p+1]&&before[p+2]===after[p+2])continue;
    changedPixels++;
    for(let c=0;c<3;c++)improvement+=(before[p+c]-rgba[p+c])**2
      -(after[p+c]-rgba[p+c])**2;
  }
  const pass=changedPixels>0&&improvement>0;
  return {pass,changedPixels,improvement,
    reason:changedPixels===0?"no_visible_change":pass?"pass":"source_rgb_regression"};
}
const api=Object.freeze({propose,compareSource});
root.MinimalizerColorGroupsV25=api;
if(typeof module!=="undefined"&&module.exports)module.exports=api;
}(typeof window!=="undefined"?window:globalThis));
