// Rasterize only the new header variant; never rewrite the original exports.
const fs=require('node:fs');
const path=require('node:path');
const sharp=process.argv[2]?require(path.resolve(process.argv[2])):require('sharp');
const root=path.resolve(__dirname,'..');
const output=path.join(root,'docs/design/brand/exports/logo-header-small.png');
fs.mkdirSync(path.dirname(output),{recursive:true});
sharp(path.join(root,'apps/android/app/src/main/assets/brand/logo-header-small.svg'),{density:288})
  .resize({width:1560}).png().toFile(output)
  .then(()=>console.log('PASS: new header PNG exported; original artwork unchanged.'))
  .catch(error=>{console.error(error.message);process.exit(1);});
