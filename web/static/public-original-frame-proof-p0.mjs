/** Stage85: prove DPR1/2 browser pixels equal source bytes; not anatomy or Safari. */
export async function auditOriginalFramePixels({width,height,sourceRgba,sourceSha256,renderedRgba,scale}){
 if(![1,2].includes(scale)||!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000||
 !(sourceRgba instanceof Uint8Array)||sourceRgba.length!==width*height*4||
 !(renderedRgba instanceof Uint8Array)||renderedRgba.length!==sourceRgba.length*scale*scale)throw Error('INVALID_FRAME_PROOF');
 const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',sourceRgba))].map(x=>x.toString(16).padStart(2,'0')).join('');
 if(hash!==sourceSha256)throw Error('ORIGINAL_SOURCE_SHA_MISMATCH');
 let mismatch=0;
 for(let y=0;y<height*scale;y++)for(let x=0;x<width*scale;x++)for(let c=0;c<4;c++)
  if(renderedRgba[4*(y*width*scale+x)+c]!==sourceRgba[4*(Math.floor(y/scale)*width+Math.floor(x/scale))+c])mismatch++;
 return {mismatchedChannels:mismatch,pixelExact:mismatch===0,wholeCharacterGolden:false,
  iphoneSafariVerified:false,paintAuthorized:false,status:'READ_ONLY_BROWSER_SOURCE_PROOF'};
}
