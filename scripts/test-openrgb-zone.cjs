'use strict';
// One explicitly authorized, fixed physical test. Never run as a regression.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),output=path.join(root,'.cache/openrgb-control/physical-test');
const {createRgbControl,digest}=require('../apps/windows-ui/rgb-control.cjs');
const DEVICE='rgb-5bef786871f7b1cbd4fce5dd91c577c0',ZONE=3;
async function main(){
 if(process.argv.slice(2).join(',')!=='--authorized-once')throw Error('explicit_current_user_authorization_required');
 fs.mkdirSync(output,{recursive:true});
 // This marker is never deleted, reset or reused; a retry needs a new reviewed procedure.
 fs.writeFileSync(path.join(output,'started.json'),JSON.stringify({v:1,at:new Date().toISOString(),scope:'One B660M Chipset Accent zone, red 8 seconds then restore',authorization:'Direct user confirmation in current chat',forced:false},null,2),{flag:'wx',mode:0o600});
 const provider=require('../apps/windows-ui/windows-read-provider.cjs').createProvider();
 const rgb=createRgbControl({directory:path.join(output,'profile'),enabled:true,
  trusted:async()=>{const r=await provider.inventory('deviceproviders');return r.state==='available'&&r.simulation===false&&r.items.some(i=>i.name==='OpenRGB'&&i.sdk_loopback_owner_verified===true&&i.sdk_restricted_to_loopback===true);},
  confirm:async q=>q.kind==='apply'&&q.purpose==='manual'&&q.targets.length===1&&q.targets[0].device==='B660M AORUS PRO DDR4'&&q.targets[0].zone==='Chipset Accent'&&q.targets[0].color==='#FF153F'&&q.targets[0].brightness===null||q.kind==='restore'&&q.purpose==='previous'&&!q.externalChange});
 const report={v:1,simulation:false,started_at:new Date().toISOString(),zone:'Chipset Accent',color:'#FF153F',duration_red_seconds:8,applied:false,restored:false,physical_user_observation:'pending',agent_modified:false,installation_modified:false};
 let original;
 try{
  const state=await rgb.request({v:1,op:'refresh',args:{}}),d=state.devices.find(d=>d.id===DEVICE);
  if(!d||d.name!=='B660M AORUS PRO DDR4'||d.zones[ZONE]?.name!=='Chipset Accent'||d.zones[ZONE].count!==1||!d.modes[d.activeMode].perLed)throw Error('physical_target_or_mode_changed');
  original=digest(d);await rgb.request({v:1,op:'save',args:{}});
  const result=await rgb.request({v:1,op:'apply',args:{target:{deviceId:DEVICE,zoneId:ZONE,modeId:null,color:'#FF153F',brightness:null}}});
  if(!result.applied||!result.readback_verified)throw Error('physical_apply_not_verified');report.applied=true;report.red_readback_at=new Date().toISOString();
  console.log(JSON.stringify({phase:'red_readback_verified',at:report.red_readback_at,observe:'Chipset Accent for 8 seconds'}));
  await new Promise(r=>setTimeout(r,8000));
 }catch(e){report.error=/^(?:rgb|physical)_[a-z_]+$/.test(e.message)?e.message:'physical_test_failed';}
 finally{
  if(rgb.view().recovery){try{const result=await rgb.request({v:1,op:'restore',args:{source:'previous'}});report.restored=result.restored===true&&result.readback_verified===true;if(report.restored){const d=result.state.devices.find(d=>d.id===DEVICE);report.original_state_equal=digest(d)===original;report.restore_readback_at=new Date().toISOString();}}catch{report.restore_error='restore_not_verified_do_not_retry';}}
  report.closed=await rgb.close();report.finished_at=new Date().toISOString();report.ok=report.applied&&report.restored&&report.original_state_equal&&!report.error;
  fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(report,null,2),{flag:'wx',mode:0o600});console.log(JSON.stringify(report));if(!report.ok)process.exitCode=1;
 }
}
if(require.main===module)main().catch(e=>{console.error(/^[a-z_]+$/.test(e.message)?e.message:'physical_session_blocked');process.exitCode=1;});
