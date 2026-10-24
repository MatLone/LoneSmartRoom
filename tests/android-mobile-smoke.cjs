// Render actual Android assets with explicit fake bridges in an isolated profile.
// No networking, packet sending, device, real agent, program launching or APK install.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const cache=path.join(root,'.cache/android-mobile-tests');
for(const name of ['profile','session','logs','crashes','screens'])fs.mkdirSync(path.join(cache,name),{recursive:true});
for(const [name,folder] of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']])app.setPath(name,path.join(cache,folder));
app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});
setTimeout(()=>app.exit(2),60000).unref();
app.whenReady().then(async()=>{
  let win;const network=[],errors=[];let scenarios=0;const responsive=[];
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>{const ok=d.url.startsWith('file:')||d.url.startsWith('data:');if(!ok)network.push(d.url);cb({cancel:!ok});});
  const evaluate=code=>win.webContents.executeJavaScript(code);
  const check=async(code,expected=true)=>{assert.deepEqual(await evaluate(code),expected,code);scenarios++;};
  const create=async(noNative=false)=>{
    win=new BrowserWindow({show:false,width:390,height:900,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true,
      preload:path.join(__dirname,'fixtures/android-native-preload.cjs'),additionalArguments:noNative?['--fixture-no-native']:[]}});
    win.webContents.on('console-message',e=>{if(e.level==='error')errors.push(e.message);});
    win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
    await win.loadFile(path.join(root,'apps/android/app/src/main/assets/index.html'));
  };
  try{
    await session.defaultSession.clearStorageData(); // Isolated test profile only.
    await create();
    await check(`document.getElementById('platformLabel').textContent`,'Android · Versão 2.0.0-fixture');
    await check(`localStorage.length`,0);
    await check(`[...document.querySelectorAll('[role="tab"]')].map(e=>e.textContent.trim())`,['Controles','Monitoramento PC','Gamer Launcher']);
    await check(`document.querySelector('#brandAsset img').getAttribute('src')`,'brand/logo-horizontal.svg');
    await check(`document.querySelector('#brandAsset img').naturalWidth>0`);
    await evaluate(`document.getElementById('brandAsset').click()`);
    await check(`document.getElementById('brandDialog').open`);
    await check(`[...document.querySelectorAll('#brandDialog img')].every(img=>img.complete&&img.naturalWidth>0)`);
    await check(`document.querySelector('#brandDialog img').getAttribute('src')`,'brand/app-icon.svg');
    await evaluate(`document.querySelector('#brandDialog [data-close]').click()`);
    await check(`[...document.scripts].some(s=>s.src.endsWith('/app.js'))`,false);
    await check(`new Set([...document.querySelectorAll('[id]')].map(n=>n.id)).size===document.querySelectorAll('[id]').length`);
    await evaluate(`localStorage.setItem('lone-wol-settings-v1', JSON.stringify({mac:'AA:BB:CC:DD:EE:FF',broadcast:'192.0.2.255',port:7,extension:'keep'}));localStorage.setItem('unrelated-data','preserve')`);
    await win.reload();await new Promise(resolve=>win.webContents.once('did-finish-load',resolve));
    await check(`document.getElementById('wolMac').value`,'AA:BB:CC:DD:EE:FF');
    await check(`document.getElementById('wolPort').value`,'7');
    await evaluate(`window.__fixture.reset();document.querySelector('[data-open="connection"]').click()`);
    await check(`document.getElementById('connectionDialog').open`);
    await evaluate(`document.getElementById('wolMac').value='11:22:33:44:55:66';document.querySelector('#connectionDialog [data-close]').click()`);
    await new Promise(resolve=>setTimeout(resolve,40)); // Native dialog close event is queued.
    await check(`document.getElementById('wolMac').value`,'AA:BB:CC:DD:EE:FF');
    await check(`JSON.parse(localStorage.getItem('lone-wol-settings-v1')).extension`,'keep');
    await evaluate(`document.getElementById('pcWakeBtn').click();document.getElementById('pcWakeBtn').click()`);
    await check(`window.__fixture.snapshot()`,[{name:'sendWake',args:['AA:BB:CC:DD:EE:FF','192.0.2.255',7]}]);
    await evaluate(`window.onLoneWakeResult({ok:true})`);
    await check(`document.getElementById('agentState').textContent`,'Desconhecido');
    await evaluate(`window.onLoneAgentStatus({state:'connected',last_success:1000,message:'Consulta autenticada de teste'});window.onLoneAppLaunch({kind:'permissions',allowed_apps:[]});window.__fixture.reset()`);
    await check(`document.getElementById('launchSteam').disabled && document.getElementById('launchCs2').disabled`);
    await evaluate(`document.getElementById('launchSteam').dispatchEvent(new MouseEvent('click',{bubbles:true}));document.getElementById('launchCs2').click()`);
    await check(`window.__fixture.snapshot()`,[]);
    await evaluate(`document.getElementById('launchSteam').disabled=false;document.getElementById('launchSteam').click()`);
    await check(`window.__fixture.snapshot()`,[]);
    await evaluate(`window.onLoneAppLaunch({kind:'permissions',allowed_apps:[]});document.getElementById('agentRefresh').click();document.getElementById('agentPair').click();document.getElementById('launchQuery').click()`);
    await check(`window.__fixture.snapshot()`,[{name:'refreshStatus',args:[]},{name:'showPairing',args:[]},{name:'refreshLaunchResult',args:[]}]);
    await evaluate(`window.__fixture.reset()`);
    await evaluate(`document.querySelector('[data-tab="gamer"]').click();window.onLoneAppLaunch({kind:'permissions',allowed_apps:['steam','arbitrary.exe']})`);
    await check(`!document.getElementById('launchSteam').disabled && document.getElementById('launchCs2').disabled`);
    await evaluate(`document.getElementById('launchSteam').click()`);
    await check(`window.__fixture.snapshot()`,[{name:'requestAppLaunch',args:['steam']}]);
    for(const [state,label]of [['requested','Solicitado'],['accepted','Aceito'],['executed','Executado'],['failed','Falha']]){
      await evaluate(`window.onLoneAppLaunch({state:'${state}'})`);
      await check(`document.getElementById('launchState').textContent`,label);
      await check(`document.querySelector('[data-command="${state}"]').classList.contains('active')`);
      if(state==='accepted')await check(`document.getElementById('launchSteam').disabled`);
      if(state==='executed')await check(`document.getElementById('launchDetail').textContent.includes('não confirma')`);
    }
    await evaluate(`window.onLoneAgentStatus({state:'disconnected',last_success:1000,message:'Sem resposta'});window.onLoneAppLaunch({kind:'permissions',allowed_apps:['steam','cs2']});window.__fixture.reset()`);
    await check(`document.getElementById('launchSteam').disabled && document.getElementById('launchCs2').disabled`);
    await check(`document.getElementById('connectionState').textContent`,'Desconectado');
    await check(`document.getElementById('connectionLast').textContent.includes(new Date(1000).toLocaleString('pt-BR'))`);
    await evaluate(`window.onLoneAgentStatus({state:'connected',last_success:1000});`);
    await check(`document.getElementById('launchSteam').disabled && document.getElementById('launchCs2').disabled`);
    await check(`window.__fixture.snapshot()`,[{name:'refreshAppPermissions',args:[]}]);
    await evaluate(`window.onLoneAppLaunch({kind:'permissions',allowed_apps:['cs2']})`);
    await check(`document.getElementById('launchSteam').disabled && !document.getElementById('launchCs2').disabled`);
    await evaluate(`window.onLoneAppLaunch({kind:'permissions',allowed_apps:[]})`);
    await check(`document.querySelectorAll('.sensor-value').length===3 && [...document.querySelectorAll('.sensor-value')].every(e=>e.textContent==='—')`);
    await evaluate(`document.querySelector('[data-tab="controls"]').click();document.querySelector('[data-open="lamp"]').click()`);
    await check(`document.getElementById('settingsDialog').open && document.querySelector('[role="switch"]').disabled`);
    await evaluate(`document.querySelector('#settingsDialog [data-close]').click()`);
    for(const width of [320,360,390,412,800]){
      win.setContentSize(width,900);
      for(const tab of ['controls','monitor','gamer']){
        await evaluate(`document.querySelector('[data-tab="${tab}"]').click()`);
        await check(`(()=>{const m=document.querySelector('main');const p=document.getElementById('panel-${tab}');return document.documentElement.scrollWidth<=innerWidth+1 && m.scrollWidth<=m.clientWidth+1 && p.scrollWidth<=p.clientWidth+1})()`);
        responsive.push({width,tab});
        if(width===390){await new Promise(r=>setTimeout(r,80));fs.writeFileSync(path.join(cache,'screens',tab+'.png'),(await win.webContents.capturePage()).toPNG());}
      }
    }
    await evaluate(`document.querySelector('[data-tab="controls"]').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}))`);
    await check(`document.activeElement.id`,'tab-monitor');
    await check(`localStorage.getItem('unrelated-data')`,'preserve');
    win.destroy();await create(true);
    await check(`document.getElementById('pcWakeBtn').disabled && document.getElementById('launchSteam').disabled && document.getElementById('launchCs2').disabled && document.getElementById('agentPair').disabled`);
    await check(`window.__fixture.snapshot()`,[]);
    assert.deepEqual(network,[]);assert.deepEqual(errors,[]);
    const result={ok:true,scenarios,responsive,externalRequests:0,realBridgeCalls:0,realAppLaunches:0,deviceAccess:false,fixtureDataOnly:true};
    fs.writeFileSync(path.join(cache,'result.json'),JSON.stringify(result,null,2));
    console.log(`PASS: ${scenarios} Android renderer assertions, ${responsive.length} responsive cases; fake bridges only, no external requests.`);
    app.exit(0);
  }catch(error){console.error(error.stack||error);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
