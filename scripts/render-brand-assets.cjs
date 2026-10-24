// SVG rasterization only. Supply an already installed sharp module if needed.
// Does not install dependencies or interact with devices/native applications.
const fs=require('node:fs');
const path=require('node:path');
const sharp=process.argv[2]?require(path.resolve(process.argv[2])):require('sharp');
const root=path.resolve(__dirname,'..');
const input=path.join(root,'apps/android/app/src/main/assets/brand');
const output=path.join(root,'docs/design/brand/exports');
async function main(){
  fs.mkdirSync(output,{recursive:true});
  for(const [name,width] of [['logo-horizontal',1560],['logo-compact',960],['symbol',448],['app-icon',1024],['splash-screen',1080]]){
    await sharp(path.join(input,name+'.svg'),{density:288}).resize({width}).png().toFile(path.join(output,name+'.png'));
  }
  for(const size of [512,192])await sharp(path.join(input,'app-icon.svg'),{density:288}).resize(size,size).png().toFile(path.join(output,'app-icon-'+size+'.png'));
  for(const [name,width] of [['logo-horizontal',1560],['logo-compact',960]]){
    await sharp(path.join(input,name+'.svg'),{density:288}).resize({width}).flatten({background:'#080a0d'}).png().toFile(path.join(output,name+'-on-graphite.png'));
  }
  console.log('PASS: nine PNG exports rendered from SVG without network, fonts or device access.');
}
main().catch(error=>{console.error(error.message);process.exit(1);});
