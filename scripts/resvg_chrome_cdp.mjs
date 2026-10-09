// Zero-dependency real Chrome DevTools Protocol smoke driver (Node 26).
import {spawn} from "node:child_process";
import {mkdtemp,rm} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
const sleep=(ms)=>new Promise(ok=>setTimeout(ok,ms));
const chrome=process.env.CHROME_PATH ||
  String.raw`C:\Program Files\Google\Chrome\Application\chrome.exe`;
const port=Number(process.env.RESVG_CDP_PORT||"9237");

export async function pageValue(url,expression,timeoutMs=55000) {
 const profile=await mkdtemp(path.join(os.tmpdir(),"minimalizer-resvg-cdp-"));
 let child,ws;const pending=new Map();let index=0;
 async function call(method,params={}) {
   const id=++index;
   return await new Promise((resolve,reject)=>{
     pending.set(id,{resolve,reject});
     ws.send(JSON.stringify({id,method,params}));
   });
 }
 try {
  child=spawn(chrome,["--headless=new","--disable-gpu","--no-sandbox",
    "--no-first-run","--no-default-browser-check","--disable-extensions",
    "--remote-debugging-port="+port,"--user-data-dir="+profile,"about:blank"],
    {stdio:"ignore",windowsHide:true});
  let targets;
  for(let i=0;i<100;i++) {
   try {
     const res=await fetch("http://127.0.0.1:"+port+"/json/list");
     if(res.ok) {
       const list=await res.json();
       targets=list.find(x=>x.type==="page"&&x.webSocketDebuggerUrl);
       if(targets)break;
     }
   } catch {}
   await sleep(150);
  }
  if(!targets)throw new Error("Chrome DevTools socket unavailable");
  ws=new WebSocket(targets.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{
    ws.addEventListener("open",resolve,{once:true});
    ws.addEventListener("error",reject,{once:true});
  });
  ws.addEventListener("message",ev=>{
    const msg=JSON.parse(ev.data);
    if(msg.id && pending.has(msg.id)) {
      const entry=pending.get(msg.id);pending.delete(msg.id);
      msg.error?entry.reject(new Error(msg.error.message)):entry.resolve(msg.result);
    }
  });
  await call("Page.enable");
  await call("Runtime.enable");
  await call("Page.navigate",{url});
  const deadline=Date.now()+timeoutMs;
  let last="pending";
  while(Date.now()<deadline) {
    const ans=await call("Runtime.evaluate",{
      expression,returnByValue:true,awaitPromise:true
    });
    if(ans.exceptionDetails)last=JSON.stringify(ans.exceptionDetails).slice(0,250);
    else {
      last=String(ans.result?.value||"pending");
      if(last.startsWith("RESVG_BROWSER_RESULT=") ||
        last.startsWith("RESVG_ROUTE_RESULT=") ||
        last.startsWith("RESVG_BROWSER_FAILURE=") ||
        last.startsWith("RESVG_ROUTE_FAILURE=") ||
        last.startsWith("CLIPPER2_BROWSER_RESULT=") ||
        last.startsWith("CLIPPER2_ROUTE_RESULT=") ||
        last.startsWith("CLIPPER2_BROWSER_FAILURE=") ||
        last.startsWith("CLIPPER2_ROUTE_FAILURE=") ||
        last.startsWith("VTRACER_BROWSER_RESULT=") ||
        last.startsWith("VTRACER_ROUTE_RESULT=") ||
        last.startsWith("VTRACER_BROWSER_FAILURE=") ||
        last.startsWith("VTRACER_ROUTE_FAILURE=")) return last;
    }
    await sleep(200);
  }
  throw new Error("timed out waiting for real browser: "+last);
 } finally {
  for(const x of pending.values())x.reject(new Error("driver closed"));
  try{ws?.close();}catch{}
  try{child?.kill();}catch{}
  await sleep(400);
  await rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:200}).catch(()=>{});
 }
}
if(process.argv[1]?.endsWith("resvg_chrome_cdp.mjs")) {
 const url=process.argv[2];
 const selector=process.argv[3]||"#result";
 if(!url)throw new Error("usage: node resvg_chrome_cdp.mjs URL '#result'");
 const result=await pageValue(url,"document.querySelector("+JSON.stringify(selector)+")?.textContent");
 console.log(result);
 if(result.includes("_FAILURE="))process.exitCode=1;
}
