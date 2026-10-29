'use strict';
const assert=require('node:assert/strict'),{proposal}=require('../apps/windows-ui/nex-rgb.cjs');let checks=0;
for(const id of ['gamer','trabalho','relaxar','noturno']){assert.deepEqual(proposal('Ativar cena '+id),{op:'sceneApply',args:{id}});checks++;}
assert.deepEqual(proposal('Desligar RGB'),{op:'off',args:{deviceId:null}});checks++;
assert.deepEqual(proposal('Consultar dispositivos conectados'),{op:'refresh',args:{}});checks++;
for(const message of ['executar powershell','ativar cena gamer; desligar PC','aplicar cena ../evil','desligar windows','ligar Steam','Ativar cena Gamer\nsem confirmar','a'.repeat(1001),null]){assert.equal(proposal(message),null);checks++;}
console.log(`PASS: ${checks} typed NEX RGB proposals; no execution from text`);
