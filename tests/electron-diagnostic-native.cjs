'use strict';
// Actual development Electron, main/preload/renderer. Fixtures only, no sensors.
const {app,session}=require('electron'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
if(app.isPackaged||!process.argv.includes('--lone-development-review')||!process.argv.includes('--lone-diagnostics-preview')||
   !/^[a-f0-9]{32}$/.test(process.env.LONE_DIAGNOSTICS_REVIEW_ID||''))throw Error('Isolated diagnostic review required');
const root=path.resolve(__dirname,'..'),scale=process.env.LONE_TEST_SCALE||'1';
if(!['1','1.25','1.5'].includes(scale))throw Error('Unsupported review scale');
const out=path.join(root,'.cache/validation/diagnostic-center-2026-10-26/native',scale);fs.mkdirSync(out,{recursive:true});
const cp=require('node:child_process');let childAttempts=0;
for(const name of ['spawn','spawnSync','exec','execSync','execFile','execFileSync','fork'])cp[name]=()=>{childAttempts++;throw Error('External process forbidden in fixture preview');};
let controller,tray,menu,windows=0,checks=0,externalRequests=0;const errors=[],shots=[];
const check=(value,message)=>{assert(value,message);checks++;};
const desktop=require('../apps/windows-ui/desktop-window.cjs'),create=desktop.createController;
desktop.createController=options=>{
  const NativeTray=options.Tray;
  class ReviewTray extends NativeTray{constructor(...args){super(...args);tray=this;}}
  controller=create({...options,Tray:ReviewTray,Menu:{buildFromTemplate:items=>{menu=options.Menu.buildFromTemplate(items);return menu;}}});
  return controller;
};
const receipt={ok:false,scale,source:'actual development Electron main/preload/renderer',simulation:true,
  productionApplicationRun:false,realSensors:false,operationalReaders:false,networkRequests:0};
const save=()=>fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({...receipt,checks,windows,childAttempts,externalRequests,errors,shots},null,2)+'\n');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function until(test,message){for(let i=0;i<100;i++){if(await test())return;await wait(40);}throw Error(message);}
app.once('will-quit',()=>{receipt.closedNormally=true;receipt.trayDestroyed=tray?.isDestroyed()===true;save();});
app.once('quit',()=>{receipt.hostClosed=require('../apps/windows-ui/desktop-main.cjs').diagnosticPreview().closed;save();});
app.on('browser-window-created',(_event,win)=>{
  windows++;
  win.webContents.on('render-process-gone',()=>errors.push('renderer_process_gone'));
  win.webContents.on('console-message',event=>{if(event.level==='error')errors.push('renderer_console_error');});
  win.webContents.once('did-finish-load',()=>void (async()=>{
    const ev=js=>win.webContents.executeJavaScript(js,true);
    const snap=async name=>{
      await until(()=>ev(`document.getElementById('diagnosticCenter').hidden||!document.getElementById('diagnosticScenario').disabled`),'Stable preview controls');
      await wait(80);const image=await win.webContents.capturePage();check(!image.isEmpty(),'Nonempty actual Electron capture');
      fs.writeFileSync(path.join(out,name+'.png'),image.toPNG());shots.push(name+'.png');
    };
    const geometry=async label=>{
      const result=await ev(`(()=>{const c=document.getElementById('diagnosticCenter'),m=document.getElementById('workspace');return {bodyOverflow:document.body.scrollWidth>innerWidth+2,mainOverflow:m.scrollWidth>m.clientWidth+2,centerOverflow:c.scrollWidth>c.clientWidth+2,clipped:[...c.querySelectorAll('button,select,article,p,h2,h3,summary')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&e.scrollWidth>e.clientWidth+2;}).map(e=>e.className||e.tagName)}})()`);
      check(!result.bodyOverflow&&!result.mainOverflow&&!result.centerOverflow&&!result.clipped.length,'No horizontal overflow: '+label+' '+JSON.stringify(result));
    };
    const scenario=async name=>{
      await until(()=>ev(`!document.getElementById('diagnosticScenario').disabled`),'Scenario input ready');
      await ev(`document.getElementById('diagnosticScenario').value=${JSON.stringify(name)};document.getElementById('diagnosticScenario').dispatchEvent(new Event('change',{bubbles:true}))`);
      await until(()=>ev(`document.getElementById('diagnosticGrid').getAttribute('aria-busy')==='false'`),'Scenario rendered');
      check(await ev(`document.getElementById('diagnosticError').hidden`),'Fixture scenario accepted: '+name);
    };
    try{
      check(path.resolve(app.getAppPath())===path.join(root,'apps/windows-ui'),'Actual existing Electron app entry');
      check(app.getPath('userData').includes(path.join('.cache','windows-diagnostics-review',process.env.LONE_DIAGNOSTICS_REVIEW_ID)),'Dedicated isolated profile');
      const prefs=win.webContents.getLastWebPreferences();check(prefs.contextIsolation&&prefs.sandbox&&!prefs.nodeIntegration&&prefs.webSecurity,'Native renderer security');
      check(require('../apps/windows-ui/desktop-main.cjs').monitoringDiagnostics()===null,'No monitoring host created');
      check(require('../apps/windows-ui/desktop-main.cjs').diagnosticPreview().simulation,'Explicit simulation flag');
      const webRequest=session.defaultSession.webRequest,original=webRequest.onBeforeRequest.bind(webRequest);
      // Existing main policy already blocks external traffic; do not replace it.
      webRequest.onCompleted(d=>{if(/^https?:/.test(d.url))externalRequests++;});
      check(typeof original==='function','Existing native resource policy installed');
      // The helper starts with SW_HIDE to avoid a terminal window. Explicitly
      // show this isolated review window after the native startup transition.
      await wait(120);if(!win.isVisible())win.show();
      await until(()=>win.isVisible(),'Development window visible');
      await ev(`window.loneDesktop.setWindowMode('dashboard')`);win.setSize(1440,1000);await wait(120);
      await ev('Promise.all([...document.images].map(i=>i.decode()))');
      check(await ev(`typeof require==='undefined'&&typeof process==='undefined'&&document.querySelectorAll('[role=tab]').length===3`),'No Node in renderer; three tabs');
      for(const tab of ['controls','monitor','gamer']){
        await ev(`document.querySelector('[data-tab="${tab}"]').click()`);
        check(await ev(`!document.getElementById('panel-${tab}').hidden`),'Existing section: '+tab);
      }
      await ev(`document.querySelector('[data-tab="monitor"]').click()`);
      if(scale==='1')await snap('01-monitoramento-entrada');
      await ev(`document.getElementById('diagnosticOpen').click()`);
      await until(()=>ev(`document.querySelectorAll('.diagnostic-card').length===7&&document.getElementById('diagnosticGrid').getAttribute('aria-busy')==='false'`),'Central rendered via preload');
      check(await ev(`!document.getElementById('diagnosticDemo').hidden&&document.getElementById('diagnosticCenter').dataset.simulation==='true'&&[...document.querySelectorAll('.diagnostic-data-tag')].every(e=>e.textContent==='SIMULADO')`),'Simulation obvious on panel and every card');
      await geometry('dashboard');await snap('02-central-dashboard');
      if(scale==='1'){
        await ev(`document.querySelector('[data-card="security"]').scrollIntoView({block:'start'})`);await geometry('security');await snap('02b-seguranca-pendencias');
        await ev(`document.getElementById('diagnosticCenter').scrollIntoView({block:'start'})`);
        await ev(`document.querySelector('.diagnostic-card[data-card="https"] details').open=true;document.getElementById('diagnosticCenter').scrollIntoView({block:'start'})`);
        await geometry('technical details');await snap('03-detalhes-https');
        await ev(`document.querySelector('.diagnostic-card[data-card="https"] details').open=false`);
        const labels=new Set();
        for(const s of require('../apps/windows-ui/diagnostics-model.js').scenarios){
          await scenario(s);const states=await ev(`[...document.querySelectorAll('.diagnostic-status')].map(e=>e.textContent)`);states.forEach(x=>labels.add(x));
          if(['auth-failure','inactive','stale'].includes(s)){await ev(`document.getElementById('diagnosticCenter').scrollIntoView({block:'start'})`);await snap('cenario-'+s);}
        }
        check(['Saudável','Inativo normalmente','Indisponível','Desatualizado','Falha','Não verificado'].every(x=>labels.has(x)),'Six states exercised through actual main/preload');
        receipt.observedLabels=[...labels];
      }
      await scenario('inactive');
      await ev(`document.getElementById('widgetToggle').click()`);
      await until(()=>ev(`document.getElementById('dashboard').dataset.mode==='widget'&&innerWidth<650`),'Native widget mode');
      await ev(`document.getElementById('diagnosticCenter').scrollIntoView({block:'start'})`);await geometry('widget');await snap('04-widget');
      await ev(`document.querySelector('[data-card="monitoring"]').scrollIntoView({block:'start'})`);await geometry('widget card');
      if(scale==='1')await snap('05-widget-inativo');
      if(scale==='1'){await ev(`document.querySelector('[data-card="security"]').scrollIntoView({block:'start'})`);await snap('05b-widget-seguranca');}
      await ev(`document.getElementById('diagnosticPending').scrollIntoView({block:'end'})`);await geometry('widget pending');
      if(scale==='1')await snap('06-widget-pendencias');
      win.setSize(360,800);await wait(150);await ev(`document.getElementById('diagnosticCenter').scrollIntoView({block:'start'})`);
      await geometry('360px widget');if(scale==='1')await snap('07-widget-360');
      await ev(`document.getElementById('diagnosticClose').click()`);
      check(await ev(`document.getElementById('diagnosticCenter').hidden&&document.activeElement.id==='diagnosticOpen'`),'Close returns focus');
      await ev(`document.querySelector('[data-panel="connection"]').click()`);
      check(await ev(`document.getElementById('settingsDialog').open`),'Existing floating settings panel preserved');
      await ev(`document.getElementById('dialogClose').click()`);
      check(await ev(`document.querySelector('[data-action="steam"]').disabled&&document.querySelector('[data-action="cs2"]').disabled`),'Remote application controls remain blocked');
      check(await ev(`document.getElementById('grantsCount').textContent==='—'`),'No invented grants');
      check(menu.items.filter(x=>x.type!=='separator').map(x=>x.label).join('|')==='Abrir dashboard|Modo Widget|Sair','Tray menu preserved without shell interaction');
      check(windows===1&&externalRequests===0&&childAttempts===0&&errors.length===0,'No duplicate windows, HTTP, child collector or renderer error');
      receipt.ok=true;receipt.isolatedProfile=true;receipt.monitoringHostAbsent=true;receipt.version=app.getVersion();
    }catch(error){receipt.failureCode='development_ui_check_failed';receipt.failureMessage=error.message;console.error(error.stack);}
    finally{save();controller?.quit();}
  })());
});
setTimeout(()=>{if(!receipt.closedNormally){receipt.ok=false;receipt.failureCode='review_deadline';save();controller?.quit();}},45000).unref();
