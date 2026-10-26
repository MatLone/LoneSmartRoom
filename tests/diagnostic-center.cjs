'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{EventEmitter}=require('node:events');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'apps/windows-ui');
const model=require('../apps/windows-ui/diagnostics-model.js');
const {createDiagnosticsHost,loadFixtures}=require('../apps/windows-ui/diagnostics-host.cjs');
const fixtures=loadFixtures();let checks=0;
function check(value,label){assert(value,label);checks++;}
const clone=x=>JSON.parse(JSON.stringify(x));
const envelope=scenario=>({v:1,mode:'simulation',scenario,error:null,report:fixtures[scenario]});
function projections(){
  const states=new Set();
  for(const scenario of model.scenarios){
    const report=fixtures[scenario];check(model.validate(report),'Approved Python fixture: '+scenario);
    const view=model.project(envelope(scenario));check(view.simulation&&view.cards.length===7,'Seven explicitly simulated cards');
    check(view.pending.length===4,'All pending issues retained');
    view.cards.forEach(c=>{states.add(c.label);check(c.simulated&&c.details.every(d=>!d.message.includes('fixture-private-error')),'Sanitized fixture provenance');});
  }
  check(['Saudável','Inativo normalmente','Indisponível','Desatualizado','Falha','Não verificado'].every(s=>states.has(s)),'All six health presentations');
  const get=(s,id)=>model.project(envelope(s)).cards.find(c=>c.id===id);
  check(get('offline','https').label==='Indisponível'&&get('offline','https').summary.includes('não confirma'),'Offline never confirms PC powered off');
  check(get('listener-mismatch','https').label==='Falha','Proven simulated listener mismatch');
  check(get('auth-failure','https').label==='Falha','Simulated authentication failure');
  check(get('pipe-absent','pipe').label==='Indisponível','Absent pipe');
  check(get('inactive','monitoring').label==='Inativo normalmente','Normal inactivity');
  check(get('sensor-unavailable','sensors').label==='Indisponível','Unsupported sensor not healthy');
  check(get('stale','sensors').label==='Desatualizado','Old metrics not promoted');
  check(get('recovered','https').label==='Saudável','Recovery after failure');
  check(get('startup-inconclusive','startup').label==='Não verificado','Login dispatch inconclusive');
  check(get('healthy','security').label==='Não verificado','Healthy subsets do not certify overall security');
  check(get('provider-error','monitoring').label==='Falha','Provider verification failure');
  for(const mutate of [r=>{r.simulation=false;},r=>{r.schema_version=2;},r=>{r.repair_capability=true;},
    r=>{r.checks[0].evidence_kind='observed';},r=>{r.checks[0].age_seconds=10;},r=>{r.checks[0].observed_at='2026-10-27T12:00:00Z';},
    r=>{r.checks[0].age_seconds=NaN;},r=>{r.checks[0].detail_code='private value';},r=>{r.checks[0].extra='secret';},
    r=>{r.checks[0].component='arbitrary';},r=>{r.checks[1]=clone(r.checks[0]);},r=>{r.generated_at='2026-02-30T12:00:00Z';},
    r=>{r.checks[0].valid=false;},r=>{r.checks[0].last_communication='tomorrow';},r=>{r.checks[0].age_seconds=Infinity;},
    r=>{r.checks[0].code='provider_unknown';},r=>{r.checks[0].detail_code='tls_identity_failed';},
    r=>{r.checks[3].freshness_seconds=11;},r=>{r.checks[3].state='healthy';r.checks[3].observed_at='2026-10-26T11:59:40Z';},
    r=>{r.extra='x'.repeat(17000);},r=>{r.checks[2].last_communication='2026-10-26T12:00:00Z';}]){
    const report=clone(fixtures.healthy);mutate(report);check(!model.validate(report),'Reject invalid report');
    check(model.project({...envelope('healthy'),report}).cards.every(c=>c.state==='unknown'),'Invalid data never healthy');
  }
  for(const value of [null,{},[],{v:2,scenario:'healthy'},{v:1,scenario:'../private'},{v:1,scenario:'healthy',path:'C:/private'},
    {v:1,scenario:'__proto__'},{v:1,scenario:'x'.repeat(1000)},{v:1,scenario:1}])check(!model.request(value),'Reject invalid request');
  check(!Object.hasOwn(model.project(envelope('healthy')),'credentials'),'No credentials in view');
}
async function hosts(){
  const disabled=createDiagnosticsHost();check((await disabled.snapshot({v:1,scenario:'overview'})).error==='disabled','Disabled outside explicit development');
  let clock=0,calls=0;const host=createDiagnosticsHost({enabled:true,now:()=>clock,provider:s=>{calls++;return fixtures[s];}});
  check((await host.snapshot({v:1,scenario:'healthy'})).report.simulation,'Simulated report only');
  check((await host.snapshot({v:1,scenario:'healthy'})).error==='rate_limited','Rate limit');check(calls===1,'Rejected requests do not invoke provider');
  clock+=500;let first=await host.snapshot({v:1,scenario:'healthy'});first.report.checks[0].state='changed';clock+=500;
  check((await host.snapshot({v:1,scenario:'healthy'})).report.checks[0].state==='healthy','Mutation cannot change catalogue');
  host.stop();clock+=500;check((await host.snapshot({v:1,scenario:'overview'})).error==='disabled','Stop disables queries');
  check(host.diagnostics().operationalReaders===false,'No operational readers');
  check((await host.snapshot({v:1,scenario:'../private'})).error==='invalid_request','Fixed scenario boundary');
  const throwing=createDiagnosticsHost({enabled:true,provider:()=>{throw Error('token=private');}});
  check((await throwing.snapshot({v:1,scenario:'overview'})).error==='provider_unavailable','Sanitized exception');
  const invalid=createDiagnosticsHost({enabled:true,provider:()=>({...fixtures.healthy,simulation:false})});
  check((await invalid.snapshot({v:1,scenario:'healthy'})).error==='invalid_report','Real evidence rejected by demo host');
  let release,timer;
  const busy=createDiagnosticsHost({enabled:true,now:()=>clock,provider:()=>new Promise(r=>release=r),schedule:f=>{timer=f;return 1;},cancel(){}});
  const pending=busy.snapshot({v:1,scenario:'healthy'});await Promise.resolve();clock+=500;
  check((await busy.snapshot({v:1,scenario:'healthy'})).error==='busy','No unbounded request queue');
  timer();check((await pending).error==='provider_timeout','Bounded provider wait');release(fixtures.healthy);
}
async function bridge(){
  let api;const requests=[];
  vm.runInNewContext(fs.readFileSync(path.join(dir,'preload.cjs'),'utf8'),{require:name=>{
    check(name==='electron','Preload imports no generic native modules');return {contextBridge:{exposeInMainWorld:(name,value)=>{check(name==='loneDesktop','Existing limited bridge');api=value;}},ipcRenderer:{invoke:(...args)=>{requests.push(args);return Promise.resolve(null);},on(){},removeListener(){},send(){}}};
  }});
  for(const scenario of model.scenarios)await api.getDiagnostics(scenario);
  check(requests.every(r=>r[0]==='diagnostics:snapshot'&&model.request(r[1])),'Fixed channel and bounded v1 request');
  for(const value of ['cmd.exe','../private',{},null]){
    await assert.rejects(api.getDiagnostics(value));checks++;
  }
  check(requests.length===model.scenarios.length,'Invalid input rejected before IPC');
  check(!Object.keys(api).some(k=>/exec|shell|pipe|file|credential/i.test(k)),'No arbitrary privileged bridge');
}
async function rendererComponents(){
  const nodes=new Map(),timers=new Map(),pending=[],events=new Map();let nextTimer=0;
  class Node{
    constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.attrs={};this.handlers={};this.hidden=false;this.disabled=false;this.textContent='';}
    append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
    get lastElementChild(){return this.children.at(-1);}
    setAttribute(name,value){this.attrs[name]=value;}addEventListener(name,handler){this.handlers[name]=handler;}
    focus(){document.activeElement=this;}scrollIntoView(){this.scrolled=true;}
  }
  for(const id of ['diagnosticCenter','diagnosticGrid','diagnosticScenario','diagnosticRefresh','diagnosticError','diagnosticDemo','diagnosticClock','diagnosticPending','diagnosticOpen','diagnosticClose'])nodes.set(id,new Node());
  const document={activeElement:null,getElementById:id=>nodes.get(id),createElement:tag=>new Node(tag),createElementNS:(_ns,tag)=>new Node(tag)};
  const center=nodes.get('diagnosticCenter'),grid=nodes.get('diagnosticGrid'),select=nodes.get('diagnosticScenario');center.hidden=true;select.value='overview';
  const window={loneDiagnosticModel:model,loneDesktop:{getDiagnostics:()=>new Promise((resolve,reject)=>pending.push({resolve,reject}))},addEventListener:(name,fn)=>events.set(name,fn)};
  vm.runInNewContext(fs.readFileSync(path.join(dir,'diagnostics-renderer.js'),'utf8'),{window,document,
    setTimeout:(fn,ms)=>{const id=++nextTimer;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id)});
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  const tick=ms=>{for(const [id,t] of [...timers])if(t.ms===ms){timers.delete(id);t.fn();}};
  const click=id=>nodes.get(id).handlers.click();
  check(grid.children.length===7&&grid.children.every(c=>c.dataset.state==='unknown'),'Renderer starts with no fabricated health');
  click('diagnosticOpen');check(!center.hidden&&center.scrolled&&pending.length===1,'Open explicitly queries restricted API');
  pending.shift().resolve(envelope('overview'));await flush();
  check(grid.children.length===7&&grid.children.some(c=>c.dataset.state==='healthy'),'Actual renderer renders validated demonstration');
  check(center.dataset.simulation==='true'&&!nodes.get('diagnosticDemo').hidden,'Actual renderer labels simulation');
  check(grid.attrs['aria-busy']==='false','Busy state released');tick(550);
  click('diagnosticRefresh');click('diagnosticClose');
  check(center.hidden&&document.activeElement===nodes.get('diagnosticOpen'),'Close restores focus');
  pending.shift().resolve(envelope('auth-failure'));await flush();
  check(grid.children.find(c=>c.dataset.card==='https').dataset.state==='healthy','Closed generation ignores late error response');
  click('diagnosticOpen');pending.shift().reject(Error('credential=private-value'));await flush();
  check(grid.children.every(c=>c.dataset.state==='unknown'),'Provider exception clears previously healthy cards');
  check(!nodes.get('diagnosticError').hidden&&!nodes.get('diagnosticError').textContent.includes('private-value'),'Only sanitized provider error appears');
  tick(550);click('diagnosticRefresh');tick(2500);await flush();
  check(grid.children.every(c=>c.dataset.state==='unknown'),'UI timeout never retains healthy state');
  check(nodes.get('diagnosticError').textContent.includes('prazo'),'UI timeout explicitly explained');
  pending.shift().resolve(envelope('overview'));await flush();tick(550);
  click('diagnosticRefresh');pending.shift().resolve(envelope('recovered'));await flush();
  check(grid.children.find(c=>c.dataset.card==='https').dataset.state==='healthy','Actual renderer recovers after failed request');
  check(nodes.get('diagnosticError').hidden,'Recovery removes old error');
  events.get('pagehide')();check(![...timers.values()].some(t=>t.ms===550),'Page exit cancels presentation debounce');
}
async function mainIpc(){
  const app=new EventEmitter(),paths=[],handlers=new Map(),listeners=new Map();let controller;
  const policy=require('../apps/windows-ui/desktop-policy.cjs');
  const wc={mainFrame:{url:policy.entryUrl},isDestroyed:()=>false};
  const errors=[];
  Object.assign(app,{isPackaged:false,getVersion:()=>require('../apps/windows-ui/package.json').version,
    commandLine:{appendSwitch(){}},setPath:(...args)=>paths.push(args),getPath:()=>'/isolated',requestSingleInstanceLock:()=>true,whenReady:()=>Promise.resolve(),quit(){}});
  const fakeController={window:{webContents:wc},start(){},state:()=>({mode:'dashboard'}),quit(){},restoreCurrent(){},setMode(){},toggleMaximize(){},hideToTray(){},minimize(){},close(){}};
  const mod={exports:{}};
  vm.runInNewContext(fs.readFileSync(path.join(dir,'desktop-main.cjs'),'utf8'),{__dirname:dir,module:mod,console:{error:(...x)=>errors.push(x)},
    process:{argv:['electron','apps/windows-ui','--lone-development-review','--lone-diagnostics-preview','--lone-monitoring-development','--lone-gpu-development'],env:{LONE_DIAGNOSTICS_REVIEW_ID:'a'.repeat(32),LONE_MONITORING_RUN_ID:'b'.repeat(32)}},
    require:name=>{
      if(name==='electron')return {app,BrowserWindow:function(){throw Error('Not used in mocked controller');},ipcMain:{handle:(k,v)=>handlers.set(k,v),on:(k,v)=>listeners.set(k,v)},screen:{},session:{defaultSession:{setPermissionRequestHandler(){},setPermissionCheckHandler(){},webRequest:{onBeforeRequest(){}}}},Tray:function(){},Menu:{}};
      if(name==='node:fs')return {mkdirSync(){}};
      if(name==='./desktop-preferences.cjs')return {createStore:()=>({})};
      if(name==='./desktop-window.cjs')return {createController:()=>{controller=fakeController;return controller;}};
      if(name==='./monitoring-host.cjs')throw Error('Operational monitoring forbidden');
      return require(name.startsWith('./')?path.join(dir,name):name);
    }});
  await new Promise(resolve=>setImmediate(resolve));
  check(controller&&handlers.has('diagnostics:snapshot')&&errors.length===0,'Actual main registers dedicated route');
  check(paths.length===4&&paths.every(([,p])=>p.includes('windows-diagnostics-review')),'All profile directories isolated');
  check(mod.exports.monitoringDiagnostics()===null,'Conflicting monitoring flags cannot activate collection');
  const event={sender:wc,senderFrame:wc.mainFrame},handler=handlers.get('diagnostics:snapshot');
  check((await handler(event,{v:1,scenario:'overview'})).report.simulation,'Trusted main mediation');
  for(const wrong of [{sender:{},senderFrame:wc.mainFrame},{sender:wc,senderFrame:{url:policy.entryUrl}},{sender:wc,senderFrame:{url:'https://invalid/'}}]){
    assert.throws(()=>handler(wrong,{v:1,scenario:'healthy'}));checks++;
  }
  assert.throws(()=>handler(event,{v:1,scenario:'healthy'},'extra'));checks++;
  app.emit('will-quit');check(mod.exports.diagnosticPreview().closed,'Normal exit closes fixture host');
}
function staticPreservation(){
  const html=fs.readFileSync(path.join(dir,'index.html'),'utf8'),renderer=fs.readFileSync(path.join(dir,'diagnostics-renderer.js'),'utf8');
  check((html.match(/role="tab"/g)||[]).length===3,'Exactly three existing tabs');
  check(html.includes('diagnosticCenter')&&html.includes('panel-monitor'),'Central belongs to Monitoramento PC');
  check(html.includes("connect-src 'none'")&&html.includes("script-src 'self'"),'Strict renderer CSP retained');
  check(!/\bfetch\s*\(|XMLHttpRequest|WebSocket|innerHTML|setInterval/.test(renderer),'No network, raw HTML or recurring polling');
  const host=fs.readFileSync(path.join(dir,'diagnostics-host.cjs'),'utf8');
  check(!/child_process|https\b|node:net|windows_readers|DPAPI|winreg/.test(host),'Fixture host cannot reach operational readers');
  const policy=require('../apps/windows-ui/desktop-policy.cjs'),{pathToFileURL}=require('node:url');
  for(const f of ['diagnostics-contract.js','diagnostics-model.js','diagnostics-renderer.js','diagnostics.css'])check(policy.allowedResource(pathToFileURL(path.join(dir,f)).href),'Fixed approved UI resource');
  check(!policy.allowedResource(pathToFileURL(path.join(dir,'diagnostics-fixtures.json')).href),'Renderer cannot read fixture file directly');
  const files=require('../apps/windows-ui/package.json').build.files;
  for(const f of ['diagnostics-host.cjs','diagnostics-fixtures.json','diagnostics-contract.js','diagnostics-model.js','diagnostics-renderer.js','diagnostics.css'])check(files.includes(f),'Future package include list, without packaging');
}
(async()=>{projections();await hosts();await bridge();await rendererComponents();await mainIpc();staticPreservation();console.log(`PASS: ${checks} diagnostic center assertions; fixtures only, no Electron or sensors.`);})().catch(error=>{console.error(error);process.exitCode=1;});
