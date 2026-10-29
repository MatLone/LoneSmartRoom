'use strict';
// Fixed loopback OpenRGB SDK queries only (IDs 0,1). No LED/mode writes.
const net=require('node:net');
function packet(id,device=0){if(![0,1].includes(id)||!Number.isInteger(device)||device<0||device>31)throw Error('rgb_read_query');const b=Buffer.alloc(id===1?20:16);b.write('ORGB');b.writeUInt32LE(device,4);b.writeUInt32LE(id,8);b.writeUInt32LE(id===1?4:0,12);return b;}
function parseDevice(data){if(data.length<11||data.readUInt32LE(0)!==data.length)throw Error('rgb_descriptor_size');const length=data.readUInt16LE(8);if(length<1||length>181||10+length>data.length||data[9+length]!==0)throw Error('rgb_descriptor_name');const name=new TextDecoder('utf-8',{fatal:true}).decode(data.subarray(10,9+length));if(/[\x00-\x1f]/.test(name))throw Error('rgb_descriptor_text');return {name,type:data.readUInt32LE(4),read_verified:true,write_enabled:false};}
function createReader({trusted=async()=>false,connect=net.createConnection,now=Date.now}={}){
 let pending=null,last=null;
 const unavailable=code=>({v:1,state:'unavailable',source:'openrgb.sdk.loopback.readonly',observed_at:new Date(now()).toISOString(),items:[],error:code,physical_actions:0});
 async function read(){if(pending)return unavailable('rgb_busy');if(last&&now()-last.at>=0&&now()-last.at<15000)return structuredClone(last.value);
 pending=(async()=>{if(!await trusted())return unavailable('rgb_listener_owner_unverified');return new Promise(resolve=>{
 let socket,buffer=Buffer.alloc(0),expected={id:0,device:0},count=null,items=[],done=false,total=0;const finish=value=>{if(done)return;done=true;clearTimeout(deadline);socket?.end();socket?.destroy();resolve(value);};const deadline=setTimeout(()=>finish(unavailable('rgb_read_timeout')),5000);
 try{socket=connect({host:'127.0.0.1',port:6742});socket.setTimeout(1200,()=>finish(unavailable('rgb_read_timeout')));socket.on('error',()=>finish(unavailable('rgb_connection_unavailable')));socket.on('end',()=>finish(unavailable('rgb_connection_ended')));socket.on('connect',()=>socket.write(packet(0)));
 socket.on('data',chunk=>{if(done)return;try{total+=chunk.length;if(total>262144||buffer.length+chunk.length>65552)throw Error();buffer=Buffer.concat([buffer,chunk]);while(buffer.length>=16){if(buffer.subarray(0,4).toString()!=='ORGB'||buffer.readUInt32LE(8)!==expected.id||buffer.readUInt32LE(4)!==expected.device)throw Error();const size=buffer.readUInt32LE(12);if(size>65536)throw Error();if(buffer.length<16+size)return;const data=buffer.subarray(16,16+size);buffer=buffer.subarray(16+size);
 if(expected.id===0){if(data.length!==4)throw Error();count=data.readUInt32LE(0);if(count>32)throw Error();if(count===0)return finish({v:1,state:'available',source:'openrgb.sdk.loopback.readonly',observed_at:new Date(now()).toISOString(),protocol:0,items,physical_actions:0});expected={id:1,device:0};}
 else{items.push({id:'openrgb-'+expected.device,...parseDevice(data)});if(items.length===count)return finish({v:1,state:'available',source:'openrgb.sdk.loopback.readonly',observed_at:new Date(now()).toISOString(),protocol:0,items,physical_actions:0});expected.device++;}socket.write(packet(expected.id,expected.device));
 }}catch{finish(unavailable('rgb_invalid_response'));}});
 }catch{finish(unavailable('rgb_connection_unavailable'));}
 });})();try{const value=await pending;last={at:now(),value};return structuredClone(value);}finally{pending=null;}}
 return {read,peek:()=>last&&now()-last.at>=0&&now()-last.at<=15000?structuredClone(last.value):null};
}
module.exports={createReader,packet,parseDevice};
