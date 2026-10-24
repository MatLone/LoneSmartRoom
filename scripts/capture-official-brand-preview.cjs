// Real rendering of the integrated WebView assets with isolated test bridges.
// This is a LOCAL PREVIEW, never a Samsung screenshot or a real agent session.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),cache=path.join(root,'.cache/official-brand-preview');
const out=path.join(root,'docs/design/brand/official-board-2026-10-24/review');
for(const [name,folder]of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){
 const dir=path.join(cache,folder);fs.mkdirSync(dir,{recursive:true});app.setPath(name,dir);
}
fs.mkdirSync(out,{recursive:true});app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});setTimeout(()=>app.exit(2),60000).unref();
app.whenReady().then(async()=>{
 let win;const measurements=[];
 try{
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>cb({cancel:!d.url.startsWith('file:')&&!d.url.startsWith('data:')}));
  win=new BrowserWindow({show:false,width:390,height:844,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true,
   preload:path.join(root,'tests/fixtures/android-native-preload.cjs')}});
  await win.loadFile(path.join(root,'apps/android/app/src/main/assets/index.html'));
  const ev=source=>win.webContents.executeJavaScript(source);
  await ev(`document.getElementById('platformLabel').textContent='PRÉVIA LOCAL · 2.0.0-dev.5';window.onLoneAppLaunch({kind:'permissions',allowed_apps:[]});window.__fixture.reset()`);
  for(const [width,height]of [[390,844],[360,800]]){
   win.setContentSize(width,height);
   await ev(`new Promise(resolve=>requestAnimationFrame(()=>document.querySelector('#brandAsset img').decode().then(resolve)))`);
   for(const tab of ['controls','monitor','gamer']){
    await ev(`document.querySelector('[data-tab="${tab}"]').click()`);
    await new Promise(r=>setTimeout(r,90));
    const geometry=await ev(`(()=>{const i=document.querySelector('#brandAsset img'),m=document.querySelector('main');return {width:innerWidth,height:innerHeight,logoWidth:i.getBoundingClientRect().width,source:i.currentSrc.split('/').pop(),overflow:document.documentElement.scrollWidth>innerWidth+1||m.scrollWidth>m.clientWidth+1}})()`);
    assert.equal(geometry.overflow,false);measurements.push({tab,...geometry});
    fs.writeFileSync(path.join(out,`${width}-${tab}-preview.png`),(await win.webContents.capturePage()).toPNG());
   }
   await ev(`document.querySelector('[data-tab="controls"]').click();document.getElementById('brandAsset').click()`);
   await new Promise(r=>setTimeout(r,90));
   fs.writeFileSync(path.join(out,`${width}-brand-panel-preview.png`),(await win.webContents.capturePage()).toPNG());
   await ev(`document.querySelector('#brandDialog [data-close]').click()`);
  }
  const calls=await ev('window.__fixture.snapshot()');assert.deepEqual(calls,[]);
  fs.writeFileSync(path.join(out,'preview-measurements.json'),JSON.stringify({localPreviewOnly:true,deviceAccess:false,realBridgeCalls:0,measurements},null,2)+'\n');
  console.log('PASS: eight integrated-interface preview captures; zero native calls; 390x844 and 360x800.');
  win.destroy();app.exit(0);
 }catch(e){console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
