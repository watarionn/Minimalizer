/**
 * Research-only MinimalizerPublic P0 Stage6: plain signed source face.
 * Mask is independently historic (Stage04), SHA validated but its semantic
 * completeness is NOT proven here. No eyes, nose, mouth or brows are rendered.
 * Outside-mask eye-like patches can remain, so human Golden is still HOLD.
 */
export const VERSION='public-signed-face-blank-p0-stage6-v1';
const MAX=400*400;
function fail(s){throw new TypeError(s);}
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
async function pinned(a,hash,label){
 if(!typed(a)||typeof hash!=='string'||!/^[a-f0-9]{64}$/.test(hash))fail(label+':invalid_pin');
 if(!globalThis.crypto?.subtle)fail('SHA256_unavailable');
 const out=[...new Uint8Array(await crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');
 if(out!==hash)fail(label+':SHA_mismatch');
}
export async function blankSignedFace({width,height,sourceRgba,sourceRgbaSha256,
 baselineRgba,baselineRgbaSha256,signedFaceMask,signedFaceMaskSha256}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>MAX)fail('invalid_dimensions');
 const n=width*height;
 if(!typed(sourceRgba)||!typed(baselineRgba)||sourceRgba.length!==n*4||baselineRgba.length!==n*4||
 !typed(signedFaceMask)||signedFaceMask.length!==n)fail('invalid_RGBA_or_face');
 await Promise.all([[sourceRgba,sourceRgbaSha256,'source'],[baselineRgba,baselineRgbaSha256,'baseline'],
 [signedFaceMask,signedFaceMaskSha256,'face']].map(args=>pinned(...args)));
 let nFace=0;const skin=[];
 for(let i=0;i<n;i++){
  const v=signedFaceMask[i],o=4*i;
  if(v!==0&&v!==255)fail('nonbinary_face');
  if(!v)continue;
  nFace++;
  if(sourceRgba[o+3]!==255||baselineRgba[o+3]!==255)fail('nonopaque_face_source');
  const r=sourceRgba[o],g=sourceRgba[o+1],b=sourceRgba[o+2];
  if(r>=170&&g>=130&&b>=120&&r>=g&&g>=b-25)skin.push(i);
 }
 if(nFace<25||nFace>n*.24||skin.length<nFace*.40)fail('insufficient_source_skin_evidence');
 const chan=[[],[],[]];for(const i of skin)for(let k=0;k<3;k++)chan[k].push(sourceRgba[i*4+k]);
 const median=chan.map(a=>{a.sort((a,b)=>a-b);return (a[(a.length-1)>>1]+a[a.length>>1])/2;});
 let best=Infinity,j=-1;
 for(const i of skin){const o=i*4;const d=(sourceRgba[o]-median[0])**2+(sourceRgba[o+1]-median[1])**2+(sourceRgba[o+2]-median[2])**2;
  if(d<best){best=d;j=i;}}
 const observedRGB=[sourceRgba[j*4],sourceRgba[j*4+1],sourceRgba[j*4+2]];
 const out=new Uint8ClampedArray(baselineRgba);let changed=0;
 for(let i=0;i<n;i++)if(signedFaceMask[i]){
  const o=i*4;if(out[o]!==observedRGB[0]||out[o+1]!==observedRGB[1]||out[o+2]!==observedRGB[2])changed++;
  out[o]=observedRGB[0];out[o+1]=observedRGB[1];out[o+2]=observedRGB[2];
 }
 for(let i=0;i<n;i++){
  const o=i*4;if(out[o+3]!==baselineRgba[o+3])throw Error('alpha_changed');
  if(!signedFaceMask[i]&&(out[o]!==baselineRgba[o]||out[o+1]!==baselineRgba[o+1]||out[o+2]!==baselineRgba[o+2]))
   throw Error('outside_face_changed');
 }
 return {rgba:out,audit:{version:VERSION,facePixels:nFace,sourceSkinCandidatePixels:skin.length,
  observedFaceRGB:observedRGB,changedPixels:changed,internalFaceColorCount:1,
  internalEyesNoseMouthRendered:false,outsideSignedFaceMicrofeatureSuppressionVerified:false,
  silhouetteFixed:false,semanticGoldenPassed:false,previewOnly:true,productPromotionAuthorized:false}};
}
