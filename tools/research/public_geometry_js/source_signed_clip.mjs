// Research-only signed source cell clipping. Not imported by MinimalizerPublic.
const guard=(v,m)=>{if(!v)throw Error(m)};
export function pixelRectangles(mask,w,h){
 guard(mask instanceof Uint8Array&&mask.length===w*h&&mask.every(v=>v===0||v===1),"binary source owner mask");
 const out=[],active=new Map();
 for(let y=0;y<h;y++){
  const seen=new Set();
  for(let x=0;x<w;){
   if(!mask[y*w+x]){x++;continue;}
   const a=x;while(x<w&&mask[y*w+x])x++;
   const key=a+":"+x;
   if(active.has(key))active.get(key).height++;
   else active.set(key,{x:a,y,width:x-a,height:1});
   seen.add(key);
  }
  for(const [key,value] of active)if(!seen.has(key)){out.push(value);active.delete(key);}
 }
 out.push(...active.values());return out.sort((a,b)=>a.y-b.y||a.x-b.x);
}
export function clippedSignedSvg({mask,rgb,w,h,trianglesSvg,sourceSha,maskSha,undercoat=false}){
 guard(Number.isSafeInteger(w)&&Number.isSafeInteger(h)&&w>0&&h>0&&w*h<=4000000,"dimensions");
 guard(rgb instanceof Uint8Array&&rgb.length===w*h*3,"verified original RGB");
 guard(/^[a-f0-9]{64}$/i.test(sourceSha||"")&&/^[a-f0-9]{64}$/i.test(maskSha||""),"source authority");
 const rects=pixelRectangles(mask,w,h);guard(rects.length>0,"empty owner");
 const head=trianglesSvg.match(/^<svg xmlns="http:\/\/www\.w3\.org\/2000\/svg" width="(\d+)" height="(\d+)" viewBox="0 0 (\d+) (\d+)">/);
 guard(head&&+head[1]===w&&+head[2]===h&&+head[3]===w&&+head[4]===h,"SVG source size");
 const body=trianglesSvg.slice(head[0].length).replace(/<\/svg>\s*$/,"");
 const triangles=[...body.matchAll(/<polygon points="([0-9., \-]+)" fill="rgb\((\d{1,3}),(\d{1,3}),(\d{1,3})\)"\/>/g)];
 guard(triangles.map(v=>v[0]).join("")===body,"foreign SVG markup");
 const palette=new Set(),avg=[0,0,0];let n=0;
 for(let i=0;i<mask.length;i++)if(mask[i]){
  const c=[rgb[3*i],rgb[3*i+1],rgb[3*i+2]];palette.add(c.join(","));n++;
  for(let k=0;k<3;k++)avg[k]+=c[k];
 }
 avg.forEach((v,k)=>avg[k]=v/n);
 let best=-1,dmin=Infinity;
 for(let i=0;i<mask.length;i++)if(mask[i]){
  const d=avg.reduce((s,v,k)=>s+(rgb[i*3+k]-v)**2,0);
  if(d<dmin){dmin=d;best=i;}
 }
 const medoid=[rgb[3*best],rgb[3*best+1],rgb[3*best+2]];
 for(const tri of triangles){
  const pts=tri[1].trim().split(/\s+/);guard(pts.length===3,"triangle topology");
  for(const pt of pts){
   const v=pt.split(",").map(Number);
   guard(v.length===2&&v.every(Number.isFinite)&&v[0]>=0&&v[0]<=w&&v[1]>=0&&v[1]<=h,"triangle vertices");
  }
  guard(palette.has([+tri[2],+tri[3],+tri[4]].join(",")),"RGB not from signed original");
 }
 const clips=rects.map(r=>`<rect x="${r.x}" y="${r.y}" width="${r.width}" height="${r.height}"/>`).join("");
 const fill=undercoat?`<rect x="0" y="0" width="${w}" height="${h}" fill="rgb(${medoid.join(",")})"/>`:"";
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><defs><clipPath id="signed-mask" clipPathUnits="userSpaceOnUse">${clips}</clipPath></defs><g clip-path="url(#signed-mask)">${fill}${body}</g></svg>\n`;
 const shapes=rects.length+triangles.length+Number(undercoat);
 return {svg,metrics:{candidateOnly:true,productionEligible:false,sourceSha,maskSha,mode:undercoat?"undercoat_clipped":"clip_only",
  maskPixels:n,clipRects:rects.length,vertexOccurrences:4*rects.length,triangles:triangles.length,medoid,
  shapes,shapeBudget40Pass:shapes<=40,visualGolden:"HOLD"}};
}
