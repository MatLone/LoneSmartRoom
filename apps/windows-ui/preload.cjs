const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('loneDesktop',{
  getVersion:()=>ipcRenderer.invoke('widget:version'),
  minimize:()=>ipcRenderer.send('widget:minimize'),
  close:()=>ipcRenderer.send('widget:close')
});
