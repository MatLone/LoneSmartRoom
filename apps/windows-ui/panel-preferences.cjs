'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
function createPanelStore(directory,validBounds){
 const file=directory&&path.join(directory,'panel-bounds-v1.json');let data={v:1},readonly=false;
 const safe=()=>{let current=path.parse(directory).root;for(const part of path.relative(current,directory).split(path.sep)){current=path.join(current,part);if(fs.existsSync(current)){const st=fs.lstatSync(current);if(st.isSymbolicLink()||!st.isDirectory())throw Error();}else fs.mkdirSync(current);}if(fs.existsSync(file)){const st=fs.lstatSync(file);if(!st.isFile()||st.isSymbolicLink()||st.nlink!==1||st.size>4096)throw Error();}};
 if(file)try{safe();if(fs.existsSync(file)){const value=JSON.parse(fs.readFileSync(file,'utf8'));if(value.v!==1||Object.keys(value).some(k=>!['v','touch','overlay'].includes(k)))throw Error();for(const role of ['touch','overlay'])if(value[role]&&!validBounds(value[role]))throw Error();data=value;}}catch{readonly=true;}
 return {get:role=>data[role]&&{...data[role]},save(role,bounds){if(!file||readonly||!['touch','overlay'].includes(role)||!validBounds(bounds))return false;let temp,created=false;try{safe();data[role]={x:bounds.x,y:bounds.y,width:bounds.width,height:bounds.height};temp=file+'.'+crypto.randomBytes(8).toString('hex')+'.tmp';fs.writeFileSync(temp,JSON.stringify(data),{flag:'wx',mode:0o600});created=true;fs.renameSync(temp,file);created=false;return true;}catch{return false;}finally{if(created&&temp&&fs.existsSync(temp))fs.unlinkSync(temp);}}};
}
module.exports={createPanelStore};
