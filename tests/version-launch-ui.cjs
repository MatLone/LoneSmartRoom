// Node VM only: metadata rendering, native boundary, command states. No OS launch.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const directory = path.resolve(__dirname, '../apps/windows-ui');
function element() { return {textContent:'', disabled:false, listeners:{}, addEventListener(name,fn){this.listeners[name]=fn;}}; }
async function main() {
  const label = element(), window = {LoneAppInfo:{getVersionName:()=> '2.0.0-test.37'}};
  const context = vm.createContext({window, document:{getElementById:()=>label}, Promise});
  vm.runInContext(fs.readFileSync(path.join(directory,'app-version.js'),'utf8'),context);
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(label.textContent, 'Android · Versão 2.0.0-test.37');
  window.loneVersion.render('Prévia Android');
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(label.textContent, 'Prévia Android · Versão 2.0.0-test.37');
  const nodes = Object.fromEntries(['launchState','launchDetail','launchSteam','launchCs2','launchPermissions','launchQuery'].map(id=>[id,element()]));
  const requests = [];
  window.LoneAgent = {refreshAppPermissions(){},refreshLaunchResult(){},requestAppLaunch(app){requests.push(app);}};
  const launches=vm.createContext({window,document:{getElementById:id=>nodes[id]}});
  vm.runInContext(fs.readFileSync(path.join(directory,'app-launch.js'),'utf8'),launches);
  assert.equal(nodes.launchSteam.disabled,true);assert.equal(nodes.launchCs2.disabled,true);
  window.onLoneAppLaunch({kind:'permissions',allowed_apps:['steam']});
  assert.equal(nodes.launchSteam.disabled,false);assert.equal(nodes.launchCs2.disabled,true);
  nodes.launchSteam.listeners.click();assert.deepEqual(requests,['steam']);
  for(const [state,label] of [['requested','Solicitado'],['accepted','Aceito'],['executed','Executado'],['failed','Falha']]) {
    window.onLoneAppLaunch({state});assert.equal(nodes.launchState.textContent,label);
    if(state==='accepted')assert.equal(nodes.launchSteam.disabled,true);
  }
  assert.ok(!fs.readFileSync(path.join(directory,'app.js'),'utf8').includes('Versão 1.4'));
  console.log('PASS: dynamic native version, permission-gated app buttons and four command states; no app launched.');
}
main().catch(error=>{console.error(error.message);process.exit(1);});
