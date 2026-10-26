'use strict';
// Executable specification for MOCK REHEARSAL ONLY. No timers, UI or process API.
// This is not installed, imported or used by Electron or any operational launcher.
class SessionPolicy {
  constructor(launchedMonotonicSeconds){
    if(!Number.isFinite(launchedMonotonicSeconds)||launchedMonotonicSeconds<0)throw Error('invalid_clock');
    this.started=launchedMonotonicSeconds;this.last=this.started;this.exitRequested=false;
  }
  decide(now,operationBudgetSeconds=0){
    if(!Number.isFinite(now)||now<this.last||!Number.isFinite(operationBudgetSeconds)||operationBudgetSeconds<0)throw Error('invalid_clock_or_budget');
    this.last=now;const elapsed=now-this.started;
    if(elapsed>=120)return {phase:'expired',newChecks:false,requestNormalExit:!this.exitRequested,force:false,passed:false};
    if(this.exitRequested||elapsed>=45||elapsed+operationBudgetSeconds>=45)return {phase:'exit_only',newChecks:false,requestNormalExit:!this.exitRequested,force:false};
    return {phase:'checks',newChecks:true,requestNormalExit:false,force:false};
  }
  requestExit(){const first=!this.exitRequested;this.exitRequested=true;return first;}
  finish(evidence){
    // A late confirmation cannot retrospectively turn an overrun into success.
    const elapsed=evidence?.confirmedMonotonicSeconds-this.started;
    return this.exitRequested&&Number.isFinite(elapsed)&&elapsed>=0&&elapsed<120&&
      evidence.ownedProcesses===0&&evidence.ownedPipes===0&&evidence.normalExit===true&&evidence.checksComplete===true;
  }
}
module.exports={SessionPolicy};
