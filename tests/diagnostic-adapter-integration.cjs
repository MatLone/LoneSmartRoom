'use strict';
const assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..'),{createAdapterProvider}=require('../apps/windows-ui/diagnostic-adapter-provider.cjs'),model=require('../apps/windows-ui/diagnostics-model.js');
const {createDiagnosticsHost}=require('../apps/windows-ui/diagnostics-host.cjs');
(async()=>{
 let checks=0;const check=x=>{assert(x);checks++;};
 const disabled=createAdapterProvider({root});await assert.rejects(disabled.get('healthy'));checks++;check(!disabled.stats().started);
 const provider=createAdapterProvider({root,enabled:true});let now=0;
 const host=createDiagnosticsHost({enabled:true,provider:s=>provider.get(s),now:()=>now});
 for(const scenario of model.scenarios){
  const raw=await host.snapshot({v:1,scenario});check(!raw.error);check(raw.report.simulation===true);check(raw.evidence.security.known_issues.length===5);
  const view=model.project(raw);check(view.cards.length===7);check(view.simulation===true);now+=600;
 }
 await assert.rejects(provider.get('../secrets'));checks++;
 check(provider.stats().operationalReaders===false);provider.stop();host.stop();
 await assert.rejects(provider.get('healthy'));checks++;
 console.log(`PASS: ${checks} five-adapter -> bounded cache -> Python mock worker -> Electron main host -> UI-model assertions; no operational probes`);
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
