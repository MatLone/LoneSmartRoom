'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {parseDevice}=require('../apps/windows-ui/openrgb-sdk.cjs'),{descriptor}=require('./openrgb-fixture.cjs');
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.value='';this.events={};this.disabled=false;}
 append(...nodes){for(const n of nodes){this.children.push(n);n.parent=this;if(this.tag==='select'&&this.children.length===1)this.value=n.value;}}
 replaceChildren(...nodes){this.children=[];this.append(...nodes);}
 setAttribute(){}addEventListener(event,fn){this.events[event]=fn;}
 remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}
 async click(){if(this.disabled)throw Error('disabled_fixture_control');await this.events.click?.();}
 all(){return [this,...this.children.flatMap(n=>n.all())];}
}
(async()=>{
 const parsed=parseDevice(descriptor()),device={...parsed,modes:parsed.modes.map(m=>({...m,writable:true,perLed:!!(m.flags&32),colorSupported:!!(m.flags&96),brightnessSupported:!!(m.flags&16)})),zones:parsed.zones.map(z=>({...z,available:true,colors:parsed.colors.slice(z.start,z.start+z.count)}))};
 let state={v:1,state:'available',simulation:true,protocol:3,serverProtocol:5,observed_at:new Date().toISOString(),devices:[device],scenes:['gamer','trabalho','relaxar','noturno'].map(id=>({id,targets:[],suggestedColor:'#FF153F'})),automation:{enabled:false},recovery:null,saved_at:null,write_enabled:true,error:null};let calls=[];
 const api={rgb:async(op,args)=>{calls.push({op,args});return structuredClone(state);}},window={},document={createElement:t=>new Element(t)},parent=new Element('div');
 const source=fs.readFileSync(require.resolve('../apps/windows-ui/rgb-renderer.js'),'utf8');vm.runInNewContext(source,{window,document});await window.loneRGBView.mount(parent,api);
 let checks=0;const ok=v=>{assert(v);checks++;},button=text=>parent.all().find(n=>n.tag==='button'&&n.textContent===text);
 ok(parent.all().some(n=>n.textContent==='Iluminação RGB · OpenRGB'));ok(calls.length===1&&calls[0].op==='state');ok(button('Aplicar seleção'));ok(button('Restaurar estado salvo').disabled);
 await button('Adicionar dispositivo / zona à cena').click();ok(parent.all().filter(n=>n.className==='rgb-scene-row').length===1);ok(calls.length===1);
 await button('Remover destino').click();ok(parent.all().filter(n=>n.className==='rgb-scene-row').length===0);ok(calls.length===1);
 await button('Adicionar dispositivo / zona à cena').click();await button('Salvar cena GAMER').click();ok(calls.some(c=>c.op==='sceneSave'&&c.args.targets.length===1&&c.args.targets[0].color==='#FF153F'));
 const before=calls.length;await button('Aplicar seleção').click();ok(calls[before].op==='apply');ok(calls[before].args.target.deviceId===device.id);ok(calls[before].args.target.brightness===null);
 state={...state,state:'unavailable',devices:[],observed_at:null,error:'rgb_disconnected'};await button('Atualizar dispositivos e estado').click();ok(!button('Aplicar seleção'));ok(parent.all().some(n=>n.textContent.includes('Indisponível')));

 const offered=new Element('div'),count=calls.length;
 window.loneRGBView.offer(offered,{op:'sceneApply',args:{id:'gamer'}},api);ok(calls.length===count);
 ok(offered.children[0].textContent==='Confirmar solicitação RGB');await offered.children[0].click();
 ok(calls[count].op==='sceneApply'&&calls[count].args.id==='gamer');
 const rejected=new Element('div');window.loneRGBView.offer(rejected,{op:'shell',args:{}},api);ok(rejected.children.length===0);
 ok(fs.readFileSync(require.resolve('../apps/windows-ui/focused-renderer.js'),'utf8').includes('window.loneRGBView.offer(c,r.rgbRequest,api)'));
 ok(!source.includes('innerHTML'));ok(!source.includes('require('));ok(!source.includes('fetch('));
 console.log(`PASS: ${checks} RGB DOM/state/null/scenes/no-write-on-open checks; simulated DOM and providers`);
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
