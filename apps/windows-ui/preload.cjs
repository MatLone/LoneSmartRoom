'use strict';
const {contextBridge, ipcRenderer} = require('electron');
const tool=(op,args={})=>ipcRenderer.invoke('tools:request',{v:1,op,args});
contextBridge.exposeInMainWorld('loneTools',Object.freeze({
  snapshot:section=>tool('snapshot',{section}),inventory:kind=>tool('inventory',{kind}),
  cleanupPreview:()=>tool('cleanup'),repairPlan:id=>tool('repair',{id}),
  saveProfile:(name,adjustments)=>tool('profile',{name,adjustments}),
  saveBundle:(name,packages)=>tool('bundle',{name,packages}),
  saveDevice:device=>tool('device',device),saveScene:scene=>tool('scene',scene),scenePreview:id=>tool('scenePreview',{id}),
  saveGameProfile:profile=>tool('gameProfile',profile),askNex:message=>tool('nex',{message}),
  readAudit:()=>tool('audit'),networkTest:(kind,target)=>tool('network',{kind,target}),
  displays:()=>ipcRenderer.invoke('tools:displays'),exportSettings:()=>ipcRenderer.invoke('tools:export'),
  importSettings:()=>ipcRenderer.invoke('tools:import'),importPresentmon:()=>ipcRenderer.invoke('tools:presentmon'),
  exportHistory:minutes=>{if(![5,30,60].includes(minutes))return Promise.reject(Error('history_window'));return ipcRenderer.invoke('history:export',minutes);}
}));
contextBridge.exposeInMainWorld('loneDesktop', Object.freeze({
  getVersion: () => ipcRenderer.invoke('widget:version'),
  getMetrics: () => ipcRenderer.invoke('monitoring:snapshot'),
  getPerformanceHistory: minutes => {
    if(![5,30,60].includes(minutes))return Promise.reject(new Error('Invalid history window'));
    return ipcRenderer.invoke('history:read',{v:1,minutes});
  },
  getDiagnostics: (scenario='overview') => {
    if(typeof scenario!=='string'||!['overview','healthy','inactive','offline','listener-mismatch','auth-failure','pipe-absent','sensor-unavailable','stale','provider-error','unverified','recovered','startup-inconclusive'].includes(scenario))
      return Promise.reject(new Error('Invalid diagnostic scenario'));
    return ipcRenderer.invoke('diagnostics:snapshot',{v:1,scenario});
  },
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
