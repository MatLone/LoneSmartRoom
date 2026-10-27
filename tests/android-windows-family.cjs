// Actual Android renderer, offline fixtures only. Never loads Electron production main/preload.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),cache=path.join(root,'.cache/android-windows-family');
const out=path.join(cache,'screens');fs.mkdirSync(out,{recursive:true});
for(const [key,name] of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){
 const dir=path.join(cache,name);fs.mkdirSync(dir,{recursive:true});app.setPath(key,dir);
}
app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});setTimeout(()=>app.exit(2),90000).unref();
app.whenReady().then(async()=>{
 let win;let checks=0;const responsive=[],external=[],errors=[];
 try{
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>{const local=d.url.startsWith('file:')||d.url.startsWith('data:');if(!local)external.push(d.url);cb({cancel:!local});});
  win=new BrowserWindow({show:false,width:390,height:844,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true,backgroundThrottling:false,preload:path.join(root,'tests/fixtures/android-native-preload.cjs')}});
  win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  win.webContents.on('console-message',e=>{if(e.level==='error')errors.push(e.message);});
  await win.loadFile(path.join(root,'apps/android/app/src/main/assets/index.html'));
  win.webContents.setZoomFactor(1);
  const ev=code=>win.webContents.executeJavaScript(code);
  const check=async(code,expected=true)=>{assert.deepEqual(await ev(code),expected,code);checks++;};
  const settle=()=>ev('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');
  win.webContents.debugger.attach('1.3');
  const css=fs.readFileSync(path.join(root,'apps/windows-ui/desktop.css'),'utf8');
  for(const [name,value]of [['--bg','#0b0b0e'],['--surface','#151518'],['--raised','#1e1e23'],['--red','#ff153f'],['--primary','#df0c32']]){
   assert(css.includes(name+':'+value));await check(`getComputedStyle(document.documentElement).getPropertyValue('${name}').trim()` ,value);
  }
  for(const name of ['logo-horizontal.svg','logo-header-small.svg'])assert.deepEqual(fs.readFileSync(path.join(root,'apps/windows-ui/assets/brand',name)),fs.readFileSync(path.join(root,'apps/android/app/src/main/assets/brand',name)));
  await check(`document.querySelector('#panel-controls h1').textContent`,'Seu espaço,sob controle.');
  await check(`document.querySelectorAll('.sensor-value').length`,4);
  await check(`[...document.querySelectorAll('.sensor-value')].every(e=>e.textContent==='Indisponível')`);
  await check(`[...document.querySelectorAll('.metric-row strong')].every(e=>e.textContent==='Indisponível')`);
  await check(`document.querySelectorAll('[role="progressbar"]').length`,0);
  await ev(`window.__fixture.reset()`);
  for(const [width,height]of [[320,740],[360,800],[390,844],[412,915],[600,960],[800,1024],[844,390]]){
   win.setContentSize(width,height);
   for(const inset of [{top:0,bottom:0,left:0,right:0},{top:48,bottom:34,left:0,right:0},{top:24,bottom:24,left:18,right:18}]){
    await win.webContents.debugger.sendCommand('Emulation.setSafeAreaInsetsOverride',{insets:inset});await settle();
    for(const tab of ['controls','monitor','gamer']){
     await ev(`document.querySelector('[data-tab="${tab}"]').click()`);await settle();
     await check(`(()=>{const m=document.querySelector('main'),p=document.querySelector('#panel-${tab}');return document.documentElement.scrollWidth<=innerWidth+1&&m.scrollWidth<=m.clientWidth+1&&p.scrollWidth<=p.clientWidth+1})()`);
     await check(`(()=>{const m=document.querySelector('main'),n=document.querySelector('.navigation');return m.getBoundingClientRect().bottom<=n.getBoundingClientRect().top+1&&n.getBoundingClientRect().bottom<=innerHeight+1&&m.clientHeight>50})()`);
     await check(`(()=>{const e=document.querySelector('.app-header>.icon-button'),r=e.getBoundingClientRect();return r.width>=44&&r.height>=44&&r.top>=${Math.max(32,inset.top)+12}&&r.right<=innerWidth-${inset.right}})()`);
     await check(`parseFloat(getComputedStyle(document.querySelector('.navigation')).paddingBottom)>=${Math.max(8,inset.bottom)}`);
     await ev(`document.querySelector('main').scrollTop=99999`);await settle();
     await check(`(()=>{const m=document.querySelector('main');return m.scrollTop+m.clientHeight>=m.scrollHeight-2})()`);
     responsive.push({width,height,tab,inset});
    }
   }
  }
  win.setContentSize(360,800);
  for(const zoom of [1.25,1.5]){
   win.webContents.setZoomFactor(zoom);await settle();
   for(const tab of ['controls','monitor','gamer']){
    await ev(`document.querySelector('[data-tab="${tab}"]').click()`);await settle();
    const overflow=await ev(`(()=>{const m=document.querySelector('main');return {zoom:${zoom},tab:'${tab}',width:innerWidth,mainWidth:m.clientWidth,scrollWidth:m.scrollWidth,offenders:[...m.querySelectorAll('*')].filter(e=>!e.closest('[hidden]')&&e.getBoundingClientRect().right>m.getBoundingClientRect().right+1).slice(0,8).map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right}))}})()`);
    assert(overflow.scrollWidth<=overflow.mainWidth+1,JSON.stringify(overflow));checks++;
   }
  }
  win.webContents.setZoomFactor(1);win.setContentSize(390,844);
  await win.webContents.debugger.sendCommand('Emulation.setSafeAreaInsetsOverride',{insets:{top:32,bottom:24,left:0,right:0}});
  await ev(`document.querySelector('[data-tab="controls"]').click()`);
  for(const kind of ['connection','lamp','led','fan','tv','permissions','brand']){
   await ev(`document.querySelector('[data-open="${kind}"]').click()`);await settle();
   await check(`(()=>{const p=document.querySelector('dialog[open]'),r=p.getBoundingClientRect();return r.top>=32&&r.bottom<=innerHeight-24&&r.left>=0&&r.right<=innerWidth&&p.scrollWidth<=p.clientWidth+1})()`);
   await ev(`document.querySelector('dialog[open]').scrollTop=99999`);await settle();
   await check(`(()=>{const d=document.querySelector('dialog[open]');return d.scrollTop+d.clientHeight>=d.scrollHeight-2})()`);
   await ev(`document.querySelector('dialog[open]').close()`);await settle();
  }
  await check('window.__fixture.snapshot()',[]);
  for(const state of ['connected','disconnected','unknown']){
   await ev(`window.onLoneAgentStatus({state:'${state}',last_success:1000});window.onLoneAppLaunch({kind:'permissions',allowed_apps:[]})`);
   await check(`document.getElementById('agentState').dataset.state`,state);
   await check(`document.getElementById('launchSteam').disabled&&document.getElementById('launchCs2').disabled`);
  }
  await ev(`window.onLoneAgentStatus({state:'unknown',last_success:0,message:'Aguardando consulta autenticada.'});window.__fixture.reset();document.getElementById('platformLabel').textContent='PRÉVIA LOCAL · Android dev.8';const bar=document.createElement('div');bar.id='fixture-system-bar';bar.setAttribute('aria-hidden','true');bar.style.cssText='position:fixed;inset:0 0 auto;height:32px;z-index:99;background:#0d0d10;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font:11px Segoe UI;color:#c4c4cf;pointer-events:none';bar.innerHTML='<span>09:41</span><span>DEMONSTRAÇÃO · sem dispositivo</span>';document.body.append(bar)`);
  const capture=async name=>{await settle();await new Promise(r=>setTimeout(r,120));fs.writeFileSync(path.join(out,name+'.png'),(await win.webContents.capturePage()).toPNG());};
  for(const [width,height]of [[390,844],[360,800]]){
   win.setContentSize(width,height);
   for(const tab of ['controls','monitor','gamer']){
    await ev(`document.querySelector('[data-tab="${tab}"]').click()`);await capture(`${width}-${tab}`);
    if(width===390){await ev(`document.querySelector('main').scrollTop=99999`);await capture(`${width}-${tab}-bottom`);}
   }
  }
  win.setContentSize(390,844);await ev(`document.querySelector('[data-tab="controls"]').click();document.querySelector('[data-open="connection"]').click()`);await capture('390-connection-panel');
  await ev(`document.querySelector('dialog[open]').close();document.querySelector('[data-open="lamp"]').click()`);await capture('390-device-panel');
  await ev(`document.querySelector('dialog[open]').close();window.onLoneAgentStatus({state:'connected',last_success:1000,message:'DEMONSTRAÇÃO: status simulado, zero grants.'});window.onLoneAppLaunch({kind:'permissions',allowed_apps:[]});document.querySelector('[data-tab="gamer"]').click()`);await capture('390-gamer-zero-grants-demonstration');
  await ev(`document.querySelector('[data-tab="controls"]').click()`);await capture('390-connected-demonstration');
  await ev(`window.onLoneAgentStatus({state:'disconnected',last_success:1000,message:'DEMONSTRAÇÃO: sem resposta; energia não confirmada.'})`);await capture('390-disconnected-demonstration');
  assert.deepEqual(external,[]);assert.deepEqual(errors,[]);
  const result={ok:true,assertions:checks,responsiveCases:responsive.length,responsive,externalRequests:0,realBridgeCalls:0,physicalDeviceAccess:false,previewEngine:'existing Electron Chromium; production Android assets with explicit native fixtures',productionElectronOpened:false,sensorsStarted:false,apkInstalled:false,fixtureStatesClearlyLabeled:true};
  fs.writeFileSync(path.join(cache,'result.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({...result,responsive:undefined}));win.destroy();app.exit(0);
 }catch(e){console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
