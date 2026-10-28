'use strict';
const {app, BrowserWindow, ipcMain, screen, session, Tray, Menu} = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const crypto = require('node:crypto');
const policy = require('./desktop-policy.cjs');
const {createStore} = require('./desktop-preferences.cjs');
const {createController} = require('./desktop-window.cjs');

// Isolated development profiles never touch the installed application's userData.
const developmentReview = !app.isPackaged && process.argv.includes('--lone-development-review');
const diagnosticsReview = developmentReview && process.argv.includes('--lone-diagnostics-preview');
const monitoringDevelopment = !diagnosticsReview && developmentReview && process.argv.includes('--lone-monitoring-development') &&
  /^[a-f0-9]{32}$/.test(process.env.LONE_MONITORING_RUN_ID || '');
const gpuDevelopment=monitoringDevelopment&&process.argv.includes('--lone-gpu-development');
let monitoringHost=null, monitoringQuitReady=false, monitoringQuitting=false;
const {createHistory}=require('./performance-history.cjs');
const historyEnabled=developmentReview&&process.argv.includes('--lone-history-development')&&/^[a-f0-9]{32}$/.test(process.env.LONE_MONITORING_RUN_ID||'');
let performanceHistory=createHistory({enabled:historyEnabled,extended:true,directory:historyEnabled?path.resolve(__dirname,'../../.cache/performance-history',process.env.LONE_MONITORING_RUN_ID):null});
app.on('will-quit',()=>performanceHistory.close());
const monitoringEnabled=app.isPackaged||monitoringDevelopment;
const {createDiagnosticsHost}=require('./diagnostics-host.cjs');
const adapterReview=diagnosticsReview&&process.argv.includes('--lone-diagnostic-adapters-development');
const diagnosticAdapters=adapterReview?require('./diagnostic-adapter-provider.cjs').createAdapterProvider({root:path.resolve(__dirname,'../..'),enabled:true}):null;
const localDiagnostics=require('./local-diagnostics.cjs').createLocalDiagnostics({metrics:()=>monitoringHost?.view()||null});
const diagnosticsHost=createDiagnosticsHost({enabled:diagnosticsReview,provider:diagnosticAdapters?scenario=>diagnosticAdapters.get(scenario):null});
app.on('will-quit',()=>diagnosticAdapters?.stop());
app.on('will-quit',()=>diagnosticsHost.stop());
if (developmentReview) {
  const raw = process.argv.find(value => value.startsWith('--force-device-scale-factor='))?.split('=')[1] || '1';
  const scale = ['1', '1.25', '1.5'].includes(raw) ? raw.replace('.', '_') : '1';
  const review = process.argv.includes('--lone-tray-visual-review') ? 'visual' : 'automated';
  const diagnosticId=/^[a-f0-9]{32}$/.test(process.env.LONE_DIAGNOSTICS_REVIEW_ID||'')?process.env.LONE_DIAGNOSTICS_REVIEW_ID:'local';
  const base = diagnosticsReview
    ? path.resolve(__dirname, '../../.cache/windows-diagnostics-review', diagnosticId, scale)
    : process.argv.includes('--lone-workbench-development')&&/^[a-f0-9]{32}$/.test(process.env.LONE_WORKBENCH_RUN_ID||'')
    ? path.resolve(__dirname,'../../.cache/windows-workbench-review',process.env.LONE_WORKBENCH_RUN_ID)
    : monitoringDevelopment
    ? path.resolve(__dirname, '../../.cache/windows-monitoring-development', process.env.LONE_MONITORING_RUN_ID)
    : path.resolve(__dirname, '../../.cache/windows-tray-review/dev5', review, scale);
  for (const [name, sub] of [['userData', 'profile'], ['sessionData', 'session'], ['logs', 'logs'], ['crashDumps', 'crashes']]) {
    const directory = path.join(base, sub);fs.mkdirSync(directory, {recursive: true});app.setPath(name, directory);
  }
}
app.commandLine.appendSwitch('disable-background-networking');
let controller, auxiliary=null;
let workbench=null,gameArchive=null;
let lastHistoryRead=-Infinity;
function state() {return controller?.state() || null;}
function configureHistory(history){
  performanceHistory.close();
  performanceHistory=createHistory({enabled:history.enabled,extended:true,
    directory:path.join(app.getPath('userData'),'workbench','history'),storageRoot:app.getPath('userData'),
    retentionSeconds:history.retentionHours*3600,maxPoints:Math.min(20000,history.retentionHours*1800),maxBytes:4194304});
}
function updateActivity(){if(monitoringHost)monitoringHost.setActive(Boolean(controller?.window&&!controller.window.isDestroyed()&&controller.window.isVisible()&&!controller.window.isMinimized()&&controller.window.isFocused()||auxiliary?.views().some(w=>!w.window.isDestroyed()&&w.window.isVisible())));}
function registerIpc() {
  const trusted = (event, args, count) => policy.trustedSender(event, controller?.window?.webContents) && args.length === count;
  let budgetAt=performance.now(),budget=0;const dialogPending=new Set();
  const limitedDialogs=new Set(['tools:export','tools:import','tools:presentmon','history:export']);
  const handle = (channel, count, callback) => ipcMain.handle(channel, (event, ...args) => {
    if (!trusted(event, args, count)) throw new Error('Untrusted window request');
    const now=performance.now();if(now-budgetAt>=1000){budgetAt=now;budget=0;}if(++budget>64)throw Error('window_request_rate');
    if(limitedDialogs.has(channel)){if(dialogPending.has(channel))throw Error('dialog_pending');dialogPending.add(channel);return Promise.resolve().then(()=>callback(...args)).finally(()=>dialogPending.delete(channel));}
    return callback(...args);
  });
  handle('widget:version', 0, () => app.getVersion());
  handle('tools:request',1,async query=>{const result=await workbench.handle(query);if(query.op==='historyPolicy')configureHistory(result.settings.history);return result;});
  handle('tools:open-panel',1,query=>{if(!query||Object.keys(query).sort().join(',')!=='displayId,role')throw Error('panel_request');return auxiliary.open(query.role,query.displayId);});
  for(const [channel,count,action]of [['context',0,e=>auxiliary.context(e)],['snapshot',0,e=>auxiliary.snapshot(e)],['close',0,e=>auxiliary.close(e)],['fullscreen',1,(e,v)=>auxiliary.fullscreen(e,v)],['main',1,(e,v)=>auxiliary.showMain(e,v)]])ipcMain.handle('panel:'+channel,(event,...args)=>{if(args.length!==count)throw Error('panel_arguments');return action(event,...args);});
  handle('tools:displays',0,()=>screen.getAllDisplays().map(d=>({id:d.id,label:d.label,
    width:d.size.width,height:d.size.height,scale_factor:d.scaleFactor,refresh_hz:d.displayFrequency,
    color_depth:d.colorDepth,touch_support:d.touchSupport,primary:d.id===screen.getPrimaryDisplay().id})));
  handle('tools:export',0,async()=>{
    const {dialog}=require('electron');const report=await workbench.handle({v:1,op:'export',args:{}});
    const selected=await dialog.showSaveDialog(controller.window,{defaultPath:'Lone-Smart-Room-configuracoes.json',filters:[{name:'Configurações LSR',extensions:['json']}]});
    if(selected.canceled)return {v:1,canceled:true};fs.writeFileSync(selected.filePath,JSON.stringify(report,null,2),{flag:'wx'});return {v:1,saved:true};
  });
  handle('tools:import',0,async()=>{
    const {dialog}=require('electron');const selected=await dialog.showOpenDialog(controller.window,{properties:['openFile'],filters:[{name:'Configurações LSR',extensions:['json']}]});
    if(selected.canceled)return {v:1,canceled:true};const file=selected.filePaths[0];if(fs.statSync(file).size>131072)throw Error('settings_import_size');
    const result=await workbench.handle({v:1,op:'import',args:{data:JSON.parse(fs.readFileSync(file,'utf8'))}});configureHistory(result.settings.history);return result;
  });
  handle('tools:inspect-temp',1,scope=>require('./maintenance-inspector.cjs').createInspector({ownCache:path.join(app.getPath('userData'),'workbench','tool-cache')}).inspect(scope));
  handle('tools:game-sessions',0,()=>gameArchive.list());
  handle('tools:presentmon',0,async()=>{
    const {dialog}=require('electron');const selected=await dialog.showOpenDialog(controller.window,{properties:['openFile'],filters:[{name:'PresentMon CSV',extensions:['csv']}]});
    if(selected.canceled)return {v:1,canceled:true};const file=selected.filePaths[0];if(fs.statSync(file).size>8388608)throw Error('presentmon_import_size');
    return gameArchive.add(require('./workbench-model.js').presentmon(fs.readFileSync(file,'utf8')));
  });
  handle('history:export',1,async minutes=>{
    const csv=performanceHistory.exportCsv(minutes),{dialog}=require('electron');
    const selected=await dialog.showSaveDialog(controller.window,{defaultPath:'Lone-Smart-Room-historico.csv',filters:[{name:'CSV',extensions:['csv']}]});
    if(selected.canceled)return {v:1,canceled:true};
    fs.writeFileSync(selected.filePath,csv,{flag:'wx'});return {v:1,saved:true};
  });
  handle('window:state', 0, state);
  handle('window:mode', 1, next => {controller.setMode(next);return state();});
  handle('window:maximize', 0, () => {controller.toggleMaximize();return state();});
  handle('window:tray', 0, () => ({hidden: controller.hideToTray(), state: state()}));
  handle('monitoring:snapshot', 0, () => monitoringHost?.view() ||
    ({v:1,connection:'disabled',simulated:false,error:null,snapshot:null,last_valid_at:{}}));
  handle('diagnostics:snapshot', 1, query => diagnosticsReview?diagnosticsHost.snapshot(query):localDiagnostics.snapshot(query));
  handle('history:read',1,query=>{
    if(!query||query.v!==1||Object.keys(query).sort().join(',')!=='minutes,v'||![5,30,60,360,1440,10080].includes(query.minutes))throw Error('invalid_history_query');
    const now=performance.now();if(now-lastHistoryRead<500)throw Error('history_rate_limited');lastHistoryRead=now;
    return performanceHistory.query(query.minutes);
  });
  ipcMain.on('widget:minimize', (event, ...args) => {if (trusted(event, args, 0)) controller.minimize();});
  ipcMain.on('widget:close', (event, ...args) => {if (trusted(event, args, 0)) controller.close();});
}
function createWindow(bounds) {
  const win = new BrowserWindow({
    ...bounds, minWidth: 350, minHeight: 530,
    frame: false, transparent: false, resizable: true, backgroundColor: '#0b0b0e',
    show: false, autoHideMenuBar: true, title: 'Lone Smart Room',
    icon: path.join(__dirname, 'assets/brand/windows-icon.png'),
    webPreferences: {preload: path.join(__dirname, 'preload.cjs'), contextIsolation: true,
      nodeIntegration: false, sandbox: true, webSecurity: true, devTools: !app.isPackaged}
  });
  win.webContents.setWindowOpenHandler(() => ({action: 'deny'}));
  win.webContents.on('will-navigate', (event, url) => {if (url !== policy.entryUrl) event.preventDefault();});
  win.webContents.on('will-attach-webview', event => event.preventDefault());
  win.webContents.on('will-frame-navigate', (event, url) => {if (url !== policy.entryUrl) event.preventDefault();});
  win.on('closed',()=>auxiliary?.closeAll());
  win.loadFile(path.join(__dirname, 'index.html'));
  return win;
}

