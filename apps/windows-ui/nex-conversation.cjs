'use strict';
// Bounded app-local conversation only. Corrupt/foreign files are preserved.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
function createConversation(directory){
 if(typeof directory!=='string'||!path.isAbsolute(directory))throw Error('conversation_directory');
 const file=path.join(directory,'nex-conversation-v1.json');let entries=[],error=null,expectedHash=null;
 const digest=data=>crypto.createHash('sha256').update(data).digest('hex');
 function safe(){
  let cursor=path.parse(directory).root;
  for(const part of path.relative(cursor,directory).split(path.sep)){
   cursor=path.join(cursor,part);const stat=fs.lstatSync(cursor);
   if(!stat.isDirectory()||stat.isSymbolicLink())throw Error('conversation_directory');
  }
  if(fs.existsSync(file)){const s=fs.lstatSync(file);if(!s.isFile()||s.isSymbolicLink()||s.nlink!==1||s.size>65536)throw Error('conversation_file');}
 }
 function valid(value){
  if(!value||Object.keys(value).sort().join(',')!=='entries,v'||value.v!==1||!Array.isArray(value.entries)||value.entries.length>40)throw Error('conversation_contract');
  for(const r of value.entries)if(!r||Object.keys(r).sort().join(',')!=='at,role,text'||!['user','nex'].includes(r.role)||typeof r.text!=='string'||r.text.length>1800||typeof r.at!=='string'||!Number.isFinite(Date.parse(r.at)))throw Error('conversation_entry');
  if(Buffer.byteLength(JSON.stringify(value))>65536)throw Error('conversation_size');
  return value.entries;
 }
 try{safe();if(fs.existsSync(file)){const data=fs.readFileSync(file);entries=valid(JSON.parse(data.toString('utf8')));expectedHash=digest(data);}}catch{error='conversation_rejected_preserved';}
 return Object.freeze({view:()=>({entries:structuredClone(entries),error,persisted:!error}),append(user,reply,at){
  if(error)return false;
  const next=[...entries,{at,role:'user',text:user},{at,role:'nex',text:reply}].slice(-40);
  while(Buffer.byteLength(JSON.stringify({v:1,entries:next}))>65536&&next.length>2)next.splice(0,2);
  const temporary=file+'.'+crypto.randomBytes(8).toString('hex')+'.tmp';let owned=false;
  try{valid({v:1,entries:next});safe();if((fs.existsSync(file)?digest(fs.readFileSync(file)):null)!==expectedHash){error='conversation_changed_preserved';return false;}
   const data=JSON.stringify({v:1,entries:next});fs.writeFileSync(temporary,data,{flag:'wx',mode:0o600});owned=true;fs.renameSync(temporary,file);owned=false;entries=next;expectedHash=digest(data);return true;}
  catch{error='conversation_write_failed';return false;}
  finally{if(owned)fs.unlinkSync(temporary);}
 }});
}
module.exports={createConversation};
