'use strict';
// Renderer-only review. Explicit simulation, isolated profiles, no production main or native providers.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
// Install the owned-test watchdog before any path/profile work can fail.
const watchdog=setTimeout(()=>app.exit(2),60000);watchdog.unref();
const root=path.resolve(__dirname,'..'),out=path.join(root,'docs/development-night-2026-10-27/captures'),cache=path.join(root,'.cache/night-renderer-review');
for(const [key,sub]of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){const p=path.join(cache,sub);fs.mkdirSync(p,{recursive:true});app.setPath(key,p);}
app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});
app.whenReady().then(async()=>{
 let win;const errors=[],external=[],captures=[];let checks=0;
 try{
  fs.mkdirSync(out,{recursive:true});
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>{const allowed=d.url.startsWith('file:')||d.url.startsWith('data:');if(!allowed)external.push(d.url);cb({cancel:!allowed});});
  const fixture=JSON.parse(fs.readFileSync(path.join(root,'.cache/telemetry-tests/https-frame.json')));
  const snapshot=fixture.snapshot;
  const metricView={v:1,connection:'connected',simulated:true,gpu_enabled:true,snapshot,refreshing:false,gpu_resume_state:'ready',last_valid_at:{}};
  const {createHistory}=require('../apps/windows-ui/performance-history.cjs');let t=Date.parse(snapshot.generated_at);
  const history=createHistory({enabled:true,now:()=>t});
  for(let i=0;i<150;i++){t+=2000;const s=structuredClone(snapshot);s.sequence=i+1;for(const m of s.metrics){m.collected_at=new Date(t).toISOString();if(m.id==='cpu.utilization')m.value=10+i%15;}history.record({...metricView,snapshot:s});}
  const historyReports=Object.fromEntries([5,30,60].map(n=>[n,history.query(n)]));
  const diagnostic=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/diagnostic-evidence.json'))).scenarios.online;
  async function create(width,height,script){
   win=new BrowserWindow({show:false,width,height,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true,backgroundThrottling:false}});
   win.webContents.on('console-message',e=>{if(e.level==='error')errors.push(e.message);});
   await win.loadURL('data:text/html,<meta charset="utf-8">');
   win.webContents.debugger.attach('1.3');await win.webContents.debugger.sendCommand('Page.enable');
   await win.webContents.debugger.sendCommand('Page.addScriptToEvaluateOnNewDocument',{source:script});
  }
  const ev=s=>win.webContents.executeJavaScript(s);
  async function capture(name){console.log('capture',name);await ev('Promise.race([Promise.all([...document.images].map(i=>i.decode().catch(()=>{}))),new Promise(r=>setTimeout(r,500))])');await new Promise(r=>setTimeout(r,100));fs.writeFileSync(path.join(out,name+'.png'),(await win.webContents.capturePage()).toPNG());captures.push(name+'.png');}
  const banner=`(()=>{const b=document.createElement('div');b.textContent='PRÉVIA DE DESENVOLVIMENTO · SIMULAÇÃO EXPLÍCITA · SEM SENSORES REAIS';b.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#33101b;color:#fff;padding:5px;text-align:center;font:10px Segoe UI;pointer-events:none';document.body.append(b)})()`;
  await create(390,844,`let actualModel;Object.defineProperty(window,'loneTelemetry',{get:()=>actualModel,set:m=>actualModel={...m,normalize:(r,o)=>m.normalize(r,{...o,simulation:true})}});const fixture=${JSON.stringify(fixture)};window.LoneAppInfo={getVersionName:()=> '2.0.0-dev.9'};let fixtureSequence=fixture.snapshot.sequence;window.LoneAgent={refreshTelemetry:id=>setTimeout(()=>{const r=structuredClone(fixture);r.snapshot.sequence=++fixtureSequence;r.snapshot.generated_at=new Date().toISOString();for(const m of r.snapshot.metrics){m.collected_at=r.snapshot.generated_at;m.age_seconds=0;}window.onLoneTelemetry({...r,request_id:id,transport_seconds:0});},10),refreshStatus(){},refreshAppPermissions(){},refreshLaunchResult(){}};`);
  console.log('load Android');await win.loadFile(path.join(root,'apps/android/app/src/main/assets/index.html'));console.log('Android loaded');await ev(banner);
  for(const width of [390,360]){
   win.setContentSize(width,width===390?844:800);
   for(const tab of ['controls','monitor','gamer']){
    await ev(`document.getElementById('tab-${tab}').click()`);await new Promise(r=>setTimeout(r,70));
    assert(await ev(`document.documentElement.scrollWidth<=innerWidth+1&&document.querySelector('main').scrollWidth<=document.querySelector('main').clientWidth+1`));checks++;
    await capture('android-'+width+'-'+tab);
   }
  }
  await ev(`document.getElementById('tab-monitor').click()`);await new Promise(r=>setTimeout(r,80));
  assert((await ev(`document.querySelector('[data-telemetry="gpu.adlx.fan_rpm"]').textContent`)).includes('0 RPM'));checks++;
  win.setContentSize(390,844);await ev(`document.querySelector('main').scrollTop=570`);await capture('android-monitor-gpu-details');
  await ev(`document.querySelector('main').scrollTop=1100`);await capture('android-monitor-storage');
  win.destroy();
  await create(1280,900,`let mode='dashboard';window.loneDesktop={getVersion:()=>Promise.resolve('2.0.0-dev.7'),getMetrics:()=>Promise.resolve(${JSON.stringify(metricView)}),onMetrics:()=>()=>{},getPerformanceHistory:n=>Promise.resolve((${JSON.stringify(historyReports)})[n]),getDiagnostics:scenario=>Promise.resolve({v:1,mode:'simulation',scenario,report:${JSON.stringify(diagnostic.report)},evidence:{schema_version:1,simulation:true,security:${JSON.stringify(diagnostic.security)}}}),getWindowState:()=>Promise.resolve({mode,maximized:false,trayAvailable:false,hiddenToTray:false}),setWindowMode:m=>{mode=m;return Promise.resolve({mode,maximized:false,trayAvailable:false});},onWindowState:()=>()=>{},minimize(){},close(){}};`);
  await win.loadFile(path.join(root,'apps/windows-ui/index.html'));await ev(banner);
  await capture('windows-controls');
  await ev(`document.getElementById('tab-monitor').click()`);await new Promise(r=>setTimeout(r,150));await capture('windows-monitor');
  await ev(`document.getElementById('performanceHistory').scrollIntoView({block:'start'})`);await capture('windows-history');
  assert((await ev(`document.querySelectorAll('.history-chart').length`))>0);checks++;
  await ev(`document.getElementById('diagnosticOpen').click()`);await new Promise(r=>setTimeout(r,100));await capture('windows-diagnostics');
  assert((await ev(`document.querySelectorAll('.diagnostic-card').length`))===7);checks++;
  await ev(`document.getElementById('tab-gamer').click()`);await capture('windows-gamer');
  await ev(`document.getElementById('gameSession').scrollIntoView({block:'start'})`);await capture('windows-game-session');
  win.setContentSize(390,800);await ev(`document.getElementById('widgetToggle').click();document.getElementById('tab-monitor').click();document.getElementById('diagnosticClose').click();document.getElementById('workspace').scrollTop=0`);await capture('windows-widget');
  assert(await ev(`document.documentElement.scrollWidth<=innerWidth+1`));checks++;
  assert.deepEqual(external,[]);assert.deepEqual(errors,[]);checks+=2;
  const report={ok:true,checks,captures,engine:'existing Electron Chromium; actual Android and Windows renderers',simulation:true,productionMainLoaded:false,nativeBridges:false,realCollectors:false,externalRequests:external.length,consoleErrors:errors.length};
  fs.writeFileSync(path.join(root,'.cache/night-development/preview-results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));win.destroy();history.close();app.exit(0);
 }catch(e){console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
