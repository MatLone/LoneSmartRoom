'use strict';
(()=>{
 const panel=document.getElementById('performanceHistory');if(!panel)return;
 const select=document.getElementById('historyWindow'),label=document.getElementById('historyState'),grid=document.getElementById('historyCharts');
 let pending=false,request=0,timer=null;
 const names={'cpu.utilization':'CPU · utilização','gpu.adlx.utilization':'GPU · utilização','gpu.adlx.temperature':'GPU · temperatura','ram.used':'RAM · utilizada','ram.utilization':'RAM · utilização'};
 function draw(report){
  if(!report||report.v!==1||!Array.isArray(report.fields)||!Array.isArray(report.rows)||report.rows.length>120||JSON.stringify(report).length>131072)throw Error();
  label.textContent=report.state==='disabled'?'Histórico desativado · disponível apenas em desenvolvimento':report.rows.length?(report.simulation?'DEMONSTRAÇÃO · dados simulados':'Histórico de medições locais'):'Sem amostras registradas';
  const legacy=document.querySelector('.chart-card');if(legacy)legacy.hidden=report.state!=='disabled';
  grid.replaceChildren();
  if(!report.rows.length)return;
  for(let i=0;i<report.fields.length;i++){
   const [id,unit]=report.fields[i],points=report.rows.map(r=>[r[0],r[i+2]]),card=document.createElement('article');card.className='history-chart';
   const title=document.createElement('h3');title.textContent=names[id]||id.replace('storage.','Volume ').replace('.',' · ');card.append(title);
   const values=points.filter(p=>p[1][1]==='available'&&typeof p[1][0]==='number'&&Number.isFinite(p[1][0]));
   const summary=document.createElement('p');summary.textContent=values.length?`${values.length} pontos válidos · ${unit} · sem interpolação`:'Indisponível neste intervalo';card.append(summary);
   const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 300 80');svg.setAttribute('role','img');svg.setAttribute('aria-label',title.textContent+' · série temporal');
   const max=unit==='percent'?100:Math.max(1,...values.map(p=>p[1][0])),start=report.rows[0][0],duration=Math.max(1,report.rows.at(-1)[0]-start);
   let segment=[];const append=()=>{if(!segment.length)return;const line=document.createElementNS(svg.namespaceURI,'polyline');line.setAttribute('points',segment.join(' '));svg.append(line);segment=[];};
   for(const [t,m]of points){if(m[1]!=='available'||m[0]===null){append();continue;}segment.push(`${5+(t-start)/duration*290},${75-m[0]/max*65}`);}append();card.append(svg);grid.append(card);
  }
 }
 async function load(){
  if(pending||document.hidden||document.getElementById('panel-monitor').hidden)return;
  pending=true;const id=++request;
  try{const r=await window.loneDesktop?.getPerformanceHistory(Number(select.value));if(id===request)draw(r||{v:1,state:'disabled',fields:[],rows:[]});}
  catch{label.textContent='Histórico indisponível · nenhuma leitura foi criada';}finally{pending=false;}
 }
 function schedule(){clearInterval(timer);if(!document.hidden&&!document.getElementById('panel-monitor').hidden){void load();timer=setInterval(()=>void load(),10000);}}
 select.addEventListener('change',()=>void load());document.addEventListener('visibilitychange',schedule);
 new MutationObserver(schedule).observe(document.getElementById('panel-monitor'),{attributes:true,attributeFilter:['hidden']});
 schedule();window.addEventListener('pagehide',()=>{request++;clearInterval(timer);});
})();
