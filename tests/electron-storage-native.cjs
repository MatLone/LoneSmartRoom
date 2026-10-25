'use strict';
const {app,BrowserWindow,session}=require('electron'),path=require('node:path'),fs=require('node:fs'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),id=process.env.LONE_MONITORING_RUN_ID;
const out=path.join(root,'.cache/validation/monitoring-storage-2026-10-25');
if(!/^[a-f0-9]{32}$/.test(id||'')||!process.argv.includes('--lone-monitoring-development')||!process.argv.includes('--lone-development-review')||process.argv.includes('--lone-monitoring-simulated'))throw Error('Explicit storage validation required');
const marker=JSON.parse(fs.readFileSync(path.join(out,'physical-attempt.json'),'utf8'));
if(marker.runId!==id||marker.maximumSeconds!==90)throw Error('Storage authorization marker mismatch');
const model=require('../apps/windows-ui/monitoring-model.js'),start=performance.now(),errors=[],cases=[],views=[],ui=[];
let started=false,timer=null,result={ok:false},network=0;
function save(name,data){const p=path.join(out,name),tmp=p+'.tmp';fs.writeFileSync(tmp,JSON.stringify(data,null,2)+'\n');fs.renameSync(tmp,p);}
const check=(value,label)=>{assert(value,label);cases.push(label);};
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const watchdog=setTimeout(()=>{result.error='validation_deadline';app.quit();},74000);watchdog.unref();
app.on('web-contents-created',(_event,web)=>{
  const send=web.send.bind(web);
  web.send=function(channel,...args){
    if(channel==='monitoring:state')views.push({utc:new Date().toISOString(),elapsed_seconds:(performance.now()-start)/1000,view:structuredClone(args[0])});
    return send(channel,...args);
  };
  web.on('console-message',event=>{if(event.level==='error')errors.push(event.message.slice(0,200));});
  web.on('render-process-gone',(_event,details)=>errors.push(details.reason));
  web.on('did-finish-load',async()=>{
    if(started)return;started=true;const win=BrowserWindow.fromWebContents(web),ev=code=>web.executeJavaScript(code);
    async function until(fn,label,ms=10000){const end=performance.now()+ms;while(performance.now()<end){if(await fn())return;await wait(60);}throw Error(label);}
    function runtime(){
      const diag=require('../apps/windows-ui/desktop-main.cjs').monitoringDiagnostics();
      const electron=app.getAppMetrics().map(m=>m.pid);
      save('runtime-pids.json',{utc:new Date().toISOString(),mainPid:process.pid,
        groups:{electron,collector:diag?.collectorPid?[diag.collectorPid]:[],ipc:diag?.bridgePid?[diag.bridgePid]:[]},diagnostics:diag});
      if(fs.existsSync(path.join(out,'abort-validation.json'))){result.error='agent_preservation_gate_failed';app.quit();}
    }
    async function tab(name){await ev(`document.getElementById('tab-${name}').click()`);await wait(100);}
    async function screenshot(name){const image=await win.capturePage();fs.writeFileSync(path.join(out,name+'.png'),image.toPNG());}
    async function display(label){
      let evidence;
      // A renderer tick and IPC response can straddle the call. Retry comparison only, never collection/relaunch.
      for(let i=0;i<5;i++){
        evidence=await ev(`(async()=>{const view=await window.loneDesktop.getMetrics();return {view,mode:document.getElementById('dashboard').dataset.mode,
          overflow:document.documentElement.scrollWidth>innerWidth+1||document.querySelector('main').scrollWidth>document.querySelector('main').clientWidth+1,
          locked:[...document.querySelectorAll('[data-action],.switch')].every(b=>b.disabled),
          rows:[...document.querySelectorAll('#storageMetrics .metric-row')].map(n=>({id:n.dataset.metricId,text:n.querySelector('strong').textContent,state:n.dataset.availability,title:n.title}))};})()`);
        if(evidence.view.connection==='connected'&&evidence.rows.every(row=>row.text===model.format(evidence.view.snapshot.metrics.find(m=>m.id===row.id))))break;
        await wait(40);
      }
      check(!evidence.overflow&&evidence.locked,'Geometry and blocked actions '+label);
      check(evidence.view.connection==='connected'&&!evidence.view.simulated&&!evidence.view.snapshot.contains_simulated,'Authenticated local provenance '+label);
      const metrics=new Map(evidence.view.snapshot.metrics.map(m=>[m.id,m]));
      check(['cpu.utilization','ram.used','ram.available','storage.c.total','storage.d.total'].every(k=>metrics.get(k)?.valid),'CPU RAM and capacity remain valid '+label);
      check(evidence.rows.every(row=>{const m=metrics.get(row.id);return row.text===model.format(m)&&row.state===m.state&&row.title.includes(m.source)&&row.title.includes(m.unit);}),
        'Values, source, units and validity match IPC '+label);
      check(evidence.rows.filter(row=>!metrics.get(row.id).valid).every(row=>row.text==='—'),'Unavailable is not zero '+label);
      check(evidence.rows.filter(row=>metrics.get(row.id).valid&&metrics.get(row.id).value===0).every(row=>row.text.startsWith('0')),'Valid zero remains numeric '+label);
      ui.push({label,utc:new Date().toISOString(),...evidence});
    }
    try{
      check(app.getPath('userData')===path.join(root,'.cache/windows-monitoring-development',id,'profile'),'Isolated unique development profile');
      check(!app.isPackaged&&path.resolve(app.getAppPath())===path.join(root,'apps/windows-ui'),'Actual source Electron; installed application not used');
      const prefs=web.getLastWebPreferences();check(prefs.contextIsolation&&prefs.sandbox&&!prefs.nodeIntegration,'Actual renderer isolation preserved');
      runtime();timer=setInterval(runtime,1000);
      await until(()=>ev(`window.loneDesktop.getMetrics().then(v=>v.connection==='connected'&&v.snapshot.metrics.some(m=>m.id==='cpu.utilization'&&m.valid))`),'CPU startup failed');
      await until(()=>win.isVisible(),'Visible native window');await tab('monitor');
      // Give PDH initial raw pairs time to warm; do not wait for nonzero activity or generate load.
      while(performance.now()-start<7000)await wait(100);
      await display('dashboard');await screenshot('dashboard-monitor');
      await ev(`document.querySelector('main').scrollTop=document.getElementById('storageMetrics').offsetTop-90`);await wait(100);await screenshot('dashboard-storage');
      await ev(`document.querySelectorAll('#storageMetrics details').forEach(d=>d.open=true)`);await wait(100);await screenshot('dashboard-storage-origin');
      await ev(`document.querySelectorAll('#storageMetrics details').forEach(d=>d.open=false);document.getElementById('widgetToggle').click()`);await wait(200);
      await tab('monitor');await display('widget');await screenshot('widget-monitor');
      await ev(`document.querySelector('main').scrollTop=document.getElementById('storageMetrics').offsetTop-70`);await wait(100);await screenshot('widget-storage-c');
      await ev(`document.querySelector('main').scrollTop=document.querySelector('[data-volume="d"]').offsetTop-70`);await wait(100);await screenshot('widget-storage-d');
      win.setSize(350,680);await wait(100);await display('narrow-widget');await screenshot('widget-narrow');
      await ev(`document.getElementById('widgetToggle').click()`);await wait(200);await tab('monitor');
      while(performance.now()-start<65000)await wait(250);
      await display('dashboard-final');await ev(`document.querySelector('main').scrollTop=document.getElementById('storageMetrics').offsetTop-90`);await wait(100);await screenshot('dashboard-storage-final');
      check(network===0&&errors.length===0,'No HTTP traffic, renderer errors or crash');
      result={ok:true,runId:id,checks:cases.length,cases,networkRequests:network,errors,
        actualElectron:true,simulated:false,profileRelative:path.relative(root,app.getPath('userData')),elapsedBeforeQuitSeconds:(performance.now()-start)/1000};
    }catch(error){result={ok:false,runId:id,error:error.message,checks:cases.length,cases,errors};}
    finally{if(timer)clearInterval(timer);runtime();save('views.json',views);save('ui-verification.json',ui);app.quit();}
  });
});
app.whenReady().then(()=>session.defaultSession.webRequest.onCompleted(d=>{if(/^https?:/.test(d.url))network++;}));
app.on('will-quit',()=>{
  clearTimeout(watchdog);result.transport=require('../apps/windows-ui/desktop-main.cjs').monitoringDiagnostics();
  result.ok=result.ok&&result.transport?.cleanStop===true;result.elapsedSeconds=(performance.now()-start)/1000;
  save('views.json',views);save('electron-result.json',result);
});
