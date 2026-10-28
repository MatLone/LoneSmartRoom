'use strict';
// Pure projection of the existing owned collector's cache. No readers or I/O.
((root,factory)=>{
  const api=factory(typeof module==='object'&&module.exports?require('./monitoring-model.js'):root.loneMetricModel);
  if(typeof module==='object'&&module.exports)module.exports=api;else root.loneHardwareDiagnostics=api;
})(globalThis,metrics=>{
  const groups=[['cpu','CPU · utilização',['cpu.utilization']],
    ['ram','Memória RAM',['total','used','available','utilization'].map(k=>'ram.'+k)],
    ['gpu','GPU · AMD ADLX',[...metrics.gpuIds]],
    ...['c','d'].flatMap(v=>[
      ['volume-'+v,'Volume '+v.toUpperCase()+': · capacidade',['total','free','available','used','occupation'].map(k=>'storage.'+v+'.'+k)],
      ['io-'+v,'Volume '+v.toUpperCase()+': · atividade',['read_rate','write_rate','activity'].map(k=>'storage.'+v+'.'+k)]])];
  const labels=Object.freeze({available:'Leituras disponíveis',partial:'Suporte parcial',unknown:'Não verificado',
    unavailable:'Sem leitura atual',unsupported:'Não suportado',stale:'Leituras desatualizadas',
    error:'Erro de leitura',permission_denied:'Leitura não permitida',warming_up:'Aguardando amostra',disabled:'Coleta desativada'});
  function empty(reason='unknown',origin='none'){
    return {v:1,origin,reason,sequence:null,generatedAt:null,rows:groups.map(([id,title,ids])=>
      ({id,title,state:reason,label:labels[reason],valid:0,expected:ids.length,evidence:[]}))};
  }
  function project(view,{elapsedSeconds=0,now=Date.now()}={}){
    try{
      if(!view||view.v!==1||new TextEncoder().encode(JSON.stringify(view)).byteLength>65536||!Number.isFinite(now)||
        !Number.isFinite(elapsedSeconds)||elapsedSeconds<0||typeof view.simulated!=='boolean'||
        !['connected','connecting','disconnected','disabled','stopped'].includes(view.connection))return empty();
      const origin=view.simulated?'simulated':'real';
      if(view.connection!=='connected')return empty(view.connection==='disabled'?'disabled':'unavailable');
      if(typeof view.gpu_enabled!=='boolean'||typeof view.refreshing!=='boolean'||view.error!==null||
        view.gpu_resume_state!==undefined&&!['disabled','idle','updating','ready','unavailable'].includes(view.gpu_resume_state)||
        !view.snapshot||Date.parse(view.snapshot.generated_at)>now)return empty();
      // Validate provenance, units, numbers, cadence and temporal admission again.
      // Host's display projection includes null information-age when there is no
      // ingress timestamp. The wire normalizer expects that optional field absent.
      const input={...view.snapshot,metrics:view.snapshot.metrics.map(m=>{
        if(m?.information_age_seconds===null&&m.ingress_age_seconds===undefined){
          const {information_age_seconds,...wire}=m;return wire;
        }
        return m;
      })};
      const snapshot=metrics.age(metrics.normalize(input,{simulated:view.simulated,gpu:view.gpu_enabled,now}),elapsedSeconds);
      const byId=new Map(snapshot.metrics.map(m=>[m.id,m]));
      const rows=groups.map(([id,title,ids])=>{
        const evidence=ids.map(key=>byId.get(key)).filter(Boolean);
        let state='unknown';
        if(id==='gpu'&&!view.gpu_enabled)state='disabled';
        else if(evidence.length===ids.length){
          if(evidence.some(m=>m.state==='error'))state='error';
          else if(evidence.some(m=>m.state==='permission_denied'))state='permission_denied';
          else if(evidence.some(m=>m.stale))state='stale';
          else if(evidence.every(m=>m.state==='unsupported'))state='unsupported';
          else if(evidence.some(m=>m.state==='unavailable'))state='unavailable';
          else if(evidence.some(m=>m.state==='warming_up'))state='warming_up';
          else if(evidence.every(m=>m.valid))state='available';
          else if(evidence.some(m=>m.valid)&&evidence.every(m=>m.valid||m.state==='unsupported'))state='partial';
        }
        if(id==='gpu'&&view.gpu_enabled){
          if(view.refreshing||view.gpu_resume_state==='updating')state='warming_up';
          else if(view.gpu_resume_state==='unavailable')state='unavailable';
        }
        const withheld=id==='gpu'&&(view.refreshing||['updating','unavailable'].includes(view.gpu_resume_state));
        return {id,title,state,label:labels[state],valid:withheld?0:evidence.filter(m=>m.valid).length,expected:ids.length,
          evidence:evidence.map(m=>({id:m.id,source:m.source,state:m.state,stale:m.stale,
            collectedAt:m.collected_at,ageSeconds:m.age_seconds,limitSeconds:metrics.displayLimit(m)}))};
      });
      return {v:1,origin,reason:null,sequence:snapshot.sequence,generatedAt:snapshot.generated_at,rows};
    }catch{return empty();}
  }
  return Object.freeze({project,labels});
});
