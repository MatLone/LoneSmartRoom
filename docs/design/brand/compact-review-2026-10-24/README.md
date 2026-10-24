# Cabeçalho compacto Android e revisão TLS

24/10/2026 · America/Sao_Paulo · branch `feature/ui-migration-preview`.
Base preservada desta etapa: `95acf3b522b0d0ee3b8eae3f4cf61765d2ce1316`.
Commit da variante Android: `00b5f24`.

## Identidade visual entregue

O cabeçalho pequeno agora utiliza **símbolo + LONE**, sem o subtítulo que ficava com aproximadamente 5 px de altura. Ampliá-lo substancialmente mantendo a largura disponível exigiria mudar a proporção da composição completa. Foi usada a alternativa autorizada de omitir o subtítulo somente nessa aplicação.

- [Comparação completa × compacta e cabeçalhos antes/depois](00-completa-versus-compacta.png).
- [Capturas Android lado a lado](01-capturas-android.png).
- [Captura útil 390 × 844](captures/390x844-android-compacto.png).
- [Captura útil 360 × 800](captures/360x800-android-compacto.png).

O novo asset é `apps/android/app/src/main/assets/brand/logo-header-small.svg`, reproduzível por `scripts/build-header-brand.py`. O PNG está em [exports/logo-header-small.png](../exports/logo-header-small.png), gerado com `scripts/render-header-brand.cjs` e o módulo Sharp já instalado, sem download de dependências.

O HTML seleciona a variante por `<picture>` até 600 CSS px; em larguras maiores continua selecionando `logo-horizontal.svg`. A splash mantém sua arte completa. O nome acessível permanece “Lone Smart Room”. Os caminhos, o traço, o brilho e a transformação do símbolo são os mesmos do original. Os contornos de LONE também são os mesmos; somente sua posição vertical passa de y=28 para y=37 para centralizar a palavra ao lado do símbolo, sem o subtítulo. Nenhum CSS ou JavaScript funcional foi alterado.

Os cinco SVGs originais, seu manifesto, todos os PNGs anteriores e a referência aprovada foram preservados. Seus hashes foram comparados com o manifesto original. A diferença dos **cantos retos/chanfrados**, em relação à aparência mais suavizada da referência, permanece sem correção; ela é apresentada na [revisão ampliada anterior](../final-review-2026-10-24/01-detalhes-ampliados.png) para aprovação visual.

| Área útil | Logo | Altura geométrica de LONE | Resultado |
| --- | ---: | ---: | --- |
| 390 × 844 | 216 × 62,02 px | aproximadamente 21 px | Asset compacto carregado; sem transbordamento horizontal da página. |
| 360 × 800 | 194 × 55,70 px | aproximadamente 18,9 px | Asset compacto carregado; sem transbordamento horizontal da página. |

As imagens foram capturadas da prévia integrada em navegador, sem bridges reais. Os recortes de tamanho exato removem somente a faixa externa de demonstração de 28 px. As capturas brutas e [métricas](captures/metrics.json) foram preservadas. Os cabeçalhos completos usados na comparação são as capturas anteriores, identificadas como anteriores. Steam/CS2 estavam desabilitados na prévia. Não houve validação no display físico do Samsung.

## Estado dos testes

| Verificação | Resultado |
| --- | --- |
| Suíte segura completa `scripts/test-safe.ps1` | **74/74 Python**, 22,364 s, sem alterar testes existentes de transporte. |
| Complementos da suíte segura | Teste legado com mocks; versão/comandos Android; **11 cenários WoL** aprovados. |
| Renderer Android final | **65 asserções**, **15 casos responsivos**; inclui seleção do asset compacto em 320/360/390/412 e completo em 800 px. |
| Pacote WoL Kotlin | Aprovado usando classes existentes, sem UDP e sem nova build Android. |
| Inventário de preservação | **86 registros** aprovados. |
| Matriz TLS final | **432 requisições diagnósticas** em fixtures; não representa 432 testes aprovados. Resets e outros erros foram registrados. |

Os [logs](evidence/) incluem a execução completa, o renderer final, o pacote Kotlin, a preservação e as matrizes TLS inicial/final. A primeira execução válida do renderer tinha 60 asserções; após adicionar cinco verificações do asset responsivo, o resultado final passou a 65. O diagnóstico TLS foi refinado de timeout por operação para **prazo absoluto** de descarte e recebeu um caso de payload lento antes da matriz final. Isso motivou nova execução do experimento; não houve retries automáticos das requisições nem alteração da suíte para tolerar reset.

Tentativas iniciais sob o sandbox não foram válidas para medir a comunicação: o loopback foi bloqueado com WinError 10013 e o renderer encerrou sem resultados. As execuções posteriores autorizadas fora dessa restrição usaram somente fixtures locais e renderer isolado. Esse erro de permissão não foi confundido com o reset WinError 10054 investigado.

## TLS e preservação operacional

O [relatório TLS](TLS.md) separa rejeição de payload, fechamento de conexão e perda inesperada da resposta. A causa provável continua sendo o encerramento com dados pendentes após a rejeição do corpo excessivo. O descarte estritamente limitado melhorou os casos moderados na fixture, mas o **agente operacional não foi modificado** e a falha não está declarada corrigida.

O experimento fica exclusivamente em `tests/diagnostics/tls_body_limits.py`, executado por CLI explícita. Seus handlers experimentais não são importados pelo agente. Não foram alterados endpoints, autenticação, HMAC, certificados, grants ou código sob `agent/`.

Android/Kotlin, package name, versão, assinatura, armazenamento, Wake-on-LAN, bridges, pareamento, credenciais e executores Steam/CS2 permanecem preservados. Não houve acesso ao Samsung, APK novo, instalação, lançamento real de aplicativos, restart do agente, alteração de firewall ou configuração do Windows. Build/lint/assinatura serão verificados na próxima etapa de build, ainda não executada.

Próximos passos: aprovar a aplicação compacta e a manutenção dos cantos chanfrados; depois preparar, em tarefa específica, ícone adaptativo e splash nativa com nova build assinada. A correção TLS proposta exige revisão separada antes de qualquer aplicação ao agente operacional.
