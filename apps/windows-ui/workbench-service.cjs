'use strict';
// Main-process application state/planning only. No system mutations or generic executor.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const catalog=require('./workbench-catalog.cjs'),model=require('./workbench-model.js');
const OPS=Object.freeze({snapshot:['section'],inventory:['kind'],repair:['id'],profile:['name','adjustments'],bundle:['name','packages'],device:['id','name','connector','entity'],scene:['name','deviceIds','color','brightness'],scenePreview:['id'],nex:['message'],cleanup:[],export:[],import:['data'],audit:[],network:['kind','target'],gameProfile:['name','monitoring','overlay'],game:['name','steamAppId'],historyPolicy:['enabled','retentionHours']});
const INVENTORIES=['hardware','memory','network','processes','applications','startup','services','drivers','events','disks','peripherals','games'];
const text=(s,max=80)=>typeof s==='string'&&s.length>0&&s.length<=max&&!/[\x00-\x08\x0b-\x1f]/.test(s);
const object=o=>o&&typeof o==='object'&&!Array.isArray(o);
function exact(o,keys){if(!object(o)||Object.keys(o).sort().join(',')!==[...keys].sort().join(','))throw Error('invalid_tool_contract');}
function defaults(){return {v:1,profile:{name:'Padrão',adjustments:[]},bundles:[],devices:[],scenes:[],gameProfiles:[],games:[],audit:[],history:{enabled:false,retentionHours:1}};}
function validateState(s){
 if(object(s)&&s.v===1&&!Object.hasOwn(s,'history'))s={...s,history:{enabled:false,retentionHours:1}};
 if(object(s)&&s.v===1&&!Object.hasOwn(s,'games'))s={...s,games:[]};
 exact(s,['v','profile','bundles','devices','scenes','gameProfiles','audit','history','games']);if(s.v!==1)throw Error('state_version');
 exact(s.history,['enabled','retentionHours']);if(typeof s.history.enabled!=='boolean'||![1,6,24,168].includes(s.history.retentionHours))throw Error('history_policy');
 exact(s.profile,['name','adjustments']);if(!catalog.PROFILES.includes(s.profile.name)||!Array.isArray(s.profile.adjustments)||s.profile.adjustments.length>catalog.ADJUSTMENTS.length||s.profile.adjustments.some(id=>!catalog.ADJUSTMENTS.some(a=>a.id===id)))throw Error('profile');
 for(const [key,max]of [['bundles',20],['devices',32],['scenes',20],['gameProfiles',30],['games',100],['audit',120]])if(!Array.isArray(s[key])||s[key].length>max)throw Error('state_limit');
 for(const b of s.bundles){exact(b,['name','packages']);if(!text(b.name)||!Array.isArray(b.packages)||b.packages.length>catalog.PACKAGES.length||b.packages.some(id=>!catalog.PACKAGES.some(p=>p.id===id)))throw Error('bundle');}
 for(const d of s.devices){exact(d,['id','name','connector','entity']);if(!text(d.id,32)||!/^[a-z0-9-]+$/.test(d.id)||!text(d.name)||!catalog.CONNECTORS.some(c=>c.id===d.connector)||typeof d.entity!=='string'||d.entity.length>100||d.entity&&!/^[a-z_]+\.[a-z0-9_]+$/.test(d.entity))throw Error('device');}
 if(new Set(s.devices.map(d=>d.id)).size!==s.devices.length)throw Error('device_duplicate');
 for(const scene of s.scenes){exact(scene,['id','name','deviceIds','color','brightness']);if(!/^[a-f0-9]{16}$/.test(scene.id)||!text(scene.name)||!Array.isArray(scene.deviceIds)||scene.deviceIds.length>32||scene.deviceIds.some(id=>!s.devices.some(d=>d.id===id))||!/^#[0-9a-fA-F]{6}$/.test(scene.color)||!Number.isInteger(scene.brightness)||scene.brightness<0||scene.brightness>100)throw Error('scene');}
 for(const g of s.games){exact(g,['name','steamAppId']);if(!text(g.name)||g.steamAppId!==null&&(!Number.isSafeInteger(g.steamAppId)||g.steamAppId<1||g.steamAppId>2147483647))throw Error('game_metadata');}
 for(const g of s.gameProfiles){exact(g,['name','monitoring','overlay']);if(!text(g.name)||typeof g.monitoring!=='boolean'||typeof g.overlay!=='boolean')throw Error('game_profile');}
 for(const a of s.audit){exact(a,['at','operation','outcome']);if(!Number.isFinite(Date.parse(a.at))||!Object.hasOwn(OPS,a.operation)||!['saved','planned'].includes(a.outcome))throw Error('audit');}
 if(Buffer.byteLength(JSON.stringify(s))>131072)throw Error('state_bytes');return s;
}
function createService({directory,enabled=false,inventory=async()=>({v:1,state:'unavailable',source:'unconfigured',items:[]}),network=async()=>({v:1,state:'unavailable'}),metrics=()=>null,now=()=>new Date().toISOString()}={}){
 if(!path.isAbsolute(directory)||typeof enabled!=='boolean')throw Error('private_app_directory');
 const file=path.join(directory,'workbench-v1.json');let state=defaults(),readOnly=false,error=null,conversation=[];
 function safeDirectory(){let current=path.parse(directory).root;for(const part of path.relative(current,directory).split(path.sep)){current=path.join(current,part);if(fs.existsSync(current)){const s=fs.lstatSync(current);if(!s.isDirectory()||s.isSymbolicLink())throw Error('unsafe_app_directory');}else fs.mkdirSync(current);}if(fs.existsSync(file)){const s=fs.lstatSync(file);if(!s.isFile()||s.isSymbolicLink()||s.nlink!==1)throw Error('unsafe_state_file');}}
 if(enabled)try{safeDirectory();if(fs.existsSync(file)){if(fs.statSync(file).size>131072)throw Error();state=validateState(JSON.parse(fs.readFileSync(file,'utf8')));}}catch{error='state_rejected_preserved';readOnly=true;}
 function save(next,op,outcome='saved'){
  if(!enabled||readOnly)throw Error('app_settings_disabled');
  next.audit=[...state.audit,{at:now(),operation:op,outcome}].slice(-120);validateState(next);safeDirectory();
  const temp=path.join(directory,'.workbench-'+crypto.randomBytes(12).toString('hex')+'.tmp');let owned=false;
  try{fs.writeFileSync(temp,JSON.stringify(next),{flag:'wx',mode:0o600});owned=true;fs.renameSync(temp,file);owned=false;state=next;error=null;}
  finally{if(owned)fs.unlinkSync(temp);}
 }
 const clone=()=>JSON.parse(JSON.stringify(state));
 function cleanupPreview(){
  // Inspect ONLY cache owned by this module. No personal/system/temp-root scan.
  const root=path.join(directory,'tool-cache'),items=[];let bytes=0;
  if(fs.existsSync(root)){
   const s=fs.lstatSync(root);if(!s.isDirectory()||s.isSymbolicLink())throw Error('cleanup_scope_rejected');
   for(const name of fs.readdirSync(root).slice(0,250)){
    const p=path.join(root,name),st=fs.lstatSync(p);if(!st.isFile()||st.isSymbolicLink()||st.nlink!==1||Date.now()-st.mtimeMs<86400000)continue;
    const id=crypto.createHash('sha256').update(name+'|'+st.size+'|'+st.mtimeMs).digest('hex');items.push({id,name:name.slice(0,120),bytes:st.size,modified_at:st.mtime.toISOString()});bytes+=st.size;
   }
  }
  return {v:1,state:'preview',scope:'cache_proprio_lsr',items,estimated_bytes:bytes,execution_enabled:false,excluded:['Dados pessoais','Credenciais e pareamento','Caches ativos','Windows e instaladores desconhecidos','Lixeira: requer seleção e homologação própria']};
 }
 async function handle(q){
  exact(q,['v','op','args']);if(q.v!==1||typeof q.op!=='string'||!Object.hasOwn(OPS,q.op)||JSON.stringify(q).length>131072)throw Error('tool_request_rejected');exact(q.args,OPS[q.op]);
  const a=q.args;if(q.op==='snapshot'){
   if(!catalog.SECTIONS.some(s=>s.id===a.section))throw Error('unknown_section');
   return {v:1,enabled,read_only:readOnly,error,catalog,settings:clone(),conversation:conversation.slice(-20),system_actions_enabled:false};
  }
  if(!enabled)throw Error('development_tools_disabled');
  if(q.op==='inventory'){if(!INVENTORIES.includes(a.kind))throw Error('inventory_kind');return inventory(a.kind);}
  if(q.op==='network'){if(!['ping','dns'].includes(a.kind)||!text(a.target,253)||!/^([a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?|[0-9a-fA-F:]{2,})$/.test(a.target)||a.target.startsWith('-')||a.target.includes('..'))throw Error('network_target');return network(a.kind,a.target);}
  if(q.op==='cleanup')return cleanupPreview();
  if(q.op==='repair'){const p=catalog.REPAIRS.find(p=>p.id===a.id);if(!p)throw Error('repair_id');return {v:1,...p,state:'plan_only',execution_enabled:false};}
  if(q.op==='export')return {v:1,kind:'lone_workbench_settings',settings:clone()};
  if(q.op==='audit')return {v:1,entries:clone().audit};
  if(q.op==='nex'){
   if(!text(a.message,1000))throw Error('nex_message');
   const message=a.message.toLocaleLowerCase('pt-BR');let intent='explain',reply='Sou o NEX em modo local. Posso organizar as ferramentas e resumir evidências disponíveis. Nenhum provedor de IA ou voz está configurado.',section=null;
   for(const [pattern,id]of [[/temperatura|cpu|gpu|memória|memoria|monitor/,'hardware'],[/limp|repar|sfc|dism/,'maintenance'],[/jogo|fps|gamer/,'games'],[/rede|internet|ping|dns/,'network'],[/rgb|quarto|luz|cena/,'environment']])if(pattern.test(message)){intent='navigate';section=id;reply='Abra '+catalog.SECTIONS.find(s=>s.id===id).title+'. Ações no Windows e em equipamentos exigem autorização específica.';break;}
   if(/estado|diagn[oó]stico|resumo/.test(message)){intent='summarize_evidence';const v=metrics();reply=v?.connection==='connected'?'O monitoramento local informa conexão com o coletor. Consulte origem e horário de cada métrica; isso não comprova a saúde do agente HTTPS.':'Não há evidência atual suficiente para confirmar a saúde dos serviços. A ausência de dados não comprova falha ou PC desligado.';}
   conversation.push({role:'user',text:a.message},{role:'nex',text:reply});conversation=conversation.slice(-40);
   return {v:1,provider:'local_rules',ai:false,intent,section,reply,execution:false,history_persisted:false};
  }
  if(q.op==='scenePreview'){
   const s=state.scenes.find(s=>s.id===a.id);if(!s)throw Error('scene_id');
   return {v:1,state:'plan_only',name:s.name,actions:s.deviceIds.map(id=>({device:state.devices.find(d=>d.id===id).name,color:s.color,brightness:s.brightness,available:false,reason:'Conector não ativado/homologado'})),physical_actions:0};
  }
  let next=clone();
  if(q.op==='profile')next.profile={name:a.name,adjustments:a.adjustments};
  if(q.op==='historyPolicy')next.history={enabled:a.enabled,retentionHours:a.retentionHours};
  if(q.op==='bundle'){if(!text(a.name))throw Error('bundle_name');next.bundles=next.bundles.filter(b=>b.name!==a.name);next.bundles.push({name:a.name,packages:a.packages});}
  if(q.op==='device'){next.devices=next.devices.filter(d=>d.id!==a.id);next.devices.push({...a});}
  if(q.op==='scene'){next.scenes=next.scenes.filter(s=>s.name!==a.name);next.scenes.push({id:crypto.randomBytes(8).toString('hex'),...a});}
  if(q.op==='game'){next.games=next.games.filter(g=>g.name!==a.name);next.games.push({...a});}
  if(q.op==='gameProfile'){next.gameProfiles=next.gameProfiles.filter(p=>p.name!==a.name);next.gameProfiles.push({...a});}
  if(q.op==='import'){exact(a.data,['v','kind','settings']);if(a.data.v!==1||a.data.kind!=='lone_workbench_settings')throw Error('settings_import');next=validateState(JSON.parse(JSON.stringify(a.data.settings)));}
  save(next,q.op);return {v:1,saved:true,applied_to_windows:false,settings:clone()};
 }
 return Object.freeze({handle,stats:()=>({enabled,readOnly,error,bytes:Buffer.byteLength(JSON.stringify(state))}),close(){conversation=[];}});
}
module.exports={createService,validateState,OPS,INVENTORIES};
