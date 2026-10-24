// Node VM: storage and bridge contract only. No UDP, Android or native process.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../apps/android/app/src/main/assets/wol-ui.js'),'utf8');
const key = 'lone-wol-settings-v1';
const fixture = {mac:'AA:BB:CC:DD:EE:FF', broadcast:'192.0.2.255', port:7, futureField:'preserve'};
function setup(raw, {available=true, readError=false, writeError=false}={}) {
  const nodes = Object.fromEntries(['pcWakeBtn','wolFeedback','wolSettingsFeedback','wolMac','wolBroadcast','wolPort','wolSave'].map(id=>[id,{
    value:'',textContent:'',disabled:false,dataset:{},listeners:{},
    addEventListener(kind,fn){this.listeners[kind]=fn;},removeAttribute(name){if(name==='data-success')delete this.dataset.success;}
  }]));
  const calls=[], writes=[], timers=[];
  const window = {};
  if(available)window.LoneAndroid={sendWake(...args){calls.push(args);}};
  const storage = {getItem(name){assert.equal(name,key);if(readError)throw Error('unavailable');return raw??null;},setItem(name,value){
    if(writeError){const e=Error('blocked');e.name='QuotaExceededError';throw e;}writes.push([name,value]);
  }};
  const ctx=vm.createContext({window,document:{getElementById:id=>nodes[id]},localStorage:storage,
    setTimeout(fn){timers.push(fn);return timers.length;},clearTimeout(){}});
  vm.runInContext(source,ctx);
  return {nodes,calls,writes,timers,window,click:id=>nodes[id].listeners.click()};
}
let count=0;
function test(name,fn){fn();count++;}
test('existing raw settings and unknown fields preserved without writes',()=>{
  const raw=JSON.stringify(fixture,null,2), t=setup(raw);
  assert.equal(t.nodes.wolMac.value,fixture.mac);assert.equal(t.nodes.wolPort.value,'7');
  t.window.loneWolUI.syncFields();assert.deepEqual(t.writes,[]);
  t.click('pcWakeBtn');t.click('pcWakeBtn');assert.deepEqual(t.calls,[[fixture.mac,fixture.broadcast,7]]);
  assert.deepEqual(t.writes,[]);assert.equal(t.nodes.pcWakeBtn.disabled,true);
  t.window.onLoneWakeResult({ok:true});assert.equal(t.nodes.pcWakeBtn.disabled,false);
  assert.ok(t.nodes.wolFeedback.textContent.includes('Pacote Wake-on-LAN enviado'));
});
test('absence does not persist defaults on load',()=>assert.deepEqual(setup(null).writes,[]));
test('malformed records fail closed and stay intact until explicit save',()=>{
  for(const raw of ['{bad','null','[]','"string"']){
    const t=setup(raw);assert.equal(t.nodes.pcWakeBtn.disabled,true);t.click('pcWakeBtn');assert.deepEqual(t.calls,[]);assert.deepEqual(t.writes,[]);
    Object.entries({wolMac:fixture.mac,wolBroadcast:fixture.broadcast,wolPort:'9'}).forEach(([k,v])=>t.nodes[k].value=v);
    t.click('wolSave');assert.equal(t.writes.length,1);assert.equal(t.nodes.pcWakeBtn.disabled,false);
  }
});
test('save validates, normalizes and retains extensions',()=>{
  const t=setup(JSON.stringify(fixture));t.nodes.wolMac.value='aa-bb-cc-dd-ee-ff';t.nodes.wolPort.value='9';t.click('wolSave');
  assert.deepEqual(JSON.parse(t.writes[0][1]),{...fixture,port:9});
});
test('invalid MAC, IPv4 and unsafe UDP port never persist or send',()=>{
  for(const [field,value] of [['wolMac','bad'],['wolBroadcast','999.1.1.1'],['wolBroadcast','192.000.2.255'],['wolPort','80']]){
    const t=setup(JSON.stringify(fixture));t.nodes[field].value=value;t.click('wolSave');assert.deepEqual(t.writes,[]);assert.deepEqual(t.calls,[]);
    t.window.loneWolUI.syncFields();assert.equal(t.nodes.wolPort.value,'7');
  }
});
test('unsaved edits do not change outbound packet',()=>{
  const t=setup(JSON.stringify(fixture));t.nodes.wolMac.value='11:22:33:44:55:66';t.click('pcWakeBtn');
  assert.deepEqual(t.calls,[[fixture.mac,fixture.broadcast,7]]);
});
test('storage write failure keeps prior saved configuration',()=>{
  const t=setup(JSON.stringify(fixture),{writeError:true});t.nodes.wolPort.value='9';t.click('wolSave');
  assert.deepEqual(t.writes,[]);t.click('pcWakeBtn');assert.equal(t.calls[0][2],7);
  assert.ok(t.nodes.wolSettingsFeedback.textContent.includes('anterior foi mantida'));
});
test('read failure never silently overwrites',()=>{const t=setup(null,{readError:true});assert.equal(t.nodes.pcWakeBtn.disabled,true);assert.deepEqual(t.writes,[]);});
test('no native sender cannot simulate successful send',()=>{const t=setup(JSON.stringify(fixture),{available:false});t.click('pcWakeBtn');assert.deepEqual(t.calls,[]);assert.equal(t.nodes.pcWakeBtn.disabled,true);});
test('timeout does not resend or confirm power state',()=>{const t=setup(JSON.stringify(fixture));t.click('pcWakeBtn');t.timers[0]();assert.equal(t.calls.length,1);assert.ok(t.nodes.wolFeedback.textContent.includes('não verificado'));});
test('negative callback reports failure',()=>{const t=setup(JSON.stringify(fixture));t.click('pcWakeBtn');t.window.onLoneWakeResult({ok:false});assert.equal(t.nodes.wolFeedback.dataset.success,'false');});
console.log(`PASS: ${count} Android WoL storage/validation scenarios; zero real packet sends.`);
