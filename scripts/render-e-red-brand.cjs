// Existing sharp only. Source Windows icon remains byte-identical; no device/API calls.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const sharp=process.argv[2]?require(path.resolve(process.argv[2])):require('sharp');
const root=path.resolve(__dirname,'..'),brand=path.join(root,'apps/android/app/src/main/assets/brand');
const win=path.join(root,'apps/windows-ui/assets/brand'),res=path.join(root,'apps/android/app/src/main/res');
const docs=path.join(root,'docs/design/brand/e-red-windows-icon-2026-10-26'),out=path.join(docs,'exports');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const bg='#080a0d';
const mask=(n,shape)=>Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${n}" height="${n}" viewBox="0 0 100 100">${shape==='circle'?'<circle cx="50" cy="50" r="50" fill="white"/>':'<rect width="100" height="100" rx="25" fill="white"/>'}</svg>`);
async function foreground(scale){
 const layer=108*scale,tile=72*scale;
 // Uniform scaling and translation only. In the launcher's 72dp viewport this
 // is the original Windows tile, without a second inset tile or drawn outline.
 const input=await sharp(path.join(win,'windows-icon.png')).resize(tile,tile).png().toBuffer();
 return sharp({create:{width:layer,height:layer,channels:4,background:{r:0,g:0,b:0,alpha:0}}})
  .composite([{input,left:18*scale,top:18*scale}]).png().toBuffer();
}
async function splashForeground(){
 // Preserve the existing full-logo splash geometry; only E changes color.
 const legacy=fs.readFileSync(path.join(root,'docs/design/brand/official-board-2026-10-24/android-adaptive-foreground.svg'),'utf8');
 const old='M197 0 H242 L238 7 H190 Z M190 14 H234 V21 H197 V31 H239 V38 H197 L190 31 Z';
 if(legacy.split(`<path d="${old}"/>`).length!==2)throw Error('Expected original splash E');
 const source=legacy.replace(`<path d="${old}"/>`,`<path fill="#ff153f" d="${old}"/>`);
 const master=await sharp(Buffer.from(source),{density:288}).resize(1024,960).png().toBuffer();
 const {data,info}=await sharp(master).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 let x0=info.width,y0=info.height,x1=0,y1=0;
 for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]>=8){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
 const cx=(x0+x1)/2,cy=(y0+y1)/2;let radius=0;
 for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++)if(data[(y*info.width+x)*4+3]>=8)radius=Math.max(radius,Math.hypot(x-cx,y-cy)+.71);
 const factor=315/radius,input=await sharp(master).resize(Math.round(info.width*factor),Math.round(info.height*factor)).png().toBuffer();
 const composed=await sharp({create:{width:1080,height:1080,channels:4,background:{r:0,g:0,b:0,alpha:0}}})
  .composite([{input,left:Math.round(540-cx*factor),top:Math.round(540-cy*factor)}]).png().toBuffer();
 return sharp(composed).resize(432,432).png().toBuffer();
}
async function main(){
 fs.mkdirSync(out,{recursive:true});
 for(const [name,width]of [['logo-horizontal',1560],['logo-header-small',1440],['logo-compact',1024],['splash-screen',540]])
  await sharp(path.join(brand,name+'.svg'),{density:288}).resize({width}).png().toFile(path.join(out,name+'.png'));
 fs.copyFileSync(path.join(win,'windows-icon.png'),path.join(out,'windows-original.png'));
 fs.copyFileSync(path.join(win,'windows-icon.png'),path.join(out,'android-source-identical.png'));
 const adaptive=await foreground(10);
 await sharp(adaptive).toFile(path.join(out,'android-adaptive-foreground-1080.png'));
 const composed=await sharp({create:{width:1080,height:1080,channels:4,background:bg}}).composite([{input:adaptive}]).png().toBuffer();
 const viewport=await sharp(composed).extract({left:180,top:180,width:720,height:720}).png().toBuffer();
 for(const shape of ['circle','rounded'])for(const size of [48,56,72,512])
  await sharp(viewport).resize(size,size).composite([{input:mask(size,shape),blend:'dest-in'}]).png().toFile(path.join(out,`android-${shape}-${size}.png`));
 for(const [density,scale]of [['mdpi',1],['hdpi',1.5],['xhdpi',2],['xxhdpi',3],['xxxhdpi',4]]){
  const folder=path.join(res,'mipmap-'+density);fs.mkdirSync(folder,{recursive:true});
  await sharp(await foreground(scale)).toFile(path.join(folder,'ic_lone_foreground.png'));
  const n=48*scale;
  await sharp(path.join(win,'windows-icon.png')).resize(n,n).png().toFile(path.join(folder,'ic_launcher.png'));
  await sharp(path.join(win,'windows-icon.png')).resize(n,n).composite([{input:mask(n,'circle'),blend:'dest-in'}]).png().toFile(path.join(folder,'ic_launcher_round.png'));
 }
 await sharp(await splashForeground()).toFile(path.join(res,'drawable-nodpi/lone_splash_safe.png'));
 await sharp(path.join(brand,'logo-compact.svg'),{density:288}).resize(512,480).png().toFile(path.join(res,'drawable-nodpi/lone_splash_lockup.png'));
 const before=JSON.parse(fs.readFileSync(path.join(docs,'reference/before-sha256.json'),'utf8'));
 const changes={};for(const [rel,digest]of Object.entries(before)){const after=hash(path.join(root,rel));if(after!==digest)changes[rel]={before:digest,after};}
 fs.writeFileSync(path.join(docs,'change-manifest.json'),JSON.stringify({checkpoint:'098d1a2',officialRed:'#ff153f',
  windowsIconSource:'apps/windows-ui/assets/brand/windows-icon.png',windowsIconSha256:hash(path.join(win,'windows-icon.png')),
  windowsIconUnchanged:true,uniformIconScaleOnly:true,adaptiveLayerDp:108,originalTileViewportDp:72,criticalSymbolSafeDiameterDp:66,
  originalFrameMayBeClippedByLauncherMask:true,androidInstalled:false,apkBuilt:false,authorizedChanges:changes},null,2)+'\n');
 console.log('PASS: Windows source copied; five Android densities, masks, and E-red native splash exported; no devices or builds.');
}
main().catch(e=>{console.error(e.message);process.exit(1);});
