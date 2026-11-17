/* MinimalizerPublic, source-free iPhone reviewer. NO network calls and no image synthesis. */
'use strict';
(() => {
const CASES=Object.freeze({
 GC001:['e5726add97ea1d4745d10acabe83f93195b7f991fa99d7857b5140654aa62b06','75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e','f5dce30d123dcafc443c845a4eee0325a0fbe2553471bc0201da97b8fa9acbc5'],
 Raden:['abbedd28df86789cc100824d1507434b9319e9a1407f95edf2ef5afe4c64e5d5','d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00','a66adf85450833ce36e40369b6be75adffcbdcc34ed49d84abefd612ecc29688']});
const ROLES=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
const PALETTE=['#00000000','#6bbde6','#a476d4','#ffce9d','#f0a083','#6699db','#44a66e','#e3a84b','#c875ad','#858c97'];
const N=340*340,MAX=340*340*4;
const $=id=>document.getElementById(id),cv=$('drawing'),ctx=cv.getContext('2d',{alpha:true});
let meta=null,raw=null,src=null,labels=new Uint8Array(N),originalOpaque=0,mode='draw',zoom=1,history=[],redo=[],active=new Map(),stroke=null,dirty=false,renderPending=false,saveTimer=0,storageOkay=true;
const report=s=>{$('status').textContent=s};
const HEX=a=>Array.from(a,x=>x.toString(16).padStart(2,'0')).join('');
const fail=s=>{throw new Error(s)};
const storageKey=()=>meta?`minimalizer.review.iphone.v1.${meta.slot}.${meta.caseId}.${meta.originalRgbaSha256}`:'';
function toRle(arr){const r=[];let last=-1;for(const b of arr){if(b!==last){r.push([b,1]);last=b;}else r[r.length-1][1]++;}return r;}
function fromRle(r){if(!Array.isArray(r)||r.length===0||r.length>N)fail('不正なRLE');const arr=new Uint8Array(N);let j=0;
 for(const run of r){if(!Array.isArray(run)||run.length!==2||!Number.isInteger(run[0])||run[0]<0||run[0]>=ROLES.length||!Number.isSafeInteger(run[1])||run[1]<1||j+run[1]>N)fail('不正なRLE値');arr.fill(run[0],j,j+run[1]);j+=run[1];}if(j!==N)fail('画素数が不一致');return arr;}
function sourceValid(d){if(!d||d.format!=='MinimalizerPublic-P0-iPhone-source-v1'||!['A','B'].includes(d.slot)||!CASES[d.meta?.caseId]||d.meta.width!==340||d.meta.height!==340||JSON.stringify(d.meta.roles)!==JSON.stringify(ROLES)||typeof d.sourceRgbaBase64!=='string'||d.sourceRgbaBase64.length>650000)fail('専用原画ファイルではありません');
 const pin=CASES[d.meta.caseId];if(d.meta.originalRgbaSha256!==pin[0]||d.meta.sourcePngSha256!==pin[1]||d.meta.sourceEligibilitySha256!==pin[2])fail('既知の元画像SHAと不一致');return d;}
async function digest(a){if(!crypto?.subtle)fail('HTTPSのSafariで開いてください（SHA256不可）');return HEX(new Uint8Array(await crypto.subtle.digest('SHA-256',a)));}
function validateDraft(d){if(!meta||!d||d.format!=='MinimalizerPublic-P0-fullframe-review-draft-v1'||d.caseId!==meta.caseId||JSON.stringify(d.dimensions)!=='[340,340]'||d.sourcePngSha256!==meta.sourcePngSha256||d.sourceRgbaSha256!==meta.originalRgbaSha256||d.sourceEligibilitySha256!==meta.sourceEligibilitySha256||JSON.stringify(d.roles)!==JSON.stringify(ROLES)||d.approved!==false||d.paintAuthorized!==false||d.reviewerAuthenticated!==false||d.status!=='UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL')fail('ケース・元画像・承認状態が不一致');
 const next=fromRle(d.rle);for(let i=0;i<N;i++)if(next[i]&&raw[i*4+3]!==255)fail('透明画素に分類を設定できません');return next;}
function currentDraft(){if(!meta)fail('元画像未読み込み');return {format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:meta.caseId,dimensions:[340,340],sourcePngSha256:meta.sourcePngSha256,sourceRgbaSha256:meta.originalRgbaSha256,sourceEligibilitySha256:meta.sourceEligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles:ROLES.slice(),rle:toRle(labels)};}
function render(){renderPending=false;if(!src)return;ctx.clearRect(0,0,340,340);ctx.drawImage(src,0,0);for(let i=0;i<N;i++)if(labels[i]){ctx.fillStyle=PALETTE[labels[i]]+'af';ctx.fillRect(i%340,(i/340)|0,1,1);}const marked=labels.reduce((n,v)=>n+(v!==0),0),unknown=labels.reduce((n,v)=>n+(v===9),0);
 $('progress').textContent=`${marked.toLocaleString()}/${originalOpaque.toLocaleString()} px 分類済 ／ 保留 ${unknown.toLocaleString()} px`;}
function requestRender(){if(!renderPending){renderPending=true;requestAnimationFrame(render);}}
function snapshot(){history.push(labels.slice());if(history.length>60)history.shift();redo.length=0;}
function autosave(){if(!meta)return;clearTimeout(saveTimer);try{localStorage.setItem(storageKey(),JSON.stringify(currentDraft()));dirty=false;storageOkay=true;report('端末内に途中保存済み。作業終了時は必ずJSONも保存してね。');}
 catch(e){storageOkay=false;report('このSafariでは端末内保存に失敗しました。JSONを「ファイル」に保存してね（'+e.name+'）。');}}
function scheduleSave(){dirty=true;clearTimeout(saveTimer);saveTimer=setTimeout(autosave,650);}
function editPixel(x,y){let r=Number($('brush').value),v=Number($('role').value);for(let yy=Math.max(0,y-r);yy<=Math.min(339,y+r);yy++)for(let xx=Math.max(0,x-r);xx<=Math.min(339,x+r);xx++){const i=yy*340+xx;if(raw[4*i+3]===255)labels[i]=v;}}
function line(a,b){let x0=a[0],y0=a[1],x1=b[0],y1=b[1],dx=Math.abs(x1-x0),dy=-Math.abs(y1-y0),sx=x0<x1?1:-1,sy=y0<y1?1:-1,err=dx+dy;while(true){editPixel(x0,y0);if(x0===x1&&y0===y1)break;const twice=2*err;if(twice>=dy){err+=dy;x0+=sx;}if(twice<=dx){err+=dx;y0+=sy;}}requestRender();scheduleSave();}
function xy(e){const b=cv.getBoundingClientRect();return [Math.min(339,Math.max(0,Math.floor((e.clientX-b.left)*340/b.width))),Math.min(339,Math.max(0,Math.floor((e.clientY-b.top)*340/b.height)))];}
function setMode(v){mode=v;active.clear();stroke=null;$('drawMode').classList.toggle('selected',v==='draw');$('panMode').classList.toggle('selected',v==='pan');$('drawMode').setAttribute('aria-pressed',String(v==='draw'));$('panMode').setAttribute('aria-pressed',String(v==='pan'));}
function setZoom(z){zoom=Math.max(1,Math.min(8,Number(z)||1));$('zoom').value=String(zoom);$('zoomLabel').textContent=zoom+'×';cv.style.width=340*zoom+'px';cv.style.height=340*zoom+'px';}
async function importSource(file){if(!file||file.size>850000)fail('原画JSONが大きすぎます');const d=sourceValid(JSON.parse(await file.text()));
 const byteString=atob(d.sourceRgbaBase64);if(byteString.length!==MAX)fail('原画ピクセルサイズ不一致');const rgb=Uint8Array.from(byteString,x=>x.charCodeAt(0));if(await digest(rgb)!==d.meta.originalRgbaSha256)fail('元画像SHA256検証失敗');
 if(d.meta.caseId==='GC001'&&d.meta.originalRgbaSha256!==CASES.GC001[0])fail('元画像不一致');
 meta={...d.meta,slot:d.slot};raw=rgb;src=document.createElement('canvas');src.width=src.height=340;src.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(raw),340,340),0,0);
 originalOpaque=0;for(let i=0;i<N;i++)if(raw[4*i+3]===255)originalOpaque++;
 labels=new Uint8Array(N);history=[];redo=[];active.clear();stroke=null;setMode('draw');setZoom(1);$('viewer').scrollTop=0;$('viewer').scrollLeft=0;$('loadedCase').textContent=`${meta.slot} / ${meta.caseId}`;
 let recovered=false;try{const backup=localStorage.getItem(storageKey());if(backup){labels=validateDraft(JSON.parse(backup));recovered=true;}}catch(e){storageOkay=false;report('途中保存の読み込みに失敗。バックアップJSONを使用してね。');}
 $('workspace').hidden=false;render();report(recovered?'元画像SHA256 OK。前回の端末内作業を復元したよ。':'元画像SHA256 OK。塗り分けを開始してね。原画はサーバーへ送信しません。');
 window.__reviewReady=true;return {caseId:meta.caseId,slot:meta.slot,recovered};}
