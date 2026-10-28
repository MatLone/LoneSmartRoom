'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),{execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),program=path.join(process.env.SystemRoot||'C:\\Windows','System32/WindowsPowerShell/v1.0/powershell.exe');
let checks=0;for(const name of ['all','cores-fail','descriptor-fail','both-fail']){
 const raw=execFileSync(program,['-NoProfile','-NonInteractive','-File',path.join(root,'tests/fixtures/hardware-provider-mock.ps1'),'-Case',name],{cwd:root,shell:false,encoding:'utf8',windowsHide:true});
 const value=JSON.parse(raw);assert(!raw.includes('PRIVATE_PATH_SHOULD_NOT_LEAK'));checks++;
 const failedDescriptor=['descriptor-fail','both-fail'].includes(name),failedCores=['cores-fail','both-fail'].includes(name);
 assert.equal(value.items.length,failedDescriptor?0:1);assert.equal(value.extra.cores.length,failedCores?0:2);checks+=2;
 assert.equal(value.state,name==='both-fail'?'unavailable':'available');assert.equal(value.extra.partial,name!=='all');checks+=2;
 assert.equal(value.extra.cpu_descriptor_state,failedDescriptor?'unavailable':'available');assert.equal(value.extra.per_core_state,failedCores?'unavailable':'available');checks+=2;
 if(!failedCores){assert.equal(value.extra.cores[0].utilization_percent,0);checks++;}
 if(!failedDescriptor){assert.equal(value.items[0].cpu_temperature_celsius,null);assert.equal(value.items[0].reported_clock_mhz,2500);checks+=2;}
}
console.log(`PASS: ${checks} isolated PowerShell source-partition, zero/null and sanitized-error checks; mocked CIM only`);
