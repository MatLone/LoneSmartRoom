'use strict';
const fs=require('node:fs'),path=require('node:path');
function inventory(root){const list=[];function walk(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isSymbolicLink())throw Error('package_symlink');if(e.isDirectory())walk(p);else list.push(path.relative(root,p).replaceAll('\\','/'));}}walk(root);return list;}
async function afterPack(context){
 const previous=fs.readFileSync(path.join(__dirname,'previous-dev8-files.txt'),'utf8').trim().split(/\r?\n/);
 const known=[...new Set([...previous,...inventory(context.appOutDir),'uninstallerIcon.ico','Uninstall Lone Smart Room.exe'])].sort();
 if(known.includes('debug.log')||known.length>512||known.some(n=>!/^[-a-zA-Z0-9_ ./]+$/.test(n)||n.includes('..')||path.isAbsolute(n)))throw Error('unsafe_package_inventory');
 fs.writeFileSync(path.join(__dirname,'package-files.txt'),known.join('\n')+'\n');
 const deletes=known.map(n=>'  Delete "$INSTDIR\\'+n.replaceAll('/','\\')+'"').join('\n');
 fs.writeFileSync(path.join(__dirname,'package-remove.nsh'),'!macro customRemoveFiles\n'+deletes+'\n!macroend\n');
}
module.exports={afterPack,inventory};
