'use strict';
const {app}=require('electron'),path=require('node:path'),fs=require('node:fs');
if(app.isPackaged||!process.argv.includes('--lone-development-review')||!process.argv.includes('--lone-tray-visual-review'))throw Error('Isolated visual review only');
const root=path.resolve(__dirname,'..'),out=path.join(root,'docs/windows-tray-dev4/native-review');
fs.mkdirSync(out,{recursive:true});
const native=require('../apps/windows-ui/desktop-window.cjs'),create=native.createController;
let controller,tray,menu,windowCreated=0;
native.createController=options=>{
  const NativeTray=options.Tray;
  class ReviewTray extends NativeTray {constructor(...args){super(...args);tray=this;}}
  const ReviewMenu={buildFromTemplate:items=>{menu=options.Menu.buildFromTemplate(items);return menu;}};
  controller=create({...options,Tray:ReviewTray,Menu:ReviewMenu});return controller;
};
app.on('browser-window-created',(_event,win)=>{
 windowCreated++;
 let menusShown=0;
 const showMenu=()=>{
  if(!tray||tray.isDestroyed()||!menu||win.isDestroyed()||menusShown>=2)return;
  try {const b=win.getBounds();tray.popUpContextMenu(menu,{x:b.x+b.width-230,y:b.y+110});menusShown++;}
  catch(error){fs.writeFileSync(path.join(out,'review-error.json'),JSON.stringify({name:error.name,message:error.message},null,2));console.error(error.stack);}
 };
 win.on('focus',()=>setTimeout(showMenu,400));
 win.webContents.on('console-message',event=>{if(event.level==='error')console.error('Renderer error:',event.message);});
 win.webContents.once('did-finish-load',()=>setTimeout(()=>{
  if(!controller||win.isDestroyed())return;
  const b=win.getBounds(),receipt={utc:new Date().toISOString(),version:app.getVersion(),source:'actual development Electron main/preload',isolatedProfile:app.getPath('userData').startsWith(path.join(root,'.cache/windows-tray-review/dev4/visual')),windowCreated,nativeTrayCreated:!tray.isDestroyed(),trayBounds:tray.getBounds(),windowBounds:b,profileImported:false,operationalClient:false};
  fs.writeFileSync(path.join(out,'provenance.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log('Isolated Tray review ready');
  // Show the actual Tray menu within the window region so it can be captured.
  showMenu();
 },1800));
});
app.once('will-quit',()=>{
 fs.writeFileSync(path.join(out,'closed.json'),JSON.stringify({utc:new Date().toISOString(),trayDestroyed:tray?.isDestroyed(),windowsCreated:windowCreated},null,2)+'\n');
});
// Review-only safety timeout: quit through the controller, never kill processes.
setTimeout(()=>controller?.quit(),240000).unref();
