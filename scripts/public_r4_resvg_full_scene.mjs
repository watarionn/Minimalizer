/**
 * MinimalizerPublic R4: independent whole-scene SVG -> PNG renderer.
 * Real pinned @resvg/resvg-wasm@2.6.2, no CDNs and no conversion-route hooks.
 * Input original SVG bytes are read-only; output PNG is exclusive-create.
 * Refuses unsupported dimensions or unresolved external images.
 */
import {readFileSync,writeFileSync} from "node:fs";
import {fileURLToPath} from "node:url";
import {dirname,resolve} from "node:path";
import {Resvg,initWasm} from "../web/static/vendor/resvg-wasm/index.mjs";
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const WASM=resolve(ROOT,"web/static/vendor/resvg-wasm/index_bg.wasm");
export async function render(sourcePath,destinationPath,width=340) {
  if(![340,680].includes(width))throw Error("unapproved output width");
  const input=readFileSync(sourcePath);
  if(input.length>2000000)throw Error("source too large");
  const svg=input.toString("utf8");
  if(!svg.startsWith("<svg ") || !svg.endsWith("</svg>") ||
     !svg.includes("data:image/png;base64,"))
     throw Error("not archived v34 hybrid source SVG");
  if(/<script\b|<foreignObject\b|https?:\/\//i.test(svg.replace(/xmlns="http:\/\/www\.w3\.org\/2000\/svg"/,'').replace(/xmlns:xlink="http:\/\/www\.w3\.org\/1999\/xlink"/,'')))
     throw Error("untrusted active or remote SVG content");
  await initWasm(readFileSync(WASM));
  let renderer,output;
  try{
    renderer=new Resvg(svg,{fitTo:width===340?{mode:"original"}:{mode:"width",value:width},font:{loadSystemFonts:false}});
    const images=renderer.imagesToResolve();
    if(images?.length)throw Error("external image unresolved");
    output=renderer.render();
    if(output.width!==width || output.height!==width)
      throw Error("unexpected render dimensions: "+output.width+"x"+output.height);
    const png=Buffer.from(output.asPng());
    if(png.toString("hex",0,8)!=="89504e470d0a1a0a")
      throw Error("invalid resvg output");
    writeFileSync(destinationPath,png,{flag:"wx"});
    return {width:output.width,height:output.height,pngBytes:png.length,
            renderer:"@resvg/resvg-wasm@2.6.2",notProduction:true};
  } finally {
    if(output?.free)output.free();
    if(renderer?.free)renderer.free();
  }
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const [src,dst,scale]=process.argv.slice(2);
  if(!src||!dst||!scale)throw Error("usage: node file.mjs input.svg out.png 340|680");
  const result=await render(src,dst,Number(scale));
  console.log(JSON.stringify(result));
}
