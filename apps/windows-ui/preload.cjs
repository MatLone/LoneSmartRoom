'use strict';
const {contextBridge, ipcRenderer} = require('electron');
const tool=(op,args={})=>ipcRenderer.invoke('tools:request',{v:1,op,args});
contextBridge.exposeInMainWorld('loneTools',Object.freeze({
  snapshot:section=>tool('snapshot',{section}),inventory:kind=>tool('inventory',{kind}),
  inspectTemp:scope=>{if(!['own','user_temp','windows_temp'].includes(scope))return Promise.reject(Error('scope'));return ipcRenderer.invoke('tools:inspect-temp',scope);},
  cleanupPreview:()=>tool('cleanup'),repairPlan:id=>tool('repair',{id}),
  saveProfile:(name,adjustments)=>tool('profile',{name,adjustments}),
  saveBundle:(name,packages)=>tool('bundle',{name,packages}),
  saveDevice:device=>tool('device',device),saveScene:scene=>tool('scene',scene),scenePreview:id=>tool('scenePreview',{id}),
  inspectRgb:()=>ipcRenderer.invoke('devices:inspect-rgb'),
  rgb:(op,args={})=>{if(!['state','refresh','save','apply','off','on','restore','sceneSave','sceneApply','automation'].includes(op))return Promise.reject(Error('rgb_operation'));return ipcRenderer.invoke('rgb:request',{v:1,op,args});},
  requestLocalLaunch:app=>{if(!['steam','cs2'].includes(app))return Promise.reject(Error('launch_app'));return ipcRenderer.invoke('gamer:launch',app);},
  checkLocalLaunch:app=>{if(!['steam','cs2'].includes(app))return Promise.reject(Error('launch_app'));return ipcRenderer.invoke('gamer:launch-check',app);},
  gamer:(op='view',policy=null)=>{if(!['view','poll','configure'].includes(op))return Promise.reject(Error('gamer_operation'));return ipcRenderer.invoke('gamer:request',{v:1,op,policy});},
  onGamer:callback=>{if(typeof callback!=='function')throw TypeError('callback');const h=(_e,v)=>callback(v);ipcRenderer.on('gamer:state',h);return()=>ipcRenderer.removeListener('gamer:state',h);},
  saveGame:game=>tool('game',game),gameSessions:()=>ipcRenderer.invoke('tools:game-sessions'),
  saveGameProfile:profile=>tool('gameProfile',profile),askNex:message=>tool('nex',{message}),
  attachFpsSource:()=>ipcRenderer.invoke('tools:fps-attach'),
  fpsSnapshot:()=>ipcRenderer.invoke('tools:fps-snapshot'),stopFpsSource:()=>ipcRenderer.invoke('tools:fps-stop'),
  readAudit:()=>tool('audit'),networkTest:(kind,target)=>tool('network',{kind,target}),
  configureHistory:(enabled,retentionHours)=>tool('historyPolicy',{enabled,retentionHours}),
  openPanel:(role,displayId)=>ipcRenderer.invoke('tools:open-panel',{role,displayId}),
  onNavigate:callback=>{if(typeof callback!=='function')throw TypeError('callback');const handler=(_event,section)=>callback(section);ipcRenderer.on('tools:navigate',handler);return()=>ipcRenderer.removeListener('tools:navigate',handler);},
  displays:()=>ipcRenderer.invoke('tools:displays'),exportSettings:()=>ipcRenderer.invoke('tools:export'),
  importSettings:()=>ipcRenderer.invoke('tools:import'),importPresentmon:()=>ipcRenderer.invoke('tools:presentmon'),
  exportHistory:minutes=>{if(![5,30,60,360,1440,10080].includes(minutes))return Promise.reject(Error('history_window'));return ipcRenderer.invoke('history:export',minutes);}
}));
contextBridge.exposeInMainWorld('loneDesktop', Object.freeze({
  getVersion: () => ipcRenderer.invoke('widget:version'),
  getMetrics: () => ipcRenderer.invoke('monitoring:snapshot'),
  getPerformanceHistory: minutes => {
    if(![5,30,60,360,1440,10080].includes(minutes))return Promise.reject(new Error('Invalid history window'));
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
