// Development-only NODE_OPTIONS bootstrap: actual package main, preload and UI.
// No fixture replaces the bridge. Never used by the packaged application.
'use strict';
const {app,session}=require('electron');
const path=require('node:path'),fs=require('node:fs'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),scale=process.env.LONE_TEST_SCALE;
if(!['1','1.25','1.5'].includes(scale)||!process.argv.includes('--lone-development-review'))throw new Error('Explicit isolated development review required');
const out=path.join(root,'docs/design/windows-desktop-integration/review',scale.replace('.','_'));fs.mkdirSync(out,{recursive:true});
let checks=0,started=false;const cases=[],errors=[],network=[];
const check=(value,message)=>{assert(value,message);checks++;};
const wait=ms=>new Promise(r=>setTimeout(r,ms));
setTimeout(()=>{console.error('Native test timeout');app.exit(2);},90000).unref();
app.on('browser-window-created',(_event,win)=>{
 if(started)return;started=true;
 win.webContents.on('console-message',event=>{if(event.level==='error')errors.push(event.message);});
 win.webContents.once('did-finish-load',async()=>{
  const ev=code=>win.webContents.executeJavaScript(code);
  async function until(predicate,label){for(let i=0;i<200;i++){if(await predicate())return;await wait(40);}throw new Error('Timed out: '+label);}
  async function snap(name){await ev('document.activeElement?.blur()');await wait(140);fs.writeFileSync(path.join(out,name+'.png'),(await win.webContents.capturePage()).toPNG());}
  async function tab(name){await ev(`document.getElementById('tab-${name}').click()`);await wait(30);}
  async function geometry(label){
   const v=await ev(`(()=>{const main=document.querySelector('main'),nav=document.querySelector('nav').getBoundingClientRect(),bar=document.querySelector('.topbar').getBoundingClientRect();return {width:innerWidth,height:innerHeight,dpr:devicePixelRatio,mode:document.getElementById('dashboard').dataset.mode,selected:document.querySelector('[role="tab"][aria-selected="true"]').dataset.tab,panels:[...document.querySelectorAll('[role="tabpanel"]')].filter(n=>!n.hidden).length,overflow:document.documentElement.scrollWidth>innerWidth+1||main.scrollWidth>main.clientWidth+1,mainHeight:main.clientHeight,navBottom:nav.bottom,barBottom:bar.bottom,actionsDisabled:[...document.querySelectorAll('[data-action],.switch')].every(b=>b.disabled)}})()`);
   check(!v.overflow,'No horizontal overflow '+label);check(v.mainHeight>=100&&v.navBottom<=v.height+1,'Navigation and content fit '+label);check(v.panels===1&&v.actionsDisabled,'Single tab and unavailable actions stay locked');cases.push({label,...v});return v;
  }
  async function panel(id){
   if(id==='lamp')await tab('controls');if(id==='permissions')await tab('gamer');if(id==='sensors')await tab('monitor');
   await ev(`document.querySelector('[data-panel="${id}"]').click()`);
   const v=await ev(`(()=>{const d=document.querySelector('dialog'),r=d.getBoundingClientRect();return {open:d.open,fit:r.left>=0&&r.top>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1,overflow:d.scrollWidth>d.clientWidth+1,disabled:[...d.querySelectorAll('input,select,.button,.switch')].every(n=>n.disabled)}})()`);
   check(v.open&&v.fit&&!v.overflow&&v.disabled,'Native viewport modal '+id);
   await snap('panel-'+id+'-'+(await ev('document.getElementById("dashboard").dataset.mode'))+'-'+(await ev('innerWidth')));
   await ev('document.getElementById("dialogClose").click()');check(await ev('!document.querySelector("dialog").open'),'Modal closes');
  }
  try{
   check(path.resolve(app.getAppPath())===path.join(root,'apps/windows-ui'),'Actual Electron package is running');
   check(app.getVersion()==='2.0.0-dev.3','Actual package version');
   check(app.getPath('userData').startsWith(path.join(root,'.cache/windows-desktop-review')),'Production profile untouched');
   const prefs=win.webContents.getLastWebPreferences();
   console.log('Native webPreferences:',JSON.stringify({contextIsolation:prefs.contextIsolation,sandbox:prefs.sandbox,nodeIntegration:prefs.nodeIntegration,preloadListed:prefs.preload!==undefined,exposedWindowApi:await ev('typeof window.loneDesktop')}));
   check(prefs.contextIsolation&&prefs.sandbox&&!prefs.nodeIntegration,'Actual sandbox and isolation');
   await until(()=>win.isVisible(),'Native window ready');
   await until(()=>ev(`document.getElementById('platformLabel').textContent.includes('2.0.0-dev.3')`),'Native version label');
   await ev('Promise.all([...document.images].map(i=>i.decode()))');
   const metadata=await ev(`({api:Object.keys(window.loneDesktop),node:typeof require,agent:typeof LoneAgent,dpr:devicePixelRatio})`);
   check(metadata.api.length===7&&metadata.node==='undefined'&&metadata.agent==='undefined','Limited real bridge; no agent');
   check(Math.abs(metadata.dpr-Number(scale))<.03,'Per-process DPI factor applied');
   check(await ev(`document.querySelector('h1').textContent.includes('sob controle')`),'Neutral heading');
   check(await ev(`document.getElementById('communicationState').textContent.includes('NÃO INTEGRADA')`),'Separate honest communication state');
   session.defaultSession.webRequest.onCompleted(details=>{if(/^https?:/.test(details.url))network.push(details.url);});
   for(const name of ['controls','monitor','gamer']){await tab(name);await geometry('dashboard-'+name);await snap('dashboard-'+name);}
   for(const id of ['connection','lamp','permissions','sensors','about'])await panel(id);
   await tab('controls');win.focus();
   win.webContents.sendInputEvent({type:'keyDown',keyCode:'Right'});win.webContents.sendInputEvent({type:'keyUp',keyCode:'Right'});
   // Native keyboard delivery depends on focus ownership; deterministic handler
   // coverage is also exercised directly without claiming physical key input.
   await ev(`document.getElementById('tab-controls').focus();document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}))`);
   check(await ev(`document.getElementById('tab-monitor').getAttribute('aria-selected')==='true'`),'Keyboard handler');
   await ev('window.loneDesktop.toggleMaximize()');await until(()=>win.isMaximized(),'Native maximize');check(win.isMaximized(),'Native maximize works');
   await ev('window.loneDesktop.toggleMaximize()');await until(()=>!win.isMaximized(),'Native restore');
   const dashboardBounds=win.getBounds();
   await ev('document.getElementById("widgetToggle").click()');
   await until(()=>ev(`document.getElementById('dashboard').dataset.mode==='widget'&&innerWidth<=500`),'Native widget resize');
   const widgetBounds=win.getBounds();check(widgetBounds.width<=500&&widgetBounds.width>=350&&win.isResizable(),'Native compact window resizable');
   for(const name of ['controls','monitor','gamer']){await tab(name);await geometry('widget-'+name);await snap('widget-'+name);}
   for(const id of ['connection','lamp','permissions','sensors'])await panel(id);
   await ev('window.loneDesktop.toggleMaximize()');check(!win.isMaximized(),'Widget maximization unavailable');
   const rejected=await ev(`window.loneDesktop.setWindowMode('cmd.exe').then(()=>false,()=>true)`);check(rejected,'Invalid visual mode rejected before IPC');
   win.setSize(350,650);await wait(150);
   for(const name of ['controls','monitor','gamer']){await tab(name);await geometry('small-widget-'+name);}
   for(const id of ['connection','lamp','permissions'])await panel(id);
   await tab('controls');await ev(`document.querySelector('main').scrollTop=100000`);await wait(80);
   check(await ev(`(()=>{const m=document.querySelector('main');return m.scrollTop>0&&m.scrollTop+m.clientHeight>=m.scrollHeight-2})()`),'Main scroll reaches bottom in smallest widget');
   await snap('small-widget-controls-bottom');
   await ev('document.getElementById("widgetToggle").click()');await until(()=>ev(`document.getElementById('dashboard').dataset.mode==='dashboard'`),'Restore dashboard mode');
   check(Math.abs(win.getBounds().width-dashboardBounds.width)<=2,'Dashboard native dimensions restored');
   check(await ev(`[...document.querySelectorAll('.sensor .value')].every(n=>n.textContent.startsWith('—'))`),'No fabricated measurements');
   check(await ev(`document.getElementById('grantsCount').textContent==='—'`),'No stale audit grant count used as live state');
   await ev('document.getElementById("minimizeBtn").click()');await until(()=>win.isMinimized(),'Native minimize');check(win.isMinimized(),'Minimize to taskbar');win.restore();await until(()=>!win.isMinimized(),'Restore taskbar window');
   check(network.length===0,'No completed HTTP/HTTPS requests');check(errors.length===0,'No renderer errors');
   const result={ok:true,scale:Number(scale),checks,cases,appVersion:app.getVersion(),actualPackageMain:true,actualPreload:true,appPath:'apps/windows-ui',developmentProfileIsolated:true,offscreen:false,windowVisible:true,dashboardBounds,widgetBounds,metadata,completedHttpRequests:network.length,rendererErrors:errors,windowsSystemScaleChanged:false,actualAppsLaunched:0,grantsChanged:false};
   fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
   console.log(`PASS: native Electron ${scale}x, ${checks} checks, ${cases.length} layouts; real main/preload/window; no agent client.`);
   await ev('document.getElementById("closeBtn").click()');
  }catch(error){console.error(error.stack);app.exit(1);}
 });
});
