'use strict';
// Main-process timer: independent of renderer throttling, chat and user replies.
// Never force exit. A failed cooperative exit is a failed test, not success.
function createDeadline({enabled=false,quit,closed,write,startedAt=null,now=()=>performance.now(),schedule=setTimeout,cancel=clearTimeout,exitAt=45000,limit=120000}){
 if(typeof enabled!=='boolean'||!Number.isFinite(exitAt)||!Number.isFinite(limit)||exitAt<1000||exitAt>=limit||limit>120000)throw Error('review_deadline_policy');
 let start=null,request=null,absolute=null,finished=false,requested=false;
 function record(code){write({v:1,code,elapsed_ms:now()-start,limit_ms:limit,forced:false});}
 return Object.freeze({start(){if(!enabled||start!==null)return;start=startedAt===null?now():startedAt;if(!Number.isFinite(start)||start>now())throw Error('review_start_clock');record('started');request=schedule(()=>{requested=true;record('cooperative_exit_requested');quit();},Math.max(0,exitAt-(now()-start)));absolute=schedule(()=>{if(!finished){record('deadline_exceeded');finished=true;}},Math.max(0,limit-(now()-start)));},complete(){if(start===null||finished)return;finished=true;cancel(request);cancel(absolute);record(closed()&&now()-start<=limit?'closed_within_deadline':'closure_not_verified');},state:()=>({enabled,requested,finished})});
}
module.exports={createDeadline};
