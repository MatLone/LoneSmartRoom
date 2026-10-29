'use strict';
// Text creates a typed proposal only. Main confirmation is still mandatory.
function proposal(message){if(typeof message!=='string'||message.length>1000)return null;const text=message.trim().toLocaleLowerCase('pt-BR').replace(/[.!?]$/,'');const m=/^(?:ativar|aplicar) (?:a )?cena (gamer|trabalho|relaxar|noturno)$/.exec(text);if(m)return {op:'sceneApply',args:{id:m[1]}};if(/^(?:desligar|apagar) (?:o )?(?:rgb|iluminação)$/.test(text))return {op:'off',args:{deviceId:null}};if(/^(?:consultar|listar) dispositivos(?: rgb| conectados)?$/.test(text))return {op:'refresh',args:{}};return null;}
module.exports={proposal};
