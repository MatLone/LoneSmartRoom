'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {createRgbControl,plan,restorePlan,digest}=require('../apps/windows-ui/rgb-control.cjs');
const {parseDevice}=require('../apps/windows-ui/openrgb-sdk.cjs'),{fakeSdk,descriptor}=require('./openrgb-fixture.cjs');
let checks=0;const ok=v=>{assert(v);checks++;};
(async()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'lsr-rgb-mock-')),peer=fakeSdk();let at=Date.now(),allow=false,confirmations=0;
 const service=createRgbControl({enabled:true,directory:root,trusted:async()=>true,connect:peer.connect,now:()=>at,confirm:async()=>{confirmations++;return allow;}});
 const req=(op,args={})=>service.request({v:1,op,args});
 ok(service.view().automation.enabled===false);ok((await req('refresh')).devices.length===1);const d=service.view().devices[0],id=d.id;
 const spec={deviceId:id,zoneId:0,modeId:null,color:'#FF153F',brightness:null};
 await req('save');ok(service.view().saved_at!==null);const original=peer.state;
 ok((await req('apply',{target:spec})).canceled===true);ok(peer.sent.every(x=>[0,1,40].includes(x)));
 allow=true;ok((await req('apply',{target:spec})).readback_verified===true);ok(peer.state.colors[0]==='#FF153F');ok(peer.state.colors[1]===original.colors[1]);
 await assert.rejects(()=>req('apply',{target:spec}),/write_rate/);checks++;
 ok((await req('restore',{source:'previous'})).restored===true);assert.deepEqual(peer.state,original);checks++;
 at+=1100;ok((await req('apply',{target:{...spec,zoneId:null,modeId:1,color:'#ABCDEF',brightness:25}})).applied===true);ok(peer.state.activeMode===1);ok(peer.state.modes[1].colors[0]==='#ABCDEF');ok(peer.state.modes[1].brightness===26);
 await req('restore',{source:'saved'});assert.deepEqual(peer.state,original);checks++;
 at+=1100;await req('off',{deviceId:id});ok(peer.state.colors.every(c=>c==='#000000'));await req('on');assert.deepEqual(peer.state,original);checks++;
 for(const scene of ['gamer','trabalho','relaxar','noturno']){await req('sceneSave',{id:scene,targets:[{...spec,color:'#123456'}]});at+=1100;ok((await req('sceneApply',{id:scene})).applied===true);await req('restore',{source:'previous'});}
 ok(service.view().scenes.length===4);await req('automation',{enabled:true});ok(service.view().automation.enabled);at+=1100;const beforeAuto=confirmations;await service.gameState(true);ok(confirmations===beforeAuto);ok(service.view().recovery.purpose==='gamer_auto');await service.gameState(false);ok(service.view().recovery===null);assert.deepEqual(peer.state,original);checks++;
 at+=1100;await service.gameState(true);ok(await service.close());assert.deepEqual(peer.state,original);checks++;
 await assert.rejects(()=>req('apply',{target:spec}),/closed/);checks++;
 const loaded=createRgbControl({enabled:true,directory:root,trusted:async()=>true,connect:peer.connect});ok(loaded.view().scenes.length===4);await loaded.close();
 for(const q of [{v:2,op:'state',args:{}},{v:1,op:'shell',args:{}},{v:1,op:'state',args:{host:'evil'}},{v:1,op:'apply',args:{target:{...spec,color:'red'}}}]){await assert.rejects(()=>service.request(q));checks++;}
 const parsed=parseDevice(descriptor());for(const t of [{...spec,deviceId:'../../evil'},{...spec,zoneId:2},{...spec,zoneId:0,brightness:20},{...spec,modeId:123},{...spec,color:'<script>'}]){assert.throws(()=>plan(parsed,t));checks++;}
 const noLed={...parsed,ledCount:0,colors:[]};assert.throws(()=>plan(noLed,spec),/configured_leds/);checks++;
 const autosave=structuredClone(parsed);autosave.modes[0].flags|=512;assert.throws(()=>plan(autosave,spec),/persistent/);checks++;
 const bad=structuredClone(parsed);bad.modes[0].value=99;assert.throws(()=>restorePlan(parsed,bad));checks++;
 const same=restorePlan(parsed,parsed);ok(digest(same.expected)===digest(parsed));
 // Interrupted operation is never replayed just because the app was reopened.
 const file=path.join(root,'rgb-control-v1.json'),saved=JSON.parse(fs.readFileSync(file));saved.pending={at:new Date(at).toISOString(),purpose:'gamer_auto',outcome:'uncertain',devices:[parsed],after:null};fs.writeFileSync(file,JSON.stringify(saved));
 const prior=peer.sent.length,recovered=createRgbControl({enabled:true,directory:root,trusted:async()=>true,connect:peer.connect,confirm:async()=>true});ok(!recovered.view().automation.enabled);await recovered.gameState(false);ok(peer.sent.length===prior);ok(await recovered.close());
 // External edits prevent automated restoration from clobbering another controller.
 saved.pending=null;saved.automation.enabled=true;fs.writeFileSync(file,JSON.stringify(saved));
 const race=createRgbControl({enabled:true,directory:root,trusted:async()=>true,connect:peer.connect,confirm:async()=>true,now:()=>at});await race.gameState(true);const external=peer.state;external.colors[0]='#FFFFFF';peer.state=external;await race.gameState(false);ok(race.view().error==='rgb_gamer_recovery_required');ok(peer.state.colors[0]==='#FFFFFF');ok(!await race.close());

 // A TCP write callback is not a successful application: a non-updating peer fails closed.
 const faultRoot=fs.mkdtempSync(path.join(os.tmpdir(),'lsr-rgb-readback-')),faultPeer=fakeSdk();faultPeer.ignoreWrites=true;
 const fault=createRgbControl({enabled:true,directory:faultRoot,trusted:async()=>true,connect:faultPeer.connect,confirm:async()=>true,now:()=>at});
 await assert.rejects(()=>fault.request({v:1,op:'apply',args:{target:spec}}),/readback_mismatch/);checks++;
 ok(fault.view().state==='unavailable');ok(fault.view().devices.length===0);ok(fault.view().recovery.outcome==='uncertain');
 const marker=JSON.parse(fs.readFileSync(path.join(faultRoot,'rgb-control-v1.json'),'utf8'));
 assert.deepEqual(marker.pending.diagnostic,{v:1,rule:'readback_mismatch',identity:false,activeMode:false,colorCount:false,colorMismatches:1,modeMismatches:0});checks++;
 ok(!JSON.stringify(marker.pending.diagnostic).includes('#'));ok(faultPeer.sent.filter(n=>n===1051).length===1);
 at+=1100;await assert.rejects(()=>fault.request({v:1,op:'apply',args:{target:spec}}),/recovery_required/);checks++;
 ok((await fault.request({v:1,op:'restore',args:{source:'previous'}})).readback_verified);
 ok(fault.view().recovery===null);ok(await fault.close());
 // Corrupt settings remain byte-for-byte intact and cannot authorize writes.
 const corruptRoot=fs.mkdtempSync(path.join(os.tmpdir(),'lsr-rgb-corrupt-'));
 fs.writeFileSync(path.join(corruptRoot,'rgb-control-v1.json'),'{invalid');
 const corrupt=createRgbControl({directory:corruptRoot,enabled:true,trusted:async()=>true,connect:peer.connect});
 ok(!corrupt.view().write_enabled);ok(corrupt.view().error==='rgb_settings_rejected_preserved');
 await assert.rejects(()=>corrupt.request({v:1,op:'apply',args:{target:spec}}),/readonly/);checks++;
 ok(fs.readFileSync(path.join(corruptRoot,'rgb-control-v1.json'),'utf8')==='{invalid');await corrupt.close();
 // Golden bytes independent of the mock encoder/decoder, from the SDK v3 table.
 assert.equal(require('../apps/windows-ui/openrgb-sdk.cjs').ledsData(['#FF153F'],3).toString('hex'),'0e000000030000000100ff153f00');checks++;
 ok(peer.sent.every(x=>[0,1,40,1050,1051,1101].includes(x)));
 console.log(`PASS: ${checks} RGB control/scene/consent/recovery/persistence/automation checks; hardware not touched`);
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