// Lock is scoped by Electron userData; review and installed profiles are distinct.
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  // Ignore forwarded paths/arguments: a second launch only restores the same window.
  app.on('second-instance', () => controller?.restoreCurrent());
  app.whenReady().then(async() => {
    const mediaPermissions=require('./media-permissions.cjs').createMediaPermissions({trusted:wc=>Boolean(controller?.window?.webContents===wc&&wc.mainFrame.url===policy.entryUrl),ask:async()=>{const r=await require('electron').dialog.showMessageBox(controller.window,{type:'question',title:'Teste local de microfone',message:'Permitir até 10 segundos de leitura do nível de áudio? Não há gravação ou transmissão.',buttons:['Cancelar','Permitir teste'],defaultId:0,cancelId:0});return r.response===1;}});
    session.defaultSession.setPermissionRequestHandler(mediaPermissions.request);
    session.defaultSession.setPermissionCheckHandler(mediaPermissions.check);
    app.on('before-quit',()=>mediaPermissions.clear());
    session.defaultSession.webRequest.onBeforeRequest((details, callback) => callback({cancel: !policy.allowedResource(details.url)}));
    const stopMonitoring=async()=>{
      if(!monitoringHost){monitoringQuitReady=true;return true;}
      try{const stopped=await monitoringHost.stop();monitoringQuitReady=stopped;return stopped;}catch{return false;}
    };
    if(monitoringEnabled)app.on('before-quit',event=>{
      if(monitoringQuitReady)return;
      event.preventDefault();
      if(!monitoringQuitting){monitoringQuitting=true;stopMonitoring().then(stopped=>{
        monitoringQuitting=false;if(stopped)app.quit();else controller?.restoreCurrent();
      });}
    });
    controller = createController({app, screen, Tray, Menu, policy,
      store: createStore(app.getPath('userData')), createWindow,
      beforeExit:monitoringEnabled?stopMonitoring:null,
      icon: path.join(__dirname, 'assets/brand/windows-icon.ico'), version: app.getVersion(),
      metadata: {development: !app.isPackaged, reviewProfile: developmentReview}});
    const provider=require('./windows-read-provider.cjs').createProvider({script:app.isPackaged
      ?path.join(process.resourcesPath,'app.asar.unpacked','windows-inventory.ps1'):path.join(__dirname,'windows-inventory.ps1')});
    workbench=require('./workbench-service.cjs').createService({directory:path.join(app.getPath('userData'),'workbench'),
      enabled:app.isPackaged||developmentReview&&process.argv.includes('--lone-workbench-development'),
      inventory:provider.inventory,network:provider.network,metrics:()=>monitoringHost?.view()||null});
    gameArchive=require('./game-archive.cjs').createArchive(path.join(app.getPath('userData'),'workbench'));
    const localSettings=await workbench.handle({v:1,op:'snapshot',args:{section:'overview'}});
    if(localSettings.enabled&&localSettings.settings.history.enabled)configureHistory(localSettings.settings.history);
    app.on('will-quit',()=>workbench.close());
    auxiliary=require('./auxiliary-windows.cjs').createAuxiliaryWindows({BrowserWindow,screen,policy,
      enabled:app.isPackaged||developmentReview&&process.argv.includes('--lone-workbench-development'),
      directory:path.join(app.getPath('userData'),'workbench'),activity:updateActivity,
      metrics:()=>monitoringHost?.view()||{v:1,connection:'disabled',simulated:false,snapshot:null},
      restoreMain:()=>controller.restoreCurrent(),navigate:section=>controller.window.webContents.send('tools:navigate',section)});
    app.on('before-quit',()=>auxiliary.closeAll());
    registerIpc();controller.start();
    if(monitoringEnabled){
      const createMonitoringHost=monitoringDevelopment&&process.argv.includes('--lone-telemetry-development')
        ?require('./monitoring-telemetry-host.cjs').createTelemetryDevelopmentHost:require('./monitoring-host.cjs').createMonitoringHost;
      monitoringHost=createMonitoringHost({root:path.resolve(__dirname,'../..'),
        runId:app.isPackaged?crypto.randomBytes(16).toString('hex'):process.env.LONE_MONITORING_RUN_ID,
        packaged:app.isPackaged,resourcesPath:process.resourcesPath,version:app.getVersion(),
        gpu:app.isPackaged||gpuDevelopment,
        simulated:!app.isPackaged&&process.argv.includes('--lone-monitoring-simulated'),publish:value=>{
          performanceHistory.record(value);auxiliary?.publish(value);
          const wc=controller?.window?.webContents;
          if(wc&&!wc.isDestroyed()&&wc.mainFrame.url===policy.entryUrl)wc.send('monitoring:state',value);
        }});
      try{monitoringHost.start();}catch{
        console.error('Local monitoring unavailable; dashboard remains open');
      }
      if(app.isPackaged||gpuDevelopment){
        const win=controller.window;
        for(const event of ['hide','minimize','blur','show','restore','focus'])win.on(event,updateActivity);
      }
    }
    app.on('activate', () => controller.restoreCurrent());
  }).catch(() => {console.error('Unable to initialize desktop window');if (controller) controller.quit();else app.quit();});
  app.on('window-all-closed', () => {if (controller) controller.quit();else app.quit();});
}
if(typeof module==='object')module.exports={monitoringDiagnostics:()=>monitoringHost?.diagnostics()||null,
  diagnosticPreview:()=>diagnosticsHost.diagnostics()};
