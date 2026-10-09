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
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const {parse}=require("./public_r2_owner_geometry.cjs");
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const WASM=resolve(ROOT,"web/static/vendor/resvg-wasm/index_bg.wasm");
export async function render(sourcePath,destinationPath,width=340,component="full",negativeControl=false) {
  if(![340,680].includes(width))throw Error("unapproved output width");
  const input=readFileSync(sourcePath);
  if(input.length>2000000)throw Error("source too large");
  const svg=input.toString("utf8");
  if(!svg.startsWith("<svg ") || !svg.endsWith("</svg>") ||
     !svg.includes("data:image/png;base64,"))
     throw Error("not archived v34 hybrid source SVG");
  if(/<script\b|<foreignObject\b|https?:\/\//i.test(svg.replace(/xmlns="http:\/\/www\.w3\.org\/2000\/svg"/,'').replace(/xmlns:xlink="http:\/\/www\.w3\.org\/1999\/xlink"/,'')))
     throw Error("untrusted active or remote SVG content");
  if(!["full","facet","paths"].includes(component))throw Error("unapproved diagnostic component");
  // Derive fragments only from an already-validated original v34 hybrid source.
  // Component isolation is a diagnostic experiment, never a candidate output.
  // The only permitted adversarial alteration is the exact black test rect,
  // enabled solely by the explicit offline negative-control CLI argument.
  const marker='<rect x="0" y="0" width="340" height="340" fill="#000"/>';
  const canonical=negativeControl?svg.replace(marker+"</svg>","</svg>"):svg;
  if(negativeControl && canonical===svg)throw Error("unrecognized negative control");
  const original=parse(canonical);
  const rawPaths=original.groups.map(g=>g.original).join("");
  const prefix=original.prefix;
  const facet=prefix+original.suffix;
  const imageMarker=/<image [^>]*\/>$/;
  if(!imageMarker.test(prefix))throw Error("cannot isolate signed raster component");
  const pathsOnly=prefix.replace(imageMarker,"")+rawPaths+original.suffix;
  const renderSvg=component==="facet"?facet:component==="paths"?pathsOnly:svg;
  await initWasm(readFileSync(WASM));
  let renderer,output;
  try{
    renderer=new Resvg(renderSvg,{fitTo:width===340?{mode:"original"}:{mode:"width",value:width},font:{loadSystemFonts:false}});
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
            renderer:"@resvg/resvg-wasm@2.6.2",component,notProduction:true};
  } finally {
    if(output?.free)output.free();
    if(renderer?.free)renderer.free();
  }
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const [src,dst,scale,component="full",negativeFlag]=process.argv.slice(2);
  if(!src||!dst||!scale)throw Error("usage: node file.mjs input.svg out.png 340|680");
  if(negativeFlag && negativeFlag!=="--negative-control")
    throw Error("unapproved mode flag");
  const result=await render(src,dst,Number(scale),component,negativeFlag==="--negative-control");
  console.log(JSON.stringify(result));
}
