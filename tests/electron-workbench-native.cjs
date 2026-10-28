'use strict';
const {app,session}=require('electron'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
app.disableHardwareAcceleration(); // Owned visual review only; installed app unchanged.
const run=process.env.LONE_WORKBENCH_RUN_ID;if(!/^[a-f0-9]{32}$/.test(run||'')||!process.argv.includes('--lone-development-review')||!process.argv.includes('--lone-workbench-development'))throw Error('explicit_isolated_workbench_review');
const root=path.resolve(__dirname,'..'),out=path.join(root,'docs/windows-control-center-development/captures');fs.mkdirSync(out,{recursive:true});
let checks=0,started=false,completed=false;const errors=[],network=[],captures=[];
const wait=n=>new Promise(r=>setTimeout(r,n));
setTimeout(()=>{if(!completed){console.error('Owned review deadline; requesting normal quit');app.quit();}},45000).unref();
app.on('browser-window-created',(_e,win)=>{
 if(started)return;started=true;
 win.webContents.on('console-message',e=>{if(e.level==='error')errors.push(e.message);});
 win.webContents.once('did-finish-load',async()=>{
  const ev=s=>win.webContents.executeJavaScript(s);
  const check=(value,label)=>{assert(value,label);checks++;};
  async function until(test){for(let i=0;i<80;i++){if(await test())return;await wait(30);}throw Error('workbench_not_ready');}
  async function capture(name){await wait(250);fs.writeFileSync(path.join(out,name+'.png'),(await win.webContents.capturePage()).toPNG());captures.push(name+'.png');}
  try{
   await until(()=>ev('Boolean(window.loneTools&&document.getElementById("toolSelect").options.length===12)'));
   check(app.getPath('userData').includes(run),'Unique isolated profile');
   check(require('../apps/windows-ui/desktop-main.cjs').monitoringDiagnostics()===null,'No physical collector started');
   await ev(`(()=>{const b=document.createElement('div');b.className='development-evidence-banner';b.textContent='DESENVOLVIMENTO ISOLADO · SEM COLETA FÍSICA · AÇÕES WINDOWS BLOQUEADAS';document.body.append(b)})()`);
   for(const section of ['overview','maintenance','optimization','applications','peripherals','display','network','games','environment','nex','audit','hardware']){
    await ev(`document.querySelector('[data-tool="${section}"]').click()`);await until(()=>ev(`!document.getElementById('panel-tools').hidden&&document.getElementById('toolSelect').value==='${section}'`));
    check(await ev(`document.documentElement.scrollWidth<=innerWidth+1&&document.getElementById('workspace').scrollWidth<=document.getElementById('workspace').clientWidth+1`),'No outer overflow '+section);
    await capture(section);
   }
   const response=await ev(`window.loneTools.saveProfile('Equilibrado',['notifications'])`);check(response.saved&&!response.applied_to_windows,'App-local profile only');
   const nex=await ev(`window.loneTools.askNex('Resumo do estado')`);check(!nex.ai&&!nex.execution,'NEX truthful local provider');
   await assert.rejects(()=>ev(`window.loneTools.networkTest('ping','x;shutdown /s')`));checks++;
   await ev(`window.loneDesktop.setWindowMode('widget')`);await wait(100);await ev(`document.querySelector('[data-tool="overview"]').click()`);await wait(100);
   check(await ev(`getComputedStyle(document.querySelector('.tool-nav')).display==='none'`),'Sidebar tools hidden in widget');
   check(await ev(`getComputedStyle(document.querySelector('.tool-mobile-nav')).display!=='none'`),'Compact tool selector available');await capture('widget');
   check(errors.length===0,'No renderer errors');
   const report={ok:true,checks,runId:run,realElectron:true,actualMainPreloadRenderer:true,physicalCollectors:false,operationalCommands:false,profile:app.getPath('userData'),captures,errors,network};
   fs.writeFileSync(path.join(root,'.cache','windows-workbench-review',run,'result.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({...report,profile:'isolated'}));completed=true;app.quit();
  }catch(error){console.error(error.stack);fs.writeFileSync(path.join(root,'.cache','windows-workbench-review',run,'failure.json'),JSON.stringify({ok:false,error:String(error.message),errors,captures}));completed=true;app.quit();process.exitCode=1;}
 });
});
app.whenReady().then(()=>session.defaultSession.webRequest.onBeforeRequest((details,callback)=>{
 const policy=require('../apps/windows-ui/desktop-policy.cjs');if(!policy.allowedResource(details.url))network.push(details.url);callback({cancel:!policy.allowedResource(details.url)});
}));
