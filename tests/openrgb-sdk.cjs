'use strict';
const assert=require('node:assert/strict'),{descriptor,fakeSdk}=require('./openrgb-fixture.cjs'),sdk=require('../apps/windows-ui/openrgb-sdk.cjs');
let checks=0;const check=(v)=>{assert(v);checks++;};
(async()=>{
 const parsed=sdk.parseDevice(descriptor());check(parsed.name==='SIMULATED Nollie');check(parsed.zones.length===2);check(parsed.modes[1].brightness===55);check(parsed.colors[0]==='#123456');const reversed=require('./openrgb-fixture.cjs').mode(1);reversed.speedMin=9;reversed.speedMax=0;check(sdk.parseDevice(descriptor({modes:[reversed],activeMode:0})).modes[0].speedMin===9);
 for(let i=0;i<descriptor().length;i+=7){assert.throws(()=>sdk.parseDevice(descriptor().subarray(0,i)));checks++;}
 for(const id of [50,140,150,151,1000,1100,1102,-1,'1050']){assert.throws(()=>sdk.frame(id));checks++;}
 for(const v of ['red','#ffff','#ff0000ff','000000']){assert.throws(()=>sdk.ledsData([v]));checks++;}
 const peer=fakeSdk(),client=sdk.createClient({trusted:async()=>true,connect:peer.connect});
 await client.session(async s=>{check(s.protocol===3&&s.serverProtocol===5);const d=(await s.inventory())[0];check(d.id===parsed.id);await s.send(1051,0,sdk.ledsData(['#FF153F'],0));check((await s.descriptor(0)).colors[0]==='#FF153F');});
 await assert.rejects(()=>sdk.createClient({trusted:async()=>false,connect:()=>{throw Error('must_not_connect');}}).session(()=>{}),/owner_unverified/);checks++;
 peer.disconnected=true;await assert.rejects(()=>client.session(s=>s.inventory()),/disconnected/);checks++;peer.disconnected=false;await client.session(async s=>check((await s.inventory()).length===1));
 check(peer.sent.every(id=>[0,1,40,1051].includes(id)));
 console.log('PASS: '+checks+' OpenRGB SDK v3 parser/framing/limits/owner/reconnection checks; mocks only');
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
