/* BrowserFallback v27: independent source-image part evidence, no render authority.
 * Selfie multiclass ONNX: Google weights converted by senty-au (Apache 2.0).
 * MediaPipe PoseLandmarker (CPU browser-only): optional, no invented arm masks.
 * Artifact URLs and SHA-256 are pinned; model failures ABSTAIN.
 */
import * as ort from "./vendor/onnxruntime/ort.wasm.min.mjs";
const VERSION="browser-part-evidence-v27";
const MODEL_URL="https://huggingface.co/senty-au/selfie_multiclass_256x256-ONNX/resolve/6db8421a7150ac20558f2c24675078eb3a1a04d0/onnx/model.onnx";
const MODEL_SHA="35ec1ecd9ee7f85073c99c00020b7f6751b69506eeacf683bc8665f6117f85b0";
const POSE_MODEL_URL="https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";
const POSE_SHA="59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a";
const POSE_JS_URL="https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.32/vision_bundle.mjs";
const POSE_WASM_URL="https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.32/wasm";
const LABELS=Object.freeze(["background","hair","body_skin","face_skin","clothes","accessories"]);
ort.env.wasm.wasmPaths = new URL("./vendor/onnxruntime/", import.meta.url).href;
ort.env.wasm.numThreads = 1;
async function verifiedBuffer(url,expectedSha) {
  const res=await fetch(url,{mode:"cors",cache:"force-cache"});
  if(!res.ok)throw Error("v27 model fetch status="+res.status);
  const bytes=new Uint8Array(await res.arrayBuffer());
  const digest=new Uint8Array(await crypto.subtle.digest("SHA-256",bytes));
  const hex=[...digest].map(b=>b.toString(16).padStart(2,"0")).join("");
  if(hex!==expectedSha)throw Error("v27 model SHA-256 mismatch");
  return bytes;
}
function canvasPixels(image) {
  const w=256,h=256;
  const canvas=document.createElement("canvas");canvas.width=w;canvas.height=h;
  const ctx=canvas.getContext("2d",{willReadFrequently:true});
  if(!ctx)throw Error("canvas 2d unavailable");
  ctx.fillStyle="#ffffff";ctx.fillRect(0,0,w,h);
  ctx.drawImage(image,0,0,w,h);
  const pixels=ctx.getImageData(0,0,w,h).data;
  const input=new Float32Array(w*h*3);
  for(let i=0;i<w*h;i++){
    input[3*i]=pixels[4*i]/255;
    input[3*i+1]=pixels[4*i+1]/255;
    input[3*i+2]=pixels[4*i+2]/255;
  }
  return input;
}
async function segment(image,modelUrl=MODEL_URL) {
  // Caller cannot silently inject an unknown checkpoint without changing SHA.
  const bytes=await verifiedBuffer(modelUrl,MODEL_SHA);
  const session=await ort.InferenceSession.create(bytes,{
    executionProviders:["wasm"],graphOptimizationLevel:"all"
  });
  try{
    const input=new ort.Tensor("float32",canvasPixels(image),[1,256,256,3]);
    const result=await session.run({input_29:input});
    const output=result.Identity;
    if(!output||output.data.length!==256*256*6)
      throw Error("v27 invalid selfie multiclass logits");
    const categories=new Uint8Array(256*256),probability=new Float32Array(256*256);
    const margins=new Float32Array(256*256),counts=new Array(6).fill(0);
    for(let i=0;i<256*256;i++){
      const offset=i*6;
      let max=-Infinity,top=-1,second=-Infinity;
      for(let j=0;j<6;j++){
        const v=output.data[offset+j];
        if(!Number.isFinite(v))throw Error("v27 invalid segmentation logit");
        if(v>max){second=max;max=v;top=j;}
        else if(v>second)second=v;
      }
      let denom=0;
      for(let j=0;j<6;j++)denom+=Math.exp(output.data[offset+j]-max);
      categories[i]=top;
      probability[i]=1/denom;
      margins[i]=(1-Math.exp(second-max))/denom;
      counts[top]++;
    }
    return {categories,probability,margins,counts,
      modelUrl,modelSha256:MODEL_SHA,
      provider:"senty-au/selfie_multiclass_256x256-ONNX",model:"selfie-multiclass-256x256"};
  }finally{
    if(typeof session.release==="function")await session.release();
  }
}
async function pose(image) {
  const bytes=await verifiedBuffer(POSE_MODEL_URL,POSE_SHA);
  const {PoseLandmarker,FilesetResolver}=await import(POSE_JS_URL);
  const wasm=await FilesetResolver.forVisionTasks(POSE_WASM_URL);
  const detector=await PoseLandmarker.createFromOptions(wasm,{
    baseOptions:{modelAssetBuffer:bytes,delegate:"CPU"},
    runningMode:"IMAGE",numPoses:1,
    minPoseDetectionConfidence:0.50,
    minPosePresenceConfidence:0.50
  });
  try{
    const result=detector.detect(image);
    const candidates=result?.landmarks||[];
    if(candidates.length!==1||candidates[0].length<17)
      return {status:"pose_not_found",landmarks:[],provider:"mediapipe-tasks-vision",
        model:"pose_landmarker_lite",modelSha256:POSE_SHA};
    const lm=candidates[0].map(p=>({
      x:+p.x.toFixed(7),y:+p.y.toFixed(7),
      visibility:+(p.visibility??0).toFixed(7),presence:+(p.presence??0).toFixed(7)
    }));
    return {status:"pose_observed",landmarks:lm,
      provider:"mediapipe-tasks-vision",model:"pose_landmarker_lite",
      modelSha256:POSE_SHA};
  }finally{detector.close();}
}
function distSegmentSquared(px,py,a,b,w,h) {
  const ax=a.x*w,ay=a.y*h,bx=b.x*w,by=b.y*h;
  const dx=bx-ax,dy=by-ay,length=dx*dx+dy*dy;
  const t=length?Math.max(0,Math.min(1,((px-ax)*dx+(py-ay)*dy)/length)):0;
  return (px-ax-dx*t)**2+(py-ay-dy*t)**2;
}
function validateEvidence(item,foreground,width,height) {
  const n=width*height;
  if(!Number.isInteger(width)||!Number.isInteger(height)||width<2||height<2
     ||!foreground||foreground.provider!=="browser-u2netp"
     ||foreground.model!=="u2netp"||foreground.probability?.length!==n
     ||foreground.confidence?.length!==n)
    throw Error("v27 invalid/unverified foreground");
  if(!item||item.version!=="browser-structural-evidence-v26"
    ||item.width!==width||item.height!==height
    ||item.provenance?.visibleOutputAuthority!==false
    ||item.provenance?.partAuthority!==false
    ||!Array.isArray(item.segments))throw Error("v27 missing genuine v26 edges");
}
function bindObservations(edges,foreground,multi,poseResult,width,height,options={}) {
  validateEvidence(edges,foreground,width,height);
  const minClassProb=options.minClassProb??0.72;
  const minClassMargin=options.minClassMargin??0.32;
  const minFg=options.minForeground??0.8;
  const minFgConfidence=options.minForegroundConfidence??0.25;
  const minPoseVisibility=options.minPoseVisibility??0.75;
  if([minClassProb,minClassMargin,minFg,minFgConfidence,minPoseVisibility]
    .some(v=>!Number.isFinite(v)||v<0||v>1))
    throw Error("v27 unsupported thresholds");
  const n=width*height,classes=new Uint8Array(n).fill(255),
    valid=new Uint8Array(n),cue=new Uint8Array(n),counts=new Array(6).fill(0);
  const validMulticlass=multi?.categories?.length===256*256
    &&multi.probability?.length===256*256
    &&multi.margins?.length===256*256
    &&multi.modelSha256===MODEL_SHA
    &&multi.provider==="senty-au/selfie_multiclass_256x256-ONNX";
  const arms={"left_arm":[11,13,15],"right_arm":[12,14,16]};
  const tracks={};
  const poseValid=poseResult?.status==="pose_observed"
    &&poseResult.provider==="mediapipe-tasks-vision"
    &&poseResult.modelSha256===POSE_SHA
    &&poseResult.landmarks?.length>=17;
  if(poseValid)for(const [name,ids] of Object.entries(arms)){
    const samples=ids.map(i=>poseResult.landmarks[i]);
    if(samples.every(p=>p&&Number.isFinite(p.x)&&Number.isFinite(p.y)
      &&p.x>=0&&p.x<=1&&p.y>=0&&p.y<=1
      &&p.visibility>=minPoseVisibility&&p.presence>=minPoseVisibility))
      tracks[name]=samples;
  }
  const poseCueCounts={left_arm:0,right_arm:0};
  const cueMap=new Uint8Array(n);
  const radius=options.corridorRadius??Math.max(4,Math.round(width*.025));
  for(let i=0;i<n;i++){
    if(foreground.probability[i]<minFg||
       foreground.confidence[i]<minFgConfidence)continue;
    if(validMulticlass){
      const x=i%width,y=Math.floor(i/width),j=
        Math.min(255,Math.floor(y*256/height))*256+
        Math.min(255,Math.floor(x*256/width));
      const category=multi.categories[j];
      if(category>5)throw Error("v27 unknown multiclass category");
      if(multi.probability[j]>=minClassProb&&multi.margins[j]>=minClassMargin){
        classes[i]=category;valid[i]=1;counts[category]++;
      }
    }
    if(valid[i]!==1||![2,4].includes(classes[i]))continue;
    const px=i%width+.5,py=Math.floor(i/width)+.5;
    for(const [name,points] of Object.entries(tracks)){
      if(distSegmentSquared(px,py,points[0],points[1],width,height)<=radius*radius
      ||distSegmentSquared(px,py,points[1],points[2],width,height)<=radius*radius) {
        cueMap[i]|=name==="left_arm"?1:2;
        poseCueCounts[name]++;
      }
    }
  }
  const segments=edges.segments.map(seg=>{
    let garment=0,hair=0,armLeft=0,armRight=0,unknown=0,skin=0;
    for(const i of seg.pixelIndices){
      if(!Number.isInteger(i)||i<0||i>=n)throw Error("v27 edge outside source");
      if(classes[i]===4)garment++;
      else if(classes[i]===1)hair++;
      else if(classes[i]===2)skin++;
      else unknown++;
      if(cueMap[i]&1)armLeft++;
      if(cueMap[i]&2)armRight++;
    }
    const total=seg.pixelIndices.length;
    // Observations are descriptive only, never final semantic labels.
    const roleCandidates=[];
    if(garment>=8&&garment/total>=0.55)
      roleCandidates.push({role:"clothing_observation",
        evidenceFraction:+(garment/total).toFixed(5),
        provenance:"selfie_multiclass_clothes",
        authority:false,domainCalibrated:false});
    if(armLeft>=8&&armLeft/total>=0.4)
      roleCandidates.push({role:"left_arm_pose_corridor",
        evidenceFraction:+(armLeft/total).toFixed(5),
        provenance:"pose_landmarks+multiclass+foreground",
        authority:false,domainCalibrated:false});
    if(armRight>=8&&armRight/total>=0.4)
      roleCandidates.push({role:"right_arm_pose_corridor",
        evidenceFraction:+(armRight/total).toFixed(5),
        provenance:"pose_landmarks+multiclass+foreground",
        authority:false,domainCalibrated:false});
    return {evidenceId:seg.evidenceId,
      pixelCount:total,semanticPart:"unbound",bindingConfidence:0,
      observedCounts:{garment,hair,skin,unknown,armLeft,armRight},
      roleCandidates};
  });
  const clothes=segments.filter(s=>s.roleCandidates.some(r=>r.role==="clothing_observation")).length;
  const left=segments.filter(s=>s.roleCandidates.some(r=>r.role==="left_arm_pose_corridor")).length;
  const right=segments.filter(s=>s.roleCandidates.some(r=>r.role==="right_arm_pose_corridor")).length;
  return {version:VERSION,width,height,
    decision:"research_part_observations_only",
    provenance:{
      source:"original_rgb+v26_source_edges",
      foregroundProvider:foreground.provider,foregroundModel:foreground.model,
      multiclassProvider:validMulticlass?multi.provider:null,
      multiclassSHA:validMulticlass?MODEL_SHA:null,
      poseProvider:poseValid?poseResult.provider:null,
      poseSHA:poseValid?POSE_SHA:null,
      inferenceOnDevice:true,partOwnershipAuthority:false,
      visibleOutputAuthority:false,generatedPixels:false,
      domainCalibratedForAnime:false
    },
    summary:{sourceEdges:segments.length,unbound:segments.length,
      garmentCueSegments:clothes,leftArmCueSegments:left,rightArmCueSegments:right,
      acceptedClassPixels:counts,poseCuePixels:poseCueCounts,
      usablePoseTracks:Object.keys(tracks),
      animeValidatedPartSegments:0,
      finalSemanticBoundSegments:0,
      garmentsWithIndependentPartCorroboration:0,
      multiclassStatus:validMulticlass?"verified":"unavailable",
      poseStatus:poseValid?Object.keys(tracks).length?"observed":"low_confidence":
        poseResult?.status==="pose_observed"?"withheld_unverified_pose":
          poseResult?.status||"unavailable"},
    segments,categoryMap:classes,armCueMap:cueMap};
}
async function observe(image,foreground,edgeEvidence,width,height,options={}) {
  const failure={reason:null};
  let multi=null,poseResult=null;
  try{multi=await segment(image,options.modelUrl??MODEL_URL);}
  catch(error){failure.multiclass=String(error);}
  try{poseResult=await pose(image);}
  catch(error){failure.pose=String(error);}
  return {...bindObservations(edgeEvidence,foreground,multi,poseResult,width,height,options),
    failures:failure};
}
const api=Object.freeze({VERSION,MODEL_SHA,POSE_SHA,LABELS,segment,pose,
  bindObservations,observe});
globalThis.MinimalizerBrowserPartEvidenceV27=api;
export const MinimalizerBrowserPartEvidenceV27=api;
