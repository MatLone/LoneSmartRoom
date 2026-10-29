'use strict';
// Conventional Electron windows. No game hooks, injection or display-mode changes.
const path=require('node:path'),{pathToFileURL}=require('node:url');
const ENTRY=pathToFileURL(path.join(__dirname,'panel.html')).href;
function createAuxiliaryWindows({BrowserWindow,screen,policy,metrics,restoreMain,navigate,enabled=false,directory=null,activity=()=>{}}){
 const windows=new Map();
 const store=require('./panel-preferences.cjs').createPanelStore(directory,policy.validBounds);
 const find=event=>[...windows.values()].find(w=>!w.win.isDestroyed()&&event.sender===w.win.webContents&&event.senderFrame===w.win.webContents.mainFrame&&event.senderFrame.url===ENTRY);
 function open(role,displayId){
  if(!enabled||!['touch','overlay'].includes(role)||!Number.isInteger(displayId))throw Error('panel_not_authorized');
  const display=screen.getAllDisplays().find(d=>d.id===displayId);if(!display)throw Error('display_not_found');
  if(windows.has(role)){const w=windows.get(role).win;if(!w.isDestroyed()){w.show();return {v:1,opened:true,reused:true,role};}}
  const bounds=policy.clampBounds(store.get(role)||{x:display.workArea.x+12,y:display.workArea.y+12,width:role==='touch'?1600:340,height:role==='touch'?900:420},display.workArea);
  const win=new BrowserWindow({...bounds,minWidth:role==='touch'?700:270,minHeight:role==='touch'?420:250,
   frame:false,resizable:true,alwaysOnTop:role==='overlay',backgroundColor:'#101015',show:false,
   icon:path.join(__dirname,'assets/brand/windows-icon.png'),title:'Lone Smart Room · '+role,
   webPreferences:{preload:path.join(__dirname,'panel-preload.cjs'),sandbox:true,contextIsolation:true,nodeIntegration:false,webSecurity:true}});
  windows.set(role,{win,role,displayId});win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  win.webContents.on('will-navigate',(e,url)=>{if(url!==ENTRY)e.preventDefault();});win.webContents.on('will-attach-webview',e=>e.preventDefault());
  win.webContents.on('will-frame-navigate',(e,url)=>{if(url!==ENTRY)e.preventDefault();});
  win.on('close',()=>{if(!win.isFullScreen())store.save(role,win.getBounds());});
  win.on('closed',()=>{windows.delete(role);activity();});
  for(const event of ['show','hide','minimize','restore','focus','blur'])win.on(event,activity);
  win.once('ready-to-show',()=>win.show());win.loadFile(path.join(__dirname,'panel.html'));
  return {v:1,opened:true,reused:false,role};
 }
 function context(event){const w=find(event);if(!w)throw Error('untrusted_panel');return {v:1,role:w.role,display_id:w.displayId};}
 function snapshot(event){context(event);return metrics();}
 function close(event){const w=find(event);if(!w)throw Error('untrusted_panel');w.win.close();}
 function fullscreen(event,value){const w=find(event);if(!w||w.role!=='touch'||typeof value!=='boolean')throw Error('panel_fullscreen_scope');w.win.setFullScreen(value);}
 function showMain(event,section){const w=find(event);if(!w||w.role!=='touch'||!['overview','hardware','games','environment','nex'].includes(section))throw Error('panel_navigation_scope');restoreMain();navigate(section);}
 function publish(value){for(const {win}of windows.values())if(!win.isDestroyed()&&win.webContents.mainFrame.url===ENTRY)win.webContents.send('monitoring:state',value);}
 function recover(){for(const item of windows.values()){if(item.win.isDestroyed())continue;const display=screen.getAllDisplays().find(d=>d.id===item.displayId);if(!display){item.win.setFullScreen(false);item.displayId=screen.getPrimaryDisplay().id;item.win.setBounds(policy.restoreBounds(item.win.getBounds(),screen.getAllDisplays().map(d=>d.workArea),screen.getPrimaryDisplay().workArea));}}}
 screen.on('display-removed',recover);
 return Object.freeze({open,context,snapshot,close,fullscreen,showMain,publish,closeRole(role){if(!['touch','overlay'].includes(role))throw Error('panel_role');const w=windows.get(role)?.win;if(w&&!w.isDestroyed())w.close();},closeAll(){for(const {win}of windows.values())if(!win.isDestroyed())win.close();windows.clear();screen.removeListener('display-removed',recover);},views:()=>[...windows.values()].map(w=>({role:w.role,window:w.win}))});
}
module.exports={createAuxiliaryWindows,ENTRY};
