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
    assert(visible>0&&red>0&&bright>0,'Red angular symbol and white LONE lettering must survive scaling');
    assert(maxRadius<=33,'Visible foreground must fit the conservative 66dp safe circle');
    assert.equal(data[3],0,'Foreground corners must be transparent, without a baked tile');
    measurements.push({density,visiblePixels:visible,maxVisibleRadiusDp:maxRadius,redPixels:red,brightPixels:bright});checked++;
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
  console.log(JSON.stringify({ok:true,checkedImageAndVectorFiles:checked,measurements,officialVectorsVerified:true,
    actualSamsungTested:false,alphaThreshold:8,realDeviceOperations:0},null,2));
}
main().catch(error=>{console.error(error.message);process.exit(1);});
