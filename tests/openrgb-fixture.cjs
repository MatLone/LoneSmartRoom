'use strict';
// Explicitly simulated SDK peer. Never opens a socket or accesses hardware.
const {EventEmitter}=require('node:events');
const {modeData}=require('../apps/windows-ui/openrgb-sdk.cjs');
const u16=n=>{const b=Buffer.alloc(2);b.writeUInt16LE(n);return b;};
const u32=n=>{const b=Buffer.alloc(4);b.writeUInt32LE(n);return b;};
const text=s=>{const b=Buffer.from(s+'\0');return Buffer.concat([u16(b.length),b]);};
const mode=(id=0)=>({id,name:id?'Pulse':'Direct',value:id,flags:id?81:32,speedMin:0,speedMax:100,brightnessMin:1,brightnessMax:100,colorsMin:id?1:0,colorsMax:id?1:0,speed:20,brightness:55,direction:0,colorMode:id?2:1,colors:id?['#123456']:[]});
function descriptor({name='SIMULATED Nollie',activeMode=0,modes=[mode(),mode(1)],colors=['#123456','#654321'],flags=null}={}){
 const parts=[u32(0),u32(4),text(name),text('Fixture'),text('Explicit mock'),text('1'),text('fixture-serial'),text('fixture-location'),u16(modes.length),u32(activeMode),...modes.map(modeData),u16(2),text('Zone 1'),u32(1),u32(1),u32(1),u32(1),u16(0),text('Zone 2'),u32(1),u32(1),u32(1),u32(1),u16(0),u16(2),text('LED 1'),u32(0),text('LED 2'),u32(1),u16(colors.length),...colors.map(s=>Buffer.from([parseInt(s.slice(1,3),16),parseInt(s.slice(3,5),16),parseInt(s.slice(5,7),16),0]))];
 const b=Buffer.concat(parts);b.writeUInt32LE(b.length);return b;
}
function fakeSdk(){let state={activeMode:0,modes:[mode(),mode(1)],colors:['#123456','#654321']},sent=[],disconnect=false,ignoreWrites=false;
 const connect=options=>{if(options.host!=='127.0.0.1'||options.port!==6742)throw Error('external_endpoint');const s=new EventEmitter();s.end=()=>{};s.destroy=()=>{};
 s.write=(b,cb)=>{const id=b.readUInt32LE(8),dev=b.readUInt32LE(4),p=b.subarray(16);sent.push(id);if(disconnect){queueMicrotask(()=>s.emit('error',Error('mock_disconnected')));return;}
 let reply=null;if(id===40)reply=u32(5);if(id===0)reply=u32(1);if(id===1)reply=descriptor(state);
 if(id===1050&&!ignoreWrites)state.colors=Array.from({length:p.readUInt16LE(4)},(_,i)=>'#'+p.subarray(6+i*4,9+i*4).toString('hex').toUpperCase());
 if(id===1051&&!ignoreWrites){const z=p.readUInt32LE(4);state.colors[z]='#'+p.subarray(10,13).toString('hex').toUpperCase();}
 if(id===1101&&!ignoreWrites){const index=p.readUInt32LE(4),old=state.modes[index];state.activeMode=index;const n=p.readUInt16LE(8),a=8+2+n;state.modes[index]={...old,speed:p.readUInt32LE(a+32),brightness:p.readUInt32LE(a+36),direction:p.readUInt32LE(a+40),colorMode:p.readUInt32LE(a+44),colors:Array.from({length:p.readUInt16LE(a+48)},(_,i)=>'#'+p.subarray(a+50+i*4,a+53+i*4).toString('hex').toUpperCase())};}
 cb?.();if(reply){const h=Buffer.alloc(16);h.write('ORGB');h.writeUInt32LE(dev,4);h.writeUInt32LE(id,8);h.writeUInt32LE(reply.length,12);const frame=Buffer.concat([h,reply]);queueMicrotask(()=>{s.emit('data',frame.subarray(0,5));s.emit('data',frame.subarray(5));});}return true;};queueMicrotask(()=>s.emit('connect'));return s;};
 return {connect,sent,get state(){return structuredClone(state);},set state(v){state=structuredClone(v);},set disconnected(v){disconnect=v;},set ignoreWrites(v){ignoreWrites=v;}};
}
module.exports={descriptor,fakeSdk,mode};
