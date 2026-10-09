/** Research-only source-signed, source-RGB-only vector plane experiment. */
const requireValid=(v,msg)=>{if(!v)throw Error(msg)};
export function exactSourceBoundary(mask,w,h){
 requireValid(mask instanceof Uint8Array&&mask.length===w*h&&mask.every(v=>v===0||v===1),'source binary mask');
 const edgeMap=new Map(),edges=[];
 const add=(x0,y0,x1,y1,dir)=>{
  const e={x0,y0,x1,y1,dir,used:false},i=edges.push(e)-1;
  const key=x0+','+y0;
  if(!edgeMap.has(key))edgeMap.set(key,[]);
  edgeMap.get(key).push(i);
 };
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  if(!mask[y*w+x])continue;
  if(y===0||!mask[(y-1)*w+x])add(x,y,x+1,y,0);
  if(x===w-1||!mask[y*w+x+1])add(x+1,y,x+1,y+1,1);
  if(y===h-1||!mask[(y+1)*w+x])add(x+1,y+1,x,y+1,2);
  if(x===0||!mask[y*w+x-1])add(x,y+1,x,y,3);
 }
 const loops=[];
 for(let seed=0;seed<edges.length;seed++){
  if(edges[seed].used)continue;
  const loop=[],start=edges[seed],startKey=start.x0+','+start.y0;
  let curr=seed,limit=0;
  while(true){
   const e=edges[curr];requireValid(!e.used,'nonmanifold edge revisited');e.used=true;
   const a=[e.x0,e.y0];
   if(loop.length<2)loop.push(a);
   else{
    const n=loop.length,p=loop[n-2],q=loop[n-1];
    if((q[0]-p[0])*(a[1]-q[1])===(q[1]-p[1])*(a[0]-q[0]))loop[n-1]=a;
    else loop.push(a);
   }
   const endKey=e.x1+','+e.y1;
   if(endKey===startKey)break;
   const options=(edgeMap.get(endKey)||[]).filter(i=>!edges[i].used);
   requireValid(options.length>0,'broken oriented boundary');
   options.sort((a,b)=>{
    const turn=v=>(edges[v].dir-e.dir+4)%4;
    const pref=t=>t===1?0:t===0?1:t===3?2:3;
    return pref(turn(a))-pref(turn(b))||a-b;
   });
   curr=options[0];
   requireValid(++limit<=edges.length,'boundary cycle exceeded edge count');
  }
  if(loop.length>=3){
   while(loop.length>=3){
    const p=loop[loop.length-2],q=loop[loop.length-1],a=loop[0];
    if((q[0]-p[0])*(a[1]-q[1])===(q[1]-p[1])*(a[0]-q[0]))loop.pop();else break;
   }
   loops.push(loop);
  }
 }
 const path=loops.map(points=>'M'+points[0].join(' ')+' '+points.slice(1).map(p=>'L'+p.join(' ')).join(' ')+'Z').join('');
 return {path,loops:loops.length,vertices:loops.reduce((a,p)=>a+p.length,0),perimeterCellEdges:edges.length};
}
const color=(rgb,i)=>[rgb[i*3],rgb[i*3+1],rgb[i*3+2]];
const err=(c,i,rgb)=>Math.abs(c[0]-rgb[i*3])+Math.abs(c[1]-rgb[i*3+1])+Math.abs(c[2]-rgb[i*3+2]);
function nearestOriginalMedoid(indices,rgb){
 // Exact discrete L1 medoid: chosen RGB must occur in the verified original owner.
 const hist=[new Uint32Array(256),new Uint32Array(256),new Uint32Array(256)],totals=[0,0,0];
 for(const i of indices)for(let k=0;k<3;k++){
  const v=rgb[3*i+k];hist[k][v]++;totals[k]+=v;
 }
 const costs=[];
 for(let k=0;k<3;k++){
  const arr=new Float64Array(256);let countLess=0,sumLess=0;
  for(let v=0;v<256;v++){
   const count=hist[k][v],rightCount=indices.length-countLess-count;
   const rightSum=totals[k]-sumLess-v*count;
   arr[v]=v*countLess-sumLess+rightSum-v*rightCount;
   countLess+=count;sumLess+=v*count;
  }
  costs.push(arr);
 }
 let best=indices[0],bestCost=Infinity;
 for(const i of indices){
  const c=color(rgb,i),loss=costs[0][c[0]]+costs[1][c[1]]+costs[2][c[2]];
  if(loss<bestCost){bestCost=loss;best=i;}
 }
 return color(rgb,best);
}
function candidates(mask,rgb,w,h){
 const result=[];
 for(const sz of [8,12,16,24,32,48,64,96,128]){
  for(const shift of [0,Math.floor(sz/2)]){
   for(let y=-shift;y<h;y+=sz)for(let x=-shift;x<w;x+=sz){
    const x0=Math.max(0,x),y0=Math.max(0,y),x1=Math.min(w,x+sz),y1=Math.min(h,y+sz);
    if(x0>=x1||y0>=y1)continue;
    const indices=[];
    for(let yy=y0;yy<y1;yy++)for(let xx=x0;xx<x1;xx++)if(mask[yy*w+xx])indices.push(yy*w+xx);
    if(indices.length<8||indices.length/((x1-x0)*(y1-y0))<0.18)continue;
    result.push({x:x0,y:y0,w:x1-x0,h:y1-y0,indices,fill:nearestOriginalMedoid(indices,rgb)});
   }
  }
 }
 return result;
}
export function optimizeSignedColorPlanes({mask,rgb,w,h,budget=40,sourceSha,maskSha}={}){
 requireValid(Number.isSafeInteger(w)&&Number.isSafeInteger(h)&&w>0&&h>0&&w*h<=4000000,'dimensions');
 requireValid(mask instanceof Uint8Array&&mask.length===w*h&&mask.every(v=>v===0||v===1),'signed source mask');
 requireValid(rgb instanceof Uint8Array&&rgb.length===w*h*3,'unaltered source rgb');
 requireValid(/^[0-9a-f]{64}$/i.test(sourceSha||'')&&/^[0-9a-f]{64}$/i.test(maskSha||''),'provenance sha');
 requireValid(Number.isInteger(budget)&&budget>=2&&budget<=80,'budget 2..80');
 const indices=[];for(let i=0;i<mask.length;i++)if(mask[i])indices.push(i);
 requireValid(indices.length>0,'empty source owner');
 const outline=exactSourceBoundary(mask,w,h),base=nearestOriginalMedoid(indices,rgb);
 const current=new Uint8Array(w*h*3);
 for(const i of indices)current.set(base,i*3);
 const getCurrent=i=>[current[i*3],current[i*3+1],current[i*3+2]];
 const options=candidates(mask,rgb,w,h),chosen=[],used=new Set();
 let totalError=indices.reduce((a,i)=>a+err(base,i,rgb),0);const progress=[totalError];
 for(let round=0;round<budget-2;round++){
  let best=-1,gain=0;
  for(let n=0;n<options.length;n++){
   if(used.has(n))continue;
   const opt=options[n];let g=0;
   for(const i of opt.indices)g+=err(getCurrent(i),i,rgb)-err(opt.fill,i,rgb);
   if(g>gain+1e-6){gain=g;best=n;}
  }
  if(best<0||gain<=0)break;
  const opt=options[best];
  for(const i of opt.indices)current.set(opt.fill,i*3);
  totalError-=gain;progress.push(totalError);used.add(best);chosen.push(opt);
 }
 const maskClip='<path d="'+outline.path+'" clip-rule="evenodd" fill-rule="evenodd"/>';
 const layer=chosen.map(p=>'<rect x="'+p.x+'" y="'+p.y+'" width="'+p.w+'" height="'+p.h+'" fill="rgb('+p.fill.join(',')+')"/>').join('');
 const svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'"><defs><clipPath id="signed" clipPathUnits="userSpaceOnUse">'+maskClip+'</clipPath></defs><g clip-path="url(#signed)"><rect x="0" y="0" width="'+w+'" height="'+h+'" fill="rgb('+base.join(',')+')"/>'+layer+'</g></svg>\n';
 return {svg,metrics:{sourceSha,maskSha,maskPixels:indices.length,budgetRequested:budget,shapes:chosen.length+2,clipBoundaryPathCount:1,clipBoundaryVertexOccurrences:outline.vertices,clipSourceLoops:outline.loops,sourcePerimeterCellEdges:outline.perimeterCellEdges,
  colorPlaneCount:chosen.length,baseSourceMedoid:base,sourceRGBMaskedMAEApprox:totalError/(indices.length*3),inputCandidateCount:options.length,
  localShape40Gate:chosen.length+2<=40,wholeImageShapeGate:'NOT_EVALUATED',hardSourceVertexGate:'NOT_EVALUATED',golden:'HOLD',production:'UNCHANGED',faceDetails:'NOT_RENDERED'},
  planes:chosen.map(({x,y,w,h,fill})=>({x,y,w,h,fill})),progress,clipPath:outline.path,baseRgb:base,width:w,height:h};
}
