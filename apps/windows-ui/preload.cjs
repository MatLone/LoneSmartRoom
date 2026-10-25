'use strict';
const {contextBridge, ipcRenderer} = require('electron');
contextBridge.exposeInMainWorld('loneDesktop', Object.freeze({
  getVersion: () => ipcRenderer.invoke('widget:version'),
  getMetrics: () => ipcRenderer.invoke('monitoring:snapshot'),
  onMetrics: callback => {
    if(typeof callback!=='function')throw new TypeError('Expected callback');
    const handler=(_event,value)=>callback(value);
    ipcRenderer.on('monitoring:state',handler);
    return ()=>ipcRenderer.removeListener('monitoring:state',handler);
  },
  minimize: () => ipcRenderer.send('widget:minimize'),
  close: () => ipcRenderer.send('widget:close'),
  minimizeToTray: () => ipcRenderer.invoke('window:tray'),
  getWindowState: () => ipcRenderer.invoke('window:state'),
  setWindowMode: mode => {
    if (mode !== 'dashboard' && mode !== 'widget') return Promise.reject(new Error('Invalid window mode'));
    return ipcRenderer.invoke('window:mode', mode);
  },
  toggleMaximize: () => ipcRenderer.invoke('window:maximize'),
  onWindowState: callback => {
    if (typeof callback !== 'function') throw new TypeError('Expected callback');
    const handler = (_event, value) => callback(value);
    ipcRenderer.on('window:state', handler);
    return () => ipcRenderer.removeListener('window:state', handler);
  }
}));
