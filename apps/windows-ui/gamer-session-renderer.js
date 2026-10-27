'use strict';
((root)=>{
 function render(target,report){
  if(!target||!report||report.v!==1||report.game!=='cs2'||report.simulation!==true&&report.source!=='not_connected')throw Error('invalid_game_view');
  const title=document.createElement('h2');title.textContent='Sessão de jogo · desempenho';
  const note=document.createElement('p');note.className='game-session-note';note.textContent=report.simulation?'SIMULAÇÃO · frames de teste, sem jogo ou captura real':'FPS e frametime indisponíveis · fonte de captura ainda não integrada. Nenhum jogo foi iniciado.';
  const grid=document.createElement('div');grid.className='game-session-values';
  for(const [key,label,unit]of [['fps','FPS atual','FPS'],['frametime_ms','Frametime','ms'],['average_fps','FPS médio','FPS'],['one_percent_low_fps','1% Low','FPS']]){
   const article=document.createElement('article'),heading=document.createElement('h3'),value=document.createElement('strong');heading.textContent=label;
   const n=report[key];if(n!==null&&(typeof n!=='number'||!Number.isFinite(n)||n<0))throw Error('invalid_game_metric');
   value.textContent=n===null?'Indisponível':n.toLocaleString('pt-BR',{maximumFractionDigits:1})+' '+unit;article.append(heading,value);grid.append(article);
  }
  const method=document.createElement('p');method.className='fine-print';method.textContent='1% Low: inverso da média dos frametimes mais lentos (1%, arredondado para cima), após pelo menos 100 frames. Sem overlay, hooks ou captura ativa.';
  target.replaceChildren(title,note,grid,method);target.dataset.simulation=String(report.simulation);
 }
 root.loneGameSessionView=Object.freeze({render});
 const target=document.getElementById('gameSession');if(target&&root.loneGameSessions)render(target,root.loneGameSessions.unavailable());
})(globalThis);
