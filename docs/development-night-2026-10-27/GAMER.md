# Fundação de sessões de jogo — sem FPS real

`gamer-session.js` implementa contrato v1, identificador de sessão, origem,
timestamps e estados `not_started`, `source_unavailable`, `warming_up`,
`capturing`, `finished` e `capacity_reached`. O único provedor implementado é
simulado. A composição normal mostra Indisponível, sem captura, timer ou processo.

Um frame de teste contém sequência, relógio monotônico e `frametime_ms` finito
positivo. Sequências repetidas, relógio regressivo, NaN/infinito e versões
incompatíveis são rejeitados. Por sessão: 60 mil frames por padrão, máximo
configurável de 120 mil; ao atingir o limite, a captura simulada para e informa
explicitamente o limite. Não anuncia estatísticas da sessão inteira se houve
truncamento. A visualização retorna até 120 pontos reais de entrada; o histórico
de resumos em memória conserva até 20 sessões, sem duplicar o mesmo identificador.
Não há persistência de sessões de produção nem importador de CSV nesta etapa.

Metodologia: FPS instantâneo = 1000 / último frametime; FPS médio = 1000 × número
de frames / soma dos frametimes. 1% Low = 1000 / média dos `ceil(N × 0,01)`
frametimes mais lentos. Exige pelo menos 100 frames para o 1% Low; antes disso o
valor permanece nulo. Isso não é a média dos FPS instantâneos nem um percentil de
FPS. A semântica preparada é frames apresentados, não necessariamente exibidos.

O componente de interface foi adicionado ao Gamer Launcher existente. Ele mostra
FPS/frametime/média/1% Low indisponíveis quando não há fonte. Prévias simuladas são
identificadas. Nenhuma API preload de captura ou execução foi acrescentada.

Estudo de fonte externa, somente documentação oficial consultada em 27/10/2026:

- [Repositório oficial PresentMon](https://github.com/GameTechDev/PresentMon):
  descreve análise de eventos ETW de apresentação e diferentes componentes,
  incluindo serviço e frontend. Isso não autoriza instalar o serviço existente.
- [Releases oficiais](https://github.com/GameTechDev/PresentMon/releases):
  distinguem métricas de apresentação e exibição; a interpretação depende da
  versão e das colunas escolhidas. Não se presume equivalência entre elas.

Uma integração futura deve fixar versão/licença, validar unidades e perda de
eventos, requisitos de permissões, seleção do processo e custo. Preferir leitura
externa ETW/saída documentada; nada de injeção, hooks, overlay em CS2, alterações
do jogo ou interferência no VAC. Nenhum binário foi baixado, instalado ou executado.

Testes: 127 verificações Node de matemática, limites, disponibilidade, origem,
duplicação e resumos, além das regressões existentes. São frames fictícios somente
de teste, não desempenho do PC. Reversão pelo commit desta etapa, sem dados de
jogos/instalações para restaurar. FPS real continua pendente de fonte e homologação.
