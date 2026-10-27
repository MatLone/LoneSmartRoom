'use strict';
// Development composition only; original approved monitoring host stays unchanged.
const path=require('node:path'),runtime=require('./monitoring-runtime.cjs');
const {createMonitoringHost}=require('./monitoring-host.cjs');
function createTelemetryDevelopmentHost(options){
 if(options.packaged||options.resolveLayout)throw Error('telemetry_development_only');
 return createMonitoringHost({...options,resolveLayout:()=>({...runtime.sourceLayout(options.root),
  script:path.join(options.root,'scripts/monitoring-telemetry-client.py')})});
}
module.exports={createTelemetryDevelopmentHost};
