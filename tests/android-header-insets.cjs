// Actual CSS env() emulation through CDP, not a replacement of production CSS.
// Fixtures only; no device, real bridge, agent or external request.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),cache=path.join(root,'.cache/android-header-insets');
const out=path.join(cache,'results');
for(const [name,folder]of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){
 const dir=path.join(cache,folder);fs.mkdirSync(dir,{recursive:true});app.setPath(name,dir);
}
fs.mkdirSync(out,{recursive:true});app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});setTimeout(()=>app.exit(2),60000).unref();
app.whenReady().then(async()=>{
 let win,phase='load';const cases=[],network=[];
 try{
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>{const ok=d.url.startsWith('file:')||d.url.startsWith('data:');if(!ok)network.push(d.url);cb({cancel:!ok});});
  win=new BrowserWindow({show:false,width:390,height:844,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,backgroundThrottling:false,preload:path.join(root,'tests/fixtures/android-native-preload.cjs')}});
  await win.loadFile(path.join(root,'apps/android/app/src/main/assets/index.html'));
  const ev=code=>win.webContents.executeJavaScript(code);
  win.webContents.debugger.attach('1.3');
  await ev(`window.__fixture.reset();document.getElementById('platformLabel').textContent='PRÉVIA · 2.0.0-dev.7';const bar=document.createElement('div');bar.id='review-status-bar';bar.setAttribute('aria-hidden','true');bar.style.cssText='position:fixed;inset:0 0 auto;height:32px;z-index:99;pointer-events:none;background:#0b0b0e;color:#f5f5f7;font:600 14px Segoe UI;display:flex;justify-content:space-between;align-items:center;padding:0 18px';bar.innerHTML='<span>09:41</span><span style="width:8px;height:8px;background:#010102;border-radius:50%"></span><span>Wi-Fi · 98%</span>';document.body.append(bar)`);
  for(const [width,height]of [[320,740],[360,800],[390,844],[412,915],[600,960]]){
   win.setContentSize(width,height);
   for(const top of [0,24,32,48]){
    phase=`safe area ${width}/${top}`;
    await win.webContents.debugger.sendCommand('Emulation.setSafeAreaInsetsOverride',{insets:{top,left:0,right:0,bottom:0}});
    const barHeight=top||32;
    await ev(`document.getElementById('review-status-bar').style.height='${barHeight}px';new Promise(resolve=>requestAnimationFrame(()=>document.querySelector('#brandAsset img').decode().then(resolve)))`);
    for(const tab of ['controls','monitor','gamer']){
     await ev(`document.querySelector('[data-tab="${tab}"]').click()`);
     const v=await ev(`(()=>{const rect=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,right:r.right}};const main=document.querySelector('main');return {header:rect('.app-header'),logo:rect('#brandAsset'),version:rect('#platformLabel'),settings:rect('.app-header>.icon-button'),main:rect('main'),paddingTop:parseFloat(getComputedStyle(document.querySelector('.app-header')).paddingTop),overflow:document.documentElement.scrollWidth>innerWidth+1||main.scrollWidth>main.clientWidth+1,gearBodies:[...document.querySelectorAll('[data-open="connection"] svg')].map(n=>n.innerHTML)}})()`);
     assert.equal(v.paddingTop,Math.max(32,top)+12,'CSS env top must use max(), then add breathing room once');
     assert(v.logo.y>=barHeight+12&&v.settings.y>=barHeight+12&&v.version.y>=barHeight+12,'Header must clear the simulated system bar');
     assert(v.logo.right<=width&&v.settings.right<=width&&v.version.right<=width,'Header controls must fit horizontally');
     assert(v.settings.width>=44&&v.settings.height>=44,'Settings touch area must remain 44px');
     assert(v.main.height>=120&&!v.overflow,'Content must remain usable and scrollable');
     assert.equal(v.gearBodies.length,2);assert.equal(v.gearBodies[0],v.gearBodies[1]);
     cases.push({width,height,safeAreaTop:top,simulatedStatusBar:barHeight,tab,...v});
    }
   }
  }
  win.setContentSize(390,844);await win.webContents.debugger.sendCommand('Emulation.setSafeAreaInsetsOverride',{insets:{top:32,left:0,right:0,bottom:0}});
  await ev(`document.getElementById('review-status-bar').style.height='32px';document.querySelector('[data-tab="controls"]').click();document.querySelector('[data-open="lamp"]').click()`);
  assert(await ev(`document.querySelector('#settingsDialog [data-close]').getBoundingClientRect().top>=44`));
  await ev(`document.querySelector('#settingsDialog [data-close]').click()`);
  assert.deepEqual(await ev('window.__fixture.snapshot()'),[]);assert.deepEqual(network,[]);
  const result={ok:true,cases,cdpSafeAreaEmulation:true,statusBarIsDemonstration:true,realBridgeCalls:0,deviceAccess:false,externalRequests:0};
  fs.writeFileSync(path.join(out,'inset-measurements.json'),JSON.stringify(result,null,2)+'\n');
  console.log(`PASS: ${cases.length} header/inset/tab cases; CSS env emulated, 44px touch target, zero native calls.`);
  win.destroy();app.exit(0);
 }catch(e){console.error(phase,e.stack);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
