// Isolated actual renderers and clearly labeled visual simulations. No installed app.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),out=path.join(root,'docs/design/brand/e-red-windows-icon-2026-10-26');
const cache=path.join(root,'.cache/e-red-brand-review');
for(const [key,name]of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){
 const dir=path.join(cache,name);fs.mkdirSync(dir,{recursive:true});app.setPath(key,dir);
}
app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});setTimeout(()=>app.exit(2),60000).unref();
app.whenReady().then(async()=>{
 let window;const external=[],errors=[];
 try{
  session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>{const local=d.url.startsWith('file:')||d.url.startsWith('data:');if(!local)external.push(d.url);cb({cancel:!local});});
  const create=preload=>{window=new BrowserWindow({show:false,width:390,height:844,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true,...(preload?{preload}: {})}});window.webContents.setWindowOpenHandler(()=>({action:'deny'}));window.webContents.on('console-message',e=>{if(e.level==='error')errors.push(e.message);});};
  const ev=code=>window.webContents.executeJavaScript(code);
  const capture=async(name,rect)=>{await ev('Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))');await new Promise(r=>setTimeout(r,120));fs.writeFileSync(path.join(out,name),(await window.webContents.capturePage(rect)).toPNG());};
  create(path.join(root,'tests/fixtures/android-native-preload.cjs'));
  await window.loadFile(path.join(root,'apps/android/app/src/main/assets/index.html'));window.webContents.setZoomFactor(1);
  await ev(`window.__fixture.reset();document.getElementById('platformLabel').textContent='PRÉVIA VISUAL · SEM INSTALAÇÃO';const bar=document.createElement('div');bar.style.cssText='position:fixed;inset:0 0 auto;height:32px;background:#0b0b0e;color:#c4c4cf;font:11px Segoe UI;display:flex;align-items:center;justify-content:space-between;padding:0 18px;z-index:99;pointer-events:none';bar.innerHTML='<span>09:41</span><span>DEMONSTRAÇÃO LOCAL</span>';document.body.append(bar)`);
  for(const width of [390,360]){
   window.setContentSize(width,width===390?844:800);
   await capture(`android-header-${width}.png`);
  }
  if((await ev('window.__fixture.snapshot()')).length!==0)throw Error('Unexpected fixture action');
  window.destroy();
  create();window.setContentSize(1280,880);
  await window.loadFile(path.join(root,'apps/windows-ui/index.html'));
  await ev(`document.getElementById('platformLabel').textContent='PRÉVIA · assets em desenvolvimento';document.getElementById('runtimeLabel').textContent='PRÉVIA ISOLADA · sem agente ou sensores'`);
  await capture('windows-dashboard-preview.png');
  await capture('windows-header-preview.png',{x:0,y:0,width:232,height:180});window.destroy();
  fs.copyFileSync(path.join(root,'apps/android/app/src/main/res/drawable-nodpi/lone_splash_safe.png'),path.join(out,'exports/native-splash-safe.png'));
  const css=`*{box-sizing:border-box}body{margin:0;background:#0b0b0e;color:#f3f3f6;font:15px Segoe UI,Arial;padding:30px}h1{margin:0 0 10px;font-size:26px}p{color:#a5a5b1;line-height:1.5;margin:0 0 24px}h2{color:#ff153f;font-size:17px;margin:0 0 16px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{border:1px solid #2d2d35;background:#151518;border-radius:16px;padding:22px;min-width:0}.logo{width:100%;height:150px;object-fit:contain}.icons{display:flex;align-items:center;gap:28px}.icons img{width:150px;height:150px}.icons small{display:block;color:#a5a5b1;max-width:210px;margin-top:10px}.small-icon{image-rendering:auto;width:56px!important;height:56px!important}.row{display:flex;align-items:center;gap:20px;flex-wrap:wrap}.phone{width:320px;height:570px;border:1px solid #3a3a44;border-radius:30px;background:radial-gradient(ellipse at bottom,#31121e,#080a0d 70%);padding:22px;margin:0 auto;position:relative}.system{display:flex;justify-content:space-between;font-size:12px}.home-icon{display:grid;justify-items:center;gap:8px;position:absolute;bottom:80px;left:24px;width:88px;font-size:11px;text-align:center}.home-icon img{width:56px;height:56px}.splash{display:grid;place-items:center;height:470px;background:#080a0d;border-radius:14px}.splash img{width:220px;height:220px}.footer{margin-top:24px;color:#a5a5b1;font-size:13px}`;
  const html=`<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; connect-src 'none'"><title>Lone Smart Room · revisão E vermelho / ícone Windows</title><style>${css}</style><h1>LONE SMART ROOM · revisão visual</h1><p>Somente E em vermelho oficial #ff153f · geometria preservada · ícone original Windows no Android</p><div class="grid"><section class="card"><h2>Logomarca anterior</h2><img class="logo" src="reference/logo-horizontal.svg" alt="LONE anteriormente branco"></section><section class="card"><h2>Proposta: L O N brancos · E vermelho</h2><img class="logo" src="exports/logo-horizontal.png" alt="Somente E vermelho; SMART ROOM preservado"></section><section class="card"><h2>Windows original → fonte Android idêntica</h2><div class="icons"><div><img src="exports/windows-original.png" alt="Ícone original Windows"><small>Windows · original intacto</small></div><div><img src="exports/android-source-identical.png" alt="Mesmo PNG usado no Android"><small>Android · cópia exata do mesmo PNG</small></div></div></section><section class="card"><h2>Máscaras do launcher Android</h2><div class="icons"><div><img src="exports/android-circle-512.png" alt="Máscara circular"><small>Circular · moldura original recortável</small></div><div><img src="exports/android-rounded-512.png" alt="Máscara arredondada"><small>Arredondada · símbolo preservado</small></div></div></section></div><p class="footer">Prévia local. Máscaras demonstrativas; nenhum Samsung ou aplicativo instalado foi modificado. A moldura externa acompanha o recorte do launcher, sem redesenhar o símbolo.</p></html>`;
  fs.writeFileSync(path.join(out,'review.html'),html,'utf8');
  create();window.setContentSize(1200,820);await window.loadFile(path.join(out,'review.html'));await capture('comparison-windows-android.png');window.destroy();
  const home=`<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'"><style>${css}</style><h1>Android · ícone de 56 px</h1><p>Simulação de tela inicial Samsung · não é captura física</p><div class="phone"><div class="system"><span>09:41</span><span>DEMONSTRAÇÃO</span></div><div class="home-icon"><img src="exports/android-rounded-56.png" alt="Ícone original Windows adaptado"><span>Lone Smart<br>Room</span></div></div><p class="footer">Mesmo asset Windows. Sem instalação ou acesso ao aparelho.</p></html>`;
  fs.writeFileSync(path.join(out,'samsung-simulation.html'),home,'utf8');
  create();window.setContentSize(560,850);await window.loadFile(path.join(out,'samsung-simulation.html'));await capture('samsung-icon-simulation.png');window.destroy();
  const splash=`<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'"><style>${css}</style><h1>Splash · E em vermelho</h1><p>Simulação do recurso nativo · composição do sistema variável</p><div class="splash"><img src="exports/native-splash-safe.png" alt="Recurso nativo com somente E em vermelho"></div><p class="footer">Layout controlado pelo Android. Recurso completo mantém o lettering e a geometria anteriores.</p></html>`;
  fs.writeFileSync(path.join(out,'splash-simulation.html'),splash,'utf8');
  create();window.setContentSize(560,740);await window.loadFile(path.join(out,'splash-simulation.html'));await capture('native-splash-simulation.png');window.destroy();
  if(external.length||errors.length)throw Error('Unexpected network request or renderer error');
  fs.writeFileSync(path.join(out,'preview-provenance.json'),JSON.stringify({ok:true,actualProjectRenderers:true,productionAppOpened:false,physicalSamsungAccess:false,nativeBridgeCalls:0,externalRequests:0,realSensors:false,homeAndSplashAreSimulations:true,apkBuilt:false},null,2)+'\n');
  console.log('PASS: actual local headers, original/new logo comparison, source/masks and labeled Samsung/splash simulations.');app.exit(0);
 }catch(e){console.error(e.stack);if(window&&!window.isDestroyed())window.destroy();app.exit(1);}
});
