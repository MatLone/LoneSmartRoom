// Compose real renderer screenshots into a labeled local review, no native bridges.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const out=path.join(root,'docs/design/android-windows-family-dev8-2026-10-26');
const cache=path.join(root,'.cache/android-family-review');
for(const [key,name]of [['userData','profile'],['sessionData','session'],['logs','logs'],['crashDumps','crashes']]){
 const dir=path.join(cache,name);fs.mkdirSync(dir,{recursive:true});app.setPath(key,dir);
}
app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
setTimeout(()=>app.exit(2),30000).unref();
app.whenReady().then(async()=>{
 let win;
 try{
  fs.mkdirSync(out,{recursive:true});
  for(const name of fs.readdirSync(path.join(root,'.cache/android-windows-family/screens'))){
   if(name.endsWith('.png'))fs.copyFileSync(path.join(root,'.cache/android-windows-family/screens',name),path.join(out,name));
  }
  const cards=[['controls','Controles'],['monitor','Monitoramento PC'],['gamer','Gamer Launcher']];
  const html=`<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; connect-src 'none'"><title>Lone Smart Room · Android dev.8 · Revisão</title><style>*{box-sizing:border-box}body{margin:0;background:#0b0b0e;color:#f3f3f6;font:14px Segoe UI,Arial;padding:24px}h1{font-size:23px;margin:0 0 8px}p{color:#a5a5b1;margin:0 0 20px}h2{font-size:15px;margin:0 0 12px;color:#ff153f}.grid{display:grid;grid-template-columns:repeat(3,390px);gap:18px}figure{margin:0}img{display:block;width:390px;border:1px solid #2d2d35}footer{color:#a5a5b1;margin-top:14px;font-size:12px}@media(max-width:900px){.grid{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}img{max-width:100%;height:auto}}</style><h1>LONE SMART ROOM · Android 2.0.0-dev.8</h1><p>Prévia local dos assets reais · Chromium isolado · Sem Samsung ou sensores · Estados demonstrativos</p><div class="grid">${cards.map(([key,label])=>`<figure><h2>${label}</h2><img src="390-${key}.png" width="390" height="844" alt="Prévia Android: ${label}"></figure>`).join('')}</div><footer>390 × 844 · identidade Windows adaptada ao toque · métricas remotas indisponíveis · nenhuma instalação realizada</footer></html>`;
  fs.writeFileSync(path.join(out,'review.html'),html,'utf8');
  session.defaultSession.webRequest.onBeforeRequest((d,cb)=>cb({cancel:!d.url.startsWith('file:')&&!d.url.startsWith('data:')}));
  win=new BrowserWindow({show:false,width:1254,height:1048,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true}});
  await win.loadFile(path.join(out,'review.html'));
  await win.webContents.executeJavaScript('Promise.all([...document.images].map(i=>i.decode()))');
  await new Promise(r=>setTimeout(r,120));
  fs.writeFileSync(path.join(out,'comparison-three-tabs.png'),(await win.webContents.capturePage()).toPNG());
  console.log('PASS: labeled comparison of three real local renderer captures; no device or production profile.');
  win.destroy();app.exit(0);
 }catch(e){console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
