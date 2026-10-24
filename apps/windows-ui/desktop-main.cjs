'use strict';
const {app, BrowserWindow, ipcMain, screen, session} = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const policy = require('./desktop-policy.cjs');

// Explicit development review uses its own profile. Packaged/ordinary launches
// retain Electron's existing userData location and never migrate or clear it.
const developmentReview = !app.isPackaged && process.argv.includes('--lone-development-review');
if (developmentReview) {
  const raw = process.argv.find(value => value.startsWith('--force-device-scale-factor='))?.split('=')[1] || '1';
  const scale = ['1', '1.25', '1.5'].includes(raw) ? raw.replace('.', '_') : '1';
  const base = path.resolve(__dirname, '../../.cache/windows-desktop-review', scale);
  for (const [name, sub] of [['userData', 'profile'], ['sessionData', 'session'], ['logs', 'logs'], ['crashDumps', 'crashes']]) {
    const directory = path.join(base, sub);fs.mkdirSync(directory, {recursive: true});app.setPath(name, directory);
  }
}
app.commandLine.appendSwitch('disable-background-networking');
let win, mode = 'dashboard', dashboardBounds, dashboardMaximized = false;

function state() {
  if (!win || win.isDestroyed()) return null;
  const [width, height] = win.getContentSize();
  return {mode, maximized: win.isMaximized(), width, height, development: !app.isPackaged, reviewProfile: developmentReview,
    communication: 'not-integrated', operationalActionsAvailable: false};
}
function publishState() {
  if (win && !win.isDestroyed() && win.webContents.mainFrame.url === policy.entryUrl) {
    win.webContents.send('window:state', state());
  }
}
function setMode(next) {
  if (!policy.validMode(next)) throw new Error('Invalid window mode');
  if (next === mode) return state();
  const area = screen.getDisplayMatching(win.getBounds()).workArea;
  if (next === 'widget') {
    dashboardBounds = win.getNormalBounds();dashboardMaximized = win.isMaximized();
    if (win.isMaximized()) win.unmaximize();
    mode = next;win.setBounds(policy.initialBounds(next, area));
  } else {
    mode = next;
    win.setBounds(policy.clampBounds(dashboardBounds || policy.initialBounds(next, area), area));
    if (dashboardMaximized) win.maximize();
  }
  publishState();return state();
}
function registerIpc() {
  function verify(event, args, count) {
    if (!policy.trustedSender(event, win?.webContents) || args.length !== count) throw new Error('Untrusted window request');
  }
  ipcMain.handle('widget:version', (event, ...args) => {verify(event, args, 0);return app.getVersion();});
  ipcMain.handle('window:state', (event, ...args) => {verify(event, args, 0);return state();});
  ipcMain.handle('window:mode', (event, ...args) => {verify(event, args, 1);return setMode(args[0]);});
  ipcMain.handle('window:maximize', (event, ...args) => {
    verify(event, args, 0);
    if (mode === 'widget') return state();
    if (win.isMaximized()) win.unmaximize();else win.maximize();return state();
  });
  // Preserve the legacy minimize/close capabilities; no tray existed before.
  ipcMain.on('widget:minimize', (event, ...args) => {if (policy.trustedSender(event, win?.webContents) && args.length === 0) win.minimize();});
  ipcMain.on('widget:close', (event, ...args) => {if (policy.trustedSender(event, win?.webContents) && args.length === 0) win.close();});
}
function createWindow() {
  mode = 'dashboard';
  const area = screen.getPrimaryDisplay().workArea;
  win = new BrowserWindow({
    ...policy.initialBounds(mode, area), minWidth: 350, minHeight: 530,
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
  for (const event of ['resize', 'maximize', 'unmaximize']) win.on(event, publishState);
  win.once('ready-to-show', () => {win.show();publishState();});
  win.loadFile(path.join(__dirname, 'index.html'));
  win.on('closed', () => {win = null;});
}
app.whenReady().then(() => {
  // This visual-only stage has no network client, permission flow or executors.
  session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  session.defaultSession.setPermissionCheckHandler(() => false);
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => callback({cancel: !policy.allowedResource(details.url)}));
  registerIpc();createWindow();
  app.on('activate', () => {if (BrowserWindow.getAllWindows().length === 0) createWindow();});
});
app.on('window-all-closed', () => {if (process.platform !== 'darwin') app.quit();});
