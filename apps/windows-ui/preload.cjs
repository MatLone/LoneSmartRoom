const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('loneDesktop',{
  minimize:()=>ipcRenderer.send('widget:minimize'),
  close:()=>ipcRenderer.send('widget:close')
});
