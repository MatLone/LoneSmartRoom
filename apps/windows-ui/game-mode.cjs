'use strict';
// Application-only game session policy. No launch, game hooks or OS mutation.
const fs=require('node:fs'),path=require('node:path');
const DEFAULT={v:1,enabled:false,reduceHistory:true,quietUi:true,overlay:false};
function validate(v){if(!v||Object.keys(v).sort().join(',')!=='enabled,overlay,quietUi,reduceHistory,v'||v.v!==1||['enabled','reduceHistory','quietUi','overlay'].some(k=>typeof v[k]!=='boolean'))throw Error('gamer_policy');return {...v};}
function createGameMode({directory,inspect,apply=()=>{},publish=()=>{},now=Date.now,interval=setInterval,clear=clearInterval}={}){
 if(!path.isAbsolute(directory)||typeof inspect!=='function')throw Error('gamer_context');
 const file=path.join(directory,'gamer-mode-v1.json');let policy={...DEFAULT},entries=[],active=null,present=false,available=false,error=null,busy=false,timer=null,closed=false,lastCheck=null;
 function safe(){let c=path.parse(directory).root;for(const part of path.relative(c,directory).split(path.sep)){c=path.join(c,part);if(!fs.existsSync(c))fs.mkdirSync(c);const s=fs.lstatSync(c);if(!s.isDirectory()||s.isSymbolicLink())throw Error('gamer_directory');}if(fs.existsSync(file)){const s=fs.lstatSync(file);if(!s.isFile()||s.isSymbolicLink()||s.nlink!==1||s.size>65536)throw Error('gamer_file');}}
 try{safe();if(fs.existsSync(file)){const v=JSON.parse(fs.readFileSync(file,'utf8'));policy=validate(v.policy);if(v.v!==1||!Array.isArray(v.sessions)||v.sessions.length>40)throw Error();for(const s of v.sessions)if(!s||Object.keys(s).sort().join(',')!=='ended,game,outcome,started'||s.game!=='cs2'||!Number.isFinite(s.started)||s.ended!==null&&!Number.isFinite(s.ended)||!['running','closed','app_exit','interrupted'].includes(s.outcome))throw Error();entries=v.sessions;if(entries.at(-1)?.ended===null)entries=entries.map(s=>s.ended===null?{...s,ended:now(),outcome:'interrupted'}:s);}}
 catch{error='gamer_state_rejected_preserved';}
 function save(){if(error==='gamer_state_rejected_preserved')throw Error(error);safe();const temp=file+'.'+require('node:crypto').randomBytes(8).toString('hex')+'.tmp';const data=JSON.stringify({v:1,policy,sessions:entries.slice(-40)});let own=false;try{fs.writeFileSync(temp,data,{flag:'wx',mode:0o600});own=true;fs.renameSync(temp,file);own=false;}finally{if(own)try{fs.unlinkSync(temp);}catch{}}}
 const view=()=>({v:1,policy:{...policy},state:error?'unavailable':active?'active':available?'idle':'not_verified',error,last_checked_at:lastCheck,game:active?'cs2':null,detected_game:available&&!error&&present?'cs2':null,sessions:structuredClone(entries),application_only:true,launch_enabled:false});
 function emit(){publish(view());}
 function leave(outcome){if(!active)return;entries=entries.map(s=>s.ended===null?{...s,ended:now(),outcome}:s);active=null;apply({active:false,reduceHistory:false,quietUi:false,overlay:false});try{save();}catch{error='gamer_persistence_failed';}}
 async function poll(){if(closed||busy)return view();busy=true;try{
  const r=await inspect();if(closed)return view();if(r?.state!=='available'||r.simulation!==false||!Array.isArray(r.items)||r.items.some(i=>i.game!=='cs2'||!Number.isSafeInteger(i.pid)||i.pid<=0))throw Error();
  lastCheck=new Date(now()).toISOString();available=true;present=r.items.length>0;if(error!=='gamer_state_rejected_preserved')error=null;
  if(r.items.length&&policy.enabled&&!error){if(!active){active={started:now()};entries.push({game:'cs2',started:active.started,ended:null,outcome:'running'});entries=entries.slice(-40);save();apply({active:true,reduceHistory:policy.reduceHistory,quietUi:policy.quietUi,overlay:policy.overlay});}}
  else leave('closed');
 }catch{if(!closed)error=error||'game_detection_unavailable';}finally{busy=false;emit();}return view();}
 function schedule(){if(timer!==null)clear(timer);timer=null;if(policy.enabled&&!closed){timer=interval(()=>void poll(),5000);timer?.unref?.();void poll();}}
 return Object.freeze({view,poll,configure(value){if(closed)throw Error('gamer_closed');const next=validate(value);const old=policy;policy=next;try{save();}catch(e){policy=old;throw e;}if(!policy.enabled)leave('closed');else if(active)apply({active:true,reduceHistory:policy.reduceHistory,quietUi:policy.quietUi,overlay:policy.overlay});schedule();emit();return view();},start(){schedule();return view();},close(){closed=true;if(timer!==null)clear(timer);timer=null;leave('app_exit');emit();}});
}
module.exports={createGameMode,validate,DEFAULT};
