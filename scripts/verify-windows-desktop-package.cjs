'use strict';
// Offline resource inspection only; never executes the generated application.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),app=path.join(root,'apps/windows-ui');
const asar=require(path.join(app,'node_modules/@electron/asar'));
const bundle=path.resolve(process.argv[2]||path.join(root,'.cache/artifacts/windows/desktop-dev3/win-unpacked'));
const exe=path.join(bundle,'Lone Smart Room.exe'),archive=path.join(bundle,'resources/app.asar');
const hash=buffer=>crypto.createHash('sha256').update(buffer).digest('hex');
const files=['main.cjs','desktop-main.cjs','desktop-policy.cjs','desktop-window.cjs','desktop-preferences.cjs','preload.cjs','index.html','desktop.css','desktop.js','app-version.js','assets/brand/windows-icon.ico','assets/brand/windows-icon.svg','assets/brand/windows-icon.png','assets/brand/logo-horizontal.svg','assets/brand/logo-header-small.svg'];
for(const name of files)assert(asar.extractFile(archive,name.split('/').join(path.sep)).equals(fs.readFileSync(path.join(app,name))),name);
const pkg=JSON.parse(asar.extractFile(archive,'package.json'));
const sourcePackage=JSON.parse(fs.readFileSync(path.join(app,'package.json'),'utf8'));
assert.equal(pkg.version,'2.0.0-dev.4');assert.equal(pkg.name,'lone-smart-room');
// electron-builder strips its build configuration from packaged package.json.
assert.equal(sourcePackage.build.appId,'com.lone.smartroom');
const raw=fs.readFileSync(exe),u16=p=>raw.readUInt16LE(p),u32=p=>raw.readUInt32LE(p);
const pe=u32(0x3c);assert.equal(raw.subarray(pe,pe+4).toString('hex'),'50450000');
const sectionCount=u16(pe+6),optional=pe+24,dirs=optional+(u16(optional)===0x20b?112:96),resRva=u32(dirs+16),table=optional+u16(pe+20);
function offset(rva){for(let i=0;i<sectionCount;i++){const p=table+40*i,va=u32(p+12),length=Math.max(u32(p+8),u32(p+16));if(va<=rva&&rva<va+length)return u32(p+20)+rva-va;}throw Error('RVA outside sections');}
const base=offset(resRva);
function entries(rel){const p=base+rel,n=u16(p+12)+u16(p+14);return Array.from({length:n},(_,i)=>[u32(p+16+8*i),u32(p+20+8*i)]);}
function leaves(rel){return entries(rel).flatMap(([_key,value])=>{if(value&0x80000000)return leaves(value&0x7fffffff);const p=base+value,start=offset(u32(p));return [raw.subarray(start,start+u32(p+4))];});}
let icons=[],groups=[];for(const [kind,target]of entries(0)){if(kind===3)icons=leaves(target&0x7fffffff);if(kind===14)groups=leaves(target&0x7fffffff);}
const ico=fs.readFileSync(path.join(app,'assets/brand/windows-icon.ico')),count=ico.readUInt16LE(4);
for(let i=0;i<count;i++){const p=6+16*i,size=ico.readUInt32LE(p+8),start=ico.readUInt32LE(p+12),image=ico.subarray(start,start+size);assert(icons.some(icon=>icon.equals(image)),'Official ICO image missing from PE');}
assert(groups.length>0);
const result={ok:true,version:pkg.version,appIdFromBuildConfiguration:sourcePackage.build.appId,packagedName:pkg.name,resourcesVerified:files,exeSha256:hash(raw),asarSha256:hash(fs.readFileSync(archive)),peIconGroups:groups.length,peIconImages:icons.length,officialIconImagesMatched:count,generatedExecutableRun:false,installerExecuted:false};
const output=path.join(root,'.cache/validation/windows-tray-dev4/package-inspection.json');fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(`PASS: ${files.length} ASAR files, package identity and ${count} official PE icon images; executable not run.`);