function shareFile(){const name=`${meta.slot}_${meta.caseId}_review.json`,blob=new Blob([JSON.stringify(currentDraft())],{type:'application/json'}),file=new File([blob],name,{type:'application/json'});return {name,blob,file};}
function download(){if(!meta)return;autosave();const {blob,name}=shareFile(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),8000);report(name+' をダウンロード。iPhoneの「ファイル」アプリで保存先を確認してね。');}
async function share(){if(!meta)return;autosave();const {file,name}=shareFile();if(navigator.share&&navigator.canShare?.({files:[file]})){try{await navigator.share({files:[file]});report('共有画面から「ファイルに保存」を選択したか確認してね。ファイル名: '+name);return;}catch(e){if(e.name==='AbortError'){report('共有をキャンセルしたよ。JSONの保存は未確認。');return;}report('共有エラー。ダウンロードで保存してね: '+e.message);return;}}
 download();}
function importDraft(d){const next=validateDraft(d);snapshot();labels=next;requestRender();autosave();report('同じ元画像の途中JSONを復元しました。');}
function pointerStart(e){if(!raw)return;if(e.pointerType==='mouse'&&e.button!==0)return;e.preventDefault();cv.setPointerCapture?.(e.pointerId);active.set(e.pointerId,[e.clientX,e.clientY]);if(active.size>1){stroke=null;return;}if(mode==='draw'){snapshot();stroke={id:e.pointerId,last:xy(e)};editPixel(...stroke.last);requestRender();scheduleSave();}}
function pointerMove(e){if(!active.has(e.pointerId))return;e.preventDefault();const prior=active.get(e.pointerId),now=[e.clientX,e.clientY];active.set(e.pointerId,now);
 if(active.size===2){const pts=[...active.values()],before=[pts[0],pts[1]],centerX=(pts[0][0]+pts[1][0])/2,centerY=(pts[0][1]+pts[1][1])/2;
 // Two-finger pan avoids painting; zoom is controllable through the large on-screen slider.
 $('viewer').scrollLeft-=now[0]-prior[0];$('viewer').scrollTop-=now[1]-prior[1];return;}
 if(mode==='pan'){$('viewer').scrollLeft-=now[0]-prior[0];$('viewer').scrollTop-=now[1]-prior[1];return;}
 if(!stroke||stroke.id!==e.pointerId)return;const target=xy(e);line(stroke.last,target);stroke.last=target;}
