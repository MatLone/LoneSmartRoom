'use strict';
// NODE_OPTIONS preload for the owned review profile only. No sensor flags.
const {app,BrowserWindow}=require('electron'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const run=process.env.LONE_WORKBENCH_RUN_ID;
if(!/^[a-f0-9]{32}$/.test(run||'')||!process.argv.includes('--lone-development-review')||process.argv.includes('--lone-monitoring-development'))throw Error('isolated_deadline_review_only');
app.disableHardwareAcceleration();
const root=path.resolve(__dirname,'..'),out=path.join(root,'.cache/windows-workbench-review',run);
const sourceHashes=Object.fromEntries(['desktop-main.cjs','desktop-window.cjs','development-deadline.cjs','monitoring-renderer.js','workbench-renderer.js'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'apps/windows-ui',n))).digest('hex')]));
let phase='dashboard',samples=[],timer=null,started=performance.now(),failure=null;
app.on('browser-window-created',(_event,win)=>win.webContents.once('did-finish-load',()=>{
 const ev=s=>win.webContents.executeJavaScript(s);
 app.getAppMetrics();timer=setInterval(()=>samples.push({elapsed_seconds:(performance.now()-started)/1000,phase,processes:app.getAppMetrics().map(m=>({type:m.type,cpu_percent:m.cpu.percentCPUUsage,rss_mib:m.memory.workingSetSize/1024}))}),1000);
 setTimeout(()=>{phase='widget';void ev("window.loneDesktop.setWindowMode('widget')").catch(()=>failure='widget');},8000);
 setTimeout(()=>{phase='tray';void ev('window.loneDesktop.minimizeToTray()').catch(()=>failure='tray');},16000);
 setTimeout(()=>{phase='restored';app.emit('second-instance');},24000);
 // Deliberately no call to quit here: real main deadline must request closure.
}));
app.on('will-quit',()=>{
 clearInterval(timer);fs.mkdirSync(out,{recursive:true});
 const file=path.join(app.getPath('logs'),'review-deadline.jsonl');
 const events=fs.readFileSync(file,'utf8').trim().split(/\r?\n/).map(JSON.parse);
 const requested=events.find(e=>e.code==='cooperative_exit_requested');
 const report={ok:!failure&&!!requested&&performance.now()-started<120000,elapsed_seconds:(performance.now()-started)/1000,requested_elapsed_ms:requested?.elapsed_ms,
  sourceHashes,realElectron:true,physicalCollectors:false,installedApp:false,profileIsolated:app.getPath('userData').includes(run),normalExit:true,failure,samples,events};
 fs.writeFileSync(path.join(out,'deadline-result.json'),JSON.stringify(report,null,2));
});
