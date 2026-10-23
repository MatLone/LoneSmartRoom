const { app, BrowserWindow, ipcMain, screen, nativeImage } = require('electron');
const path = require('path');
let win;
function createWidget(){
  const size={width:465,height:830};
  const workArea=screen.getPrimaryDisplay().workArea;
  win=new BrowserWindow({
    ...size,
    x:Math.max(workArea.x,workArea.x+workArea.width-size.width-28),
    y:Math.max(workArea.y,workArea.y+Math.floor((workArea.height-size.height)/2)),
    minWidth:350,minHeight:530,
    frame:false,transparent:true,resizable:true,
    backgroundColor:'#00000000',
    show:false,autoHideMenuBar:true,
    title:'Lone Smart Room',
    icon:path.join(__dirname,'assets','icon.png'),
    webPreferences:{preload:path.join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true,devTools:true}
  });
  win.loadFile('index.html');
  win.once('ready-to-show',()=>win.show());
  win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  win.webContents.on('will-navigate',(event,url)=>{
    if(!url.startsWith('file://')) event.preventDefault();
  });
}
app.whenReady().then(()=>{
  ipcMain.handle('widget:version',()=>app.getVersion());
  ipcMain.on('widget:minimize',()=>win?.minimize());
  ipcMain.on('widget:close',()=>win?.close());
  createWidget();
  app.on('activate',()=>{if(BrowserWindow.getAllWindows().length===0)createWidget()});
});
app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit()});
