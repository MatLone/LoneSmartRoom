// Hidden renderer smoke test: no native energy/app commands or external navigation.
const {app,BrowserWindow,ipcMain} = require('electron');
const path = require('path');
const fs = require('fs');
const cache=path.resolve(__dirname,'../.cache/electron-smoke');
for(const name of ['profile','session','crashes','logs'])fs.mkdirSync(path.join(cache,name),{recursive:true});
app.setPath('userData',path.join(cache,'profile'));
app.setPath('sessionData',path.join(cache,'session'));
app.setPath('crashDumps',path.join(cache,'crashes'));
app.setPath('logs',path.join(cache,'logs'));
app.commandLine.appendSwitch('disable-background-networking');
setTimeout(()=>app.exit(2),20000).unref();
app.whenReady().then(async () => {
  const metadata=require('../apps/windows-ui/package.json');
  ipcMain.handle('widget:version',()=>metadata.version);
  const win = new BrowserWindow({show:false,webPreferences:{preload:path.resolve(__dirname,'../apps/windows-ui/preload.cjs'),sandbox:true,nodeIntegration:false,contextIsolation:true}});
  try {
    await win.loadFile(path.resolve(__dirname,'../apps/windows-ui/index.html'));
    const result = await win.webContents.executeJavaScript(`(async () => {
      const version=await window.loneDesktop.getVersion();
      await new Promise(resolve=>setTimeout(resolve,25));
      if(!document.querySelector('#platformLabel').textContent.includes('Versão '+version))throw Error('version does not match metadata');
      const tabs = [...document.querySelectorAll('[role="tab"]')].map(x=>x.textContent);
      document.querySelector('[data-tab="monitor"]').click();
      if(document.querySelector('#panel-monitor').hidden)throw Error('monitor tab');
      document.querySelector('[data-tab="gamer"]').click();
      if(document.querySelector('#panel-gamer').hidden)throw Error('gamer tab');
      document.querySelector('[data-tab="controls"]').click();
      if(document.querySelector('#panel-controls').hidden)throw Error('controls tab');
      if(!document.querySelector('#agentPair').disabled)throw Error('native pairing falsely enabled');
      if(!document.querySelector('#wolMac'))throw Error('WoL settings missing');
      window.onLoneAgentStatus({state:'connected',last_success:1234,message:'Agente acessível'});
      if(document.querySelector('#agentState').textContent!=='Conectado')throw Error('connected state');
      window.onLoneAgentStatus({state:'disconnected',last_success:1234,message:'Sem resposta'});
      if(document.querySelector('#agentState').textContent!=='Desconectado')throw Error('disconnected state');
      if(document.querySelector('[data-remote-action="shutdown"]').disabled!==true)throw Error('status enabled a power action');
      if(!document.querySelector('#launchSteam').disabled||!document.querySelector('#launchCs2').disabled)throw Error('unpaired native app launch enabled');
      if(document.querySelector('#platformLabel').textContent.includes('Versão 1.4'))throw Error('fixed legacy version returned');
      return {tabs,devices:document.querySelectorAll('[data-device]').length,version};
    })()`);
    if(JSON.stringify(result.tabs)!==JSON.stringify(['Controles','Monitoramento PC','Gamer Launcher'])||result.devices!==4)throw Error('UI regression');
    console.log('PASS: hidden Electron renderer, three tabs, four devices, WoL settings and native-only pairing.');
    fs.writeFileSync(path.join(cache,'result.json'),JSON.stringify({ok:true,electron:process.versions.electron,...result}));
    app.exit(0);
  } catch(error) { console.error(error.message);app.exit(1); }
});
