# Histórico de desempenho — opt-in de desenvolvimento

`performance-history.cjs` recebe snapshots do host já existente. Não chama
sensores, não cria processos e não registra nada quando desativado. A ativação
exige revisão de desenvolvimento + `--lone-history-development` + identificador
de sessão hexadecimal. Não é ativado na instalação nem em build empacotada.

Mantém CPU, utilização/temperatura GPU, RAM utilizada/percentual e ocupação,
leitura, gravação e atividade de C:/D:. Origem e unidade são campos fixos;
timestamp original e estado acompanham cada ponto. Falhas/nulos interrompem
linhas do gráfico, sem interpolação ou preenchimento com zero.

Política inicial configurável no construtor confiável: 2 s entre registros,
retenção máxima de 1 hora, 1.800 pontos, arquivo ≤2 MiB, flush no máximo a cada
30 s e ao encerrar. Não há timer de coleta adicional: o callback do monitoramento
alimenta o módulo. A consulta seleciona 5/30/60 min e retorna até 120 pontos reais,
conservando o último ponto de cada bloco. Isso reduz resolução em janelas longas;
não representa médias ou extremos desses blocos.

Persistência em `.cache/performance-history/<sessão>/performance-history-v1.json`,
separada de perfis e bancos operacionais. Escrita temporária exclusiva + rename,
limite de bytes antes de ler, rejeição de diretórios/arquivos simbólicos e versão
desconhecida. Só remove temporário comprovadamente criado pela própria operação.
Pode perder o lote ainda não gravado em uma falha abrupta. Não é uma garantia de
durabilidade transacional. Processos sob a mesma conta não ficam isolados por
essa política de arquivos; o conteúdo não inclui credenciais ou arquivos pessoais.

Main intermedeia `history:read` com remetente confiável, versão e enum fechado.
Preload acrescenta apenas `getPerformanceHistory(5|30|60)`, sem caminho/SQL/comando.
Resposta ≤128 KiB, 500 ms mínimo. O renderer consulta somente na aba visível,
a cada 10 s, sem canal de rede. `contextIsolation`, sandbox e CSP continuam ativos.
A pinagem de preservação do preload foi atualizada para essa extensão específica;
os testes conferem também a lista exata de métodos e a rejeição dos argumentos.

Validação: 1.928 verificações Node incluindo 1.900 inserções simuladas, capacidade,
janela, cópia defensiva, timestamps/valores inválidos, arquivo corrompido, limite
de disco e API preload. Regressões: 891 verificações Node e 378 testes Python.
Os testes usam somente diretórios temporários próprios em `.cache`.

O contrato `v:1` com campos fixos e linhas [timestamp, sequência, métricas] prepara
a futura consulta Android; nenhuma rota HTTP de histórico foi ativada. O histórico
não foi medido com sensores reais nem homologado na instalação. Não existe
captura permanente fora do opt-in. Reverter o commit desta etapa remove apenas
a integração de desenvolvimento; não exige restaurar bancos ou perfis.
