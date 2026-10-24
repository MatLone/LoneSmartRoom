// Deterministic Android resource packaging from the preserved NEX cutout.
// Requires an existing sharp installation; never installs tools or accesses devices.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const sharp=process.argv[2]?require(path.resolve(process.argv[2])):require('sharp');
const root=path.resolve(__dirname,'..');
const brand=path.join(root,'docs/design/brand');
const master=path.join(brand,'nex-icon/foreground-master.png');
const reference=path.join(brand,'nex-hexagon-icon.png');
const res=path.join(root,'apps/android/app/src/main/res');
const out=path.join(brand,'nex-icon');
const background='#080a0d';
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function png(buffer,file){fs.mkdirSync(path.dirname(file),{recursive:true});await sharp(buffer).png().toFile(file);}
async function main(){
  const {data,info}=await sharp(master).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  let x0=info.width,y0=info.height,x1=0,y1=0;
  for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]>=8){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
  if(x1<=x0||y1<=y0)throw Error('Transparent or invalid foreground');
  const cx=(x0+x1)/2,cy=(y0+y1)/2;
  let radius=0;
  for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++)if(data[(y*info.width+x)*4+3]>=8)radius=Math.max(radius,Math.hypot(x-cx,y-cy)+0.71);
  const foreground=async(scale)=>{
    const factor=31.5*scale/radius;
    const w=Math.round(info.width*factor),h=Math.round(info.height*factor),size=Math.round(108*scale);
    const image=await sharp(master).resize(w,h).png().toBuffer();
    return sharp({create:{width:size,height:size,channels:4,background:{r:0,g:0,b:0,alpha:0}}})
      .composite([{input:image,left:Math.round(size/2-cx*factor),top:Math.round(size/2-cy*factor)}]).png().toBuffer();
  };
  const mask=(size,shape)=>Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 100 100">${shape==='circle'?'<circle cx="50" cy="50" r="50" fill="white"/>':'<rect width="100" height="100" rx="25" fill="white"/>'}</svg>`);
  const adaptive=await foreground(10);
  const composed=await sharp({create:{width:1080,height:1080,channels:4,background}})
    .composite([{input:adaptive}]).png().toBuffer();
  const tile=await sharp(composed).extract({left:180,top:180,width:720,height:720}).png().toBuffer();
  await png(adaptive,path.join(out,'adaptive-foreground-1080.png'));
  await png(tile,path.join(out,'unmasked-tile-720.png'));
  const masked=async(size,shape)=>sharp(tile).resize(size,size).composite([{input:mask(size,shape),blend:'dest-in'}]).png().toBuffer();
  for(const [density,scale]of [['mdpi',1],['hdpi',1.5],['xhdpi',2],['xxhdpi',3],['xxxhdpi',4]]){
    const dir=path.join(res,'mipmap-'+density);fs.mkdirSync(dir,{recursive:true});
    await png(await foreground(scale),path.join(dir,'ic_nex_foreground.png'));
    await png(await masked(Math.round(48*scale),'rounded'),path.join(dir,'ic_launcher.png'));
    await png(await masked(Math.round(48*scale),'circle'),path.join(dir,'ic_launcher_round.png'));
  }
  for(const shape of ['circle','rounded'])for(const size of [48,56,72,96,512])await png(await masked(size,shape),path.join(out,`${shape}-${size}.png`));
  const web=path.join(root,'apps/android/app/src/main/assets/brand/nex-app-icon.png');
  await png(await masked(512,'rounded'),web);
  const resourceFiles=[];
  for(const name of fs.readdirSync(res).filter(n=>n.startsWith('mipmap-')))
    for(const file of fs.readdirSync(path.join(res,name)))if(file.endsWith('.png')){
      const absolute=path.join(res,name,file);resourceFiles.push({path:path.relative(root,absolute).split(path.sep).join('/'),sha256:hash(absolute)});
    }
  const record={referenceSha256:hash(reference),foregroundMasterSha256:hash(master),
    method:'imagegen cutout from approved source, followed by deterministic resize/composition only',
    background,layerDp:108,visibleViewportDp:72,safeZoneDiameterDp:66,
    designContentDiameterDp:63,alphaThresholdForSafeArea:8,
    masterAnchor:{x:cx,y:cy,visibleRadius:radius},outerRoundedFrameIncluded:false,
    monochromeLayerProvided:false,originalHeaderAndVectorsUnchanged:true,resources:resourceFiles,webIconSha256:hash(web)};
  fs.writeFileSync(path.join(out,'icon-manifest.json'),JSON.stringify(record,null,2)+'\n');
  console.log('PASS: five density sets, adaptive foreground and mask previews generated; no device or runtime operations.');
}
main().catch(e=>{console.error(e.message);process.exit(1);});
