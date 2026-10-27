# Arquitetura modular proposta — contrato de fronteiras

Esta é uma especificação para implementação incremental, não um novo serviço
ativo. Reutiliza os pacotes de monitoramento e diagnóstico existentes. Não altera
versão do wire protocol, IPC, capacidades do agente ou empacotamento atual.

```text
Android / NEX                    Electron renderer (sem Node/segredos)
  cliente nativo HTTPS             preload: operações enumeradas
          |                                |
  API específica futura             main: sender/frame + limites
          |                                |
  autenticação + capacidade         projeções de leitura
          |                                |
          +---- contratos sanitizados ------+
                          |
        diagnóstico / inventários / cache métrico existente
                          |
        adaptadores fixos Win32 / PDH / ADLX somente leitura

Escrita futura (canal separado e inicialmente ausente):
  plano -> preview -> confirmação local -> executor fixo
        -> verificação -> recibo / rollback condicionado
```

## Responsabilidades

| Módulo lógico | Responsabilidade | Não deve fazer |
|---|---|---|
| observation | Consumir leituras existentes e inventários sob demanda | Criar sensor ou cliente pipe duplicado ao abrir cartão |
| diagnostics | Reduzir evidência em estados e explicar pendências | Converter ausência, fixture ou amostra antiga em sucesso |
| maintenance / cleanup / startup | Separar inventário, plano e alteração | Reparar/excluir/alterar Run ao apenas consultar |
| settings / profiles | Estado atual, aplicabilidade e diff de itens enumerados | Executar script, caminho, comando ou argumento importado |
| games / tools | Descoberta, testes interativos e preflight | Alterar CS2/driver/config sem plano ou abrir jogo sem grant |
| applications / debloat | Catálogo verificado, dependências, plano de instalação/remoção | Executar entrada arbitrária ou aceitar publisher apenas pelo rótulo |
| recovery / history | Recibos sanitizados e evidências de restauração | Prometer rollback universal ou exportar identidade/segredos |

Não criar framework de plugins dinâmicos. Novos adaptadores entram por código
revisado e identificador fechado, com contrato, testes e empacotamento explícitos.
A primeira implementação não precisa extrair/refatorar executores legados.

## Contrato futuro de observação

Envelope versionado com ID enumerado do módulo, origem (real/simulated), timestamp
da coleta, validade/idade, estado, motivo enumerado e dados limitados. Snapshot
novo não renova evidência antiga. Números inválidos/ausentes são nulos; zero válido
permanece zero. Erro, stale, unsupported e inatividade continuam distinguíveis.

Reutilizar o contrato métrico v1 e as regras de frescor ADLX; não estender TTL por
conveniência de UI. Respostas precisam de limites de tamanho, cardinalidade,
frequência e prazo por módulo. Os limites devem ser definidos/testados antes da
exposição da rota. Nenhuma API genérica de filesystem, Registry, shell ou URL.

Inventários lentos usam jobs canceláveis sob demanda com teto de itens/tempo,
resultados parciais explícitos e sem varredura recursiva ilimitada. Caminhos e
argumentos privados só aparecem no detalhe local necessário, nunca em exportação
automática. Histórico tem retenção limitada e opt-in de persistência.

## Contrato futuro de alterações

Um plano imutável terá `schema_version`, ID local, itens allowlisted, alvo/escopo,
valor atual e proposto, precondições, necessidade de elevação/reinício, efeitos
esperados, prazo e estratégia de recuperação por item. O executor não recebe
comando/caminho livre do renderer ou Android. Importação de perfis rejeita versões,
IDs e campos desconhecidos; perfis não concedem capacidades.

Confirmação fica vinculada ao plano mostrado. Antes de executar, revalidar estado
e permissões; divergência invalida o plano. Não usar um `confirmed=true` remoto
como autorização suficiente. Elevação fica limitada ao executor específico,
sem elevar todo Electron ou transformar o agente de status em shell.

Estados: planejado, aguardando confirmação, executando, concluído, falhou,
parcial, resultado incerto, revertido. Persistir intenção antes do despacho;
não repetir automaticamente após crash/timeout. Reversão exige verificar que o
valor atual ainda é o escrito pelo plano, evitando sobrescrever alterações
posteriores feitas pelo usuário ou Windows.

Backups de configurações devem ser limitados, protegidos e registrados. Para
arquivos, preferir quarentena quando viável; exclusão e instalações podem não ser
reversíveis. DISM/SFC, reset de rede e Update não têm rollback universal. Se não
houver recuperação suficiente, classificar explicitamente e pedir confirmação
específica. A disponibilidade de um ponto de restauração não muda essa classificação.

## Preservação e validação

Continuam obrigatórios: TLS/pin/hostname, HMAC e replay protection, DPAPI, grants
locais por dispositivo, allowlist Steam/CS2, confirmação nativa, WoL independente,
CSP/contextIsolation/sandbox, validação de sender/frame, assinatura/identidade de
atualizações e integridade dos runtimes. Nunca copiar credenciais Android para
criar um cliente desktop. Uma futura capacidade remota precisa de contrato e
consentimento próprios; o pareamento existente não a autoriza.

Testar primeiro com executores substituídos: negação por padrão, schemas,
expiração, origem, limites, revogação, concorrência, cancelamento, resultado
incerto, falha parcial e rollback. Depois revisar UI em perfil isolado; por fim,
sessão física delimitada e autorizada. Teste mock não comprova sensores, precisão
de polling, ganho de desempenho, compatibilidade anticheat ou restauração real.

Reversão desta etapa documental: reverter apenas seus commits. Não restaurar
banco, apagar credenciais, alterar instalação ou desfazer os quatro arquivos
preexistentes fora do Git. Futuras reversões funcionais serão por checkpoint,
em ordem inversa de dependência, com revisão do diff antes da implantação.
