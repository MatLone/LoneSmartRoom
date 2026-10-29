'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('lonePanel',Object.freeze({
 context:()=>ipcRenderer.invoke('panel:context'),snapshot:()=>ipcRenderer.invoke('panel:snapshot'),close:()=>ipcRenderer.invoke('panel:close'),
 fullscreen:value=>{if(typeof value!=='boolean')return Promise.reject(Error('boolean_required'));return ipcRenderer.invoke('panel:fullscreen',value);},
 showMain:section=>{if(!['overview','hardware','games','environment','nex'].includes(section))return Promise.reject(Error('section_scope'));return ipcRenderer.invoke('panel:main',section);},
 onMetrics:callback=>{if(typeof callback!=='function')throw Error('callback');const handler=(_e,v)=>callback(v);ipcRenderer.on('monitoring:state',handler);return ()=>ipcRenderer.removeListener('monitoring:state',handler);}
}));
