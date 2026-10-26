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
const monitoringEnabled=app.isPackaged||monitoringDevelopment;
const {createDiagnosticsHost}=require('./diagnostics-host.cjs');
const diagnosticsHost=createDiagnosticsHost({enabled:diagnosticsReview});
app.on('will-quit',()=>diagnosticsHost.stop());
if (developmentReview) {
  const raw = process.argv.find(value => value.startsWith('--force-device-scale-factor='))?.split('=')[1] || '1';
  const scale = ['1', '1.25', '1.5'].includes(raw) ? raw.replace('.', '_') : '1';
  const review = process.argv.includes('--lone-tray-visual-review') ? 'visual' : 'automated';
  const diagnosticId=/^[a-f0-9]{32}$/.test(process.env.LONE_DIAGNOSTICS_REVIEW_ID||'')?process.env.LONE_DIAGNOSTICS_REVIEW_ID:'local';
  const base = diagnosticsReview
    ? path.resolve(__dirname, '../../.cache/windows-diagnostics-review', diagnosticId, scale)
    : monitoringDevelopment
    ? path.resolve(__dirname, '../../.cache/windows-monitoring-development', process.env.LONE_MONITORING_RUN_ID)
    : path.resolve(__dirname, '../../.cache/windows-tray-review/dev5', review, scale);
  for (const [name, sub] of [['userData', 'profile'], ['sessionData', 'session'], ['logs', 'logs'], ['crashDumps', 'crashes']]) {
    const directory = path.join(base, sub);fs.mkdirSync(directory, {recursive: true});app.setPath(name, directory);
  }
}
app.commandLine.appendSwitch('disable-background-networking');
let controller;
function state() {return controller?.state() || null;}
function registerIpc() {
  const trusted = (event, args, count) => policy.trustedSender(event, controller?.window?.webContents) && args.length === count;
  const handle = (channel, count, callback) => ipcMain.handle(channel, (event, ...args) => {
    if (!trusted(event, args, count)) throw new Error('Untrusted window request');
    return callback(...args);
  });
  handle('widget:version', 0, () => app.getVersion());
  handle('window:state', 0, state);
  handle('window:mode', 1, next => {controller.setMode(next);return state();});
  handle('window:maximize', 0, () => {controller.toggleMaximize();return state();});
  handle('window:tray', 0, () => ({hidden: controller.hideToTray(), state: state()}));
  handle('monitoring:snapshot', 0, () => monitoringHost?.view() ||
    ({v:1,connection:'disabled',simulated:false,error:null,snapshot:null,last_valid_at:{}}));
  handle('diagnostics:snapshot', 1, query => diagnosticsHost.snapshot(query));
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
  win.loadFile(path.join(__dirname, 'index.html'));
  return win;
}

// Lock is scoped by Electron userData; review and installed profiles are distinct.
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  // Ignore forwarded paths/arguments: a second launch only restores the same window.
  app.on('second-instance', () => controller?.restoreCurrent());
  app.whenReady().then(() => {
    session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
    session.defaultSession.setPermissionCheckHandler(() => false);
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
    registerIpc();controller.start();
    if(monitoringEnabled){
      const {createMonitoringHost}=require('./monitoring-host.cjs');
      monitoringHost=createMonitoringHost({root:path.resolve(__dirname,'../..'),
        runId:app.isPackaged?crypto.randomBytes(16).toString('hex'):process.env.LONE_MONITORING_RUN_ID,
        packaged:app.isPackaged,resourcesPath:process.resourcesPath,version:app.getVersion(),
        gpu:app.isPackaged||gpuDevelopment,
        simulated:!app.isPackaged&&process.argv.includes('--lone-monitoring-simulated'),publish:value=>{
          const wc=controller?.window?.webContents;
          if(wc&&!wc.isDestroyed()&&wc.mainFrame.url===policy.entryUrl)wc.send('monitoring:state',value);
        }});
      try{monitoringHost.start();}catch{
        console.error('Local monitoring unavailable; dashboard remains open');
      }
      if(app.isPackaged||gpuDevelopment){
        const win=controller.window;
        for(const event of ['hide','minimize','blur'])win.on(event,()=>monitoringHost.setActive(false));
        for(const event of ['show','restore','focus'])win.on(event,()=>monitoringHost.setActive(true));
      }
    }
    app.on('activate', () => controller.restoreCurrent());
  }).catch(() => {console.error('Unable to initialize desktop window');if (controller) controller.quit();else app.quit();});
  app.on('window-all-closed', () => {if (controller) controller.quit();else app.quit();});
}
if(typeof module==='object')module.exports={monitoringDiagnostics:()=>monitoringHost?.diagnostics()||null,
  diagnosticPreview:()=>diagnosticsHost.diagnostics()};
