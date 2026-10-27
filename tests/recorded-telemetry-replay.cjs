'use strict';
// Historical physical evidence through HTTPS, NOT a new collection/current UI reading.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const model=require('../apps/android/app/src/main/assets/telemetry-model.js');
const evidence=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../.cache/telemetry-tests/recorded-real-https-replay.json')));
assert.equal(evidence.live,false);assert.equal(evidence.evidence_kind,'recorded_real_replay');
const view=model.normalize(evidence.body),by=new Map(view.snapshot.metrics.map(m=>[m.id,m]));
let checks=3;assert.equal(view.snapshot.metrics.length,29);
for(const volume of ['c','d']){
 const p='storage.'+volume+'.',total=by.get(p+'total'),used=by.get(p+'used'),free=by.get(p+'free');
 assert(total.valid&&used.valid&&free.valid);assert(used.value+free.value<total.value);checks+=2;
 const bad=structuredClone(evidence.body);bad.snapshot.metrics.find(m=>m.id===p+'free').value=total.value-used.value+1;
 assert.throws(()=>model.normalize(bad),/inconsistent_capacity/);checks++;
}
const aged=model.age(view,Math.max(0,(Date.now()-Date.parse(view.snapshot.generated_at))/1000));
assert(aged.snapshot.metrics.every(m=>m.value===null));checks++;
const result={ok:true,checks,evidence_kind:'recorded_real_replay',live:false,displayedAsCurrent:false,generated_at:view.snapshot.generated_at,metrics:view.snapshot.metrics.length,
 note:'Historical source timestamps retained; clock frozen only in isolated HTTPS replay; all readings expire when aged to today'};
fs.writeFileSync(path.resolve(__dirname,'../.cache/telemetry-homologation-preparation-2026-10-27/android-replay-validation.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result));
