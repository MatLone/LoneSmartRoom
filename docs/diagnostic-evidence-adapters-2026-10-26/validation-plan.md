# Próxima validação e reversão

## Gate obrigatório antes de leitores reais

Esta entrega não habilita evidências observadas. Uma integração futura exige
autorização específica e implementação/revisão separada do caminho observado,
aproveitando os leitores aprovados. Não basta remover a trava `simulated` ou
rotular recibos reais como simulação. O relatório deve manter origem e tempos
reais, e distinguir explicitamente simulação de observação.

Antes de operar, revisar o limite antes do parse, a procedência dos recibos, a
permissão efetiva de cada leitor e a sanitização. Confirmar que não houve mudança
dos fontes em relação aos testes. Preservar o contrato v1 e os guards temporais.
Se exigir elevação, instalação, novo endpoint ou mudança de configuração,
interromper a parte dependente e pedir autorização própria.

## Proposta: uma sessão passiva de no máximo 60 s

1. Com autorização nova e o caminho observado revisado, registrar manifesto e
   estado inicial mínimo, sem iniciar agente, Electron ou coletores. Confirmar
   ausência de leitor residual. Se existir divergência relevante, não começar.
2. Iniciar a contagem quando o leitor começar. Reservar os últimos 15 s para
   encerrar e conferir preservação. Não repetir automaticamente a sessão.
3. Usar somente identidade de processos, proprietário do listener, recibos dos
   componentes existentes e evidências de login/despacho já disponíveis.
4. Se expressamente abrangido, realizar no máximo duas consultas fixas de status
   HTTPS pelo mecanismo autenticado previamente validado. Não criar identidade
   desktop, copiar credenciais do Samsung ou usar endpoints de controle. Não
   enviar payload excessivo, ambíguo ou malformado.
5. Se o Electron/monitoramento estiver fechado normalmente, registrar inatividade
   normal. Não iniciá-lo para produzir cartões saudáveis. Ausência de amostra é
   ausência de evidência; não substituir por zero nem por uma fixture.
6. Medir CPU/RSS do leitor, bytes por relatório e duração. Comparar timestamps
   originais e idades; não renovar evidência ao consultar o cache.
7. Encerrar normalmente o próprio leitor até o prazo, sem sinalizar o agente.
   Conferir resíduos, listener e grants somente por leituras autorizadas. Manter
   o agente no estado inicial, sem reparo, reinicialização ou modificação.

Critérios de aprovação: limite respeitado, classificação apoiada em prova
suficiente, estado desconhecido explícito, fonte observada identificada, nenhum
segredo no relatório, ausência de processo residual e nenhuma alteração das
instalações/configurações. Consulta HTTP 200 não encerra a pendência TLS 10054;
bootstrap saudável não comprova despacho automático.

Esse plano não autoriza uma sessão física, a ativação de probes na Central ou a
implantação de uma nova versão Windows. Qualquer integração visual operacional
virá depois, com escopo separado.

## Reversão de desenvolvimento

O aplicativo instalado não foi alterado e não necessita rollback operacional.
Para retirar somente esta implementação, em uma branch de revisão limpa, avaliar
e executar `git revert 1aa7d3a` após autorização correspondente. Preservar o
commit documental posterior como histórico ou revertê-lo separadamente se isso
for desejado. Não usar reset destrutivo, checkout de perfil de produção, downgrade
Android ou restauração de backups para reverter código de desenvolvimento.

O commit independente `fe2e004` e os checkpoints solicitados devem permanecer.
Se novos commits dependerem dos adaptadores, revisar primeiro as dependências e
reverter em ordem inversa. Nenhum procedimento de reversão foi executado.

## Arquivos de evidência

- `validation-summary.json`: resumo de alcance, limites e checkpoints.
- `python-tests.json`, `node-tests.json`: resultados e hashes dos fontes.
- `preservation-before.json`, `preservation-after.json`: resultado agregado da
  preservação estática, sem caminhos privados.
- Quatro arquivos `*-SIMULATED.json`: exemplos sanitizados para revisão.
- `SHA256SUMS.json`: integridade dos arquivos públicos desta pasta, excluindo o
  próprio manifesto.

O manifesto privado que contém caminhos protegidos e os logs iniciais de teste
ficam no cache local ignorado pelo Git. Não contêm evidência de uma nova consulta
operacional nesta etapa.
