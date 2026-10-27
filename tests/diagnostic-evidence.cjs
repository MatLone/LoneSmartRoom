'use strict';
// Pure Node interoperability with Python-generated mock reports; no Electron.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),model=require('../apps/windows-ui/diagnostics-model.js');
const {createDiagnosticsHost}=require('../apps/windows-ui/diagnostics-host.cjs');
const fixtures=require('./fixtures/diagnostic-evidence.json').scenarios;
const clone=x=>JSON.parse(JSON.stringify(x));let checks=0;
const check=(value,label)=>{assert(value,label);checks++;};
function projected(bundle){
  return model.project({v:1,mode:'simulation',scenario:'overview',error:null,report:bundle.report,
    evidence:{schema_version:1,simulation:true,security:bundle.security}});
}
(async()=>{
  const states=new Set();
  for(const [name,bundle] of Object.entries(fixtures)){
    check(model.adapterBundle(bundle),'Versioned adapter bundle: '+name);
    const view=projected(bundle);check(view.simulation&&view.cards.length===7,'Card count and simulation retained');
    check(view.pending.length===5&&view.pending.some(p=>p.id==='crashpad'),'Five independent known issues remain open');
    view.cards.forEach(card=>{states.add(card.label);check(card.simulated,'No observation disguised as real');});
    check(!JSON.stringify(view).includes('secret'),'View contains no secret material');
    const host=createDiagnosticsHost({enabled:true,provider:()=>clone(bundle)});
    const response=await host.snapshot({v:1,scenario:'overview'});
    check(response.error===null&&model.project(response).cards.length===7,'Main host passes only valid report/evidence summary');
    check(model.bytes(response)<=18432,'Bounded output envelope');host.stop();
  }
  check(['Saudável','Inativo normalmente','Indisponível','Desatualizado','Falha','Não verificado'].every(s=>states.has(s)),'All six health presentations from actual adapter logic');
  const card=(scenario,id)=>projected(fixtures[scenario]).cards.find(c=>c.id===id);
  check(card('listener-mismatch','https').state==='error','Correct process with incorrect listener rejected');
  check(card('listener-mismatch','security').state==='error','Sidecar cannot conceal verified listener failure');
  check(card('auth-failure','security').state==='error','Unknown partial summary cannot conceal authentication failure');
  check(card('offline','https').state==='offline','Offline is unavailable');
  check(card('inactive','monitoring').state==='inactive','Closed collector is normally inactive');
  check(card('reconnecting','monitoring').state==='unknown','Reconnect cannot expose old healthy metrics');
  check(card('reconnected','monitoring').state==='healthy','Fresh generation resumes health');
  check(card('security-failure','security').state==='error','Security failure projected without inventing an agent fault');
  check(card('security-failure','https').state==='healthy','Security and service verdicts stay distinct');
  check(card('startup-inconclusive','startup').state==='unknown','Healthy HTTPS cannot prove Run dispatch');
  for(const mutate of [b=>{b.simulation=false;},b=>{b.schema_version=2;},b=>{b.report.checks[0].evidence_kind='observed';},
    b=>{b.security.state='healthy';},b=>{b.security.known_issues=[];},b=>{b.security.checks[0].authorized=false;},
    b=>{b.security.checks[0].private_key='PRIVATE-MARKER';},b=>{b.security.checks[0].age_seconds=NaN;},
    b=>{b.security.checks[0].checked_at='2026-10-27T12:00:00.000Z';},b=>{b.security.repair_capability=true;},
    b=>{b.security.checks[0].checked_at='2026-10-26T12:00:01.000Z';b.security.checks[0].age_seconds=1;},
    b=>{b.security.checks[0].stale=true;},b=>{b.security.state='error';},b=>{b.security.checks.push(b.security.checks[0]);},
    b=>{b.credentials='PRIVATE-MARKER';},b=>{b.security.simulation=false;},b=>{b.report.extra='PRIVATE-MARKER';}]){
    const bundle=clone(fixtures.online);mutate(bundle);
    check(!model.adapterBundle(bundle),'Malformed/private/real evidence rejected');
    const host=createDiagnosticsHost({enabled:true,provider:()=>bundle});
    const response=await host.snapshot({v:1,scenario:'overview'});
    check(response.error==='invalid_report','Host fails closed');
    check(!JSON.stringify(response).includes('PRIVATE-MARKER'),'No sensitive payload relayed');
    check(model.project(response).cards.every(c=>c.state==='unknown'),'Failed validation never keeps previous health');host.stop();
  }
  const base=clone(fixtures.online);
  base.report=clone(fixtures.stale.report);
  base.security.checks.forEach(r=>{r.checked_at='2026-10-26T11:59:50.000Z';r.age_seconds=15;r.stale=true;});base.security.state='stale';
  check(model.adapterBundle(base),'Report and original security-check time correlation preserved');
  check(projected(base).cards.find(c=>c.id==='security').state==='stale','Old check is visibly stale');
  const unknown=clone(fixtures.online);
  unknown.security.checks.forEach(r=>{r.authorized=false;r.result='not_checked';r.checked_at=null;r.age_seconds=null;r.stale=false;});
  check(model.adapterBundle(unknown),'Unperformed unauthorized checks stay explicit');
  const securityCard=projected(unknown).cards.find(c=>c.id==='security');
  check(securityCard.checkedAt===null&&securityCard.state==='unknown','No invented timestamp or healthy verdict for absent checks');
  const source=fs.readFileSync(path.join(root,'diagnostics/evidence_adapters.py'),'utf8')+fs.readFileSync(path.join(root,'diagnostics/evidence_cache.py'),'utf8');
  check(!/windows_readers|WinDLL|subprocess|winreg|import socket|import ssl|DPAPI|os\.startfile/.test(source),'New adapter path has no operational capabilities');
  console.log(`PASS: ${checks} adapter-to-main/preload-contract/view assertions; mock data only.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
