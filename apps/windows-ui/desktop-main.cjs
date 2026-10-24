'use strict';
const {app, BrowserWindow, ipcMain, screen, session, Tray, Menu} = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const policy = require('./desktop-policy.cjs');
const {createStore} = require('./desktop-preferences.cjs');
const {createController} = require('./desktop-window.cjs');

// Isolated development profiles never touch the installed application's userData.
const developmentReview = !app.isPackaged && process.argv.includes('--lone-development-review');
if (developmentReview) {
  const raw = process.argv.find(value => value.startsWith('--force-device-scale-factor='))?.split('=')[1] || '1';
  const scale = ['1', '1.25', '1.5'].includes(raw) ? raw.replace('.', '_') : '1';
  const review = process.argv.includes('--lone-tray-visual-review') ? 'visual' : 'automated';
  const base = path.resolve(__dirname, '../../.cache/windows-tray-review/dev4', review, scale);
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
    controller = createController({app, screen, Tray, Menu, policy,
      store: createStore(app.getPath('userData')), createWindow,
      icon: path.join(__dirname, 'assets/brand/windows-icon.ico'), version: app.getVersion(),
      metadata: {development: !app.isPackaged, reviewProfile: developmentReview}});
    registerIpc();controller.start();
    app.on('activate', () => controller.restoreCurrent());
  }).catch(() => {console.error('Unable to initialize desktop window');if (controller) controller.quit();else app.quit();});
  app.on('window-all-closed', () => {if (controller) controller.quit();else app.quit();});
}
