'use strict';
const assert=require('node:assert/strict'),{createProvider}=require('../apps/windows-ui/windows-read-provider.cjs');
let time=100000,counters={rx:100,tx:200},id='fixture-id',observed=100000,reads=0,checks=0;
const eq=(a,b)=>{assert.deepEqual(a,b);checks++;};
const p=createProvider({platform:'win32',now:()=>time,execute:(_program,_args,_options,done)=>{
 reads++;done(null,JSON.stringify({v:1,state:'available',source:'windows.readonly.network',simulation:false,observed_at:new Date(observed).toISOString(),extra:{},items:[{id,name:'same name',received_bytes:counters.rx,sent_bytes:counters.tx}]}));
}});
async function read(){return (await p.inventory('network')).items[0];}
(async()=>{
 let r=await read();eq(r.download_bytes_per_second,null);eq(r.upload_bytes_per_second,null);
 await read();eq(reads,1);time+=4000;observed+=4000;counters={rx:500,tx:200};r=await read();eq(r.download_bytes_per_second,100);eq(r.upload_bytes_per_second,0);
 time+=4000;observed+=4000;counters={rx:10,tx:300};r=await read();eq(r.download_bytes_per_second,null);eq(r.upload_bytes_per_second,25);
 time+=4000;observed+=4000;id='new-device-same-name';r=await read();eq(r.download_bytes_per_second,null);
 time+=4000;observed-=5000;r=await read();eq(r.download_bytes_per_second,null);
 time+=100000;observed+=100000;r=await read();eq(r.download_bytes_per_second,null);
 time-=1000;observed+=4000;counters={rx:10,tx:300};r=await read();eq(r.upload_bytes_per_second,0);eq(reads,7);
 console.log(`PASS: ${checks} network source-time, reset, adapter identity, zero/null and clock reversal checks; mock counters only`);
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
