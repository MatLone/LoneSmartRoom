// Isolated hidden renderer for docs/design/prototype only; no installed app/native APIs.
const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const cache=path.join(root,'.cache/visual-prototype-tests');
const previews=path.join(root,'docs/design/previews');
for(const name of ['profile','session','logs','crashes'])fs.mkdirSync(path.join(cache,name),{recursive:true});
fs.mkdirSync(previews,{recursive:true});
app.setPath('userData',path.join(cache,'profile'));
app.setPath('sessionData',path.join(cache,'session'));
app.setPath('logs',path.join(cache,'logs'));
app.setPath('crashDumps',path.join(cache,'crashes'));
app.disableHardwareAcceleration();
app.commandLine.appendSwitch('disable-background-networking');
app.on('window-all-closed',()=>{});
setTimeout(()=>app.exit(2),60000).unref();
app.whenReady().then(async()=>{
  let win;
  const network=[];const problems=[];const cases=[];
  session.defaultSession.setPermissionRequestHandler((_web,_permission,callback)=>callback(false));
  session.defaultSession.webRequest.onBeforeRequest((details,callback)=>{
    const allowed=details.url.startsWith('file:')||details.url.startsWith('data:');
    if(!allowed)network.push(details.url);
    callback({cancel:!allowed});
  });
  try{
    for(const platform of ['android','windows']){
      win=new BrowserWindow({show:false,width:platform==='android'?390:1366,height:platform==='android'?900:920,
        webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,offscreen:true}});
      win.webContents.on('console-message',event=>{if(event.level==='error')problems.push(String(event.message))});
      win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
      await win.loadFile(path.join(root,'docs/design/prototype',platform+'.html'));
      const check=await win.webContents.executeJavaScript(`(()=>{
        const tabs=[...document.querySelectorAll('[role="tab"]')];
        if(tabs.length!==3)throw Error('Expected three destinations');
        if(window.LoneAgent||window.LoneAndroid||window.loneDesktop)throw Error('Unexpected native integration');
        if([...document.querySelectorAll('[data-action]')].some(b=>!b.disabled))throw Error('Action unexpectedly enabled');
        if(document.querySelector('.brand-slot').textContent.replace(/\\s/g,'')!=='MARCAPENDENTE')throw Error('Unverified logo used');
        return {tabs:tabs.map(b=>b.textContent.trim()),disabledActions:document.querySelectorAll('[data-action]').length};
      })()`);
      assert.deepEqual(check.tabs,['Controles','Monitoramento PC','Gamer Launcher']);
      for(const tab of ['controls','monitor','gamer']){
        await win.webContents.executeJavaScript(`document.querySelector('[data-tab="${tab}"]').click()`);
        const state=await win.webContents.executeJavaScript(`(()=>{const panels=[...document.querySelectorAll('[role="tabpanel"]')];return {visible:panels.filter(p=>!p.hidden).map(p=>p.id),selection:document.querySelector('[role="tab"][aria-selected="true"]').dataset.tab}})()`);
        assert.deepEqual(state.visible,['panel-'+tab]);assert.equal(state.selection,tab);
        await new Promise(r=>setTimeout(r,120));
        fs.writeFileSync(path.join(previews,platform+'-'+tab+'.png'),(await win.webContents.capturePage()).toPNG());
      }
      await win.webContents.executeJavaScript(`document.querySelector('[data-tab="controls"]').click();document.querySelector('[data-open="lamp"]').click()`);
      assert.equal(await win.webContents.executeJavaScript(`document.querySelector('dialog').open && document.querySelector('dialog [role="switch"]').disabled`),true);
      fs.writeFileSync(path.join(previews,platform+'-settings.png'),(await win.webContents.capturePage()).toPNG());
      await win.webContents.executeJavaScript(`document.querySelector('[data-close]').click()`);
      await win.webContents.executeJavaScript(`document.querySelector('[data-open="connection"]').click()`);
      assert.equal(await win.webContents.executeJavaScript(`[...document.querySelectorAll('dialog input')].every(i=>i.readOnly)&&document.querySelector('dialog [data-action="pair"]').disabled`),true);
      await win.webContents.executeJavaScript(`document.querySelector('[data-close]').click();document.querySelector('[data-tab="controls"]').focus();document.querySelector('[data-tab="controls"]').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}))`);
      assert.equal(await win.webContents.executeJavaScript(`document.activeElement.dataset.tab`),'monitor');
      const widths=platform==='android'?[320,360,390,412]:[800,1024,1366];
      for(const width of widths){
        win.setContentSize(width,900);
        for(const tab of ['controls','monitor','gamer']){
          await win.webContents.executeJavaScript(`document.querySelector('[data-tab="${tab}"]').click()`);
          const overflow=await win.webContents.executeJavaScript(`(()=>{
            const root=document.documentElement;
            const main=document.querySelector('main');
            const panel=document.querySelector('[role="tabpanel"]:not([hidden])');
            return {page:root.scrollWidth>innerWidth+1,main:main.scrollWidth>main.clientWidth+1,panel:panel.scrollWidth>panel.clientWidth+1};
          })()`);
          assert.deepEqual(overflow,{page:false,main:false,panel:false},platform+' '+width+' '+tab+' overflow');
          cases.push({platform,width,tab});
        }
      }
      await win.webContents.executeJavaScript(`document.querySelector('[data-tab="gamer"]').click();document.querySelector('[data-action="cs2"]').click()`);
      assert.equal(await win.webContents.executeJavaScript(`document.querySelector('dialog').open`),false);
      assert.equal(await win.webContents.executeJavaScript(`localStorage.length`),0);
      win.destroy();win=null;
    }
    assert.deepEqual(network,[],'External request attempted');assert.deepEqual(problems,[],'Renderer error');
    const result={ok:true,platforms:2,responsiveCases:cases.length,navigationAndDialogs:true,allDeviceActionsDisabled:true,externalRequests:0,nativeBridgeCalls:0,storageWrites:0,verifiedLogoUsed:false,logoStatus:'pending',cases};
    fs.writeFileSync(path.join(cache,'result.json'),JSON.stringify(result,null,2));
    console.log('PASS: isolated visual prototypes, '+cases.length+' responsive cases, navigation, dialogs, disabled actions; no network/native/storage calls.');
    app.exit(0);
  }catch(error){console.error(error.stack||error);if(win&&!win.isDestroyed())win.destroy();app.exit(1)}
});
