'use strict';
// Fixed read-only projection. No network, native API, storage or credentials.
((root,factory)=>{const m=factory();if(typeof module==='object'&&module.exports)module.exports=m;else root.loneTelemetry=m;})(globalThis,()=>{
 const ids=new Map([['cpu.utilization','percent'],...['total','used','available','utilization'].map(k=>['ram.'+k,k==='utilization'?'percent':'bytes']),
  ...['c','d'].flatMap(v=>['total','used','free','available','occupation','read_rate','write_rate','activity'].map(k=>['storage.'+v+'.'+k,['occupation','activity'].includes(k)?'percent':k.endsWith('_rate')?'bytes_per_second':'bytes'])),
  ...['utilization','temperature','hotspot_temperature','vram_used_mb','vram_total_mb','core_clock','power','fan_rpm'].map((k,i)=>['gpu.adlx.'+k,['percent','celsius','celsius','megabytes','megabytes','megahertz','watts','rpm'][i]])]);
 const states=new Set(['available','warming_up','unsupported','unavailable','permission_denied','error','stale']);
 const num=x=>typeof x==='number'&&Number.isFinite(x);
 const stamp=x=>typeof x==='string'&&x.length<=32&&/^\d{4}-\d\d-\d\dT.*Z$/.test(x)&&Number.isFinite(Date.parse(x));
 function normalize(raw,{simulation=false,transportSeconds=0}={}){
  if(!raw||raw.ok!==true||raw.telemetry_version!==1||typeof raw.generation!=='string'||! /^[a-f0-9]{32}$/.test(raw.generation)||!num(transportSeconds)||transportSeconds<0||transportSeconds>15)throw Error('invalid_telemetry');
  if(raw.state==='unavailable'&&raw.snapshot===null)return {generation:raw.generation,snapshot:null};
  const s=raw.snapshot;
  if(raw.state!=='available'||!s||s.schema_version!==1||s.contains_simulated!==simulation||!Number.isSafeInteger(s.sequence)||s.sequence<0||!stamp(s.generated_at)||!Array.isArray(s.metrics)||s.metrics.length>29)throw Error('invalid_snapshot');
  const seen=new Set();
  const metrics=s.metrics.map(m=>{
   if(!m||ids.get(m.id)!==m.unit||seen.has(m.id)||!states.has(m.state)||typeof m.valid!=='boolean'||typeof m.stale!=='boolean'||m.valid!==(m.state==='available'&&!m.stale)||!['real','simulated','not_collected'].includes(m.data_kind))throw Error('invalid_metric');
   seen.add(m.id);
   const gpu=m.id.startsWith('gpu.'),capacity=m.id.endsWith('total_mb')||m.id.startsWith('storage.')&&!['read_rate','write_rate','activity'].includes(m.id.split('.').at(-1));
   const expected=simulation?(gpu?'fixture.adlx':'fixture.metrics'):gpu?'amd.adlx':m.id.startsWith('cpu.')?'win32.systemtimes':m.id.startsWith('ram.')?'win32.memory':capacity?'win32.volume.'+m.id.split('.')[1]:'win32.pdh.logicaldisk';
   if((m.source!==expected&&!(m.source==='unconfigured'&&m.data_kind==='not_collected'&&!m.valid))||m.data_kind!=='not_collected'&&m.data_kind!==(simulation?'simulated':'real'))throw Error('invalid_source');
   const ttl=gpu&&!capacity?m.interval_seconds+1:m.interval_seconds*3;
   if(!(capacity?[60]:gpu?[2,10]:[1,5]).includes(m.interval_seconds)||m.expires_after_seconds!==ttl||m.age_seconds!==null&&(!num(m.age_seconds)||m.age_seconds<0)||m.collected_at!==null&&(!stamp(m.collected_at)||Date.parse(m.collected_at)>Date.parse(s.generated_at)))throw Error('invalid_time');
   if(m.ingress_age_seconds!==null&&m.ingress_age_seconds!==undefined&&(!gpu||capacity||!num(m.ingress_age_seconds)||m.ingress_age_seconds<0||m.ingress_age_seconds>1.5))throw Error('invalid_ingress');
   const ranges={percent:[0,100],celsius:[-273.15,300],bytes:[0,Number.MAX_SAFE_INTEGER],bytes_per_second:[0,Number.MAX_SAFE_INTEGER],megabytes:[0,2147483647],megahertz:[0,100000],watts:[0,5000],rpm:[0,1000000]},[lo,hi]=ranges[m.unit];
   if(m.valid&&(!num(m.value)||m.value<lo||m.value>hi||m.collected_at===null||m.age_seconds===null||m.data_kind==='not_collected')||!m.valid&&m.value!==null)throw Error('invalid_value');
   const age=m.age_seconds===null?null:m.age_seconds+transportSeconds;
   const stale=m.stale||age!==null&&age>=ttl;
   return {id:m.id,source:m.source,unit:m.unit,value:m.valid&&!stale?m.value:null,valid:m.valid&&!stale,stale,state:stale&&m.state==='available'?'stale':m.state,collected_at:m.collected_at,age_seconds:age,expires_after_seconds:ttl,data_kind:m.data_kind};
  });
  return {generation:raw.generation,snapshot:{sequence:s.sequence,generated_at:s.generated_at,contains_simulated:simulation,metrics}};
 }
 function age(view,elapsed){
  if(!view?.snapshot)return view;
  return {...view,snapshot:{...view.snapshot,metrics:view.snapshot.metrics.map(m=>{
   const seconds=m.age_seconds===null?null:m.age_seconds+Math.max(0,elapsed),stale=m.stale||seconds!==null&&seconds>=m.expires_after_seconds;
   return {...m,age_seconds:seconds,stale,valid:m.valid&&!stale,value:m.valid&&!stale?m.value:null,state:stale&&m.state==='available'?'stale':m.state};
  })}};
 }
 function format(m){
  if(!m?.valid||m.value===null)return m?.state==='stale'?'Desatualizado':'Indisponível';
  const n=m.value,units={percent:'%',celsius:' °C',megabytes:' MB',megahertz:' MHz',watts:' W',rpm:' RPM'};
  if(m.unit==='percent'&&n>0&&n<0.1)return '<0,1%';
  if(m.unit==='bytes')return (n/1024**3).toLocaleString('pt-BR',{maximumFractionDigits:1})+' GiB';
  if(m.unit==='bytes_per_second')return (n/1024).toLocaleString('pt-BR',{maximumFractionDigits:2})+' KiB/s';
  return n.toLocaleString('pt-BR',{maximumFractionDigits:1})+(units[m.unit]||'');
 }
 return Object.freeze({normalize,age,format,ids:[...ids.keys()]});
});