function pointerEnd(e){if(!active.has(e.pointerId))return;active.delete(e.pointerId);if(stroke?.id===e.pointerId){stroke=null;autosave();}if(active.size>0)stroke=null;}
$('sourceFile').addEventListener('change',async e=>{try{await importSource(e.target.files[0]);$('security').textContent='SHA256検証済（画像データはこのiPhone内だけで処理）';}catch(err){report('原画ファイル読込失敗：'+err.message);}e.target.value='';});
$('draftFile').addEventListener('change',async e=>{try{const file=e.target.files[0];if(!file||file.size>5e6)fail('ファイルサイズが不正');importDraft(JSON.parse(await file.text()));}catch(err){report('ドラフト読込拒否：'+err.message);}e.target.value='';});
$('drawMode').onclick=()=>setMode('draw');$('panMode').onclick=()=>setMode('pan');$('zoom').oninput=e=>setZoom(e.target.value);
$('undo').onclick=()=>{if(!history.length)return;redo.push(labels.slice());labels=history.pop();requestRender();scheduleSave();};$('redo').onclick=()=>{if(!redo.length)return;history.push(labels.slice());labels=redo.pop();requestRender();scheduleSave();};
$('saveLocal').onclick=autosave;$('shareDraft').onclick=share;$('downloadDraft').onclick=download;
$('clear').onclick=()=>{if(!confirm('この原画の塗り分けをすべて消す？取り消しは「戻す」でできるよ。'))return;snapshot();labels.fill(0);requestRender();autosave();};
$('jump').onclick=()=>{if(!meta)return;const n=Number($('tile').value);if(!Number.isInteger(n)||n<0||n>120){report('タイル番号は0〜120');return;}$('viewer').scrollLeft=(n%11)*32*zoom;$('viewer').scrollTop=Math.floor(n/11)*32*zoom;};
$('nextTile').onclick=()=>{$('tile').value=String((Number($('tile').value)+1)%121);$('jump').click();};
cv.addEventListener('pointerdown',pointerStart);cv.addEventListener('pointermove',pointerMove);cv.addEventListener('pointerup',pointerEnd);cv.addEventListener('pointercancel',pointerEnd);cv.addEventListener('lostpointercapture',pointerEnd);
window.addEventListener('pagehide',()=>{if(dirty)autosave();});
window.__reviewTest={importSource,importDraft,currentDraft,sourceValid,validateDraft,getLabels:()=>labels.slice(),getMeta:()=>meta};
})();
