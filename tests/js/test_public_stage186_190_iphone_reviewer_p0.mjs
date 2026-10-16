import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const base=new URL('../../web/static/iphone-reviewer/',import.meta.url);
const html=readFileSync(new URL('index.html',base),'utf8');
const js=readFileSync(new URL('review.js',base),'utf8');
const css=readFileSync(new URL('review.css',base),'utf8');
test('186 HTTPS static UI is source-free (no original pixel literals)',()=>{
 assert(!html.includes('sourceB64='));
 assert(!js.includes('sourceB64='));
 assert(js.length<40000&&html.length<15000);
 assert(!html.includes('<img src="data:image'));
});
test('186 source not transferred: CSP forbids connections and external dependencies',()=>{
 assert(html.includes("connect-src 'none'"));
 assert(html.includes("default-src 'none'"));
 assert(!/fetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket\s*\(/.test(js));
 assert(!/https?:\/\//.test(js));
});
test('186 original SHA256 constant pins both GC001 and Raden',()=>{
 assert(js.includes('e5726add97ea1d4745d10acabe83f93195b7f991fa99d7857b5140654aa62b06'));
 assert(js.includes('abbedd28df86789cc100824d1507434b9319e9a1407f95edf2ef5afe4c64e5d5'));
 assert(js.includes("digest('SHA-256',a)"));
});
test('187 reviewer A/B remains separated by per-slot source file',()=>{
 assert(js.includes("['A','B'].includes(d.slot)"));
 assert(js.includes('meta.slot'));
 assert(js.includes('storageKey()'));
});
test('187 image must not be changed in place or generated',()=>{
 assert(js.includes('new ImageData(new Uint8ClampedArray(raw),340,340)'));
 assert(!/img2img|generative.?fill|imagegen|stable.?diffusion/i.test(js));
});
test('188 10 fixed classes with no per-eye/nose/mouth invention',()=>{
 assert(js.includes('uncertain_subject'));
 assert(js.includes('face_proposal'));
 assert(!js.includes('eye_proposal'));
 assert(html.includes('目・口の個別指定は不要'));
});
test('188 touch pointer drawing with stroke interpolation, undo and redo',()=>{
 assert(js.includes('pointerdown'));
 assert(js.includes('pointermove'));
 assert(js.includes('lostpointercapture'));
 assert(js.includes('function line('));
 assert(js.includes('history.push'));
 assert(js.includes('redo.push'));
});
test('188 mobile viewport and finger-friendly buttons',()=>{
 assert(html.includes('width=device-width'));
 assert(css.includes('touch-action:none'));
 assert(css.includes('min-height:42px'));
});
test('189 autosave/recover SHA-pinned, and source file not stored',()=>{
 assert(js.includes('localStorage.setItem(storageKey(),JSON.stringify(currentDraft()))'));
 assert(js.includes('localStorage.getItem(storageKey())'));
 assert(js.includes('meta.originalRgbaSha256'));
 assert(!js.includes('localStorage.setItem(storageKey(),JSON.stringify(raw))'));
});
test('189 share sheet or manual download, no automatic upload',()=>{
 assert(js.includes('navigator.canShare'));
 assert(js.includes('navigator.share'));
 assert(js.includes('URL.createObjectURL(blob)'));
 assert(js.includes("type:'application/json'"));
});
test('190 release remains never-authorized regardless user input',()=>{
 assert(js.includes("approved:false,paintAuthorized:false,reviewerAuthenticated:false"));
 assert(js.includes("status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL'"));
 assert(!js.includes('productReleaseAuthorized:true'));
});
test('190 source and draft reject cross-case, transparent, and malformed RLE',()=>{
 assert(js.includes("d.meta.originalRgbaSha256!==pin[0]"));
 assert(js.includes("d.caseId!==meta.caseId"));
 assert(js.includes('raw[i*4+3]!==255'));
 assert(js.includes("fail('不正なRLE値')"));
});
