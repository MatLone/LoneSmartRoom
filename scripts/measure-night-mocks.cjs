'use strict';
// Cost of this isolated mock workload only, NOT physical PC telemetry or installed-app consumption.
const fs=require('node:fs'),path=require('node:path'),{createHistory}=require('../apps/windows-ui/performance-history.cjs'),{createSession}=require('../apps/windows-ui/gamer-session.js');
const source=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../.cache/telemetry-tests/https-frame.json'))).snapshot;
let clock=Date.parse(source.generated_at),rss=[process.memoryUsage().rss];
const history=createHistory({enabled:true,now:()=>clock});
const cpu=process.cpuUsage(),started=performance.now();
for(let i=0;i<600;i++){
 clock+=2000;const snapshot=structuredClone(source);snapshot.sequence=i+1;
 for(const m of snapshot.metrics)m.collected_at=new Date(clock).toISOString();
 history.record({connection:'connected',simulated:true,snapshot});if(i%50===0){history.query(30);rss.push(process.memoryUsage().rss);}
}
const game=createSession({startedAt:new Date(clock).toISOString(),simulation:true});
for(let i=0;i<1200;i++)game.record({v:1,sequence:i,monotonic_seconds:i/60,frametime_ms:1000/60});game.view();
const elapsed=performance.now()-started,usage=process.cpuUsage(cpu);rss.push(process.memoryUsage().rss);
const result={v:1,workload:'600 simulated history records plus 1200 simulated frames; same Node process',physicalSensors:false,productionProcessesMeasured:false,
 elapsed_ms:elapsed,cpu_user_ms:usage.user/1000,cpu_system_ms:usage.system/1000,rss_sample_mean_mib:rss.reduce((a,b)=>a+b,0)/rss.length/1048576,rss_sample_peak_mib:Math.max(...rss)/1048576,
 rss_samples:rss.length,points_retained:history.stats().points,scope:'Includes Node/runtime/test fixture overhead; no extrapolation to Electron, collector, GPU or total PC CPU percentage'};
history.close();const out=path.resolve(__dirname,'../.cache/night-development/mock-resource-results.json');fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(result,null,2));console.log(JSON.stringify(result));
