'use strict';
// Explicit development validation of existing fixed read-only Windows helpers.
// No installed app, sensor collector, HTTP agent, game, repair or external ping.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
async function main(){
 if(!['--read-only-development','--read-only-development --hardware-only','--read-only-development --network-only'].includes(process.argv.slice(2).join(' ')))throw Error('explicit_readonly_development_required');
 const {createProvider}=require('../apps/windows-ui/windows-read-provider.cjs');
 const {createService}=require('../apps/windows-ui/workbench-service.cjs');
 const run=crypto.randomBytes(16).toString('hex'),directory=path.join(root,'.cache/local-tool-validation',run);
 fs.mkdirSync(directory,{recursive:true});
 const provider=createProvider(),service=createService({directory,enabled:true,inventory:provider.inventory,network:provider.network});
 const results=[];const start=performance.now();
 const hardwareOnly=process.argv.includes('--hardware-only'),networkOnly=process.argv.includes('--network-only');let first=true;
 for(const kind of hardwareOnly?['hardware']:networkOnly?['network','network']:['hardware','memory','disks','network','processes','applications','startup','services','drivers','peripherals','games','events']){
  if(networkOnly&&!first)await new Promise(r=>setTimeout(r,3200));first=false;
  const at=performance.now();const value=await service.handle({v:1,op:'inventory',args:{kind}});
  const row={kind,state:value.state,source:value.source,observed_at:value.observed_at||null,items:value.items?.length||0,error:value.error||null,duration_ms:Math.round(performance.now()-at),simulation:value.simulation};
  if(kind==='hardware')row.sources={descriptor:value.extra?.cpu_descriptor_state||null,per_core:value.extra?.per_core_state||null,partial:value.extra?.partial??null,failures:value.extra?.failures||[]};
  if(kind==='hardware'&&value.state==='available'){row.cpu=value.items.map(x=>({name:x.name,logical_processors:x.logical_cores,physical_cores:x.physical_cores,reported_clock_mhz:x.reported_clock_mhz,max_clock_mhz:x.max_clock_mhz,cpu_temperature_celsius:x.cpu_temperature_celsius}));row.cores_observed=value.extra?.cores?.length||0;row.per_core=value.extra?.cores||[];row.clock_semantic=value.extra?.clock_semantic||null;}
  if(kind==='memory'&&value.state==='available')row.installed_bytes=value.items.reduce((n,x)=>n+(x.capacity_bytes||0),0);
  if(kind==='disks'&&value.state==='available')row.volumes=value.items.map(x=>({volume:x.name,total_bytes:x.capacity_bytes,free_bytes:x.free_bytes}));
  if(kind==='network'&&value.state==='available'){row.adapters=value.items.map((x,index)=>({index,link_bits_per_second:x.link_bits_per_second,download_bytes_per_second:x.download_bytes_per_second,upload_bytes_per_second:x.upload_bytes_per_second}));row.rate_interval_seconds=value.extra?.rate_interval_seconds??null;}
  results.push(row);
 }
 for(const kind of hardwareOnly||networkOnly?[]:['ping','dns']){
  const value=await service.handle({v:1,op:'network',args:{kind,target:'localhost'}});
  results.push({kind,scope:'loopback only; not Internet performance',state:value.state,items:value.items?.length||0,statistics:value.statistics||null,simulation:value.simulation});
 }
 service.close();
 const report={v:1,run,development:true,read_only:true,installed_app_started:false,agent_queried:false,repairs:false,hardware_collectors_started:false,elapsed_seconds:(performance.now()-start)/1000,results};
 fs.writeFileSync(path.join(directory,'report.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
