'use strict';
const path=require('node:path'),fs=require('node:fs'),{execFile}=require('node:child_process');
const {text,effectUrl}=require('./signalrgb-sdk.cjs');
function createEnvironment({script=path.join(__dirname,'signalrgb-environment.ps1'),execute=execFile}={}){
 const system=process.env.SystemRoot||'C:\\Windows',program=path.join(system,'System32','WindowsPowerShell','v1.0','powershell.exe');
 const environment={};for(const k of ['SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','ProgramFiles','ProgramData'])if(process.env[k])environment[k]=process.env[k];environment.PSModulePath=path.join(system,'System32','WindowsPowerShell','v1.0','Modules');
 async function inspect(){if(!path.isAbsolute(script)||fs.lstatSync(script).isSymbolicLink())throw Error('rgb_environment_script');return new Promise((resolve,reject)=>execute(program,['-NoLogo','-NoProfile','-NonInteractive','-File',script],{shell:false,windowsHide:true,env:environment,timeout:10000,maxBuffer:262144,encoding:'utf8'},(err,out)=>{
  if(err)return reject(Error('rgb_environment_unavailable'));
  try{const v=JSON.parse(out.replace(/^\uFEFF/,''));for(const k of ['verified','signalRunning','openRunning','launcherValid','apiBroadBinding'])if(typeof v[k]!=='boolean')throw Error();if(v.v!==1||v.version!==null&&!/^[0-9.]{1,40}$/.test(v.version)||!Array.isArray(v.effects)||v.effects.length>512)throw Error();
   if(v.launcherBuild!==null&&!/^[0-9.]{1,40}$/.test(v.launcherBuild))throw Error();resolve({v:1,verified:v.verified,signalRunning:v.signalRunning,openRunning:v.openRunning,launcherValid:v.launcherValid,launcherBuild:v.launcherBuild,apiBroadBinding:v.apiBroadBinding,version:v.version,effects:v.effects.map(e=>{if(!text(e.id)||!text(e.name)||e.source!=='documented_local_html')throw Error();return {id:e.id,name:e.name,source:e.source};})});}catch{reject(Error('rgb_environment_contract'));}
 }));}
 async function dispatch(name){effectUrl(name);const e=await inspect();if(!e.verified||!e.launcherValid||!e.launcherBuild||!e.signalRunning||e.openRunning||!e.effects.some(x=>x.name===name))throw Error('rgb_signal_dispatch_guard');
  const launcher=path.join(process.env.LOCALAPPDATA,'VortxEngine','app-'+e.launcherBuild,'SignalRgbLauncher.exe');
  // Official --url bridge; fixed signed launcher, typed installed name, never a shell.
  return new Promise((resolve,reject)=>execute(launcher,['--url=effect/apply/'+encodeURIComponent(name)+'?-silentlaunch-'],{shell:false,windowsHide:true,env:environment,timeout:5000,maxBuffer:16384},err=>err?reject(Error('rgb_signal_dispatch_failed')):resolve()));
 }
 return Object.freeze({inspect,dispatch});
}
module.exports={createEnvironment};
