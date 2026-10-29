'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const vm = require('node:vm'), {EventEmitter} = require('node:events');
const root = path.resolve(__dirname, '..'), directory = path.join(root, 'apps/windows-ui');
const policy = require(path.join(directory, 'desktop-policy.cjs'));
const preferences = require(path.join(directory, 'desktop-preferences.cjs'));
const {createController} = require(path.join(directory, 'desktop-window.cjs'));
let checks = 0;
const check = (value, message) => {assert(value, message);checks++;};
const copy = value => JSON.parse(JSON.stringify(value));
const primary = {x:0,y:0,width:1920,height:1040};
function fixture({saved = preferences.defaults(), trayFailure = false, menuFailure = false, writeFailure = false,beforeExit=null,beforeRestore=null} = {}) {
  const app = new EventEmitter(), screen = new EventEmitter(), timers = new Map(), trays = [], saves = [];
  let win, windows = 0, quits = 0, nextTimer = 0;
  screen.displays = [{workArea:primary}];screen.getAllDisplays = () => screen.displays;
  screen.getPrimaryDisplay = () => screen.displays[0];
  const store = {status:'loaded',load:()=>copy(saved),save:value=>{if(writeFailure)return false;saves.push(copy(value));return true;}};
  class Window extends EventEmitter {
    constructor(bounds) {super();this.bounds = {...bounds};this.visible = false;this.minimized = false;this.maximized = false;this.destroyed = false;this.focused = false;this.sent = [];
      this.webContents = {mainFrame:{url:policy.entryUrl},send:(...args)=>this.sent.push(args)};}
    isDestroyed(){return this.destroyed;} isVisible(){return this.visible;} isMinimized(){return this.minimized;} isMaximized(){return this.maximized;}
    getNormalBounds(){return {...this.bounds};} getBounds(){return {...this.bounds};} getContentSize(){return [this.bounds.width,this.bounds.height];}
    setBounds(bounds){this.bounds = {...bounds};this.emit('resize');this.emit('move');}
    maximize(){this.maximized = true;this.emit('maximize');} unmaximize(){this.maximized = false;this.emit('unmaximize');}
    show(){this.visible = true;} hide(){this.visible = false;} focus(){this.focused = true;}
    minimize(){this.minimized = true;this.emit('minimize');} restore(){this.minimized = false;this.emit('restore');}
    close(){if(this.destroyed)return;const event={defaultPrevented:false,preventDefault(){this.defaultPrevented=true;}};this.emit('close',event);if(event.defaultPrevented)return;this.destroyed = true;this.emit('closed');app.emit('window-all-closed');}
  }
  class Tray extends EventEmitter {
    constructor(icon){super();if(trayFailure)throw Error('No shell');this.icon = icon;this.destroyed = false;this.destroyCalls = 0;trays.push(this);}
    isDestroyed(){return this.destroyed;} destroy(){this.destroyed = true;this.destroyCalls++;}
    setToolTip(value){this.tooltip = value;} setContextMenu(menu){if(menuFailure)throw Error('Menu unavailable');this.menu = menu;}
  }
  app.quit = () => {if(quits)return;quits++;app.emit('before-quit');if(win&&!win.destroyed)win.close();};
  const controller = createController({app,screen,Tray,Menu:{buildFromTemplate:v=>v},policy,store,beforeExit,beforeRestore,
    createWindow:bounds=>{windows++;win = new Window(bounds);return win;},icon:'official.ico',version:'2.0.0-dev.4',
    schedule:fn=>{const id=++nextTimer;timers.set(id,fn);return id;},cancel:id=>timers.delete(id)});
  app.on('window-all-closed',controller.quit);
  controller.start();win.emit('ready-to-show');
  return {controller,app,screen,trays,saves,timers,store,get win(){return win;},get windows(){return windows;},get quits(){return quits;},
    pending:()=>{const pending=[...timers.values()];timers.clear();pending.forEach(fn=>fn());}};
}
function lifecycle() {
  const f=fixture(),c=f.controller,t=f.trays[0];
  check(f.windows===1&&f.trays.length===1&&f.win.visible,'One visible native window and one Tray');
  check(t.icon==='official.ico'&&t.tooltip.includes('2.0.0-dev.4'),'Official icon and version tooltip');
  check(t.menu.map(v=>v.label||v.type).join(',')==='Abrir dashboard,Modo Widget,separator,Sair','Restricted Tray menu');
  c.start();check(f.windows===1&&f.trays.length===1,'Repeated start never duplicates window or Tray');
  c.minimize();check(f.win.minimized&&f.win.visible&&!c.state().hiddenToTray,'Existing minimize remains taskbar minimize');
  t.emit('click');check(!f.win.minimized&&f.win.visible&&f.win.focused,'Tray click restores minimized window');
  check(c.hideToTray()&&!f.win.visible&&c.state().hiddenToTray,'Explicit minimize-to-Tray hides only after Tray exists');
  t.emit('click');check(f.win.visible&&!c.state().hiddenToTray&&f.windows===1,'Tray click reveals same window');
  c.setMode('widget');f.win.setBounds({x:210,y:30,width:390,height:700});f.pending();
  c.minimize();c.hideToTray();t.emit('double-click');
  check(c.state().mode==='widget'&&!f.win.minimized&&f.win.visible,'Widget restores correctly after taskbar and Tray minimize');
  t.menu[0].click();check(c.state().mode==='dashboard'&&f.win.visible,'Open dashboard forces full mode');
  t.menu[1].click();check(c.state().mode==='widget'&&f.win.visible,'Widget menu uses same window');
  check(f.win.bounds.width===390&&f.win.bounds.height===700,'Widget dimensions remembered across mode changes');
  c.toggleMaximize();check(!f.win.maximized,'Widget does not maximize');
  t.menu[0].click();c.toggleMaximize();check(f.win.maximized,'Dashboard maximization still supported');
  c.setMode('widget');c.setMode('dashboard');check(f.win.maximized,'Dashboard maximization survives Widget roundtrip');
  for(const input of [null,{},[],0,'steam','widget && cmd.exe','https://localhost']){assert.throws(()=>c.setMode(input));checks++;}
  const oldBounds={...f.win.bounds};c.setMode('dashboard');check(JSON.stringify(oldBounds)===JSON.stringify(f.win.bounds),'Same mode is idempotent');
  c.hideToTray();t.menu[3].click();check(f.quits===1&&t.destroyed&&t.destroyCalls===1&&f.win.destroyed,'Sair destroys Tray and exits even while hidden');
  c.quit();check(f.quits===1&&t.destroyCalls===1,'Exit is idempotent');
  check(f.timers.size===0,'Exit flush cancels pending persistence');
  const x=fixture();x.controller.close();check(x.quits===1&&x.win.destroyed&&x.trays[0].destroyed,'X closes normally with no hidden background app');
  const failed=fixture({writeFailure:true});failed.controller.close();check(failed.quits===1,'Preference write failure never blocks normal exit');
}
function failuresAndMonitors() {
  for(const options of [{trayFailure:true},{menuFailure:true}]){
    const f=fixture(options);check(!f.controller.state().trayAvailable&&f.win.visible,'Tray creation failure leaves window visible');
    f.controller.minimize();check(!f.controller.hideToTray()&&f.win.visible&&!f.win.minimized,'Missing Tray cannot strand invisible/minimized window');
    f.controller.close();check(f.quits===1,'Exit still possible after Tray initialization failure');
  }
  const f=fixture();f.trays[0].destroy();f.controller.minimize();check(!f.controller.hideToTray()&&f.win.visible&&!f.win.minimized,'Destroyed Tray fallback restores native window');f.controller.quit();
  const saved=preferences.defaults();saved.mode='widget';saved.bounds.widget={x:4200,y:-1500,width:600,height:1700};saved.minimizeToTray=true;
  const restored=fixture({saved});check(restored.controller.state().mode==='widget'&&restored.win.visible,'Last mode restores visible, never auto-hidden');
  check(restored.win.bounds.x>=0&&restored.win.bounds.y>=0&&restored.win.bounds.x+restored.win.bounds.width<=1920&&restored.win.bounds.height<=1040,'Disconnected monitor coordinates clamped on startup');
  restored.controller.minimize();check(restored.win.minimized&&!restored.controller.state().hiddenToTray,'Reserved preference does not silently remap Minimize');
  restored.controller.restoreCurrent();restored.win.setBounds({x:-1200,y:10,width:700,height:680});
  restored.screen.displays=[{workArea:{x:0,y:0,width:1024,height:768}}];restored.screen.emit('display-removed');
  check(restored.win.bounds.x>=0&&restored.win.bounds.x+restored.win.bounds.width<=1024,'Live monitor removal brings window back into visible area');
  restored.controller.hideToTray();restored.win.bounds={x:9999,y:9999,width:800,height:700};restored.trays[0].emit('click');
  check(restored.win.visible&&restored.win.bounds.x+restored.win.bounds.width<=1024,'Hidden window is revalidated before restoring');
  restored.controller.quit();
  const f2=fixture();f2.win.setBounds({x:44,y:55,width:1111,height:777});f2.pending();f2.controller.setMode('widget');f2.controller.quit();
  const saved2=f2.saves.at(-1),restart=fixture({saved:saved2});
  check(restart.controller.state().mode==='widget','Mode survives simulated restart');
  restart.controller.setMode('dashboard');check(restart.win.bounds.x===44&&restart.win.bounds.y===55&&restart.win.bounds.width===1111,'Dashboard position/size survive restart');restart.controller.quit();
  const left={x:-1600,y:0,width:1600,height:900},b=policy.restoreBounds({x:-1500,y:40,width:800,height:650},[primary,left],primary);
  check(b.x===-1500&&b.y===40,'Valid negative-coordinate monitor retained');
  for(const bad of [{x:NaN,y:0,width:350,height:530},{x:0,y:0,width:Infinity,height:530},{x:0,y:0,width:-1,height:500},null]){
    const v=policy.restoreBounds(bad,[primary],primary);check(Number.isFinite(v.x)&&v.width>0,'Invalid bounds fall back safely');
  }
}
function diskState() {
  const base=path.join(root,'.cache/tests-tray-preferences');fs.mkdirSync(base,{recursive:true});
  const dir=fs.mkdtempSync(path.join(base,'case-')),file=path.join(dir,'desktop-window-state.json'),store=preferences.createStore(dir);
  check(store.load().mode==='dashboard'&&store.status==='default','Missing file gives conservative defaults');
  const value=preferences.defaults();value.mode='widget';value.minimizeToTray=true;value.bounds.widget={x:-800,y:10,width:360,height:680};
  check(store.save(value)&&fs.existsSync(file),'Atomic visual save');
  const loaded=store.load();check(loaded.mode==='widget'&&loaded.minimizeToTray&&loaded.bounds.widget.x===-800,'Full allowed schema roundtrip');
  loaded.mode='dashboard';check(store.load().mode==='widget','Returned state is not shared mutable storage');
  const original=fs.readFileSync(file,'utf8');
  const io=new Proxy(fs,{get(target,key){if(key==='renameSync')return ()=>{throw Error('Access denied');};return target[key];}});
  check(!preferences.createStore(dir,io).save(preferences.defaults()),'Atomic rename failure reported');
  check(fs.readFileSync(file,'utf8')===original,'Write failure retains prior complete file');
  check(!fs.existsSync(file+'.'+process.pid+'.tmp'),'Own failed temporary write cleaned');
  fs.writeFileSync(file+'.'+process.pid+'.tmp','existing fixture');
  check(!store.save(preferences.defaults())&&fs.readFileSync(file+'.'+process.pid+'.tmp','utf8')==='existing fixture','Existing temporary target never overwritten or removed');
  fs.unlinkSync(file+'.'+process.pid+'.tmp');
  for(const body of ['{bad',JSON.stringify({...value,schema:2}),JSON.stringify({...value,credential:'not allowed'}),JSON.stringify({...value,bounds:{dashboard:null,widget:{x:0,y:0,width:NaN,height:100}}}),' '.repeat(preferences.MAX_BYTES+1)]){
    fs.writeFileSync(file,body);check(store.load().mode==='dashboard'&&store.status==='invalid','Corrupt/oversize/unknown visual schema rejected');
    check(fs.readFileSync(file,'utf8')===body,'Invalid input preserved on read, no deletion');
    check(!store.save(preferences.defaults())&&fs.readFileSync(file,'utf8')===body,'Unknown/corrupt data never overwritten by automatic saves');
  }
  const unsafe=new Proxy(fs,{get(target,key){if(key==='lstatSync')return ()=>({isFile:()=>false,isSymbolicLink:()=>true,size:1});return target[key];}});
  const linked=preferences.createStore(dir,unsafe);check(linked.load().mode==='dashboard'&&!linked.save(value),'Reparse/symlink preference target rejected');
  for(const bad of [{...value,mode:'cmd.exe'},{...value,minimizeToTray:'yes'},{...value,bounds:{dashboard:null,widget:[]}},null]){check(preferences.normalize(bad)===null,'Strict preferences accept no paths/commands/coercions');}
}
async function mainWiring(lock,monitorFailure=false) {
  const app=new EventEmitter(),ipcHandlers=new Map(),ipcEvents=new Map();let creations=0,quits=0,starts=0,restores=0,hides=0;
  app.isPackaged=true;app.commandLine={appendSwitch:()=>{}};app.requestSingleInstanceLock=()=>lock;
  app.quit=()=>{quits++;};app.whenReady=()=>Promise.resolve();app.getVersion=()=> '2.0.0-dev.5';app.getPath=()=> 'isolated-mock';
  const frame={url:policy.entryUrl},wc={mainFrame:frame,isDestroyed:()=>false};
  const controller={window:{webContents:wc,on:()=>{}},state:()=>({mode:'dashboard'}),start:()=>{starts++;},restoreCurrent:()=>{restores++;},hideToTray:()=>{hides++;return true;},setMode:m=>{if(!policy.validMode(m))throw Error('Invalid');},toggleMaximize:()=>{},minimize:()=>{},close:()=>{},quit:()=>{quits++;}};
  const monitor={start:()=>{if(monitorFailure)throw Error('mock failure');},stop:()=>Promise.resolve(true),view:()=>({v:1,connection:'disconnected'}),diagnostics:()=>({})};
  const context=vm.createContext({__dirname:directory,process:{argv:[],env:{},resourcesPath:'C:/mock-resources'},console,performance:{now:()=>Date.now()},require:name=>{
    if(name==='./game-mode.cjs')return {createGameMode:()=>({start:()=>{},close:()=>{},view:()=>({})})};
    if(name==='electron')return {app,BrowserWindow:()=>{},ipcMain:{handle:(n,fn)=>ipcHandlers.set(n,fn),on:(n,fn)=>ipcEvents.set(n,fn)},screen:{},session:{defaultSession:{setPermissionRequestHandler:()=>{},setPermissionCheckHandler:()=>{},webRequest:{onBeforeRequest:()=>{}}}},Tray:()=>{},Menu:{}};
    if(name==='./desktop-window.cjs')return {createController:()=>{creations++;return controller;}};
    if(name==='./desktop-preferences.cjs')return {createStore:()=>({})};
    if(name==='./desktop-policy.cjs')return policy;
    if(name==='./monitoring-host.cjs')return {createMonitoringHost:()=>monitor};
    if(name==='./performance-history.cjs')return require(path.join(directory,'performance-history.cjs'));
    if(name==='./diagnostics-host.cjs')return require(path.join(directory,'diagnostics-host.cjs'));
    if(name==='./workbench-service.cjs')return {createService:()=>({handle:async()=>({enabled:false}),close(){}})};
    if(name==='./game-archive.cjs')return {createArchive:()=>({list:()=>({v:1,entries:[]})})};
    if(name==='./auxiliary-windows.cjs')return {createAuxiliaryWindows:()=>({views:()=>[],closeAll(){}})};
    return require(name.startsWith('./')?path.join(directory,name):name);
  }});
  vm.runInContext(fs.readFileSync(path.join(directory,'desktop-main.cjs'),'utf8'),context);await new Promise(resolve=>setImmediate(resolve));
  if(!lock){check(quits===1&&creations===0&&ipcHandlers.size===0,'Duplicate process exits before window/Tray/IPC initialization');return;}
  check(creations===1&&starts===1,'Primary instance initializes one controller without agent dependency');
  check(quits===0,'Collector failure never closes the dashboard');
  app.emit('second-instance',{},['cmd.exe','steam://open/main'],'arbitrary');check(restores===1&&creations===1,'Second instance ignores forwarded arguments and restores only');
  const trusted={sender:wc,senderFrame:frame};
  check(ipcHandlers.get('window:tray')(trusted).hidden&&hides===1,'Only bounded Tray IPC accepted');
  for(const args of [[trusted,'extra'],[{sender:wc,senderFrame:{url:policy.entryUrl}}],[{sender:{},senderFrame:frame}]]){
    assert.throws(()=>ipcHandlers.get('window:tray')(...args));checks++;
  }
  check(hides===1,'Rejected IPC requests do not hide window');
  assert.throws(()=>ipcHandlers.get('window:mode')(trusted,'cmd.exe'));checks++;
  check([...ipcHandlers.keys()].sort().join(',')===['devices:inspect-rgb','gamer:request','gamer:launch','gamer:launch-check','widget:version','window:state','window:mode','window:maximize','window:tray','monitoring:snapshot','diagnostics:snapshot','history:read','history:export','tools:request','tools:displays','tools:export','tools:import','tools:presentmon','tools:fps-attach','tools:fps-snapshot','tools:fps-stop','tools:game-sessions','tools:inspect-temp','tools:open-panel','panel:context','panel:snapshot','panel:close','panel:fullscreen','panel:main'].sort().join(','),'Only explicitly allowed window/metric/diagnostic channels');
  const diagnostic=await ipcHandlers.get('diagnostics:snapshot')(trusted,{v:1,scenario:'overview'});check(diagnostic.mode==='local'&&diagnostic.report.checks.find(c=>c.component==='agent_https').state==='unknown','Cache-only diagnostics do not probe or certify the operational HTTPS agent');
}
async function ownedShutdown(){
  let release,stops=0;const f=fixture({beforeExit:()=>{stops++;return new Promise(resolve=>release=resolve);}});
  f.controller.close();await Promise.resolve();check(!f.win.destroyed&&f.quits===0&&!f.trays[0].destroyed,'X waits for its monitoring without hiding or destroying Tray');
  f.controller.quit();check(stops===1,'Concurrent exits do not duplicate shutdown');release(true);await new Promise(setImmediate);
  check(f.quits===1&&f.win.destroyed&&f.trays[0].destroyed,'Successful monitoring stop completes normal exit');
  const failed=fixture({beforeExit:()=>Promise.resolve(false)});failed.controller.hideToTray();failed.controller.quit();await new Promise(setImmediate);
  check(failed.quits===0&&failed.win.visible&&!failed.trays[0].destroyed,'Stop failure preserves a visible app and live Tray, no orphaning');
}
async function main(){lifecycle();failuresAndMonitors();diskState();await ownedShutdown();await mainWiring(false);await mainWiring(true);await mainWiring(true,true);console.log(`PASS: ${checks} Tray, lifecycle, instance, persistence, monitor and IPC assertions; no native applications opened.`);}
if(require.main===module)main().catch(error=>{console.error(error.stack);process.exitCode=1;});
module.exports={fixture};
