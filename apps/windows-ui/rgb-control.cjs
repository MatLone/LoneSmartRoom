'use strict';
// Main-only, bounded reversible RGB actions. No profile/firmware/resize packets.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createClient,FLAGS,ledsData,updateModeData}=require('./openrgb-sdk.cjs');
const SCENES=['gamer','trabalho','relaxar','noturno'];
const hash=v=>crypto.createHash('sha256').update(JSON.stringify(v)).digest('hex');
const clone=v=>structuredClone(v),exact=(v,keys)=>{if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).sort().join(',')!==keys.slice().sort().join(','))throw Error('rgb_contract');};
const int=(n,max)=>Number.isInteger(n)&&n>=0&&n<=max;
const color=c=>typeof c==='string'&&/^#[0-9A-Fa-f]{6}$/.test(c);
const digest=d=>hash({identity:d.identity,activeMode:d.activeMode,modes:d.modes,colors:d.colors});
// Bounded, content-free diagnostics: never include paths, descriptors or raw buffers.
function readbackDifference(expected,actual){return {v:1,rule:'readback_mismatch',identity:expected.identity!==actual.identity,activeMode:expected.activeMode!==actual.activeMode,colorCount:expected.colors.length!==actual.colors.length,colorMismatches:expected.colors.reduce((n,c,i)=>n+(c!==actual.colors[i]?1:0),0),modeMismatches:expected.modes.reduce((n,m,i)=>n+((!actual.modes[i]||hash(m)!==hash(actual.modes[i]))?1:0),0)};}
function target(t){exact(t,['deviceId','zoneId','modeId','color','brightness']);if(typeof t.deviceId!=='string'||!/^rgb-[a-f0-9]{32}$/.test(t.deviceId)||t.zoneId!==null&&!int(t.zoneId,127)||t.modeId!==null&&!int(t.modeId,127)||t.color!==null&&!color(t.color)||t.brightness!==null&&!int(t.brightness,100))throw Error('rgb_target');return clone(t);}
function publicDevice(d){return {...d,zones:d.zones.map(z=>({...z,available:z.count>0,colors:d.colors.slice(z.start,z.start+z.count)})),modes:d.modes.map(m=>({...m,writable:!(m.flags&FLAGS.AUTOMATIC_SAVE),perLed:!!(m.flags&FLAGS.PER_LED),colorSupported:!!(m.flags&(FLAGS.PER_LED|FLAGS.MODE_COLOR)),brightnessSupported:!!(m.flags&FLAGS.BRIGHTNESS)&&m.brightnessMin!==m.brightnessMax})),state_source:'openrgb_server_cache',physical_observation_verified:false};}
function plan(device,spec){
 target(spec);const d=clone(device),commands=[];let mode=d.modes[spec.modeId===null?d.activeMode:spec.modeId];
 if(!mode||d.ledCount===0)throw Error('rgb_no_configured_leds');
 if(mode.flags&FLAGS.AUTOMATIC_SAVE||d.modes[d.activeMode].flags&FLAGS.AUTOMATIC_SAVE)throw Error('rgb_persistent_mode_blocked');
 if(spec.zoneId!==null&&(spec.modeId!==null&&spec.modeId!==d.activeMode||spec.brightness!==null))throw Error('rgb_zone_mode_is_device_wide');
 let change=spec.modeId!==null&&spec.modeId!==d.activeMode;
 if(spec.brightness!==null){if(!(mode.flags&FLAGS.BRIGHTNESS)||mode.brightnessMin===mode.brightnessMax)throw Error('rgb_brightness_unsupported');mode.brightness=Math.round(mode.brightnessMin+(mode.brightnessMax-mode.brightnessMin)*spec.brightness/100);change=true;}
 if(spec.color!==null&&!(mode.flags&FLAGS.PER_LED)){
  if(spec.zoneId!==null||!(mode.flags&FLAGS.MODE_COLOR)||mode.colorsMax<1)throw Error('rgb_color_unsupported');
  mode.colors=Array.from({length:Math.max(1,mode.colorsMin)},()=>spec.color.toUpperCase());mode.colorMode=2;change=true;
 }
 if(spec.color!==null&&(mode.flags&FLAGS.PER_LED)&&mode.colorMode!==1){mode.colorMode=1;change=true;}
 if(change){d.activeMode=mode.id;commands.push({id:1101,data:updateModeData(mode)});}
 if(spec.color!==null&&(mode.flags&FLAGS.PER_LED)){
  mode.colorMode=1;
  if(spec.zoneId===null){d.colors=d.colors.map(()=>spec.color.toUpperCase());commands.push({id:1050,data:ledsData(d.colors)});}
  else{const z=d.zones[spec.zoneId];if(!z||!z.count)throw Error('rgb_zone_unavailable');const c=Array(z.count).fill(spec.color.toUpperCase());d.colors.splice(z.start,z.count,...c);commands.push({id:1051,data:ledsData(c,z.id)});}
 }
 if(!commands.length)throw Error('rgb_no_change');return {expected:d,commands};
}
function restorePlan(live,saved){
 if(!saved||live.identity!==saved.identity||live.id!==saved.id||live.colors.length!==saved.colors?.length||!int(saved.activeMode,live.modes.length-1)||live.modes.length!==saved.modes?.length||saved.colors.some(c=>!color(c)))throw Error('rgb_restore_identity');
 const commands=[],expected=clone(live);
 for(let i=0;i<live.modes.length;i++){
  const a=live.modes[i],b=saved.modes[i];
  if(!b||Object.keys(a).sort().join(',')!==Object.keys(b).sort().join(','))throw Error('rgb_restore_mode');
  for(const k of ['id','name','value','flags','speedMin','speedMax','brightnessMin','brightnessMax','colorsMin','colorsMax'])if(a[k]!==b[k])throw Error('rgb_restore_capability');
  if(['speed','brightness','direction','colorMode'].some(k=>!int(b[k],0xffffffff))||b.colorMode>3||!Array.isArray(b.colors)||b.colors.length>4096||b.colors.some(c=>!color(c)))throw Error('rgb_restore_value');
  if(a.flags&FLAGS.BRIGHTNESS&&(!int(b.brightness,Math.max(a.brightnessMin,a.brightnessMax))||b.brightness<Math.min(a.brightnessMin,a.brightnessMax)))throw Error('rgb_restore_brightness');
  if(a.flags&1&&(b.speed<Math.min(a.speedMin,a.speedMax)||b.speed>Math.max(a.speedMin,a.speedMax)))throw Error('rgb_restore_speed');
  if(a.flags&FLAGS.MODE_COLOR&&(b.colors.length<a.colorsMin||b.colors.length>a.colorsMax))throw Error('rgb_restore_colors');
  if(hash(a)!==hash(b)){if(a.flags&FLAGS.AUTOMATIC_SAVE)throw Error('rgb_persistent_mode_blocked');commands.push({id:1101,data:updateModeData({...a,speed:b.speed,brightness:b.brightness,direction:b.direction,colorMode:b.colorMode,colors:b.colors})});expected.modes[i]=clone(b);}
 }
 const active=expected.modes[saved.activeMode];if(active.flags&FLAGS.AUTOMATIC_SAVE)throw Error('rgb_persistent_mode_blocked');
 // Restore LED cache in per-LED mode if available, then restore the original mode.
 if(hash(live.colors)!==hash(saved.colors)){
  const direct=expected.modes.find(m=>m.flags&FLAGS.PER_LED&&!(m.flags&FLAGS.AUTOMATIC_SAVE));if(!direct)throw Error('rgb_restore_per_led_unavailable');
  commands.push({id:1101,data:updateModeData(direct)},{id:1050,data:ledsData(saved.colors)});expected.colors=clone(saved.colors);
 }
 if(commands.length||live.activeMode!==saved.activeMode)commands.push({id:1101,data:updateModeData(active)});expected.activeMode=saved.activeMode;
 return {expected,commands};
}
function createRgbControl({directory,trusted,connect,enabled=false,confirm=async()=>false,now=Date.now}={}){
 if(!path.isAbsolute(directory))throw Error('rgb_directory');const client=createClient({trusted,connect});
 const file=path.join(directory,'rgb-control-v1.json');let readonly=false,busy=false,closed=false,last=null,lastRead=-Infinity,lastWrite=-Infinity,error=null,automationTask=Promise.resolve();
 let store={v:1,scenes:SCENES.map((id,i)=>({id,targets:[],suggestedColor:['#FF153F','#B8C5D6','#8C65C4','#080010'][i]})),automation:{enabled:false},saved:null,pending:null};
 function safe(){let cursor=path.parse(directory).root;for(const part of path.relative(cursor,directory).split(path.sep)){cursor=path.join(cursor,part);if(!fs.existsSync(cursor))fs.mkdirSync(cursor);const s=fs.lstatSync(cursor);if(!s.isDirectory()||s.isSymbolicLink())throw Error('rgb_unsafe_directory');}if(fs.existsSync(file)){const s=fs.lstatSync(file);if(!s.isFile()||s.isSymbolicLink()||s.nlink!==1||s.size>2097152)throw Error('rgb_unsafe_file');}}
 function validateStore(v){exact(v,['v','scenes','automation','saved','pending']);if(v.v!==1||!Array.isArray(v.scenes)||v.scenes.length!==4)throw Error('rgb_storage');exact(v.automation,['enabled']);if(typeof v.automation.enabled!=='boolean')throw Error('rgb_storage');for(let i=0;i<4;i++){const s=v.scenes[i];exact(s,['id','targets','suggestedColor']);if(s.id!==SCENES[i]||!color(s.suggestedColor)||!Array.isArray(s.targets)||s.targets.length>32)throw Error('rgb_storage');s.targets.forEach(target);}for(const x of [v.saved,v.pending])if(x!==null&&(!x||!Array.isArray(x.devices)||x.devices.length>32||!Number.isFinite(Date.parse(x.at))))throw Error('rgb_storage');return v;}
 try{safe();if(fs.existsSync(file))store=validateStore(JSON.parse(fs.readFileSync(file,'utf8')));}catch{readonly=true;error='rgb_settings_rejected_preserved';}
 // An interrupted transaction is exposed for explicit recovery; never replayed on startup.
 let recoveryOnLoad=!!store.pending;if(recoveryOnLoad)store.automation.enabled=false;
 function persist(){if(readonly)throw Error('rgb_settings_readonly');safe();validateStore(store);const text=JSON.stringify(store);if(Buffer.byteLength(text)>2097152)throw Error('rgb_storage_limit');const temp=file+'.'+crypto.randomBytes(12).toString('hex')+'.tmp';let own=false;try{fs.writeFileSync(temp,text,{flag:'wx',mode:0o600});own=true;fs.renameSync(temp,file);own=false;}finally{if(own)fs.unlinkSync(temp);}}
 const view=()=>({v:1,state:error?'unavailable':last?'available':'not_verified',source:'openrgb.sdk.loopback',simulation:false,observed_at:last?.at||null,serverProtocol:last?.serverProtocol||null,protocol:3,devices:last?.devices.map(publicDevice)||[],scenes:clone(store.scenes),automation:clone(store.automation),saved_at:store.saved?.at||null,recovery:store.pending?{purpose:store.pending.purpose,outcome:store.pending.outcome,at:store.pending.at}:null,error,write_enabled:enabled&&!readonly&&!closed,physical_observation_verified:false});
 async function lock(fn){if(busy||closed)throw Error('rgb_busy_or_closed');busy=true;try{return await fn();}finally{busy=false;}}
 async function inventory(s){const devices=await s.inventory();last={at:new Date(now()).toISOString(),serverProtocol:s.serverProtocol,devices};error=null;return devices;}
 async function refresh(force=false){return lock(async()=>{if(!force&&now()-lastRead>=0&&now()-lastRead<1000)return view();lastRead=now();try{await client.session(s=>inventory(s));}catch(e){last=null;error=/^rgb_[a-z_]+$/.test(e.message)?e.message:'rgb_read_failed';}return view();});}
 async function dispatch(s,devices,plans){for(const [id,p] of plans){const current=devices.find(d=>d.id===id);for(const command of p.commands)await s.send(command.id,current.index,command.data);}const after=[];for(const [id,p] of plans){const current=devices.find(d=>d.id===id),d={...await s.descriptor(current.index),index:current.index};if(digest(d)!==digest(p.expected)){store.pending.diagnostic=readbackDifference(p.expected,d);throw Error('rgb_readback_mismatch');}after.push(d);}return after;}
 async function apply(specs,purpose='manual',ask=true,expectedRevision=null){
  if(readonly)throw Error('rgb_settings_readonly');if(!Array.isArray(specs)||!specs.length||specs.length>32)throw Error('rgb_empty_scene');specs.forEach(target);
  if(store.pending&&store.pending.outcome!=='applied')throw Error('rgb_recovery_required');if(store.pending?.purpose==='gamer_auto')throw Error('rgb_gamer_owns_state');
  if(now()-lastWrite<1000)throw Error('rgb_write_rate');
  if(ask){const devices=await client.session(s=>inventory(s));for(const spec of specs){const d=devices.find(d=>d.id===spec.deviceId);if(!d)throw Error('rgb_device_missing');plan(d,spec);}
   if(!await confirm({kind:'apply',purpose,targets:specs.map(t=>({device:devices.find(d=>d.id===t.deviceId).name,zone:t.zoneId===null?'Dispositivo inteiro':devices.find(d=>d.id===t.deviceId).zones[t.zoneId]?.name,color:t.color,brightness:t.brightness,mode:t.modeId===null?null:devices.find(d=>d.id===t.deviceId).modes[t.modeId]?.name}))}))return {v:1,canceled:true};
   return apply(specs,purpose,false,Object.fromEntries(devices.map(d=>[d.id,digest(d)])));}
  return client.session(async s=>{const devices=await inventory(s),plans=new Map();
   for(const spec of specs){if(expectedRevision){const fresh=devices.find(d=>d.id===spec.deviceId);if(!fresh||digest(fresh)!==expectedRevision[spec.deviceId])throw Error('rgb_changed_after_confirmation');}const current=plans.get(spec.deviceId)?.expected||devices.find(d=>d.id===spec.deviceId);if(!current)throw Error('rgb_device_missing');const p=plan(current,spec);plans.set(spec.deviceId,{expected:p.expected,commands:[...(plans.get(spec.deviceId)?.commands||[]),...p.commands]});}
   if(ask&&!await confirm({kind:'apply',purpose,targets:specs.map(t=>({device:devices.find(d=>d.id===t.deviceId).name,zone:t.zoneId===null?'Dispositivo inteiro':devices.find(d=>d.id===t.deviceId).zones[t.zoneId]?.name,color:t.color,brightness:t.brightness,mode:t.modeId===null?null:devices.find(d=>d.id===t.deviceId).modes[t.modeId]?.name}))}))return {v:1,canceled:true};
   store.pending={at:new Date(now()).toISOString(),purpose,outcome:'prepared',devices:clone(devices.filter(d=>plans.has(d.id))),after:null};persist();lastWrite=now();
   try{const after=await dispatch(s,devices,plans);store.pending.outcome='applied';store.pending.after=Object.fromEntries(after.map(d=>[d.id,digest(d)]));persist();for(const d of after)last.devices[last.devices.findIndex(x=>x.id===d.id)]=d;return {v:1,applied:true,readback_verified:true,physical_verified:false,state:view()};}
   catch(e){store.pending.outcome='uncertain';persist();last=null;error='rgb_write_uncertain_recovery_required';throw e;}
  });
 }
 async function restore(source='previous',ask=true,expectedRevision=null){
  const backup=source==='saved'?store.saved:store.pending;if(!backup)throw Error('rgb_no_saved_state');
  if(ask){const fresh=await client.session(s=>inventory(s));for(const saved of backup.devices){const live=fresh.find(d=>d.id===saved.id);if(!live)throw Error('rgb_restore_device_missing');restorePlan(live,saved);}
   if(!await confirm({kind:'restore',purpose:source,targets:backup.devices.map(d=>({device:d.name,zone:'Estado salvo completo'})),externalChange:!!backup.after&&fresh.some(d=>backup.after[d.id]&&backup.after[d.id]!==digest(d))}))return {v:1,canceled:true};return restore(source,false,Object.fromEntries(fresh.map(d=>[d.id,digest(d)])));}

  return client.session(async s=>{const devices=await inventory(s),plans=new Map();
   for(const saved of backup.devices){const live=devices.find(d=>d.id===saved.id);if(!live)throw Error('rgb_restore_device_missing');if(expectedRevision?expectedRevision[live.id]!==digest(live):(!backup.after||backup.after[live.id]!==digest(live)))throw Error('rgb_restore_external_change');plans.set(live.id,restorePlan(live,saved));}
   if(ask&&!await confirm({kind:'restore',purpose:source,targets:backup.devices.map(d=>({device:d.name,zone:'Estado salvo completo'})),externalChange:!!backup.after&&devices.some(d=>backup.after[d.id]&&backup.after[d.id]!==digest(d))}))return {v:1,canceled:true};
   const marker={at:new Date(now()).toISOString(),purpose:backup.purpose==='gamer_auto'?'gamer_auto':'restore',outcome:'prepared',devices:clone(backup.devices),after:null};store.pending=marker;persist();
   try{const after=await dispatch(s,devices,plans);store.pending=null;recoveryOnLoad=false;persist();for(const d of after)last.devices[last.devices.findIndex(x=>x.id===d.id)]=d;return {v:1,restored:true,readback_verified:true,physical_verified:false,state:view()};}catch(e){store.pending.outcome='uncertain';persist();last=null;error='rgb_restore_uncertain';throw e;}
  });
 }
 async function request(q){exact(q,['v','op','args']);if(q.v!==1||typeof q.op!=='string'||Buffer.byteLength(JSON.stringify(q))>32768)throw Error('rgb_request');
  const fields={state:[],refresh:[],save:[],apply:['target'],off:['deviceId'],on:[],restore:['source'],sceneSave:['id','targets'],sceneApply:['id'],automation:['enabled']};if(!Object.hasOwn(fields,q.op))throw Error('rgb_operation');exact(q.args,fields[q.op]);const a=q.args;
  if(q.op==='state')return view();if(q.op==='refresh')return refresh();if(!enabled)throw Error('rgb_control_not_enabled');
  return lock(async()=>{
   if(q.op==='apply')return apply([a.target]);
   if(q.op==='restore'){if(!['saved','previous'].includes(a.source))throw Error('rgb_restore_source');return restore(a.source);}
   if(q.op==='on'){if(store.pending?.purpose!=='off')throw Error('rgb_not_powered_off_by_lsr');return restore();}
   if(q.op==='off'){
    if(a.deviceId!==null&&!/^rgb-[a-f0-9]{32}$/.test(a.deviceId))throw Error('rgb_device_id');
    const devices=await client.session(s=>inventory(s)),chosen=a.deviceId===null?devices:devices.filter(d=>d.id===a.deviceId),specs=chosen.filter(d=>d.ledCount>0).map(d=>({deviceId:d.id,zoneId:null,modeId:d.modes.find(m=>m.flags&FLAGS.PER_LED&&!(m.flags&FLAGS.AUTOMATIC_SAVE))?.id??null,color:'#000000',brightness:null}));return apply(specs,'off');
   }
   if(q.op==='save'){store.saved={at:new Date(now()).toISOString(),devices:clone(await client.session(s=>inventory(s)))};persist();return {v:1,saved:true,state:view()};}
   if(q.op==='sceneSave'){if(!SCENES.includes(a.id)||!Array.isArray(a.targets)||a.targets.length>32)throw Error('rgb_scene');const targets=a.targets.map(target);store.scenes.find(s=>s.id===a.id).targets=targets;if(a.id==='gamer')store.automation.enabled=false;persist();return {v:1,saved:true,state:view()};}
   if(q.op==='sceneApply'){if(!SCENES.includes(a.id))throw Error('rgb_scene');return apply(store.scenes.find(s=>s.id===a.id).targets,a.id);}
   if(q.op==='automation'){if(typeof a.enabled!=='boolean')throw Error('rgb_consent');if(a.enabled){if(store.pending||!store.scenes[0].targets.length)throw Error('rgb_gamer_scene_required');if(!await confirm({kind:'automation',purpose:'CS2: aplicar Gamer e restaurar ao sair',targets:store.scenes[0].targets}))return {v:1,canceled:true};}else if(store.pending?.purpose==='gamer_auto')await restore('previous',false);store.automation.enabled=a.enabled;persist();return view();}
  });
 }
 function gameState(active){automationTask=automationTask.catch(()=>{}).then(async()=>{if(closed||recoveryOnLoad||!enabled)return;if(active&&store.automation.enabled&&!store.pending){await lock(()=>apply(store.scenes[0].targets,'gamer_auto',false));}else if(!active&&store.pending?.purpose==='gamer_auto'){await lock(()=>restore('previous',false));}}).catch(()=>{error='rgb_gamer_recovery_required';});return automationTask;}
 return Object.freeze({request,view,refresh,gameState,async close(){await automationTask;const deadline=Date.now()+15000;while(busy&&Date.now()<deadline)await new Promise(r=>setTimeout(r,25));if(busy)return false;if(!recoveryOnLoad&&store.pending?.purpose==='gamer_auto'){await gameState(false);if(store.pending)return false;}closed=true;return true;}});
}
module.exports={createRgbControl,target,plan,restorePlan,digest,readbackDifference,SCENES};
