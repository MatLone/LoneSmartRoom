# Lone Smart Room 2.0 — primeira revisão do dashboard Windows

24/10/2026 · branch `feature/ui-migration-preview` · checkpoint funcional e documental preservado: `d5323f707f2e4eb84b26f8647deb66e21618cb2b` (inclui `908538a`).

**Entrega somente de auditoria e prévia.** Nenhum arquivo do Electron funcional, Android ou agente foi modificado. Nenhuma instalação, substituição de executável, pareamento ou abertura Steam/CS2 foi realizada. A prévia integra a evolução do mesmo repositório, sem criar outro aplicativo ou pacote.

## Abrir e revisar

A prévia pode ser aberta diretamente em [index.html](index.html), sem servidor ou dependências novas. Nesta sessão também foi iniciada em `http://127.0.0.1:55702/`. Esse endereço é efêmero e vale enquanto o processo local estiver ativo.

Para iniciar outra sessão, a partir da raiz do repositório:

```powershell
.venv/Scripts/python.exe -B scripts/serve-windows-dashboard-preview.py
```

O endereço escolhido é exibido no terminal. Esse servidor serve exclusivamente os assets da prévia em `127.0.0.1`; não escuta na LAN, não tem endpoints de comando e não acessa o agente. O HTTP dessa apresentação local não modifica nem substitui o HTTPS operacional da porta 8776.

Use as três opções do menu lateral. **Configurar**, engrenagens dos dispositivos, informações de permissões, explicação dos sensores e painel da marca abrem janelas flutuantes. O botão de composição, ao lado da engrenagem superior, alterna dashboard/widget. Em larguras pequenas, o layout compacto é automático. É uma composição de interface; não implementa redimensionamento nativo, bandeja ou always-on-top.

## Capturas

[Comparativo das principais telas](review/00-comparativo-windows.jpg).

| Composição | Capturas |
| --- | --- |
| Dashboard 1440 × 1000 | [Controles](review/1440-controls.png), [Monitoramento PC](review/1440-monitor.png), [Gamer Launcher](review/1440-gamer.png) |
| Janela 1024 × 768 | [Controles](review/1024-controls.png), [Monitoramento PC](review/1024-monitor.png), [Gamer Launcher](review/1024-gamer.png) |
| Compacto 390 × 844 | [Controles](review/390-controls.png), [Monitoramento PC](review/390-monitor.png), [Gamer Launcher](review/390-gamer.png) |
| Widget em área de trabalho 1440 × 1000 | [Controles](review/widget-controls.png), [Monitoramento PC](review/widget-monitor.png), [Gamer Launcher](review/widget-gamer.png) |
| Painéis flutuantes | [Dispositivo](review/1440-panel-lamp.png), [Conexão](review/1440-panel-connection.png), [Permissões](review/1440-panel-permissions.png) |

As capturas são renderizações locais reais dos arquivos desta prévia, usando o Electron já disponível, perfil isolado, sem preload e sem acesso nativo. **Não mostram uma aplicação Windows instalada ou conectada ao agente.** Conteúdo abaixo da dobra permanece disponível por rolagem. A inspeção automatizada da URL pelo navegador integrado foi bloqueada por sua política; não foi usado outro navegador para contornar o bloqueio. As capturas e os testes do renderer de arquivos locais haviam sido concluídos antes dessa tentativa.

## O que a prévia informa

- Estado desktop **Desconhecido**, HTTPS **Não integrada**, energia **Não verificado**, última consulta **Nenhuma**. Não foi inventada uma conexão funcional, nem inferido desligamento.
- CPU, GPU, RAM, temperaturas e gráficos sem amostras. Ausência de sensor aparece como traço/indisponível, não como medição zero.
- Steam/CS2 e interruptores dos dispositivos desabilitados, sem handlers nativos de execução. Não há controles para suspender, reiniciar ou desligar.
- A contagem **zero grants** vem de leitura local do banco às **03:38:30**, identificada como fotografia da auditoria, sem atualização ao vivo. Ela não equivale a uma autorização do cliente desktop.
- NEX aparece como planejado. SignalRGB/Home Assistant estão mencionados apenas como integrações futuras no painel informativo.

## Marca e reutilização

A logo, símbolo e cabeçalho são cópias byte a byte dos assets aprovados do Android. O ícone Windows SVG/ICO vem de `docs/design/brand/official-board-2026-10-24/`, sem casa ou cubo/hexágono. A engrenagem de oito dentes usa o mesmo desenho do Android dev.7. `brand-provenance.json` registra os cinco arquivos de origem e hashes. Os arquivos de marca mestres e os ícones do aplicativo Electron existente permanecem intactos; sua substituição pertence à migração futura.

## Testes e preservação

| Verificação executada | Resultado |
| --- | --- |
| Renderer da prévia | **131 assertivas aprovadas** |
| Responsividade | **24 casos**: três abas em 1600×1000, 1440×1000, 1280×800, 1024×768, 800×600, 440×860, 390×844 e 350×650 |
| Painéis, composição widget e evento de teclado | Abertura/fechamento, limites do viewport e navegação aprovados |
| Botões operacionais | Desabilitados; mesmo habilitados artificialmente pelo teste não chamam o executor substituto |
| Rede e runtime no renderer | Zero requisições externas; nenhum Node, IPC ou bridge nativa exposta |
| Regressão UI existente | Versão dinâmica, permissões e quatro estados de comando aprovados; sem abrir aplicativos |
| Regressão WoL | 11 cenários de armazenamento/validação aprovados; zero pacotes reais |
| Fontes existentes | **99 arquivos byte a byte iguais** ao snapshot anterior |
| Originais e recuperação | **86 registros preservados** |
| Banco operacional | Zero grants e pendências; um dispositivo ativo; histórico de quatro comandos inalterado |
| Configuração, certificados e credenciais protegidas | Hashes iguais aos registrados na validação física dev.7; nenhum segredo decriptado |

Recibos em [review/visual-tests.json](review/visual-tests.json), [preservation.json](preservation.json) e [evidence/](evidence/). Nenhum novo instalador Windows foi compilado: isso carregaria os arquivos funcionais que devem ser preservados nesta primeira revisão. Não houve nova build Android ou acesso ao Samsung.

O primeiro teste falhou no envio de tecla ao renderer oculto; o teste final despacha o evento DOM diretamente para verificar o handler, sem alegar teste de teclado físico. A inicialização inicial do processo Electron foi restringida pela sandbox; a execução permitida usou somente o perfil de teste isolado. Nenhum desses ajustes exigiu alteração no produto. A suíte completa Python/TLS não foi repetida, pois o agente está fora do escopo desta entrega; sua pendência continua em [TLS.md](../brand/compact-review-2026-10-24/TLS.md).

## Próxima decisão

Revisar a organização, proporções, legibilidade e composição widget. O [relatório de auditoria e plano de migração](MIGRATION.md) detalha o que pode ser reutilizado, as lacunas funcionais e a arquitetura proposta. **A integração funcional e a substituição da versão Windows existente dependem de aprovação posterior.**
