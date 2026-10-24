// Local offscreen previews: actual production CSS with env(top)=0 and its 32px
// conservative fallback. The separate CDP test exercises non-zero env() values.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),cache=path.join(root,'.cache/header-settings-preview');
const out=path.join(root,'docs/design/header-settings-dev7-2026-10-24');
for(const [name,folder]of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){
 const dir=path.join(cache,folder);fs.mkdirSync(dir,{recursive:true});app.setPath(name,dir);
}
fs.mkdirSync(out,{recursive:true});app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});setTimeout(()=>app.exit(2),45000).unref();
app.whenReady().then(async()=>{
 let win;const results=[];
 try{
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>cb({cancel:!d.url.startsWith('file:')&&!d.url.startsWith('data:')}));
  win=new BrowserWindow({show:false,width:390,height:844,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true,preload:path.join(root,'tests/fixtures/android-native-preload.cjs')}});
  await win.loadFile(path.join(root,'apps/android/app/src/main/assets/index.html'));
  const ev=code=>win.webContents.executeJavaScript(code);
  const version=fs.readFileSync(path.join(root,'apps/android/app/build.gradle.kts'),'utf8').match(/versionName\s*=\s*"([^"]+)"/)[1];
  await ev(`window.__fixture.reset();document.getElementById('platformLabel').textContent=${JSON.stringify('PRÉVIA · '+version)};const bar=document.createElement('div');bar.setAttribute('aria-hidden','true');bar.style.cssText='position:fixed;inset:0 0 auto;height:32px;z-index:99;pointer-events:none;background:#0b0b0e;color:#f5f5f7;font:600 14px Segoe UI;display:flex;justify-content:space-between;align-items:center;padding:0 18px';bar.innerHTML='<span>09:41</span><span>Wi-Fi · 98%</span>';document.body.append(bar)`);
  const capture=async name=>{await new Promise(r=>setTimeout(r,140));fs.writeFileSync(path.join(out,name+'.png'),(await win.webContents.capturePage()).toPNG());};
  for(const [width,height]of [[390,844],[360,800]]){
   win.setContentSize(width,height);
   await ev(`new Promise(resolve=>requestAnimationFrame(()=>document.querySelector('#brandAsset img').decode().then(resolve)))`);
   for(const tab of ['controls','monitor','gamer']){
    await ev(`document.querySelector('[data-tab="${tab}"]').click()`);
    assert.equal(await ev(`document.querySelector('[role="tab"][aria-selected="true"]').dataset.tab`),tab);
    await capture(`${width}-${tab}-preview`);results.push({width,height,tab,statusBarDemonstrationPx:32});
   }
  }
  await ev(`document.querySelector('[data-tab="controls"]').click();document.querySelector('[data-open="lamp"]').click()`);
  await capture('360-device-panel-preview');await ev(`document.querySelector('#settingsDialog [data-close]').click()`);
  assert.deepEqual(await ev('window.__fixture.snapshot()'),[]);
  fs.writeFileSync(path.join(out,'preview-provenance.json'),JSON.stringify({localPreviewOnly:true,simulatedStatusBar:true,cssEnvTop:0,productionFallbackPx:32,realBridgeCalls:0,deviceAccess:false,results},null,2)+'\n');
  console.log('PASS: six tab previews and device panel; real production CSS fallback, simulated status bar, no native calls.');win.destroy();app.exit(0);
 }catch(e){console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
