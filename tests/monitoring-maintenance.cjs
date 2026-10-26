'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {fixture:hostFixture,snapshot}=require('./electron-monitoring.cjs'),{fixture:windowFixture}=require('./electron-tray.cjs');
const {rendererFixture}=require('./helpers/monitoring-dom.cjs');
const model=require('../apps/windows-ui/monitoring-model.js');let checks=0;const check=(v,n)=>{assert(v,n);checks++;};
async function hostRecovery(){
  const f=hostFixture();f.host.start();f.emit({v:1,event:'ready',bridge_pid:1,collector_pid:2,transport:'windows_named_pipe_v1',simulated:false});
  const first=snapshot();f.emit({v:1,event:'response',body:{ok:true,snapshot:first}});const stamp=f.host.view().last_valid_at['cpu.utilization'];
  const poll=[...f.timers.values()][0];poll();f.advance(2000);poll();
  check(f.host.view().connection==='disconnected'&&f.host.view().error==='read_timeout','Lost IPC times out without claiming connected');
  check(f.child.exitCode===null,'Connection failure does not kill worker/application');
  poll();const recovered=snapshot();recovered.sequence=2;f.emit({v:1,event:'response',body:{ok:true,snapshot:recovered}});
  check(f.host.view().connection==='connected'&&f.host.diagnostics().reconnections===1,'Fresh validated response recovers');
  f.advance(3100);check(f.host.view().snapshot.metrics[0].value===null,'Stale CPU never held as current');
  check(f.host.view().last_valid_at['cpu.utilization']===recovered.metrics[0].collected_at,'Last valid timestamp preserved');
  const forged=snapshot();forged.metrics[0].source='amd.adlx';f.emit({v:1,event:'response',body:{ok:true,snapshot:forged}});
  check(f.host.view().error==='invalid_metrics','GPU addon cannot enter old fixed CPU pipeline');
  f.emit({v:1,event:'response',body:{ok:false,error:'rate_limited'}});check(f.host.view().error==='rate_limited','Rate limits explicit');
  const again=snapshot();again.sequence=3;f.emit({v:1,event:'response',body:{ok:true,snapshot:again}});
  check(f.host.view().connection==='connected','Second recovery after invalid/limited response');
  check(await f.host.stop(),'Owned lifetime still closes cleanly with substitutes');
}
function windowRecovery(){
  const f=windowFixture(),win=f.win;f.controller.setMode('widget');win.setBounds({x:100,y:20,width:390,height:700});f.pending();
  f.controller.minimize();check(win.minimized&&win.visible&&!f.controller.state().hiddenToTray,'Normal minimize remains taskbar minimize');
  f.controller.restoreCurrent();check(f.win===win&&f.windows===1&&!win.minimized,'Same window restored');
  f.controller.setMode('dashboard');f.controller.setMode('widget');check(win.bounds.width===390&&win.bounds.height===700,'Resized widget dimensions persist');
  win.setBounds({x:999999,y:999999,width:390,height:700});f.controller.restoreCurrent();
  check(win.bounds.x<1920&&win.bounds.y<1040,'Offscreen coordinates constrained');
  check(f.saves.every(p=>p.minimizeToTray===false),'Resize/minimize never enables automatic Tray');
  f.controller.quit();check(f.quits===1&&win.destroyed,'Normal exit completes without native UI');
}
function rendererRecovery(){
  const f=rendererFixture(),send=(connection,s,error=null)=>f.send({v:1,connection,simulated:false,snapshot:s,error,last_valid_at:{}});
  const sample=snapshot();sample.metrics[0].value=12;const normalized=model.normalize(sample);
  f.reset();send('connected',normalized);const pushWrites=f.writes();check(pushWrites>0,'Push performs DOM writes');
  f.reset();f.tick();const timerWrites=f.writes();check(timerWrites===0&&f.timers.join()==='1000','Unchanged text is not written again by the age timer');
  f.document.hidden=true;f.document.visibilityState='hidden';f.window.innerWidth=390;f.reset();send('connected',normalized);const hiddenWrites=f.writes();
  check(hiddenWrites===0,'Hidden interface receives state without DOM writes');
  check(f.listeners.has('visibilitychange'),'Visibility restoration updates the interface');
  f.document.hidden=false;f.document.visibilityState='visible';f.listeners.get('visibilitychange')();
  send('disconnected',normalized,'read_timeout');check(f.cards[0].querySelector('.value').textContent==='—','Disconnected hides last number');
  send('connected',normalized);check(f.cards[0].querySelector('.value').textContent==='12%','Reconnect restores validated value');
  f.clock(4000);f.tick();check(f.cards[0].querySelector('.value').textContent==='—'&&f.cards[0].querySelector('small').textContent==='Desatualizada','Age advances without new IPC and marks stale');
  const invalid=snapshot();Object.assign(invalid.metrics[0],{value:null,state:'unavailable',valid:false});send('connected',model.normalize(invalid));
  check(f.cards[0].querySelector('small').textContent==='Indisponível','Recovery with unavailable metric never fabricates zero');
  return {pushWrites,timerWrites,hiddenWrites,method:'DOM setter calls in substitutes, not CPU measurements or Chromium throttling'};
}
(async()=>{await hostRecovery();windowRecovery();const writes=rendererRecovery();const result={ok:true,checks,writes,
  installedAppRun:false,realSensors:false,developmentSourceChanged:true,installedAppChanged:false};const out=path.resolve(__dirname,'../.cache/validation/adlx-preparation-2026-10-25');
  fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'maintenance-tests.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
