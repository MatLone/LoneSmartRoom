'use strict';
const SECTIONS=Object.freeze([
 ['overview','Central Windows','Ferramentas integradas e estado de disponibilidade'],['hardware','Hardware e rede','Inventário somente leitura e sensores existentes'],
 ['maintenance','Manutenção','Inspeção, prévia de limpeza e planos de reparo'],['optimization','Perfis e otimização','Ajustes explicados, reversão e execução bloqueada'],
 ['applications','Aplicativos','Inventário, favoritos e conjuntos pós-formatação'],['peripherals','Periféricos','Mouse, teclado e áudio por interação explícita'],
 ['display','GPU e tela','Informações e padrões visuais sem mudar resolução'],['network','Rede e internet','RTT, jitter, perda e DNS sob demanda'],
 ['games','Biblioteca e FPS','Biblioteca, perfis e importação PresentMon'],['environment','Quarto e RGB','Dispositivos, conectores e cenas com prévia'],
 ['nex','NEX','Intenções locais e diagnóstico baseado em evidências'],['audit','Backup e auditoria','Configurações validadas e histórico limitado']
].map(([id,title,description])=>({id,title,description})));
const REPAIRS=Object.freeze([
 {id:'sfc-verify',title:'Integridade de arquivos Windows',executable:'sfc.exe',arguments:['/verifyonly'],admin:true,restart:'Pode ser necessário após reparo',effect:'Verifica arquivos protegidos; não repara nesta opção.',rollback:'Diagnóstico sem reversão de arquivos.'},
 {id:'dism-check',title:'Saúde da imagem Windows',executable:'DISM.exe',arguments:['/Online','/Cleanup-Image','/CheckHealth'],admin:true,restart:'Conforme diagnóstico',effect:'Consulta o estado conhecido da imagem.',rollback:'Diagnóstico sem reversão de arquivos.'},
 {id:'sfc-repair',title:'Reparar arquivos protegidos',executable:'sfc.exe',arguments:['/scannow'],admin:true,restart:'Possível',effect:'Pode substituir arquivos do sistema.',rollback:'Não há reversão completa garantida; exige backup e janela de manutenção.'},
 {id:'dism-repair',title:'Reparar imagem Windows',executable:'DISM.exe',arguments:['/Online','/Cleanup-Image','/RestoreHealth'],admin:true,restart:'Possível',effect:'Pode acessar Windows Update e substituir componentes.',rollback:'Não há reversão completa garantida.'},
 {id:'windows-update',title:'Windows Update',executable:null,arguments:[],admin:false,restart:'Conforme atualização',effect:'Inventário de estado e orientação; não dispara atualização.',rollback:'Reversibilidade depende da atualização.'},
 {id:'dns',title:'Diagnóstico DNS',executable:null,arguments:[],admin:false,restart:'Não',effect:'Consulta DNS pela ferramenta de rede; não limpa cache nem muda adaptadores.',rollback:'Somente leitura.'}
]);
const ADJUSTMENTS=Object.freeze([
 {id:'startup-review',title:'Revisar programas de inicialização',benefit:'Pode reduzir trabalho no login se houver aplicativos desnecessários.',sideEffect:'Aplicativos removidos da inicialização deixam de abrir após login.',admin:false,restart:'Próximo login',rollback:'Restaurar a entrada original preservada no backup.'},
 {id:'visual-effects',title:'Efeitos visuais',benefit:'Pode reduzir animações; efeito em jogos depende da carga.',sideEffect:'Altera a aparência do Windows.',admin:false,restart:'Conforme ajuste',rollback:'Restaurar os valores originais registrados.'},
 {id:'notifications',title:'Notificações durante jogos',benefit:'Reduz interrupções visuais.',sideEffect:'Avisos podem ser adiados.',admin:false,restart:'Não',rollback:'Restaurar preferências anteriores.'},
 {id:'background-apps',title:'Aplicativos em segundo plano',benefit:'Permite revisar consumidores observados.',sideEffect:'Restringir aplicativos pode atrasar sincronização.',admin:false,restart:'Conforme aplicativo',rollback:'Restaurar cada permissão registrada.'},
 {id:'power-review',title:'Plano de energia',benefit:'Comparação de opções, sem promessa de ganho de FPS.',sideEffect:'Pode elevar consumo, temperatura e ruído.',admin:true,restart:'Normalmente não',rollback:'Restaurar o GUID do plano anterior.'},
 {id:'optional-apps',title:'Aplicativos opcionais',benefit:'Organiza o que o usuário não utiliza.',sideEffect:'Desinstalações podem remover funções e dados.',admin:true,restart:'Conforme aplicativo',rollback:'Reinstalação não recupera necessariamente os dados.'}
]);
const PACKAGES=Object.freeze([
 ['Microsoft.VisualStudioCode','Visual Studio Code'],['Mozilla.Firefox','Firefox'],['7zip.7zip','7-Zip'],['VideoLAN.VLC','VLC'],['Git.Git','Git'],['Valve.Steam','Steam']
].map(([id,name])=>({id,name,source:'winget',origin:'manifesto precisa ser conferido antes da instalação',installable:false})));
const CONNECTORS=Object.freeze([
 {id:'home-assistant',title:'Home Assistant',state:'not_configured',support:'REST autenticada; token apenas no processo principal/cofre futuro.',readPath:'/api/states',writePath:'/api/services/{domain}/{service}'},
 {id:'openrgb',title:'OpenRGB',state:'not_configured',support:'SDK local requer software, versão e controladora compatíveis; não compartilhar controle simultâneo.'},
 {id:'signalrgb',title:'SignalRGB',state:'unverified',support:'Integração depende de API documentada disponível e hardware compatível.'},
 {id:'fan-controller',title:'Ventoinhas',state:'unsupported',support:'RPM ADLX disponível; escrita PWM/curvas sem provedor homologado.'},
 {id:'ir-bridge',title:'Ventilador / bridge IR',state:'not_configured',support:'Equipamento sem interface digital exige bridge compatível.'}
]);
const PROFILES=Object.freeze(['Padrão','Equilibrado','Desempenho','Gamer','Personalizado']);
module.exports={SECTIONS,REPAIRS,ADJUSTMENTS,PACKAGES,CONNECTORS,PROFILES};
