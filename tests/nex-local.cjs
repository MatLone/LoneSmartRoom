'use strict';
// Owned temporary files and explicit synthetic metric fixtures only.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {summarize}=require('../apps/windows-ui/nex-local.cjs'),{createConversation}=require('../apps/windows-ui/nex-conversation.cjs');
const {snapshot}=require('./electron-monitoring.cjs'),{createService}=require('../apps/windows-ui/workbench-service.cjs');
let checks=0;const yes=v=>{assert(v);checks++;},eq=(a,b)=>{assert.deepEqual(a,b);checks++;};
const stamp=Date.now();
function view(){const s=snapshot(false);return {v:1,connection:'connected',simulated:false,gpu_enabled:false,refreshing:false,gpu_resume_state:'disabled',error:null,snapshot:s};}
const v=view(),now=Date.parse(v.snapshot.generated_at);
yes(summarize(null).includes('Sem amostras'));yes(summarize({...v,simulated:true},{now}).includes('Sem amostras'));
const cpu=summarize(v,{now,topic:'cpu'});yes(cpu.includes('CPU:'));yes(cpu.includes('sensor não integrado'));yes(cpu.includes('cache local validado'));yes(!cpu.includes('Autenticado'));
yes(summarize(v,{now:now+10000,topic:'cpu'}).includes('CPU: Indisponível'));
yes(summarize(v,{now:now-1}).includes('Sem amostras'));
const small=structuredClone(v);small.snapshot.metrics.find(m=>m.id==='cpu.utilization').value=.0001;yes(summarize(small,{now,topic:'cpu'}).includes('<0,1%'));
const zero=structuredClone(v);zero.snapshot.metrics.find(m=>m.id==='cpu.utilization').value=0;yes(summarize(zero,{now,topic:'cpu'}).includes('CPU: 0%'));
const invalid=structuredClone(v);invalid.snapshot.metrics.find(m=>m.id==='cpu.utilization').value=Infinity;yes(summarize(invalid,{now}).includes('Sem amostras'));
const base=path.resolve(__dirname,'../.cache/nex-local-tests');fs.mkdirSync(base,{recursive:true});const dir=fs.mkdtempSync(path.join(base,'case-'));
const store=createConversation(dir);eq(store.view().entries.length,0);yes(store.append('estado',cpu,new Date(now).toISOString()));
eq(createConversation(dir).view().entries.length,2);
for(let i=0;i<35;i++)yes(store.append('pergunta '+i,'resposta '+i,new Date(now).toISOString()));
eq(store.view().entries.length,40);yes(fs.statSync(path.join(dir,'nex-conversation-v1.json')).size<=65536);
const file=path.join(dir,'nex-conversation-v1.json');fs.writeFileSync(file,'newer external content');eq(store.append('x','y',new Date(now).toISOString()),false);eq(fs.readFileSync(file,'utf8'),'newer external content');
const corrupt=createConversation(dir);eq(corrupt.append('x','y',new Date(now).toISOString()),false);eq(corrupt.view().error,'conversation_rejected_preserved');
(async()=>{
 const serviceDir=fs.mkdtempSync(path.join(base,'service-'));const service=createService({directory:serviceDir,enabled:true,metrics:()=>v,now:()=>new Date(now).toISOString()});
 const first=await service.handle({v:1,op:'nex',args:{message:'Resumo do estado'}});yes(first.history_persisted);yes(!first.ai&&!first.execution);yes(first.reply.includes('CPU:'));
 const reopened=createService({directory:serviceDir,enabled:true});const data=await reopened.handle({v:1,op:'snapshot',args:{section:'nex'}});eq(data.conversation.length,2);
 const navigation=await service.handle({v:1,op:'nex',args:{message:'Abrir rede'}});eq(navigation.section,'network');yes(!navigation.execution);
 for(const name of fs.readdirSync(serviceDir))yes(!/credential|\.dpapi|\.db/.test(name));service.close();reopened.close();
 console.log(`PASS: ${checks} NEX cache validity, safe navigation, bounded persistence and corruption/concurrency checks; no sensors, AI or operational commands`);
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
