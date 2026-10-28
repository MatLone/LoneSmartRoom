'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createDeadline}=require('../apps/windows-ui/development-deadline.cjs');
const {createSource}=require('../apps/windows-ui/presentmon-source.cjs');
let t=0,checks=0,quit=0,closed=false,records=[],timers=new Map(),id=0;
const schedule=(fn,ms)=>{timers.set(++id,{fn,ms});return id;};
const deadline=createDeadline({enabled:true,quit:()=>quit++,closed:()=>closed,write:v=>records.push(v),now:()=>t,schedule,cancel:i=>timers.delete(i)});
deadline.start();t=45000;[...timers.values()].find(v=>v.ms===45000).fn();assert.equal(quit,1);checks++;
closed=true;t=50000;deadline.complete();assert.equal(records.at(-1).code,'closed_within_deadline');assert.equal(timers.size,0);checks+=2;
records=[];const timeout=createDeadline({enabled:true,quit:()=>{},closed:()=>false,write:v=>records.push(v),now:()=>t,schedule,cancel:i=>timers.delete(i)});
timeout.start();t+=120000;[...timers.values()].find(v=>v.ms===120000).fn();assert.equal(records.at(-1).code,'deadline_exceeded');checks++;
// Real files only in the owned disposable test directory; no PresentMon execution.
const cache=path.resolve(__dirname,'../.cache');fs.mkdirSync(cache,{recursive:true});
const dir=fs.mkdtempSync(path.join(cache,'fps-source-')),file=path.join(dir,'fixture.csv');
try{
 fs.writeFileSync(file,'Application,ProcessID,SwapChainAddress,MsBetweenPresents\nfixture.exe,1,0,20\n');
 let ticks=0,cleared=0; t=1000000;
 const source=createSource({now:()=>t,interval:()=>++ticks,clear:()=>cleared++});
 assert.equal(source.attach(file).state,'awaiting_frames');assert.equal(source.view().report,null);checks+=2;
 fs.appendFileSync(file,Array.from({length:100},()=> 'fixture.exe,1,0,10\n').join(''));source.poll();
 assert.equal(source.view().report.streams[0].average_fps,100);assert.equal(source.view().report.streams[0].one_percent_low_fps,100);checks+=2;
 assert.equal(source.view().live_game_verified,false);assert(!JSON.stringify(source.view()).includes(dir));checks+=2;
 t+=3100;source.poll();assert.equal(source.view().state,'stale');assert.equal(source.view().report,null);checks+=2;
 fs.appendFileSync(file,'fixture.exe,1,0,20\n');source.poll();assert.equal(source.view().state,'available');checks++;
 fs.writeFileSync(file,'Application,MsBetweenPresents\n');source.poll();assert.equal(source.view().state,'awaiting_frames');checks++;
 source.stop();assert.equal(source.view().state,'inactive');assert.equal(cleared,1);checks+=2;
 fs.writeFileSync(file,'Application,WrongUnit\n');assert.throws(()=>source.attach(file));checks++;
 fs.writeFileSync(file,'Application,MsBetweenPresents\n');source.attach(file);fs.appendFileSync(file,'fixture.exe,1e-308\n');source.poll();
 assert.equal(source.view().state,'unavailable');assert.equal(source.view().report,null);checks+=2;source.stop();
 assert.throws(()=>source.attach('../arbitrary.exe'));checks++;
}finally{const resolved=fs.realpathSync(dir);if(!resolved.startsWith(fs.realpathSync(cache)+path.sep))throw Error('cleanup_scope');fs.rmSync(resolved,{recursive:true});}
const {fixture:windowFixture}=require('./electron-tray.cjs');
let invalidated=0;const w=windowFixture({beforeRestore:()=>{assert.equal(w.win.visible,false);invalidated++;}});
w.controller.hideToTray();w.trays[0].emit('click');assert.equal(invalidated,1);assert.equal(w.win.visible,true);checks+=3;w.controller.quit();
console.log(JSON.stringify({ok:true,checks,physicalCollectors:false,externalCapture:false}));
