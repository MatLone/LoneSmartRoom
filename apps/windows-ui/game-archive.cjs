'use strict';
// Summaries of user-imported PresentMon CSV only. No capture, launch or game hooks.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
function validateReport(value){
 if(!value||value.v!==1||value.source!=='presentmon_csv_import'||value.live!==false||value.simulation!==false||!Array.isArray(value.streams)||value.streams.length>32||!Number.isSafeInteger(value.rejected)||value.rejected<0)throw Error('archive_report');
 for(const s of value.streams){if(typeof s.name!=='string'||s.name.length>120||!Number.isSafeInteger(s.samples)||s.samples<1||s.samples>120000||!Array.isArray(s.points)||s.points.length>120||s.points.some(n=>!Number.isFinite(n)||n<=0||n>60000)||['average_fps','mean_frametime_ms'].some(k=>!Number.isFinite(s[k])||s[k]<=0)||s.one_percent_low_fps!==null&&(!Number.isFinite(s.one_percent_low_fps)||s.one_percent_low_fps<=0))throw Error('archive_metric');}
 return value;
}
function createArchive(directory){
 const file=path.join(directory,'game-sessions-v1.json');let entries=[],error=null,readonly=false;
 function safe(){let current=path.parse(directory).root;for(const part of path.relative(current,directory).split(path.sep)){current=path.join(current,part);if(fs.existsSync(current)){const s=fs.lstatSync(current);if(!s.isDirectory()||s.isSymbolicLink())throw Error();}else fs.mkdirSync(current);}if(fs.existsSync(file)){const s=fs.lstatSync(file);if(!s.isFile()||s.isSymbolicLink()||s.nlink!==1||s.size>1048576)throw Error();}}
 try{safe();if(fs.existsSync(file)){const v=JSON.parse(fs.readFileSync(file,'utf8'));if(v.v!==1||!Array.isArray(v.entries)||v.entries.length>20)throw Error();for(const e of v.entries){if(!/^[a-f0-9]{32}$/.test(e.id)||!Number.isFinite(Date.parse(e.imported_at)))throw Error();validateReport(e.report);}entries=v.entries;}}catch{error='archive_rejected_preserved';readonly=true;}
 return Object.freeze({list:()=>({v:1,source:'user_imported_csv',live:false,error,entries:structuredClone(entries)}),add(report){if(readonly)throw Error('archive_readonly');validateReport(report);const entry={id:crypto.randomBytes(16).toString('hex'),imported_at:new Date().toISOString(),report:structuredClone(report)};const next=[...entries,entry].slice(-20);while(Buffer.byteLength(JSON.stringify({v:1,entries:next}))>1048576&&next.length>1)next.shift();safe();const temp=file+'.'+crypto.randomBytes(8).toString('hex')+'.tmp';let created=false;try{fs.writeFileSync(temp,JSON.stringify({v:1,entries:next}),{flag:'wx',mode:0o600});created=true;fs.renameSync(temp,file);created=false;entries=next;return {...entry.report,archive_id:entry.id};}finally{if(created&&fs.existsSync(temp))fs.unlinkSync(temp);}}});
}
module.exports={createArchive,validateReport};
