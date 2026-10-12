/** Stage91: private offline original-RGBA manual segmentation workspace.
 * This module contains UI source only. Never embed source/private pixels in GitHub.
 * Saving a draft NEVER grants reviewer identity, semantics or product authority.
 */
import {buildFullFrameReviewWorklist} from './public-fullframe-review-p0.mjs';
export const VERSION='p0-stage91-private-offline-human-workspace-v1';
const fail=x=>{throw new TypeError(x)};
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
const sha=async a=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');
/** Render a PRIVATE HTML offline file for real source pixels; never put its bytes in the repo. */
export async function buildPrivateOriginalReviewerHtml(input){
 const q=await buildFullFrameReviewWorklist({...input,tileSize:32});
 if(q.width!==340||q.height!==340||!['GC001','Raden'].includes(q.caseId))fail('PRIVATE_REVIEW_FIXED_ORIGINAL_340_ONLY');
 if(typeof Buffer==='undefined')fail('NODE_PRIVATE_RENDER_ONLY');
 const original=Buffer.from(input.sourceRgba).toString('base64');
 const meta={caseId:q.caseId,width:q.width,height:q.height,
  originalRgbaSha256:q.sourceRgbaSha256,sourcePngSha256:q.sourcePngSha256,
  sourceEligibilitySha256:q.sourceEligibilitySha256,roles,tiles:q.tiles.length,
  originalSourcePixels:q.totalPixels};
 const html=HTML.replace('__PINNED_SOURCE_RGBA_BASE64__',original)
  .replace('__PRIVATE_SOURCE_METADATA__',JSON.stringify(meta).replace(/</g,'\\u003c'));
 return {html,htmlSha256:await sha(new TextEncoder().encode(html)),
  caseId:q.caseId,tiles:q.tiles.length,sourcePixels:q.totalPixels,
  humanPixelsReviewed:0,sourcePixelAltered:false,reviewerIdentityVerified:false,
  semanticGoldenApproved:false,publicDeploymentAllowed:false};
}
const HTML=`<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MinimalizerPublic P0 private full-frame manual review</title>
<style>
body{font:15px system-ui,sans-serif;max-width:980px;margin:12px auto;padding:10px;color:#e9edf2;background:#151920}
h1{font-size:20px}p{font-size:13px;line-height:1.5}.warn{border:1px solid #b39863;padding:9px;color:#ffe0aa}
main{display:grid;grid-template-columns:minmax(0,1fr) 240px;gap:15px}
@media(max-width:720px){main{grid-template-columns:1fr}}
button,select,input{font:inherit;border:1px solid #647080;background:#2e3845;color:#fff;padding:5px;margin:3px}
.controls{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin:8px 0}
#viewer{height:min(60vh,550px);min-height:280px;overflow:auto;background:#252a30;border:1px solid #7c8892}
canvas{display:block;image-rendering:pixelated;touch-action:none;cursor:crosshair}
canvas.pan{touch-action:pan-x pan-y;cursor:grab}input[type=file]{max-width:100%}
#status{font-size:12px;white-space:pre-wrap;color:#a9c3dd}
</style></head><body>
<h1>Original full-frame review: <span id="case"></span></h1>
<p class="warn">PRIVATE / offline: 元画像は変更しない。人の意味判断は一切自動承認されない。元画像にない領域を生成しない。</p>
<main><section>
<div class="controls">操作<select id="mode"><option value="draw">手動ラベル</option><option value="pan">画面スクロール</option></select>
分類<select id="role"></select> ブラシ<select id="brush"><option value="0">1px</option><option value="1">3px</option><option value="2">5px</option></select></div>
<div class="controls">倍率<input id="zoom" type="range" min="1" max="8" value="2"><span id="zoomLabel">2x</span>
<button id="undo">Undo</button><button id="redo">Redo</button><button id="clear">全ラベル消去</button></div>
<div id="viewer"><canvas id="canvas" width="340" height="340"></canvas></div>
<div class="controls">タイル<input id="tileId" type="number" value="0" min="0" max="120" style="width:65px">
<button id="goTile">移動</button> <span id="counter"></span></div>
</section><aside>
<button id="export">未認証ドラフトJSONを保存</button>
<p>同じ元画像のドラフトだけを読込</p><input id="import" type="file" accept="application/json,.json">
<h3>2案の不一致表示</h3><input type="file" id="first" accept=".json">
<input type="file" id="second" accept=".json"><button id="compare">比較</button><button id="clearCompare">比較終了</button>
<p id="reviewComparison">未確認: 人間の独立レビュー証拠なし</p>
<p id="status" role="status"></p><p>人物/背景、腕、手、肌、袖、髪、ネクタイなどを元画像全体から手動確認。保存したJSONは未認証で、製品には反映しない。</p>
</aside></main><script>
const sourceB64='__PINNED_SOURCE_RGBA_BASE64__',meta=__PRIVATE_SOURCE_METADATA__;
const $=id=>document.getElementById(id),N=340*340,canvas=$('canvas'),ctx=canvas.getContext('2d',{willReadFrequently:true});
const raw=Uint8Array.from(atob(sourceB64),x=>x.charCodeAt(0)),labels=new Uint8Array(N);
const roles=meta.roles,history=[],redo=[],paints=['#000000','#9bcbed','#a883d9','#ffe0b2','#e99f8a','#8fbfff','#6bce9a','#ffc46c','#da81ca','#aaa'];
let drawing=false,compareIndices=null,ready=false;
const status=s=>{$('status').textContent=s};
const digest=async a=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');
const src=document.createElement('canvas');src.width=src.height=340;
src.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(raw),340,340),0,0);
function redraw(){ctx.clearRect(0,0,340,340);ctx.drawImage(src,0,0);
 for(let i=0;i<N;i++)if(labels[i]){ctx.fillStyle=paints[labels[i]]+'aa';ctx.fillRect(i%340,Math.floor(i/340),1,1)}
 if(compareIndices){ctx.fillStyle='#fa2222';for(const i of compareIndices)ctx.fillRect(i%340,Math.floor(i/340),1,1)}
 let n=0;for(const v of labels)if(v)n++;$('counter').textContent=n+'px（未認証）'}
function rle(bytes){const out=[];let last=-1;for(const v of bytes){if(v!==last){out.push([v,1]);last=v}else out.at(-1)[1]++}return out}
function decode(runs){if(!Array.isArray(runs)||runs.length<1||runs.length>N)throw Error('RLE_INVALID');const out=new Uint8Array(N);let i=0;
 for(const r of runs){if(!Array.isArray(r)||r.length!==2||!Number.isInteger(r[0])||r[0]<0||r[0]>=roles.length||!Number.isSafeInteger(r[1])||r[1]<1||i+r[1]>N)throw Error('RLE_INVALID');out.fill(r[0],i,i+r[1]);i+=r[1]}
 if(i!==N)throw Error('RLE_LENGTH');for(let j=0;j<N;j++)if(out[j]&&raw[4*j+3]!==255)throw Error('SOURCE_NONOPAQUE_LABEL');return out}
function exportDraft(){return {format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:meta.caseId,dimensions:[340,340],
 sourcePngSha256:meta.sourcePngSha256,sourceRgbaSha256:meta.originalRgbaSha256,
 sourceEligibilitySha256:meta.sourceEligibilitySha256,
 status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',approved:false,paintAuthorized:false,reviewerAuthenticated:false,
 roles:roles.slice(),rle:rle(labels)}}
function validate(d){if(!d||d.format!=='MinimalizerPublic-P0-fullframe-review-draft-v1'||d.caseId!==meta.caseId||
 JSON.stringify(d.dimensions)!=='[340,340]'||d.sourcePngSha256!==meta.sourcePngSha256||
 d.sourceRgbaSha256!==meta.originalRgbaSha256||d.sourceEligibilitySha256!==meta.sourceEligibilitySha256||
 JSON.stringify(d.roles)!==JSON.stringify(roles)||d.approved!==false||d.paintAuthorized!==false||
 d.reviewerAuthenticated!==false||d.status!=='UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL')throw Error('ORIGINAL_OR_TRUST_MISMATCH');
 return decode(d.rle)}
function checkpoint(){history.push(labels.slice());if(history.length>70)history.shift();redo.length=0}
function imported(d){const b=validate(d);checkpoint();labels.set(b);compareIndices=null;redraw();return true}
function comparison(a,b){const A=validate(a),B=validate(b),difference=[];let agree=0,abstain=0;
 for(let i=0;i<N;i++){if(!A[i]||!B[i])abstain++;else if(A[i]===B[i])agree++;else difference.push(i)}
 compareIndices=difference;redraw();$('reviewComparison').textContent='一致 '+agree+'px、相違 '+difference.length+'px、未判定 '+abstain+'px（未認証）';
 return {agree,disagree:difference.length,abstain,independentHumanIdentityVerified:false}}
function xy(e){const r=canvas.getBoundingClientRect();return [Math.floor((e.clientX-r.left)*340/r.width),Math.floor((e.clientY-r.top)*340/r.height)]}
function paint(x,y){const c=Number($('role').value),k=Number($('brush').value);
 for(let yy=Math.max(0,y-k);yy<=Math.min(339,y+k);yy++)for(let xx=Math.max(0,x-k);xx<=Math.min(339,x+k);xx++){
 const i=yy*340+xx;if(raw[4*i+3]===255)labels[i]=c}}
canvas.onpointerdown=e=>{if(!ready||$('mode').value!=='draw')return;e.preventDefault();checkpoint();drawing=true;canvas.setPointerCapture(e.pointerId);paint(...xy(e));redraw()};
canvas.onpointermove=e=>{if(!drawing)return;e.preventDefault();paint(...xy(e));redraw()};
canvas.onpointerup=canvas.onpointercancel=()=>{drawing=false};
$('case').textContent=meta.caseId;roles.forEach((s,i)=>$('role').add(new Option(i+': '+s,i)));$('role').value='5';
$('mode').onchange=()=>canvas.className=$('mode').value==='pan'?'pan':'';
$('zoom').oninput=()=>{const k=Number($('zoom').value);canvas.style.width=340*k+'px';canvas.style.height=340*k+'px';$('zoomLabel').textContent=k+'x'};$('zoom').oninput();
$('undo').onclick=()=>{if(history.length){redo.push(labels.slice());labels.set(history.pop());compareIndices=null;redraw()}};
$('redo').onclick=()=>{if(redo.length){history.push(labels.slice());labels.set(redo.pop());compareIndices=null;redraw()}};
$('clear').onclick=()=>{checkpoint();labels.fill(0);compareIndices=null;redraw()};
$('goTile').onclick=()=>{const n=Number($('tileId').value);if(!Number.isInteger(n)||n<0||n>=121)throw Error('INVALID_TILE');
 const k=Number($('zoom').value);$('viewer').scrollLeft=(n%11)*32*k;$('viewer').scrollTop=Math.floor(n/11)*32*k;status('タイルを表示。目視審査の証明ではない')};
$('export').onclick=()=>{const blob=new Blob([JSON.stringify(exportDraft())],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='PRIVATE_'+meta.caseId+'_UNVERIFIED_FULLFRAME.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
async function file(el){const f=el.files?.[0];if(!f||f.size>5000000)throw Error('FILE_INVALID');return JSON.parse(await f.text())}
$('import').onchange=async()=>{try{imported(await file($('import')));status('一致する元画像の未認証ドラフトを読込')}catch(e){status('読込拒否: '+e.message)}};
$('compare').onclick=async()=>{try{comparison(await file($('first')),await file($('second')))}catch(e){status('比較拒否: '+e.message)}};
$('clearCompare').onclick=()=>{compareIndices=null;redraw()};
window.__privateReview={meta,exportDraft,importDraft:imported,compareDrafts:comparison,counts:()=>({labeled:labels.filter(Boolean).length,undo:history.length}),labelPixel:(x,y,v)=>{if(!ready||!Number.isInteger(x)||!Number.isInteger(y)||x<0||y<0||x>=340||y>=340||!Number.isInteger(v)||v<0||v>=roles.length||raw[(y*340+x)*4+3]!==255)throw Error('BAD_SOURCE_PIXEL_LABEL');checkpoint();labels[y*340+x]=v;redraw()}};
digest(raw).then(h=>{if(h!==meta.originalRgbaSha256)throw Error('PINNED_SOURCE_SHA_MISMATCH');ready=true;redraw();window.__reviewReady=true;status('SHA256検証済。元画像を非公開ローカル表示。ラベルは未認証')}).catch(e=>status('入力検証失敗：'+e.message));
</script></body></html>`;
