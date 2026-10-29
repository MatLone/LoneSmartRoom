'use strict';
// Independent protocol implementation, OpenRGB SDK v3. Fixed loopback only.
// No detection, resizing, segments, profile persistence, firmware or bus APIs.
const net=require('node:net'),crypto=require('node:crypto');
const LIMIT=262144,MAX_LEDS=4096;
const FLAGS=Object.freeze({BRIGHTNESS:16,PER_LED:32,MODE_COLOR:64,AUTOMATIC_SAVE:512});
const fail=code=>{throw Error(code);};
const u32=n=>{const b=Buffer.alloc(4);b.writeUInt32LE(n);return b;};
function frame(id,device=0,data=Buffer.alloc(0)){
 if(![0,1,40,1050,1051,1101].includes(id)||!Number.isInteger(device)||device<0||device>31||!Buffer.isBuffer(data)||data.length>LIMIT)fail('rgb_packet');
 const b=Buffer.alloc(16+data.length);b.write('ORGB');b.writeUInt32LE(device,4);b.writeUInt32LE(id,8);b.writeUInt32LE(data.length,12);data.copy(b,16);return b;
}
function parseDevice(data,{diagnostic=()=>{}}={}){
 let offset=0;
 const take=n=>{if(!Number.isSafeInteger(n)||n<0||offset+n>data.length)fail('rgb_truncated');const p=data.subarray(offset,offset+n);offset+=n;return p;};
 const n16=()=>take(2).readUInt16LE(),n32=()=>take(4).readUInt32LE();
 const text=()=>{const n=n16();if(n<1||n>1024)fail('rgb_string_limit');const b=take(n);if(b[n-1]!==0)fail('rgb_string_termination');const s=new TextDecoder('utf-8',{fatal:true}).decode(b.subarray(0,n-1));if(/[\x00-\x1f\x7f]/.test(s))fail('rgb_text');return s;};
 const colors=()=>{const n=n16();if(n>MAX_LEDS)fail('rgb_led_limit');return Array.from({length:n},()=>{const c=take(4);if(c[3]!==0)fail('rgb_color_padding');return '#'+c.subarray(0,3).toString('hex').toUpperCase();});};
 if(data.length>LIMIT||n32()!==data.length)fail('rgb_descriptor_size');
 const type=n32(),name=text(),vendor=text(),description=text(),version=text(),serial=text(),location=text(),count=n16(),activeMode=n32();
 if(count>128||activeMode>=count)fail('rgb_modes');
 const modes=Array.from({length:count},(_,id)=>{const name=text(),value=n32(),flags=n32(),speedMin=n32(),speedMax=n32(),brightnessMin=n32(),brightnessMax=n32(),colorsMin=n32(),colorsMax=n32(),speed=n32(),brightness=n32(),direction=n32(),colorMode=n32(),c=colors();
 if(colorsMin>colorsMax||colorsMax>MAX_LEDS||colorMode>3){diagnostic({rule:'mode_range',id,flags,speedMin,speedMax,brightnessMin,brightnessMax,colorsMin,colorsMax,colorMode});fail('rgb_mode_range');}
 return {id,name,value,flags,speedMin,speedMax,brightnessMin,brightnessMax,colorsMin,colorsMax,speed,brightness,direction,colorMode,colors:c};});
 const zoneCount=n16();if(zoneCount>128)fail('rgb_zone_limit');let start=0;
 const zones=Array.from({length:zoneCount},(_,id)=>{const name=text(),type=n32(),min=n32(),max=n32(),count=n32(),matrixBytes=n16();if(count>MAX_LEDS||start+count>MAX_LEDS||min>max)fail('rgb_zone_range');take(matrixBytes);const z={id,name,type,min,max,count,start};start+=count;return z;});
 const ledCount=n16();if(ledCount>MAX_LEDS)fail('rgb_led_limit');for(let i=0;i<ledCount;i++){text();n32();}
 const c=colors();if(offset!==data.length||c.length!==ledCount||start!==ledCount)fail('rgb_descriptor_layout');
 const identity=crypto.createHash('sha256').update(JSON.stringify({type,name,vendor,version,serial,location,zones,modes:modes.map(({id,name,value,flags,brightnessMin,brightnessMax,colorsMin,colorsMax})=>({id,name,value,flags,brightnessMin,brightnessMax,colorsMin,colorsMax})),ledCount})).digest('hex');
 return {id:'rgb-'+identity.slice(0,32),identity,name,vendor,type,version,activeMode,modes,zones,colors:c,ledCount};
}
function modeData(m){const name=Buffer.from(m.name+'\0');if(name.length>1024)fail('rgb_mode_name');const b=Buffer.alloc(2+name.length+48+2+m.colors.length*4);let at=0;b.writeUInt16LE(name.length,at);at+=2;name.copy(b,at);at+=name.length;
 for(const v of [m.value,m.flags,m.speedMin,m.speedMax,m.brightnessMin,m.brightnessMax,m.colorsMin,m.colorsMax,m.speed,m.brightness,m.direction,m.colorMode]){b.writeUInt32LE(v,at);at+=4;}b.writeUInt16LE(m.colors.length,at);at+=2;
 for(const c of m.colors){color(c).copy(b,at);at+=4;}return b;
}
function color(c){if(typeof c!=='string'||!/^#[0-9A-Fa-f]{6}$/.test(c))fail('rgb_color');return Buffer.from([parseInt(c.slice(1,3),16),parseInt(c.slice(3,5),16),parseInt(c.slice(5,7),16),0]);}
function ledsData(colors,zone=null){if(!Array.isArray(colors)||colors.length>MAX_LEDS)fail('rgb_led_limit');const b=Buffer.alloc((zone===null?6:10)+colors.length*4);b.writeUInt32LE(b.length);let at=4;if(zone!==null){b.writeUInt32LE(zone,at);at+=4;}b.writeUInt16LE(colors.length,at);at+=2;for(const c of colors){color(c).copy(b,at);at+=4;}return b;}
function updateModeData(m){const v=modeData(m),b=Buffer.alloc(8+v.length);b.writeUInt32LE(b.length);b.writeUInt32LE(m.id,4);v.copy(b,8);return b;}
function createClient({trusted=async()=>false,connect=net.createConnection,diagnostic=()=>{}}={}){
 let busy=false;
 async function session(fn){if(busy)fail('rgb_busy');busy=true;let socket,deadline,inactive,pending=null,buffer=Buffer.alloc(0),received=0,closed=false;
 const abort=code=>{closed=true;if(pending){pending.reject(Error(code));pending=null;}socket?.destroy();};
 try{
  if(!await trusted())fail('rgb_listener_owner_unverified');
  socket=connect({host:'127.0.0.1',port:6742});
  socket.on('error',()=>abort('rgb_disconnected'));socket.on('end',()=>abort('rgb_disconnected'));socket.on('close',()=>{if(!closed)abort('rgb_disconnected');});
  deadline=setTimeout(()=>abort('rgb_session_timeout'),12000);deadline.unref?.();
  socket.on('data',chunk=>{try{
   received+=chunk.length;if(received>4*1024*1024||buffer.length+chunk.length>LIMIT+16)fail('rgb_response_limit');buffer=Buffer.concat([buffer,chunk]);
   while(buffer.length>=16){if(buffer.subarray(0,4).toString()!=='ORGB')fail('rgb_header');const device=buffer.readUInt32LE(4),id=buffer.readUInt32LE(8),size=buffer.readUInt32LE(12);if(size>LIMIT)fail('rgb_response_limit');if(buffer.length<16+size)return;
    const data=Buffer.from(buffer.subarray(16,16+size));buffer=buffer.subarray(16+size);
    if(id===100)fail('rgb_device_list_changed');
    if(!pending||id!==pending.id||device!==pending.device)fail('rgb_unexpected_packet');
    const p=pending;pending=null;clearTimeout(inactive);p.resolve(data);
   }
  }catch(e){abort(/^rgb_[a-z_]+$/.test(e.message)?e.message:'rgb_invalid_response');}});
  await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('rgb_connect_timeout')),2000);socket.once('connect',()=>{clearTimeout(t);resolve();});socket.once('error',()=>{clearTimeout(t);reject(Error('rgb_disconnected'));});});
  const query=(id,device=0,data=Buffer.alloc(0))=>new Promise((resolve,reject)=>{if(closed||pending)return reject(Error('rgb_closed'));pending={id,device,resolve,reject};inactive=setTimeout(()=>abort('rgb_query_timeout'),2000);socket.write(frame(id,device,data));});
  const version=await query(40,0,u32(3));if(version.length!==4||version.readUInt32LE()<3)fail('rgb_protocol_requires_v3');const serverProtocol=version.readUInt32LE();
  const descriptor=async index=>parseDevice(await query(1,index,u32(3)),{diagnostic});
  const inventory=async()=>{const b=await query(0);if(b.length!==4||b.readUInt32LE()>32)fail('rgb_controller_count');const list=[];for(let i=0;i<b.readUInt32LE();i++)list.push({...await descriptor(i),index:i});if(new Set(list.map(d=>d.id)).size!==list.length)fail('rgb_ambiguous_identity');return list;};
  const send=async(id,index,data)=>{if(closed||![1050,1051,1101].includes(id))fail('rgb_write_scope');await new Promise((resolve,reject)=>socket.write(frame(id,index,data),e=>e?reject(Error('rgb_write_failed')):resolve()));};
  return await fn({inventory,descriptor,send,protocol:3,serverProtocol});
 }finally{closed=true;clearTimeout(deadline);clearTimeout(inactive);if(pending){pending.reject(Error('rgb_closed'));pending=null;}socket?.end();socket?.destroy();busy=false;}}
 return Object.freeze({session});
}
module.exports={createClient,parseDevice,modeData,ledsData,updateModeData,frame,FLAGS};
