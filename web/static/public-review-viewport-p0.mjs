/** P0 Stage42: offline pixel-exact source inspection geometry.
 * Viewport controls NEVER produce or modify color, masks, labels, or pixels.
 */
export const VERSION='p0-stage42-mobile-source-inspection-viewport-v1';
const fail=code=>{throw new TypeError(code);};
const clamp=(v,lo,hi)=>Math.min(hi,Math.max(lo,v));
const integer=(v)=>Number.isInteger(v)&&v>0&&v<=1600;
const finite=v=>Number.isFinite(v);
export function createSourceViewport({width,height,zoom=1,centerX=width/2,centerY=height/2}){
 if(!integer(width)||!integer(height)||!finite(zoom)||zoom<1||zoom>8||!finite(centerX)||!finite(centerY))fail('INVALID_VIEWPORT');
 const xLimit=width/(2*zoom),yLimit=height/(2*zoom);
 return {width,height,zoom,centerX:clamp(centerX,xLimit,width-xLimit),centerY:clamp(centerY,yLimit,height-yLimit)};
}
export function sourcePointAtFrame(viewport,clientU,clientV){
 if(!viewport||!finite(clientU)||!finite(clientV)||clientU<0||clientU>1||clientV<0||clientV>1)fail('INVALID_POINTER');
 const v=createSourceViewport(viewport);
 return {x:v.centerX+(clientU-.5)*v.width/v.zoom,y:v.centerY+(clientV-.5)*v.height/v.zoom};
}
export function zoomSourceViewport(viewport,zoom,clientU=.5,clientV=.5){
 const v=createSourceViewport(viewport),focus=sourcePointAtFrame(v,clientU,clientV);
 if(!finite(zoom)||zoom<1||zoom>8)fail('INVALID_ZOOM');
 return createSourceViewport({...v,zoom,centerX:focus.x-(clientU-.5)*v.width/zoom,centerY:focus.y-(clientV-.5)*v.height/zoom});
}
export function panSourceViewport(viewport,deltaClientX,deltaClientY,frameWidth,frameHeight){
 const v=createSourceViewport(viewport);
 if(![deltaClientX,deltaClientY,frameWidth,frameHeight].every(finite)||frameWidth<=0||frameHeight<=0)fail('INVALID_PAN');
 return createSourceViewport({...v,centerX:v.centerX-deltaClientX*v.width/(v.zoom*frameWidth),centerY:v.centerY-deltaClientY*v.height/(v.zoom*frameHeight)});
}
export function focusSourceTile(viewport,bbox,padding=1.25){
 const v=createSourceViewport(viewport);
 if(!Array.isArray(bbox)||bbox.length!==4||!bbox.every(finite)||bbox[0]<0||bbox[1]<0||bbox[2]>v.width||bbox[3]>v.height||bbox[2]<=bbox[0]||bbox[3]<=bbox[1]||!finite(padding)||padding<1||padding>3)fail('INVALID_TILE');
 const zoom=clamp(Math.min(v.width/((bbox[2]-bbox[0])*padding),v.height/((bbox[3]-bbox[1])*padding)),1,8);
 return createSourceViewport({...v,zoom,centerX:(bbox[0]+bbox[2])/2,centerY:(bbox[1]+bbox[3])/2});
}
export function viewportCssTransform(v){
 const s=createSourceViewport(v);const px=50-100*s.zoom*s.centerX/s.width,py=50-100*s.zoom*s.centerY/s.height;
 return `translate(${px}%,${py}%) scale(${s.zoom})`;
}
