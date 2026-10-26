// Static diagnostic document only. No app main/preload, native clients or sensors.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),cache=path.join(root,'.cache/diagnostics-review');
for(const [key,name]of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){
 const dir=path.join(cache,name);fs.mkdirSync(dir,{recursive:true});app.setPath(key,dir);
}
app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
setTimeout(()=>app.exit(2),30000).unref();
app.whenReady().then(async()=>{
 let window;
 try{
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>cb({cancel:!d.url.startsWith('file:')}));
  window=new BrowserWindow({show:false,width:1280,height:1450,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true}});
  const out=path.join(root,'docs/diagnostics-adapters-2026-10-26');
  await window.loadFile(path.join(out,'review.html'));
  await new Promise(r=>setTimeout(r,120));
  fs.writeFileSync(path.join(out,'SIMULATED-review.png'),(await window.webContents.capturePage()).toPNG());
  window.destroy();console.log('PASS: static, labeled simulated diagnostic preview; no operational app.');app.exit(0);
 }catch(e){console.error(e.message);if(window&&!window.isDestroyed())window.destroy();app.exit(1);}
});
