'use strict';
(function(root){
  const contract=typeof module==='object'&&module.exports?require('./diagnostics-contract.js'):root.loneDiagnosticContract;
  const scenarios=Object.freeze(['overview','healthy','inactive','offline','listener-mismatch','auth-failure','pipe-absent','sensor-unavailable','stale','provider-error','unverified','recovered','startup-inconclusive']);
  const labels=Object.freeze({healthy:'Saudável',inactive:'Inativo normalmente',unavailable:'Indisponível',offline:'Indisponível',unsupported:'Indisponível',stale:'Desatualizado',error:'Falha',unknown:'Não verificado'});
  const definitions=[['https','Agente HTTPS','shield',['agent_https','listener_8776']],
    ['monitoring','Monitoramento PC','monitor',['cpu_collector','gpu_collector','ram_collector']],
    ['pipe','Named Pipe','link',['monitoring_ipc']],['adlx','Ponte AMD ADLX','chip',['adlx_bridge']],
    ['sensors','Sensores','activity',['cpu_collector','gpu_collector','ram_collector']],
    ['startup','Inicialização automática','clock',['agent_startup']],['security','Segurança','lock',['agent_https','listener_8776','monitoring_ipc']]];
  const pending=Object.freeze([
    {id:'tls10054',title:'TLS 10054',status:'Ainda não corrigido'},
    {id:'startup',title:'Inicialização automática',status:'Inconclusiva'},
    {id:'shutdown',title:'Encerramento gracioso do agente',status:'Não validado operacionalmente'},
    {id:'crashpad',title:'Crashpad 0xE9',status:'Mensagens ainda não esclarecidas'},
    {id:'dev7',title:'Windows dev.7',status:'Homologação física parcial'}]);
  const exact=(x,keys)=>Boolean(x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k)));
  const finite=x=>typeof x==='number'&&Number.isFinite(x)&&x>=0;
  const utc=x=>typeof x==='string'&&x.length<=32&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(Date.parse(x)).toISOString().slice(0,19)===x.slice(0,19);
  function bytes(value){try{return new TextEncoder().encode(JSON.stringify(value)).length;}catch{return Infinity;}}
  function request(value){return exact(value,['v','scenario'])&&value.v===1&&typeof value.scenario==='string'&&scenarios.includes(value.scenario)&&bytes(value)<=96;}
  function validate(report,local=false){
    if(bytes(report)>16384||!exact(report,['schema_version','generated_at','mode','simulation','repair_capability','power_state','checks'])||
       report.schema_version!==1||report.simulation!==(local?false:true)||report.repair_capability!==false||report.power_state!=='unknown'||
       !['active','inactive'].includes(report.mode)||!utc(report.generated_at)||!Array.isArray(report.checks)||report.checks.length!==8)return false;
    const seen=new Set();
    for(const row of report.checks){
      if(!exact(row,['component','state','code','detail_code','evidence_kind','observed_at','age_seconds','valid','freshness_seconds','last_communication'])||
         !contract.components.includes(row.component)||seen.has(row.component)||!contract.states.includes(row.state)||!contract.codes.includes(row.code)||
         row.detail_code!==null&&!contract.details.includes(row.detail_code)||row.evidence_kind!==(local?'local_cache':'simulated')||typeof row.valid!=='boolean'||row.valid!==(row.state==='healthy')||
         ![3,5,10,11,15,300].includes(row.freshness_seconds)||row.age_seconds!==null&&!finite(row.age_seconds)||
         row.observed_at!==null&&(!utc(row.observed_at)||Date.parse(row.observed_at)>Date.parse(report.generated_at))||
         row.last_communication!==null&&(!utc(row.last_communication)||row.component!=='agent_https'||Date.parse(row.last_communication)>Date.parse(report.generated_at)))return false;
      const expectedTTL={agent_https:[10],listener_8776:[10],monitoring_ipc:[5],cpu_collector:[3,15],ram_collector:[3,15],gpu_collector:[report.mode==='active'?3:11],adlx_bridge:[report.mode==='active'?3:11],agent_startup:[300]};
      if(!expectedTTL[row.component].includes(row.freshness_seconds))return false;
      if(row.valid){
        const healthyCodes={agent_https:'authenticated_https',listener_8776:'expected_listener',monitoring_ipc:'validated_ipc',
          cpu_collector:'valid_sample',gpu_collector:'valid_sample',ram_collector:'valid_sample',adlx_bridge:'valid_sample',agent_startup:'bootstrap_observed'};
        const healthyDetails={agent_https:['https_status_verified'],listener_8776:['listener_identity_verified'],monitoring_ipc:[],
          cpu_collector:['metrics_valid','metrics_partial_support'],gpu_collector:['metrics_valid','metrics_partial_support'],
          ram_collector:['metrics_valid','metrics_partial_support'],adlx_bridge:['adlx_frame_valid'],agent_startup:['startup_bootstrap_seen']};
        if(row.code!==healthyCodes[row.component]||row.detail_code!==null&&!healthyDetails[row.component].includes(row.detail_code))return false;
      }
      if(row.valid&&(row.observed_at===null||row.age_seconds===null||row.age_seconds>=row.freshness_seconds||
          (Date.parse(report.generated_at)-Date.parse(row.observed_at))/1000>=row.freshness_seconds))return false;
      seen.add(row.component);
    }
    return true;
  }
  function aggregate(rows){
    if(rows.some(r=>['provider_failure','provider_timeout'].includes(r.code)))return 'error';
    if(rows.length&&rows.every(r=>r.detail_code==='application_normally_inactive'&&['unavailable','offline'].includes(r.state)))return 'inactive';
    for(const state of ['error','unknown','stale','offline','unavailable','unsupported'])if(rows.some(r=>r.state===state))return state;
    return rows.length&&rows.every(r=>r.state==='healthy')?'healthy':'unknown';
  }
  const securityIds=['process_identity','tls_identity','hmac','antireplay','device_permissions','pipe_acl','local_only'];
  const issueIds=['tls_10054','startup_unresolved','graceful_shutdown_unvalidated','crashpad_0xe9','dev7_partial'];
  function securityEvidence(value,generated){
    if(value===null)return true;
    if(bytes(value)>8192||!exact(value,['schema_version','simulation','state','observed_at','checks','known_issues','repair_capability'])||
      value.schema_version!==1||value.simulation!==true||value.repair_capability!==false||!utc(value.observed_at)||
      Date.parse(value.observed_at)>Date.parse(generated)||!Array.isArray(value.known_issues)||value.known_issues.length!==5||
      !issueIds.every(id=>value.known_issues.includes(id))||!Array.isArray(value.checks)||value.checks.length>7)return false;
    const seen=new Set();let failed=false,stale=false;
    for(const r of value.checks){
      if(!exact(r,['id','authorized','result','checked_at','age_seconds','stale'])||!securityIds.includes(r.id)||seen.has(r.id)||
        typeof r.authorized!=='boolean'||!['verified','failed','unknown','not_checked'].includes(r.result)||
        !r.authorized&&!['unknown','not_checked'].includes(r.result)||typeof r.stale!=='boolean')return false;
      if(r.checked_at===null){if(r.age_seconds!==null||r.stale||['verified','failed'].includes(r.result))return false;}
      else if(!utc(r.checked_at)||!finite(r.age_seconds)||Date.parse(r.checked_at)>Date.parse(generated)||Date.parse(r.checked_at)>Date.parse(value.observed_at)||
        Math.abs((Date.parse(generated)-Date.parse(r.checked_at))/1000-r.age_seconds)>.002||r.stale!==(r.age_seconds>=10))return false;
      failed||=r.authorized&&r.result==='failed'&&!r.stale;stale||=r.stale;seen.add(r.id);
    }
    return value.state===(failed?'error':stale?'stale':'unknown');
  }
  function adapterBundle(value){
    return exact(value,['schema_version','simulation','report','security'])&&value.schema_version===1&&value.simulation===true&&
      bytes(value)<=32768&&validate(value.report)&&securityEvidence(value.security,value.report.generated_at);
  }
  function empty(error='disabled'){
    return {v:1,simulation:false,clock:null,error,scenario:null,pending,
      cards:definitions.map(([id,title,icon])=>({id,title,icon,state:'unknown',label:labels.unknown,checkedAt:null,
        summary:'Sem evidência disponível nesta interface. Nenhuma verificação real foi feita.',details:[],simulated:false}))};
  }
  function project(envelope){
    const hasEvidence=Boolean(envelope&&Object.hasOwn(envelope,'evidence'));
    if(!exact(envelope,['v','mode','scenario','error','report',...(hasEvidence?['evidence']:[])])||envelope.v!==1||!['simulation','local','disabled'].includes(envelope.mode)||bytes(envelope)>18432)return empty('invalid_message');
    if(envelope.error!==null){
      if(!['disabled','invalid_request','rate_limited','busy','provider_unavailable','provider_timeout','invalid_report'].includes(envelope.error))return empty('invalid_message');
      return empty(envelope.error);
    }
    const local=envelope.mode==='local';
    if(!['simulation','local'].includes(envelope.mode)||!scenarios.includes(envelope.scenario)||!validate(envelope.report,local)||local&&hasEvidence)return empty('invalid_message');
    if(hasEvidence&&(!exact(envelope.evidence,['schema_version','simulation','security'])||envelope.evidence.schema_version!==1||envelope.evidence.simulation!==true||!securityEvidence(envelope.evidence.security,envelope.report.generated_at)))return empty('invalid_message');
    const report=envelope.report,byId=new Map(report.checks.map(r=>[r.component,r]));
    const cards=definitions.map(([id,title,icon,ids])=>{
      const rows=ids.map(key=>byId.get(key));let state=aggregate(rows);
      // Verified subsets never certify overall security while known issues remain.
      if(id==='security'&&state!=='error')state='unknown';
      const dates=rows.map(r=>r.observed_at).filter(Boolean).sort();
      const checkedAt=dates.length?dates[0]:null; // Conservative oldest constituent.
      let summary=state==='inactive'?'Aplicativo fechado; inatividade normal demonstrada. Nenhum componente foi iniciado.':
        state==='healthy'?'Evidências válidas neste cenário simulado. Não representa o estado real do computador.':
        state==='stale'?'A evidência simulada expirou. Uma nova consulta não torna a amostra antiga atual.':
        state==='error'?'Uma verificação falhou neste cenário de demonstração. Não é um diagnóstico do seu PC.':
        state==='unknown'?'Sem evidência suficiente para concluir. Ausência de informação não comprova falha.':
        'Sem disponibilidade neste cenário. Valores ausentes não são substituídos por zero.';
      if(id==='https'&&['offline','unavailable'].includes(state))summary='Sem resposta autenticada na simulação. Isso não confirma que o computador está desligado.';
      if(id==='security')summary=state==='error'?'Falha simulada em uma verificação; nenhuma credencial é exposta.':'Verificações parciais de demonstração. As pendências de segurança continuam abertas.';
      const details=rows.map(r=>({component:r.component,state:labels[r.state],code:r.detail_code||r.code,
        message:r.code==='provider_failure'?'Erro simulado do provedor. O estado do componente não foi confirmado.':contract.messages[r.detail_code]||contract.fallback[r.code]||'Evidência inconclusiva.',
        checkedAt:r.observed_at,age:r.age_seconds,ttl:r.freshness_seconds,lastCommunication:r.last_communication}));
      if(local){summary=state==='healthy'?'Evidência atual do cache local validado. Não comprova a saúde do agente HTTPS.':state==='stale'?'Amostra local expirada. Uma consulta não renova sua idade.':state==='error'?'Erro registrado no componente local; nenhum reparo executado.':state==='unknown'?(id==='https'||id==='startup'||id==='security'?'Verificação não realizada. Sem identidade desktop autenticada, HTTPS e inicialização automática permanecem não verificados.':'Sem evidência suficiente no cache local. Isso não confirma falha.'):'Sem leitura local disponível. Nenhum sensor foi iniciado pelo diagnóstico.';}
      return {id,title,icon,state,label:labels[state],checkedAt,summary,details,simulated:!local};
    });
    const security=hasEvidence?envelope.evidence.security:null;
    if(security){
      const card=cards.find(c=>c.id==='security'),baseError=card.state==='error',baseDetails=baseError?card.details:[];
      card.state=baseError?'error':security.state;card.label=labels[card.state];
      if(!baseError)card.checkedAt=security.checks.map(r=>r.checked_at).filter(Boolean).sort()[0]||null;
      card.summary=card.state==='error'?'Falha confirmada em uma verificação simulada de segurança. O estado do agente continua sendo avaliado separadamente.':
        security.state==='stale'?'Verificações simuladas antigas. Nenhuma consulta renovou suas evidências.':'Verificações disponíveis são parciais. As cinco investigações conhecidas permanecem abertas.';
      card.details=baseDetails.concat(security.checks.map(r=>({component:r.id,state:r.stale?labels.stale:r.result==='failed'?labels.error:r.authorized&&r.result==='verified'?labels.healthy:labels.unknown,
        code:r.stale?'security_check_stale':r.result==='failed'?'security_check_failed':r.result==='verified'?'security_check_verified':'security_check_unverified',
        message:r.authorized?'Evidência de demonstração de uma verificação autorizada; não contém dados de credenciais.':'Verificação não autorizada ou não realizada neste cenário; não permite uma conclusão positiva.',checkedAt:r.checked_at,age:r.age_seconds,ttl:10,lastCommunication:null})));
    }
    return {v:1,simulation:!local,clock:report.generated_at,error:null,scenario:envelope.scenario,pending,cards};
  }
  const api=Object.freeze({scenarios,labels,pending,request,validate,project,empty,bytes,securityEvidence,adapterBundle});
  if(typeof module==='object'&&module.exports)module.exports=api;else root.loneDiagnosticModel=api;
})(typeof window==='object'?window:globalThis);
