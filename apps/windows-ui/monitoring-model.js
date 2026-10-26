'use strict';
// Shared strict display contract, no Node imports, I/O, paths or execution API.
((root, factory) => { const model=factory();if(typeof module==='object'&&module.exports)module.exports=model;else root.loneMetricModel=model; })(globalThis, () => {
  const fields=new Map([['cpu.utilization',['percent','win32.systemtimes']],
    ...['total','used','available','utilization'].map(k=>['ram.'+k,[k==='utilization'?'percent':'bytes','win32.memory']]),
    ...['c','d'].flatMap(v=>['total','free','available','used','occupation','read_rate','write_rate','activity'].map(k=>[
      'storage.'+v+'.'+k,[['occupation','activity'].includes(k)?'percent':k.endsWith('_rate')?'bytes_per_second':'bytes',
        ['read_rate','write_rate','activity'].includes(k)?'win32.pdh.logicaldisk':'win32.volume.'+v]]))]);
  const states=new Set(['available','warming_up','unsupported','unavailable','permission_denied','error','stale']);
  const gpuFields=new Map(['utilization','temperature','hotspot_temperature','vram_used_mb','vram_total_mb','core_clock','power','fan_rpm']
    .map((key,i)=>['gpu.adlx.'+key,[['percent','celsius','celsius','megabytes','megabytes','megahertz','watts','rpm'][i],'amd.adlx']]));
  function timestamp(value){return typeof value==='string'&&value.length<=40&&/Z$/.test(value)&&Number.isFinite(Date.parse(value));}
  // Display policy is separate from native admission (<=1.5 s) and v1 cache TTL.
  // Dynamic GPU: one cadence + one foreground UI poll. Capacity/basic keep v1.
  function displayLimit(m){return m.id.startsWith('gpu.adlx.')&&!m.id.endsWith('total_mb')?m.interval_seconds+1:3*m.interval_seconds;}
  function normalize(snapshot, {simulated=false, gpu=false, now=Date.now()}={}) {
    if(!snapshot||snapshot.schema_version!==1||!Number.isSafeInteger(snapshot.sequence)||snapshot.sequence<0||
      !timestamp(snapshot.generated_at)||Date.parse(snapshot.generated_at)>now+5000||
      snapshot.contains_simulated!==simulated||!Array.isArray(snapshot.metrics)||snapshot.metrics.length>(gpu?29:21))throw Error('invalid_snapshot');
    const seen=new Set();
    const metrics=snapshot.metrics.map(m=>{
      const isGpu=!!m&&gpuFields.has(m.id),expected=m&&(fields.get(m.id)||(gpu&&gpuFields.get(m.id)));
      if(!expected||seen.has(m.id)||m.unit!==expected[0]||!states.has(m.state)||typeof m.valid!=='boolean'||typeof m.stale!=='boolean'||
        m.source!==(simulated?(isGpu?'fixture.adlx':'fixture.metrics'):expected[1])||!['real','simulated','not_collected'].includes(m.data_kind)||
        (m.data_kind!=='not_collected'&&m.data_kind!==(simulated?'simulated':'real'))||
        (m.collected_at!==null&&!timestamp(m.collected_at))||
        (m.collected_at!==null&&Date.parse(m.collected_at)>Date.parse(snapshot.generated_at))||
        (m.age_seconds!==null&&(!Number.isFinite(m.age_seconds)||m.age_seconds<0))||
        !Number.isFinite(m.interval_seconds)||
        !(isGpu?(m.id==='gpu.adlx.vram_total_mb'?[60]:[2,10]):m.id.startsWith('storage.')&&!['read_rate','write_rate','activity'].includes(m.id.split('.').at(-1))
          ?[60]:[1,5]).includes(m.interval_seconds))throw Error('invalid_metric');
      seen.add(m.id);
      const ingress=m.ingress_age_seconds;
      if(ingress!==undefined&&(!isGpu||m.id.endsWith('total_mb')||!Number.isFinite(ingress)||ingress<0||ingress>1.5))throw Error('invalid_ingress_age');
      if(m.information_age_seconds!==undefined&&(!Number.isFinite(m.information_age_seconds)||m.age_seconds===null||ingress===undefined||
          Math.abs(m.information_age_seconds-m.age_seconds-ingress)>0.000002))throw Error('invalid_information_age');
      const available=m.state==='available'&&!m.stale;
      if(m.valid!==available||(available&&(!Number.isFinite(m.value)||(m.value<0&&m.unit!=='celsius')||
          (m.unit==='percent'&&m.value>100)||(m.unit==='bytes'&&!Number.isSafeInteger(m.value))||
          !timestamp(m.collected_at)||m.age_seconds===null||m.data_kind==='not_collected'))||
        (!available&&m.value!==null))throw Error('invalid_value');
      if(available&&isGpu){
        const bounds={celsius:[-273.15,300],megabytes:[0,2**31-1],megahertz:[0,100000],watts:[0,5000],rpm:[0,1000000]};
        const limits=bounds[m.unit];
        if((limits&&(m.value<limits[0]||m.value>limits[1]))||
          (['megabytes','megahertz','rpm'].includes(m.unit)&&!Number.isSafeInteger(m.value)))throw Error('invalid_gpu_value');
      }
      const expired=m.age_seconds!==null&&m.age_seconds>=displayLimit(m);
      return {id:m.id,source:m.source,unit:m.unit,collected_at:m.collected_at,age_seconds:m.age_seconds,
        ingress_age_seconds:ingress,information_age_seconds:ingress===undefined?null:m.age_seconds+ingress,
        display_limit_seconds:displayLimit(m),
        interval_seconds:m.interval_seconds,data_kind:m.data_kind,state:expired&&available?'stale':m.state,
        stale:m.stale||expired,valid:available&&!expired,value:available&&!expired?m.value:null};
    });
    // Never infer installed RAM or repair contradictory batches with fabricated numbers.
    const byId=new Map(metrics.map(m=>[m.id,m]));
    const ram=['total','used','available','utilization'].map(k=>byId.get('ram.'+k));
    if(ram.every(m=>m?.valid)&&new Set(ram.map(m=>m.collected_at)).size===1){
      const [total,used,available,percent]=ram.map(m=>m.value);
      if(total<=0||used+available!==total||Math.abs(percent-used/total*100)>1e-6)throw Error('inconsistent_ram');
    }
    const used=byId.get('gpu.adlx.vram_used_mb'),total=byId.get('gpu.adlx.vram_total_mb');
    if(total?.valid&&(total.value<=0||(used?.valid&&used.value>total.value)))throw Error('inconsistent_vram');
    return {schema_version:1,sequence:snapshot.sequence,generated_at:snapshot.generated_at,contains_simulated:simulated,metrics};
  }
  function age(snapshot, elapsedSeconds) {
    return {...snapshot,metrics:snapshot.metrics.map(m=>{
      const elapsed=Number.isFinite(elapsedSeconds)&&elapsedSeconds>=0?elapsedSeconds:Infinity;
      const seconds=m.age_seconds===null?null:m.age_seconds+elapsed,stale=m.stale||(seconds!==null&&seconds>=displayLimit(m));
      return {...m,age_seconds:seconds,information_age_seconds:m.ingress_age_seconds===undefined||seconds===null?null:seconds+m.ingress_age_seconds,
        stale,valid:m.valid&&!stale,value:m.valid&&!stale?m.value:null,state:stale&&m.state==='available'?'stale':m.state};
    })};
  }
  function format(metric){
    if(!metric?.valid||metric.stale||metric.value===null)return '—';
    const n=metric.value;
    if(metric.unit==='percent')return n>0&&n<0.1?'<0,1%':n.toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
    if(metric.unit==='bytes')return (n/1024**3).toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1})+' GiB';
    const gpuUnits={celsius:'°C',megabytes:'MB',megahertz:'MHz',watts:'W',rpm:'RPM'};
    if(gpuUnits[metric.unit])return n.toLocaleString('pt-BR',{maximumFractionDigits:1})+' '+gpuUnits[metric.unit];
    if(metric.unit==='bytes_per_second'){
      const divisor=n>=1024**2?1024**2:n>=1024?1024:1,unit=divisor===1?'bytes/s':divisor===1024?'KiB/s':'MiB/s';
      const scaled=n/divisor;
      return (scaled>0&&scaled<0.01?'<0,01':scaled.toLocaleString('pt-BR',{maximumFractionDigits:2}))+' '+unit;
    }
    return '—';
  }
  return Object.freeze({normalize,age,format,displayLimit,ids:Object.freeze([...fields.keys()]),gpuIds:Object.freeze([...gpuFields.keys()])});
});
