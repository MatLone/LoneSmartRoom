// Deterministic exports and native resources. Requires existing sharp only.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const sharp=process.argv[2]?require(path.resolve(process.argv[2])):require('sharp');
const root=path.resolve(__dirname,'..'),brand=path.join(root,'apps/android/app/src/main/assets/brand');
const docs=path.join(root,'docs/design/brand/official-board-2026-10-24');
const out=path.join(docs,'exports'),res=path.join(root,'apps/android/app/src/main/res');
const bg='#080a0d';
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const write=(rel,content)=>{const p=path.join(res,rel);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,content);};
const mask=(n,shape)=>Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${n}" height="${n}" viewBox="0 0 100 100">${shape==='circle'?'<circle cx="50" cy="50" r="50" fill="white"/>':'<rect width="100" height="100" rx="25" fill="white"/>'}</svg>`);
async function main(){
 fs.mkdirSync(out,{recursive:true});
 for(const [name,width]of [['logo-horizontal',1560],['logo-header-small',1440],['logo-compact',1024],['symbol',928],['app-icon',1024],['splash-screen',1080]])
  await sharp(path.join(brand,name+'.svg'),{density:288}).resize({width}).png().toFile(path.join(out,name+'.png'));
 await sharp(path.join(docs,'windows-icon.svg'),{density:288}).resize(1024,1024).png().toFile(path.join(out,'windows-icon.png'));
 const master=await sharp(path.join(docs,'android-adaptive-foreground.svg'),{density:288}).resize(1024,960).png().toBuffer();
 const {data,info}=await sharp(master).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 let x0=info.width,y0=info.height,x1=0,y1=0;
 for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]>=8){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
 const cx=(x0+x1)/2,cy=(y0+y1)/2;let radius=0;
 for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++)if(data[(y*info.width+x)*4+3]>=8)radius=Math.max(radius,Math.hypot(x-cx,y-cy)+.71);
 const foreground=async scale=>{
  const factor=31.5*scale/radius,size=Math.round(108*scale);
  const input=await sharp(master).resize(Math.round(info.width*factor),Math.round(info.height*factor)).png().toBuffer();
  return sharp({create:{width:size,height:size,channels:4,background:{r:0,g:0,b:0,alpha:0}}})
   .composite([{input,left:Math.round(size/2-cx*factor),top:Math.round(size/2-cy*factor)}]).png().toBuffer();
 };
 const adaptive=await foreground(10);
 await sharp(adaptive).toFile(path.join(out,'adaptive-foreground-1080.png'));
 const composed=await sharp({create:{width:1080,height:1080,channels:4,background:bg}}).composite([{input:adaptive}]).png().toBuffer();
 const tile=await sharp(composed).extract({left:180,top:180,width:720,height:720}).png().toBuffer();
 for(const shape of ['circle','rounded'])for(const size of [48,56,72,96,512])
  await sharp(tile).resize(size,size).composite([{input:mask(size,shape),blend:'dest-in'}]).png().toFile(path.join(out,`${shape}-${size}.png`));
 for(const [density,scale]of [['mdpi',1],['hdpi',1.5],['xhdpi',2],['xxhdpi',3],['xxxhdpi',4]]){
  const dir=path.join(res,'mipmap-'+density);fs.mkdirSync(dir,{recursive:true});
  await sharp(await foreground(scale)).toFile(path.join(dir,'ic_lone_foreground.png'));
  for(const name of ['ic_launcher','ic_launcher_round']){
   const size=Math.round(48*scale),shape=name.endsWith('_round')?'circle':'rounded';
   const image=shape==='rounded'?sharp(path.join(brand,'app-icon.svg'),{density:288}):sharp(tile);
   await image.resize(size,size).composite([{input:mask(size,shape),blend:'dest-in'}]).png().toFile(path.join(dir,name+'.png'));
  }
  // Superseded source resources are recoverable in Git and archived brand masters.
  const old=path.join(dir,'ic_nex_foreground.png');if(fs.existsSync(old))fs.unlinkSync(old);
 }
 const xml=`<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n    <background android:drawable="@color/ic_lone_background" />\n    <foreground android:drawable="@mipmap/ic_lone_foreground" />\n</adaptive-icon>\n`;
 for(const name of ['ic_launcher','ic_launcher_round'])write('mipmap-anydpi-v26/'+name+'.xml',xml);
 write('values/lone_brand.xml','<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_lone_background">#080a0d</color>\n</resources>\n');
 const oldColor=path.join(res,'values/nex_icon.xml');if(fs.existsSync(oldColor))fs.unlinkSync(oldColor);
 // Android 12+ uses its system-controlled splash layout, with safe inset artwork.
 fs.mkdirSync(path.join(res,'drawable-nodpi'),{recursive:true});
 await sharp(adaptive).resize(432,432).png().toFile(path.join(res,'drawable-nodpi/lone_splash_safe.png'));
 await sharp(path.join(brand,'logo-compact.svg'),{density:288}).resize(512,480).png().toFile(path.join(res,'drawable-nodpi/lone_splash_lockup.png'));
 write('drawable/lone_launch_background.xml',`<?xml version="1.0" encoding="utf-8"?>\n<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n    <item android:drawable="@color/ic_lone_background" />\n    <item android:width="192dp" android:height="180dp" android:gravity="center">\n        <bitmap android:src="@drawable/lone_splash_lockup" android:gravity="fill" />\n    </item>\n</layer-list>\n`);
 await sharp(path.join(brand,'app-icon.svg'),{density:288}).resize(512,512).png().toFile(path.join(brand,'lone-app-icon.png'));
 const oldWeb=path.join(brand,'nex-app-icon.png');if(fs.existsSync(oldWeb))fs.unlinkSync(oldWeb);
 const files=[];
 for(const folder of fs.readdirSync(res).filter(n=>n.startsWith('mipmap-')))
  for(const name of fs.readdirSync(path.join(res,folder)))if(/^(ic_launcher(?:_round)?|ic_lone_foreground)\.(png|xml)$/.test(name)){
   const p=path.join(res,folder,name);files.push({path:path.relative(root,p).split(path.sep).join('/'),sha256:hash(p)});
  }
 fs.writeFileSync(path.join(docs,'resource-manifest.json'),JSON.stringify({referenceSha256:hash(path.join(docs,'reference/approved-board.png')),
  method:'vector recreation and deterministic rasterization; no image generation',background:bg,layerDp:108,safeZoneDiameterDp:66,
  designContentDiameterDp:63,alphaThreshold:8,foregroundHasFixedFrame:false,androidInstalled:false,resources:files},null,2)+'\n');
 console.log('PASS: official brand exports, 5 density sets, adaptive layers and native splash artwork generated; no device access.');
}
main().catch(e=>{console.error(e.message);process.exit(1);});
