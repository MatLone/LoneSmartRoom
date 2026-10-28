'use strict';
// Metadata preview only. Fixed roots, bounded traversal, no delete/repair function.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
function createInspector({ownCache,userTemp=os.tmpdir(),systemTemp=path.join(process.env.SystemRoot||'C:\\Windows','Temp'),io=fs,now=Date.now}={}){
 const roots={own:ownCache,user_temp:userTemp,windows_temp:systemTemp};
 function inspect(scope){
  if(!Object.hasOwn(roots,scope)||!path.isAbsolute(roots[scope]||''))throw Error('inspection_scope');
  const root=path.resolve(roots[scope]),start=performance.now(),items=[];let visited=0,denied=0,excluded=0,bytes=0,truncated=false;
  function walk(directory,depth){
   if(visited>=2000||performance.now()-start>1000){truncated=true;return;}
   try{const st=io.lstatSync(directory);if(!st.isDirectory()||st.isSymbolicLink()){excluded++;return;}const names=io.readdirSync(directory);for(const name of names){if(++visited>2000||items.length>=250||performance.now()-start>1000){truncated=true;break;}const file=path.join(directory,name);try{const s=io.lstatSync(file);if(s.isSymbolicLink()||s.nlink!==1||/credential|token|secret|cert|password|crash|debug\.log|dump/i.test(name)){excluded++;continue;}if(s.isDirectory()){if(depth<2)walk(file,depth+1);continue;}if(!s.isFile()||now()-s.mtimeMs<7*86400000||!/\.(tmp|log|bak)$/i.test(name)){excluded++;continue;}items.push({name:path.relative(root,file).slice(0,200),bytes:s.size,modified_at:s.mtime.toISOString(),selected:false});bytes+=s.size;}catch{denied++;}}}catch{denied++;}
  }
  walk(root,0);return {v:1,source:'readonly_metadata_preview',state:denied&&!items.length?'unavailable':'preview',scope,items:items.sort((a,b)=>b.bytes-a.bytes),estimated_bytes:bytes,visited,excluded,denied,truncated,execution_enabled:false,limits:'250 candidates; 2000 entries; depth 2; 1 second; older than 7 days; tmp/log/bak only',not_included:['Personal documents','Protected diagnostics and backups','Active recent files','Recycle Bin','Installer packages requiring ownership verification']};
 }
 return Object.freeze({inspect});
}
module.exports={createInspector};
