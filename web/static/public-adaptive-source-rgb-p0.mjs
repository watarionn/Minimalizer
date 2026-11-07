/** StructuralRecovery P0 Stages136-145. ORIGINAL-OBSERVED, ADAPTIVE RGB.
 * Research ONLY. Input label pixels are UNTRUSTED semantic proposals, not people.
 * Only fully source-opaque, proposed pixels. Never invent RGB or image detail.
 * No production import; no human review, no full-character Golden authority.
 */
import {validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';
export const VERSION='p0-stage136-145-source-observed-adaptive-rgb-v1';
const fail=s=>{throw new TypeError(s)};
const ROLES=new Set([2,4,5,6,7,8,9]); // never face proposal, backdrop proposal, or unreviewed
const PAD=0xffffffff;
const pack=(r,g,b)=>(r<<16)|(g<<8)|b;
const sourcePack=(a,i)=>pack(a[i*4],a[i*4+1],a[i*4+2]);
const r=x=>(x>>16)&255,g=x=>(x>>8)&255,blue=x=>x&255;
const hex=x=>'#'+x.toString(16).padStart(6,'0');
const distance=(a,b)=>Math.abs(r(a)-r(b))+Math.abs(g(a)-g(b))+Math.abs(blue(a)-blue(b));
const sha=async raw=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(x=>x.toString(16).padStart(2,'0')).join('');
const byteCount=x=>new TextEncoder().encode(x).length;
const rectPath=([x0,y0,x1,y1])=>`M${x0} ${y0}h${x1-x0}v${y1-y0}h-${x1-x0}Z`;
function checkOptions({tileSize=16,colorsPerTile=4,maxPixelL1=765,maxRectangles=160000}={}){
 if(![8,16,32,64].includes(tileSize))fail('ADAPTIVE_TILE_SIZE_UNSUPPORTED');
 if(![1,2,4,8,16].includes(colorsPerTile))fail('ADAPTIVE_PALETTE_UNSUPPORTED');
 if(!Number.isInteger(maxPixelL1)||maxPixelL1<0||maxPixelL1>765)fail('ADAPTIVE_PIXEL_ERROR_BOUND_INVALID');
 if(!Number.isInteger(maxRectangles)||maxRectangles<1||maxRectangles>160000)fail('ADAPTIVE_RECT_CAP_INVALID');
 return {tileSize,colorsPerTile,maxPixelL1,maxRectangles};
}
function paletteForTile(pixels,limit){
 const histogram=new Map();
 for(const val of pixels)histogram.set(val,(histogram.get(val)||0)+1);
 const entries=[...histogram].sort((a,b)=>b[1]-a[1]||a[0]-b[0]);
 const chosen=[entries[0][0]],chosenSet=new Set(chosen);
 while(chosen.length<limit&&chosen.length<entries.length){
  let best=null,bestScore=-1,bestCount=-1;
  for(const [value,count]of entries){
   if(chosenSet.has(value))continue;
   let nearest=765;for(const x of chosen)nearest=Math.min(nearest,distance(value,x));
   const score=nearest*count; // observed-population weighted farthest-first
   if(score>bestScore||(score===bestScore&&(count>bestCount||
    (count===bestCount&&value<best)))){best=value;bestScore=score;bestCount=count;}
  }
  if(best===null)break;chosen.push(best);chosenSet.add(best);
 }
 return chosen;
}
function classifyOriginalTile({width,height,rgba,labels,selected,assigned,options}){
 const groupPalettes=[],ts=options.tileSize;
 for(let y0=0;y0<height;y0+=ts)for(let x0=0;x0<width;x0+=ts){
  const byRole=new Map(),endY=Math.min(height,y0+ts),endX=Math.min(width,x0+ts);
  for(let y=y0;y<endY;y++)for(let x=x0;x<endX;x++){
   const i=y*width+x,role=labels[i];if(!ROLES.has(role))continue;
   if(rgba[4*i+3]!==255)fail('ADAPTIVE_NONOPAQUE_SOURCE');
   if(!byRole.has(role))byRole.set(role,[]);
   byRole.get(role).push(i);
  }
  for(const [role,indices]of [...byRole].sort((a,b)=>a[0]-b[0])){
   const palette=paletteForTile(indices.map(i=>sourcePack(rgba,i)),options.colorsPerTile);
   const seen=new Set(indices.map(i=>sourcePack(rgba,i)));
   if(palette.some(color=>!seen.has(color)))fail('ADAPTIVE_PALETTE_NOT_IN_ORIGINAL_TILE');
   for(const i of indices){
    const original=sourcePack(rgba,i);let closest=palette[0],bestDist=distance(original,closest);
    for(const color of palette.slice(1)){const d=distance(original,color);
     if(d<bestDist||(d===bestDist&&color<closest)){closest=color;bestDist=d;}}
    if(bestDist>options.maxPixelL1)fail('ADAPTIVE_SOURCE_RGB_ERROR_BOUND_EXCEEDED');
    assigned[i]=closest;selected[i]=255;
   }
   groupPalettes.push({x0,y0,width:endX-x0,height:endY-y0,role,
    sourcePixelCount:indices.length,sourceObservedColors:palette.map(hex)});
  }
 }
 return groupPalettes;
}
function rectanglesForAssigned({width,height,labels,assigned,cap}){
 const groups=new Map();let previous=new Map(),rectangles=0;
 for(let y=0;y<height;y++){
  const next=new Map();let x=0;
  while(x<width){
   const i=y*width+x,role=labels[i],color=assigned[i];
   if(!ROLES.has(role)){if(color!==PAD)fail('ADAPTIVE_OUTSIDE_SELECTED');x++;continue;}
   if(color===PAD)fail('ADAPTIVE_MISSING_SELECTED');
   const begin=x;x++;
   while(x<width&&labels[y*width+x]===role&&assigned[y*width+x]===color)x++;
   const layer=role+'|'+color,key=layer+'|'+begin+'|'+x;
   let rect=previous.get(key);
   if(rect){rect[3]=y+1;}else{
    rect=[begin,y,x,y+1];rectangles++;
    if(rectangles>cap)fail('ADAPTIVE_RECT_COUNT_CAP_EXCEEDED');
    if(!groups.has(layer))groups.set(layer,[]);
    groups.get(layer).push(rect);
   }
   next.set(key,rect);
  }
  previous=next;
 }
 return {groups,rectangles};
}
function auditRectangles({rgba,labels,assigned,width,height,groups}){
 const actual=new Uint8Array(4*width*height),seen=new Uint8Array(width*height);
 let selected=0,totalL1=0,changed=0,maximum=0,sourceDifferenceSse=0;
 for(const [name,rects]of groups){
  const split=name.indexOf('|'),role=Number(name.slice(0,split)),color=Number(name.slice(split+1));
  for(const [x0,y0,x1,y1]of rects){
   if(x0<0||y0<0||x1>width||y1>height||x0>=x1||y0>=y1)fail('ADAPTIVE_RECT_OUTSIDE_SOURCE');
   for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
    const i=y*width+x;if(seen[i])fail('ADAPTIVE_DOUBLE_PIXEL');
    if(labels[i]!==role||rgba[i*4+3]!==255||assigned[i]!==color)
      fail('ADAPTIVE_FORGED_COLOR_OR_ROLE');
    seen[i]=1;selected++;
    const rr=r(color),gg=g(color),bb=blue(color),j=4*i;
    actual.set([rr,gg,bb,255],j);
    const dr=Math.abs(rr-rgba[j]),dg=Math.abs(gg-rgba[j+1]),db=Math.abs(bb-rgba[j+2]);
    const err=dr+dg+db;
    totalL1+=err;sourceDifferenceSse+=dr*dr+dg*dg+db*db;
    if(err)changed++;maximum=Math.max(maximum,err);
   }
  }
 }
 for(let i=0;i<seen.length;i++)if(Boolean(seen[i])!==ROLES.has(labels[i]))
  fail('ADAPTIVE_SELECTED_SOURCE_MEMBERSHIP_CHANGED');
 return {actual,selected,totalL1,changed,maximum,sourceDifferenceSse};
}
export async function buildAdaptiveSourceRgbPreview({source,draft,options={}}){
 const o=checkOptions(options);
 const validated=await validateUntrustedFullFrameDraft({...source,draft});
 const {width,height,sourceRgba:rgba}=source,n=width*height,labels=validated.labels;
 const selected=new Uint8Array(n),assigned=new Uint32Array(n);assigned.fill(PAD);
 const palettes=classifyOriginalTile({width,height,rgba,labels,selected,assigned,options:o});
 const cover=rectanglesForAssigned({width,height,labels,assigned,cap:o.maxRectangles});
 const evidence=auditRectangles({rgba,labels,assigned,width,height,groups:cover.groups});
 if(evidence.selected!==validated.proposedPixels-validated.counts[1]-validated.counts[3])
  fail('ADAPTIVE_LABEL_PIXEL_COUNT_CHANGED');
 if(evidence.maximum>o.maxPixelL1)fail('ADAPTIVE_RGB_ERROR_EXCEEDED');
 const paths=[],layers=[];
 for(const [name,rects]of cover.groups){
  const split=name.indexOf('|'),role=Number(name.slice(0,split)),color=Number(name.slice(split+1));
  const d=rects.map(rectPath).join('');
  paths.push(`<path fill="${hex(color)}" d="${d}"/>`);
  layers.push({role,sourceObservedColor:hex(color),rectangleCount:rects.length});
 }
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">${paths.join('')}</svg>`;
 return {version:VERSION,caseId:source.caseId,sourceRgbaSha256:source.sourceRgbaSha256,
  labelsSha256:validated.labelsSha256,options:o,sourceTilesWithProposals:palettes.length,
  sourceObservedPaletteGroups:palettes,outputLayers:layers,
  paintedPixels:evidence.selected,excludedOriginalPixels:n-evidence.selected,
  originalRgbChangedPixels:evidence.changed,totalRgbAbsoluteError:evidence.totalL1,
  meanRgbL1PerPaintedPixel:evidence.selected?evidence.totalL1/evidence.selected:0,
  worstPixelRgbL1:evidence.maximum,sourceRgbSse:evidence.sourceDifferenceSse,
  rectangleCount:cover.rectangles,explicitVertices:cover.rectangles*4,
  svg,svgBytes:byteCount(svg),paintedSourceMaskSha256:await sha(selected),
  renderedRgbaSha256:await sha(evidence.actual),renderedRgba:evidence.actual,
  exactMembershipAgainstUntrustedLabel:true,allPaletteRgbFoundInOriginalTile:true,
  fullCharacterHumanReviewed:false,realHumanReviewedSemanticPixels:0,
  trueWholeCharacterGeometryPassed:false,defaultPublicRouteChanged:false,
  paintAuthorized:false,releaseAuthorized:false,status:'SOURCE_ONLY_UNTRUSTED_ADAPTIVE_PREVIEW_GOLDEN_HOLD'};
}
export async function verifyAdaptiveSourceRgbPreview({source,draft,candidate}){
 if(!candidate||candidate.version!==VERSION)fail('ADAPTIVE_PREVIEW_REQUIRED');
 const baseline=await buildAdaptiveSourceRgbPreview({source,draft,options:candidate.options});
 const fields=['caseId','sourceRgbaSha256','labelsSha256','paintedPixels',
 'excludedOriginalPixels','originalRgbChangedPixels','totalRgbAbsoluteError',
 'meanRgbL1PerPaintedPixel','worstPixelRgbL1','sourceRgbSse','rectangleCount',
 'explicitVertices','svg','svgBytes','paintedSourceMaskSha256','renderedRgbaSha256',
 'sourceTilesWithProposals','exactMembershipAgainstUntrustedLabel',
 'allPaletteRgbFoundInOriginalTile','fullCharacterHumanReviewed',
 'realHumanReviewedSemanticPixels','trueWholeCharacterGeometryPassed',
 'defaultPublicRouteChanged','paintAuthorized','releaseAuthorized','status'];
 if(fields.some(x=>candidate[x]!==baseline[x])||
 JSON.stringify(candidate.sourceObservedPaletteGroups)!==JSON.stringify(baseline.sourceObservedPaletteGroups)||
 JSON.stringify(candidate.outputLayers)!==JSON.stringify(baseline.outputLayers)||
 JSON.stringify(candidate.options)!==JSON.stringify(baseline.options)||
 !(candidate.renderedRgba instanceof Uint8Array)||
 candidate.renderedRgba.length!==baseline.renderedRgba.length||
 candidate.renderedRgba.some((x,i)=>x!==baseline.renderedRgba[i]))
  fail('ADAPTIVE_SOURCE_OR_OUTPUT_TAMPERED');
 return {version:VERSION,caseId:baseline.caseId,replaySourceAndSvgMatches:true,
  authenticatedHumanPixels:0,fullBodyBudgetCertified:false,
  releaseAuthorized:false,status:'ORIGINAL_SOURCE_ADAPTIVE_REPLAY_ONLY_GOLDEN_HOLD'};
}
export function guardAdaptiveReleaseGate({cases=[]}={}){
 if(!Array.isArray(cases)||cases.length>2||cases.some(x=>!x||!['GC001','Raden'].includes(x.caseId))||
  new Set(cases.map(x=>x.caseId)).size!==cases.length)fail('ADAPTIVE_INVALID_RELEASE_CASES');
 return {version:VERSION,missing:['GC001','Raden'].filter(c=>!cases.some(x=>x.caseId===c)),
  realIndependentlyIdentifiedHumanReviewers:0,approvedBodySemanticPixels:0,
  bothRealWholeCharacterSilhouettesGolden:false,originalFullCharacterBudgetPassed:false,
  colorBoundaryGolden:false,realIphoneSafariHttpsVerified:false,rollbackExercised:false,
  defaultPublicPaintAuthorized:false,productionReleaseAuthorized:false,
  status:'SOURCE_ONLY_ADAPTIVE_RESEARCH_GOLDEN_HOLD'};
}
