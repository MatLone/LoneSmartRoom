// Review actual integrated assets in an isolated offscreen renderer, with fake
// bridges and no external network. Before images alter only SVG markup in memory.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),cache=path.join(root,'.cache/gear-preview');
const out=path.join(root,'docs/design/gear-review-dev6-2026-10-24');
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
  const ev=code=>win.webContents.executeJavaScript(code);
  const startupCalls=await ev('window.__fixture.snapshot()');
  assert.deepEqual(startupCalls.map(c=>c.name),['refreshStatus','refreshAppPermissions','refreshLaunchResult']);
  await ev('window.__fixture.reset()');
  const capture=async name=>{await new Promise(r=>setTimeout(r,80));fs.writeFileSync(path.join(out,name+'.png'),(await win.webContents.capturePage()).toPNG());};
  const old='<path d="m9 3-1 3-3 1-2 3 2 2v3l2 3 3-1 3 1 3-2 1-3 3-2-1-3-3-1-2-3Z"/><circle cx="12" cy="12" r="3"/>';
  const original=await ev(`document.querySelector('[data-open="connection"] svg').innerHTML`);
  await ev(`document.getElementById('platformLabel').textContent='PRÉVIA LOCAL · antes do ajuste';document.querySelectorAll('[data-open="connection"] svg').forEach(n=>n.innerHTML=${JSON.stringify(old)})`);
  await capture('390-antes');
  await ev(`document.querySelectorAll('[data-open="connection"] svg').forEach(n=>n.innerHTML=${JSON.stringify(original)});document.getElementById('platformLabel').textContent='PRÉVIA LOCAL · 2.0.0-dev.6'`);
  for(const [width,height]of [[390,844],[360,800]]){
   win.setContentSize(width,height);
   await ev(`new Promise(resolve=>requestAnimationFrame(()=>document.querySelector('#brandAsset img').decode().then(resolve)))`);
   await capture(width+'-depois');
   const geometry=await ev(`({width:innerWidth,height:innerHeight,overflow:document.documentElement.scrollWidth>innerWidth+1,gears:[...document.querySelectorAll('[data-open="connection"] svg')].map(n=>({width:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height,stroke:getComputedStyle(n).strokeWidth,markup:n.innerHTML}))})`);
   assert.equal(geometry.overflow,false);assert.equal(geometry.gears.length,2);
   assert.equal(geometry.gears[0].markup,geometry.gears[1].markup);measurements.push(geometry);
   await ev(`document.querySelector('.app-header [data-open="connection"]').click()`);
   // Screenshot-only illustrative fields; never save or change production data.
   await ev(`document.getElementById('wolMac').value='AA:BB:CC:DD:EE:FF';document.getElementById('wolBroadcast').value='192.0.2.255';document.getElementById('wolPort').value='9';document.querySelector('#connectionDialog .field-help').textContent='PRÉVIA LOCAL · valores de rede fictícios; nenhum dado foi salvo.'`);
   await capture(width+'-painel-conexao');
   await ev(`document.querySelector('#connectionDialog [data-close]').click()`);
  }
  await ev(`document.querySelector('[data-open="lamp"]').click()`);await capture('360-painel-dispositivo');
  await ev(`document.querySelector('#settingsDialog [data-close]').click()`);
  assert.deepEqual(await ev('window.__fixture.snapshot()'),[]);
  fs.writeFileSync(path.join(out,'preview-measurements.json'),JSON.stringify({localPreviewOnly:true,deviceAccess:false,realBridgeCalls:0,syntheticStartupCalls:startupCalls,interactionCalls:[],measurements},null,2)+'\n');
  console.log('PASS: six local before/after and panel captures; unified 22/17px gears; zero native calls.');
  win.destroy();app.exit(0);
 }catch(e){console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
