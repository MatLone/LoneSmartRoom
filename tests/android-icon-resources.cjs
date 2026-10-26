// Validate actual packaged-source pixels and density geometry, not a mock launcher.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const sharp=process.argv[2]?require(path.resolve(process.argv[2])):require('sharp');
const root=path.resolve(__dirname,'..');
const res=path.join(root,'apps/android/app/src/main/res');
async function main(){
  let checked=0;
  const manifest=fs.readFileSync(path.join(root,'apps/android/app/src/main/AndroidManifest.xml'),'utf8');
  assert(manifest.includes('android:icon="@mipmap/ic_launcher"'));
  assert(manifest.includes('android:roundIcon="@mipmap/ic_launcher_round"'));
  assert(manifest.includes('android:label="Lone Smart Room"'));
  assert(manifest.includes('android:usesCleartextTraffic="false"'));
  for(const name of ['ic_launcher','ic_launcher_round']){
    const xml=fs.readFileSync(path.join(res,'mipmap-anydpi-v26',name+'.xml'),'utf8');
    assert(xml.includes('<adaptive-icon'));
    assert(xml.includes('@mipmap/ic_lone_foreground'));
    assert(xml.includes('@color/ic_lone_background'));
    assert(!xml.includes('@drawable/ic_launcher'));
  }
  const measurements=[];
  for(const [density,scale]of [['mdpi',1],['hdpi',1.5],['xhdpi',2],['xxhdpi',3],['xxxhdpi',4]]){
    const file=path.join(res,'mipmap-'+density,'ic_lone_foreground.png');
    const {data,info}=await sharp(file).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    assert.equal(info.width,108*scale);assert.equal(info.height,108*scale);
    let visible=0,maxRadius=0,red=0,bright=0;
    for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++){
      const n=(y*info.width+x)*4;
      if(data[n+3]<8)continue;
      visible++;maxRadius=Math.max(maxRadius,Math.hypot(x+.5-info.width/2,y+.5-info.height/2)/scale);
      if(data[n]>150&&data[n]>data[n+1]*1.5)red++;
      if(data[n]>210&&data[n+1]>180&&data[n+2]>150)bright++;
    }
    assert(visible>0&&red>0&&bright===0,'Exact Windows symbol-only icon; no white LONE lettering');
    // The original Windows tile/frame may extend into the maskable area.
    // Critical symbol safety and exact source pixels are checked independently.
    const source=fs.readFileSync(path.join(root,'apps/windows-ui/assets/brand/windows-icon.svg'),'utf8').replace(/<rect[^>]*\/>/,'');
    const critical=await sharp(Buffer.from(source),{density:288}).resize(72*scale,72*scale).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    let criticalRadius=0;
    for(let y=0;y<critical.info.height;y++)for(let x=0;x<critical.info.width;x++)if(critical.data[(y*critical.info.width+x)*4+3]>=8)
      criticalRadius=Math.max(criticalRadius,Math.hypot(x+.5-critical.info.width/2,y+.5-critical.info.height/2)/scale);
    assert(criticalRadius<=33,'Unmodified Windows critical symbol must fit the conservative 66dp safe circle');
    assert.equal(data[3],0,'Foreground corners must be transparent, without a baked tile');
    measurements.push({density,visiblePixels:visible,maxVisibleRadiusDp:maxRadius,criticalSymbolRadiusDp:criticalRadius,redPixels:red,brightPixels:bright});checked++;
    const expected=await sharp(path.join(root,'apps/windows-ui/assets/brand/windows-icon.png')).resize(48*scale,48*scale).ensureAlpha().raw().toBuffer();
    const actual=await sharp(path.join(res,'mipmap-'+density,'ic_launcher.png')).ensureAlpha().raw().toBuffer();
    assert.deepEqual(actual,expected,'Legacy Android launcher is a direct resize of Windows original');checked++;
    for(const name of ['ic_launcher','ic_launcher_round']){
      const m=await sharp(path.join(res,'mipmap-'+density,name+'.png')).metadata();
      assert.equal(m.width,48*scale);assert.equal(m.height,48*scale);checked++;
    }
  }
  const original=JSON.parse(fs.readFileSync(path.join(root,'apps/android/app/src/main/assets/brand/brand-manifest.json')));
  for(const [name,hash]of Object.entries(original.svgSha256)){
    const bytes=fs.readFileSync(path.join(root,'apps/android/app/src/main/assets/brand',name));
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),hash);checked++;
  }
  const review=path.join(root,'docs/design/brand/e-red-windows-icon-2026-10-26');
  const before=JSON.parse(fs.readFileSync(path.join(review,'reference/before-sha256.json'),'utf8'));
  const splashDeltas=[];
  for(const name of ['lone_splash_safe.png','lone_splash_lockup.png']){
    const originalFile=path.join(review,'reference',name),relative='apps/android/app/src/main/res/drawable-nodpi/'+name;
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(originalFile)).digest('hex'),before[relative]);
    const a=await sharp(originalFile).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    const b=await sharp(path.join(root,relative)).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    assert.equal(a.info.width,b.info.width);assert.equal(a.info.height,b.info.height);
    let changed=0,x0=a.info.width,y0=a.info.height,x1=0,y1=0;
    for(let y=0;y<a.info.height;y++)for(let x=0;x<a.info.width;x++){
      const k=(y*a.info.width+x)*4;
      assert.equal(a.data[k+3],b.data[k+3],'Splash alpha/shape must remain identical');
      if(a.data[k]!==b.data[k]||a.data[k+1]!==b.data[k+1]||a.data[k+2]!==b.data[k+2]){
        changed++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);
      }
    }
    assert(changed>0);
    if(name==='lone_splash_lockup.png'){
      // Original E contours: x=190..242, y=0..38, word translate(7,157), scale 2.
      assert(x0>=392&&x1<=500&&y0>=312&&y1<=392,'Only the original E bounds may change');
    }else{
      assert(x0>a.info.width*.6&&y0>a.info.height*.55&&(x1-x0)<a.info.width*.15&&(y1-y0)<a.info.height*.12,'Safe splash changes confined to E at lower-right of original word');
    }
    splashDeltas.push({name,changedPixels:changed,alphaDifferences:0,changedBounds:[x0,y0,x1,y1]});checked++;
  }
  console.log(JSON.stringify({ok:true,checkedImageAndVectorFiles:checked,measurements,splashDeltas,officialVectorsVerified:true,
    actualSamsungTested:false,alphaThreshold:8,realDeviceOperations:0},null,2));
}
main().catch(error=>{console.error(error.message);process.exit(1);});
