'use strict';
// Actual visible Electron window; sensors are simulated unless explicitly authorized by the outer one-shot runner.
const {app,BrowserWindow,session}=require('electron'),path=require('node:path'),fs=require('node:fs'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),id=process.env.LONE_MONITORING_RUN_ID;
if(!/^[a-f0-9]{32}$/.test(id||'')||!process.argv.includes('--lone-development-review')||!process.argv.includes('--lone-monitoring-development'))throw Error('Isolated monitoring review required');
const simulated=process.argv.includes('--lone-monitoring-simulated'),out=path.join(root,'.cache/validation/monitoring-electron-2026-10-25',simulated?'simulated':'physical');
fs.mkdirSync(out,{recursive:true});const start=performance.now(),errors=[],network=[],cases=[],samples=[];
let started=false,result={ok:false,simulated},monitorTimer=null;
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const check=(value,label)=>{assert(value,label);cases.push(label);};
function save(name,value){const file=path.join(out,name),tmp=file+'.tmp';fs.writeFileSync(tmp,JSON.stringify(value,null,2)+'\n');fs.renameSync(tmp,file);}
const watchdog=setTimeout(()=>{result.error='session_deadline';app.quit();},74000);watchdog.unref();
app.on('web-contents-created',(_event,web)=>{
  web.on('console-message',event=>{if(event.level==='error')errors.push(event.message.slice(0,300));});
  web.on('render-process-gone',(_event,details)=>errors.push(details.reason));
  web.on('did-finish-load',async()=>{
    if(started)return;started=true;const win=BrowserWindow.fromWebContents(web),ev=code=>web.executeJavaScript(code);
    async function until(fn,label,ms=12000){const end=performance.now()+ms;while(performance.now()<end){if(await fn())return;await wait(80);}throw Error(label);}
    async function tab(name){await ev(`document.getElementById('tab-${name}').click()`);await wait(100);}
    async function geometry(label){const v=await ev(`(()=>{const m=document.querySelector('main');return {overflow:document.documentElement.scrollWidth>innerWidth+1||m.scrollWidth>m.clientWidth+1,mode:document.getElementById('dashboard').dataset.mode,width:innerWidth,height:innerHeight,actionsLocked:[...document.querySelectorAll('[data-action],.switch')].every(b=>b.disabled),selected:[...document.querySelectorAll('[role=tabpanel]')].filter(n=>!n.hidden).length}})()`);
      check(!v.overflow&&v.actionsLocked&&v.selected===1,'Geometry and blocked operational controls '+label);return v;}
    async function snap(name){const img=await win.capturePage();fs.writeFileSync(path.join(out,name+'.png'),img.toPNG());}
    function runtime(){
      try{
        const diag=require('../apps/windows-ui/desktop-main.cjs').monitoringDiagnostics();
        const pids=[...new Set([...app.getAppMetrics().map(m=>m.pid),diag?.bridgePid,diag?.collectorPid,diag?.childPid].filter(Number.isSafeInteger))];
        save('runtime-pids.json',{utc:new Date().toISOString(),pids,mainPid:process.pid,diagnostics:diag});
      }catch{errors.push('runtime_metadata_failed');}
    }
    try{
      const wanted=path.join(root,'.cache/windows-monitoring-development',id);
      check(app.getPath('userData')===path.join(wanted,'profile'),'Exact isolated development profile');
      check(!app.isPackaged&&path.resolve(app.getAppPath())===path.join(root,'apps/windows-ui'),'Actual source Electron entry, no installed application');
      const prefs=web.getLastWebPreferences();check(prefs.contextIsolation&&prefs.sandbox&&!prefs.nodeIntegration,'Native sandbox, isolation and Node disabled');
      check(await ev(`typeof window.require==='undefined'&&typeof window.loneDesktop.getMetrics==='function'`),'Narrow actual preload bridge');
      runtime();monitorTimer=setInterval(async()=>{
        runtime();try{const value=await ev('window.loneDesktop.getMetrics()');samples.push({elapsed_seconds:(performance.now()-start)/1000,view:value});}catch{}
      },1000);
      await until(()=>ev(`window.loneDesktop.getMetrics().then(v=>v.connection==='connected'&&v.snapshot.metrics.some(m=>m.id==='cpu.utilization'&&m.valid))`),'Validated CPU sample not received');
      const view=await ev('window.loneDesktop.getMetrics()');check(view.simulated===simulated&&view.snapshot.contains_simulated===simulated,'Real/fixture provenance verified end to end');
      await until(()=>win.isVisible(),'Visible native window');
      await tab('controls');await geometry('dashboard controls');await snap('dashboard-controls');
      await tab('monitor');await geometry('dashboard monitoring');
      check(await ev(`document.querySelector('#sensorGrid .sensor .value').textContent!=='—'`),'Real numeric indicator rendered');
      check(await ev(`document.querySelector('.sensor progress').hidden===false`),'Valid utilization bar rendered');
      check(await ev(`document.querySelectorAll('#sensorGrid .sensor')[1].querySelector('.value').textContent.startsWith('—')`),'GPU remains unavailable');
      await snap('dashboard-monitor');
      await ev(`document.querySelector('main').scrollTop=document.getElementById('storageMetrics').offsetTop-100`);await wait(100);await snap('dashboard-storage');
      await ev(`document.querySelector('main').scrollTop=0;document.querySelector('.metric-meta').open=true`);await wait(100);await snap('dashboard-origin');
      await ev(`document.querySelector('.metric-meta').open=false`);
      if(simulated){
        // Only explicit demonstration frames, sent from this test's main process. No sensor state is forged in the physical session.
        web.send('monitoring:state',{...view,connection:'disconnected',error:'read_unavailable'});
        await wait(30);check(await ev(`document.querySelector('#sensorGrid .sensor .value').textContent==='—'&&document.querySelector('.monitoring-status').textContent.includes('DEMONSTRAÇÃO')`),'Disconnected demonstration clears numbers');
        await snap('demo-disconnected');
        const stale=structuredClone(view);stale.snapshot.metrics.forEach(m=>{m.age_seconds=1000;});web.send('monitoring:state',stale);
        await wait(30);check(await ev(`document.querySelector('#sensorGrid .sensor .value').textContent==='—'`),'Stale demonstration never displayed as zero');
        await snap('demo-stale');
        await until(()=>ev(`document.querySelector('#sensorGrid .sensor .value').textContent!=='—'`),'Live fixture reconnect');
      }
      await tab('gamer');await geometry('gamer launcher');
      await ev(`document.querySelector('[data-panel="permissions"]').click()`);await wait(100);
      check(await ev(`document.querySelector('dialog').open`),'Existing floating panel opens');await snap('permissions-panel');
      await ev(`document.getElementById('dialogClose').click()`);
      await ev(`document.getElementById('widgetToggle').click()`);await wait(200);
      await tab('monitor');await geometry('widget monitor');await snap('widget-monitor');
      await ev(`document.querySelector('main').scrollTop=document.getElementById('storageMetrics').offsetTop-80`);await wait(100);await snap('widget-storage');
      win.setSize(350,680);await wait(150);await geometry('narrow widget');await snap('widget-narrow-storage');
      await ev(`document.getElementById('widgetToggle').click()`);await wait(200);await tab('controls');
      await geometry('restored dashboard');
      if(!simulated){while(performance.now()-start<66000)await wait(500);}
      check(errors.length===0,'No renderer crash or console error');check(network.length===0,'No completed HTTP or HTTPS traffic');
      result={ok:true,simulated,actualElectron:true,checks:cases.length,cases,errors,networkRequests:network.length,
        durationBeforeQuitSeconds:(performance.now()-start)/1000,profileRelative:path.relative(root,app.getPath('userData')),
        screenshots:fs.readdirSync(out).filter(f=>f.endsWith('.png')),windowsVersion:app.getVersion(),operationalActions:0};
    }catch(error){result={ok:false,simulated,checks:cases.length,cases,error:error.message,errors};}
    finally{
      if(monitorTimer)clearInterval(monitorTimer);runtime();save('samples.json',samples);app.quit();
    }
  });
});
app.whenReady().then(()=>session.defaultSession.webRequest.onCompleted(details=>{if(/^https?:/.test(details.url))network.push('unexpected_network');}));
app.on('will-quit',()=>{
  clearTimeout(watchdog);result.runId=id;result.elapsedSeconds=(performance.now()-start)/1000;
  const diagnostics=require('../apps/windows-ui/desktop-main.cjs').monitoringDiagnostics();result.transport=diagnostics;
  result.ok=result.ok&&diagnostics?.cleanStop===true;
  const crypto=require('node:crypto'),files=[];
  for(const directory of ['monitoring','tests/monitoring','apps/windows-ui','scripts','tests']){
    for(const name of fs.readdirSync(path.join(root,directory))){
      const selected=directory==='monitoring'||directory==='tests/monitoring'?name.endsWith('.py'):
        directory==='apps/windows-ui'?/\.(?:cjs|js|css|html|json)$/.test(name)&&name!=='package-lock.json':
        directory==='scripts'?/^monitoring-.*\.py$/.test(name)||['test-monitoring-pipe-isolated.py','preservation_rules.py','test-monitoring-isolated.py','test-monitoring-basic-isolated.py'].includes(name):
        /^electron-monitoring.*\.cjs$/.test(name)||['electron-tray.cjs','electron-window-policy.cjs'].includes(name);
      if(selected)files.push(directory+'/'+name);
    }
  }
  result.sourceHashes=Object.fromEntries(files.sort().map(file=>[file,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex')]));
  save('electron-result.json',result);
});
