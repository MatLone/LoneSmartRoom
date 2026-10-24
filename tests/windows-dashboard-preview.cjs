// Existing Electron runtime, isolated profile, no preload, network or real executors.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const folder=path.join(root,'docs/design/windows-dashboard-preview');
const output=path.join(folder,'review');fs.mkdirSync(output,{recursive:true});
const cache=path.join(root,'.cache/windows-dashboard-preview-test');
for(const [name,sub]of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){const dir=path.join(cache,sub);fs.mkdirSync(dir,{recursive:true});app.setPath(name,dir);}
app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});setTimeout(()=>app.exit(2),60000).unref();
app.whenReady().then(async()=>{
 let win;let assertions=0;const cases=[],requests=[],errors=[];
 const check=(condition,message)=>{assert(condition,message);assertions++;};
 try{
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>{const local=d.url.startsWith('file:')||d.url.startsWith('data:');if(!local)requests.push(d.url);cb({cancel:!local});});
  win=new BrowserWindow({show:false,width:1440,height:1000,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true}});
  win.webContents.on('console-message',event=>{if(event.level==='error'||event.level>=3)errors.push(event.message);});
  await win.loadFile(path.join(folder,'index.html'));
  const ev=code=>win.webContents.executeJavaScript(code);
  await ev('Promise.all([...document.images].map(i=>i.decode()))');
  check(await ev(`!window.require&&!window.process&&!window.LoneAgent&&!window.loneDesktop`),'Preview must have no native or Node bridge');
  check(await ev(`document.querySelector('meta[http-equiv="Content-Security-Policy"]').content.includes("connect-src 'none'")`),'No network capability');
  check(await ev(`!document.querySelector('[src^="http"],[href^="http"]')`),'No remote assets');
  const widths=[[1600,1000],[1440,1000],[1280,800],[1024,768],[800,600],[440,860],[390,844],[350,650]];
  for(const [width,height]of widths){
   win.setContentSize(width,height);await ev('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');
   for(const tab of ['controls','monitor','gamer']){
    await ev(`document.getElementById('tab-${tab}').click()`);
    const m=await ev(`(()=>{const main=document.querySelector('main'),nav=document.querySelector('nav'),r=nav.getBoundingClientRect();return {selected:document.querySelector('[role="tab"][aria-selected="true"]').dataset.tab,overflow:document.documentElement.scrollWidth>innerWidth+1||main.scrollWidth>main.clientWidth+1,scrollable:main.scrollHeight>=main.clientHeight,visiblePanels:[...document.querySelectorAll('[role=tabpanel]')].filter(n=>!n.hidden).length,contentHeight:main.clientHeight,navBottom:r.bottom,viewportHeight:innerHeight,unavailable:[...document.querySelectorAll('[data-action],.switch')].every(n=>n.disabled),mode:document.querySelector('#dashboard').dataset.mode}})()`);
    check(m.selected===tab&&m.visiblePanels===1,'Exactly one selected tab');check(!m.overflow,'No horizontal overflow '+width+'/'+tab);check(m.contentHeight>=120&&m.navBottom<=height+1,'Usable main and visible navigation');check(m.unavailable,'Unavailable controls must stay disabled');
    cases.push({width,height,tab,...m});
    if(width===1440||width===1024||width===390){await new Promise(r=>setTimeout(r,120));fs.writeFileSync(path.join(output,`${width}-${tab}.png`),(await win.webContents.capturePage()).toPNG());}
   }
  }
  win.setContentSize(1440,1000);await ev(`document.getElementById('tab-controls').click()`);
  const panels=['connection','lamp','led','fan','tv','about','wol'];
  for(const id of panels){
   await ev(`document.querySelector('[data-panel="${id}"]').click()`);
   check(await ev('document.querySelector("dialog").open'),'Panel opens '+id);
   const m=await ev(`(()=>{const d=document.querySelector('dialog'),r=d.getBoundingClientRect();return {fits:r.x>=0&&r.y>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1,disabled:[...d.querySelectorAll('input,select,.switch,.button')].every(n=>n.disabled)}})()`);
   check(m.fits&&m.disabled,'Panel fits and operational controls disabled');
   if(id==='lamp'||id==='connection'){await new Promise(r=>setTimeout(r,120));fs.writeFileSync(path.join(output,`1440-panel-${id}.png`),(await win.webContents.capturePage()).toPNG());}
   await ev('document.querySelector("#dialogClose").click()');check(await ev('!document.querySelector("dialog").open'),'Panel closes');
  }
  await ev(`document.getElementById('tab-gamer').click();document.querySelector('[data-panel="permissions"]').click()`);
  check(await ev(`document.querySelector('#dialogBody').textContent.includes('não acompanha alterações posteriores')`),'Audit snapshot must be identified as stale/non-live');
  await new Promise(r=>setTimeout(r,120));fs.writeFileSync(path.join(output,'1440-panel-permissions.png'),(await win.webContents.capturePage()).toPNG());await ev('document.querySelector("#dialogClose").click()');
  await ev(`document.getElementById('tab-monitor').click();document.querySelector('[data-panel="sensors"]').click()`);check(await ev('document.querySelector("dialog").open'),'Sensor plan opens');await ev('document.querySelector("#dialogClose").click()');
  await ev(`document.querySelector('[data-metric="GPU"]').click()`);check(await ev(`document.querySelector('#chartTitle').textContent.endsWith('GPU')`),'Chart selector changes only unavailable metric label');
  check(await ev(`[...document.querySelectorAll('.sensor .value')].every(n=>n.textContent.startsWith('—'))`),'No fabricated sensor values');
  await ev(`document.getElementById('tab-controls').click();document.getElementById('widgetToggle').click()`);
  check(await ev(`document.querySelector('#dashboard').dataset.mode==='widget'`),'Explicit widget composition');
  for(const tab of ['controls','monitor','gamer']){await ev(`document.getElementById('tab-${tab}').click()`);await new Promise(r=>setTimeout(r,120));fs.writeFileSync(path.join(output,`widget-${tab}.png`),(await win.webContents.capturePage()).toPNG());}
  await ev(`document.querySelector('[data-panel="connection"]').click()`);check(await ev(`document.querySelector('dialog').getBoundingClientRect().bottom<=innerHeight`),'Panel fits widget preview');await ev('document.querySelector("#dialogClose").click()');
  await ev(`document.getElementById('widgetToggle').click();document.getElementById('tab-controls').focus();document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}))`);
  check(await ev(`document.querySelector('[aria-selected="true"]').dataset.tab==='monitor'`),'Keyboard navigation');
  const calls=await ev(`(()=>{const calls=[];window.LoneAgent={requestAppLaunch:app=>calls.push(app),refreshStatus:()=>calls.push('status')};for(const b of document.querySelectorAll('[data-action]')){b.disabled=false;b.click();b.disabled=true;}delete window.LoneAgent;return calls;})()`);
  check(calls.length===0,'Even forcibly enabled prototype buttons cannot invoke a native executor');
  const source=fs.readFileSync(path.join(folder,'dashboard.js'),'utf8');
  check(!/\b(?:fetch|XMLHttpRequest|WebSocket|ipcRenderer|exec|spawn|requestAppLaunch|localStorage|sessionStorage)\s*[.(]/.test(source),'No backend, process or production storage code');
  check(requests.length===0,'Zero external/agent requests');check(errors.length===0,'Zero renderer errors');
  const result={ok:true,assertions,responsiveCases:cases.length,cases,errors,externalRequests:requests.length,nativeBridge:false,actualAppsStarted:0,productionProfileAccess:false};
  fs.writeFileSync(path.join(output,'visual-tests.json'),JSON.stringify(result,null,2)+'\n');
  console.log(`PASS: ${assertions} assertions, ${cases.length} responsive tab cases, modal/widget/keyboard checks; no native bridge or external requests.`);win.destroy();app.exit(0);
 }catch(e){console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
