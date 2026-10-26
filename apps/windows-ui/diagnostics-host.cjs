'use strict';
// Main-process fixture reader only. No Python/Windows reader/HTTPS/pipe imports.
const fs=require('node:fs'),path=require('node:path'),model=require('./diagnostics-model.js');
const MAX_BUNDLE=128*1024;
function loadFixtures(){
  const filename=path.join(__dirname,'diagnostics-fixtures.json');
  if(fs.statSync(filename).size>MAX_BUNDLE)throw Error('fixture_limit');
  const raw=fs.readFileSync(filename);if(raw.length>MAX_BUNDLE)throw Error('fixture_limit');
  const value=JSON.parse(raw.toString('utf8'));
  if(value.v!==1||value.simulation!==true||value.clock_policy!=='frozen'||
     Object.keys(value.scenarios||{}).length!==model.scenarios.length||
     !model.scenarios.every(s=>model.validate(value.scenarios[s])))throw Error('fixture_contract');
  return value.scenarios;
}
function createDiagnosticsHost({enabled=false,provider=null,now=Date.now,schedule=setTimeout,cancel=clearTimeout}={}){
  let fixtures=null,last=-Infinity,inFlight=false,closed=false;
  const response=(scenario,error=null,report=null)=>({v:1,mode:enabled?'simulation':'disabled',scenario,error,report});
  async function snapshot(query){
    if(!model.request(query))return response(null,'invalid_request');
    if(!enabled||closed)return response(query.scenario,'disabled');
    const stamp=now();
    if(!Number.isFinite(stamp)||stamp<last||stamp-last<500)return response(query.scenario,'rate_limited');
    if(inFlight)return response(query.scenario,'busy');
    last=stamp;inFlight=true;let timer;
    try{
      if(!provider&&!fixtures)fixtures=loadFixtures();
      const timed=new Promise(resolve=>{timer=schedule(()=>resolve(null),1000);timer?.unref?.();});
      const report=await Promise.race([Promise.resolve().then(()=>provider?provider(query.scenario):fixtures[query.scenario]),timed]);
      if(closed)return response(query.scenario,'disabled');
      if(report===null)return response(query.scenario,'provider_timeout');
      if(!model.validate(report))return response(query.scenario,'invalid_report');
      // Clone so a recipient/test cannot alter the immutable scenario catalogue.
      return response(query.scenario,null,JSON.parse(JSON.stringify(report)));
    }catch{return response(query.scenario,'provider_unavailable');}
    finally{if(timer!==undefined)cancel(timer);inFlight=false;}
  }
  return Object.freeze({snapshot,stop(){closed=true;fixtures=null;},
    diagnostics:()=>({simulation:enabled,operationalReaders:false,closed,inFlight,maxReportBytes:16384,minIntervalMs:500})});
}
module.exports={createDiagnosticsHost,loadFixtures};
