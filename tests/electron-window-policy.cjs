'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),app=path.join(root,'apps/windows-ui');
const policy=require(path.join(app,'desktop-policy.cjs'));
let checks=0;const check=(value,message)=>{assert(value,message);checks++;};
async function main(){
 const frame={url:policy.entryUrl},wc={mainFrame:frame,isDestroyed:()=>false};
 check(policy.trustedSender({sender:wc,senderFrame:frame},wc),'Exact main-frame sender accepted');
 for(const event of [{sender:{},senderFrame:frame},{sender:wc,senderFrame:{url:policy.entryUrl}},{sender:wc,senderFrame:{url:'https://example.invalid'}},{sender:wc,senderFrame:null}])check(!policy.trustedSender(event,wc),'Untrusted frame rejected');
 check(!policy.trustedSender({sender:wc,senderFrame:frame},null),'No window rejected');
 check(policy.allowedResource(policy.entryUrl),'Exact UI file allowed');
 for(const url of ['http://127.0.0.1:8776/v2/status','https://127.0.0.1:8776/v2/status','steam://open/main','file:///C:/Windows/win.ini',policy.entryUrl+'?other=1','data:text/html,bad'])check(!policy.allowedResource(url),'No operational or arbitrary resource URL');
 for(const value of [null,{},[],['widget'],0,'steam','Widget','widget;cmd.exe','https://example.invalid'])check(!policy.validMode(value),'Window mode enumeration');
 check(policy.validMode('dashboard')&&policy.validMode('widget'),'Two visual modes accepted');
 for(const area of [{x:0,y:0,width:1920,height:1040},{x:-1280,y:0,width:1280,height:720},{x:0,y:0,width:800,height:600}]){
  for(const mode of ['dashboard','widget']){
   const b=policy.initialBounds(mode,area);check(b.x>=area.x&&b.y>=area.y&&b.x+b.width<=area.x+area.width&&b.y+b.height<=area.y+area.height,'Window fits work area');
  }
 }
 const calls=[],listeners=new Map();let api;
 const ipc={invoke:(name,...args)=>{calls.push([name,...args]);return Promise.resolve({mode:'dashboard'});},send:(name,...args)=>calls.push([name,...args]),on:(name,handler)=>listeners.set(name,handler),removeListener:(name,handler)=>{if(listeners.get(name)===handler)listeners.delete(name);}};
 const context=vm.createContext({require:name=>{assert.equal(name,'electron');return {contextBridge:{exposeInMainWorld:(name,value)=>{assert.equal(name,'loneDesktop');api=value;}},ipcRenderer:ipc};}});
 vm.runInContext(fs.readFileSync(path.join(app,'preload.cjs'),'utf8'),context);
 check(Object.keys(api).sort().join(',')===['minimizeToTray','close','getVersion','getWindowState','minimize','onWindowState','setWindowMode','toggleMaximize'].sort().join(','),'Strict eight-method window API');
 for(const mode of ['dashboard','widget'])await api.setWindowMode(mode);
 const count=calls.length;
 for(const bad of [null,{},[],'steam','cmd.exe','widget && calc']){await assert.rejects(api.setWindowMode(bad));checks++;}
 check(calls.length===count,'Rejected input never reaches IPC');
 let received;const remove=api.onWindowState(value=>{received=value;});const value={mode:'widget'};listeners.get('window:state')({sender:'not exposed'},value);check(received===value,'IPC event never exposed to renderer');remove();check(listeners.size===0,'Specific listener unsubscribes');
 await api.minimizeToTray();api.minimize();api.close();await api.getVersion();await api.getWindowState();await api.toggleMaximize();
 check(calls.every(([name])=>['window:mode','widget:minimize','widget:close','widget:version','window:state','window:maximize','window:tray'].includes(name)),'Only visual IPC channels');
 const html=fs.readFileSync(path.join(app,'index.html'),'utf8');
 check(html.includes('Seu espaço, sob controle')&&!html.includes('audit-data.js'),'Neutral title and no stale audit snapshot in application');
 check(!/<script[^>]+src="(?:app|agent-status|app-launch)\.js"/.test(html),'Legacy simulations and operational adapters not loaded');
 check(html.includes("connect-src 'none'"),'Renderer networking prohibited');
 const source=fs.readFileSync(path.join(app,'desktop.js'),'utf8');
 check(!/\b(?:fetch|XMLHttpRequest|WebSocket|requestAppLaunch|localStorage|sessionStorage)\s*[.(]/.test(source),'Renderer has no operational client or storage writes');
 const pkg=JSON.parse(fs.readFileSync(path.join(app,'package.json'),'utf8'));for(const n of ['desktop-main.cjs','desktop-policy.cjs','desktop-window.cjs','desktop-preferences.cjs','desktop.js','desktop.css','preload.cjs'])check(pkg.build.files.includes(n),'Packaged integrated resources included');
 console.log(`PASS: ${checks} window policy/preload/packaging assertions; no native process actions.`);
}
main().catch(error=>{console.error(error.stack);process.exit(1);});
