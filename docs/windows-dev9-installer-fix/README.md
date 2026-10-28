# Correção do instalador dev.9 — 28/10/2026

Uma tentativa assistida da candidata r9 foi autorizada e executada. O helper
abortou ANTES de remover a instalação anterior. A dev.8, os 118 arquivos da
instalação e os 83 arquivos do perfil permaneceram idênticos à verificação inicial.
Não houve abertura do dashboard instalado nem início do agente. A porta 8776
estava livre; banco íntegro, zero grants. Android não foi acessado.

O backup `Windows-before-dev9-20261028T132507Z` está fora do Git, com ACL exclusiva:
201 arquivos, 403.361.107 bytes; SHA-256 do manifesto:
`f6131c8f01068abde895404fb87d16f5b1904a990c6ba8c01c9e80420034c02a`.

## Causas verificadas e correção

1. O NSIS x86 utilizava o caminho de sistema sujeito ao redirecionamento WOW64.
O host x86 tem política efetiva Restricted neste PC; o x64 já estava Unrestricted.
A correção seleciona o host x64, correspondente ao aplicativo e ao helper testado,
por Sysnative. Nenhuma política foi alterada e não há ExecutionPolicy/Bypass.
O comportamento de redirecionamento está documentado pela
[Microsoft](https://learn.microsoft.com/en-us/windows/win32/winprog64/file-system-redirector).
2. O teste NSIS real com instalação FICTÍCIA encontrou também
`CommandNotFoundException` em Get-FileHash e `CouldNotAutoloadMatchingModule`
na aplicação da ACL. Os testes anteriores chamavam o helper diretamente de uma
sessão PowerShell e não reproduziam o ambiente herdado do NSIS.
3. SHA-256 por streaming e aplicação de ACL usam agora as APIs .NET equivalentes.
O helper exige processo x64. Erros registram somente fase, linha, código numérico
e identificador de regra de uma allowlist. A recusa retorna exit code 2.

O novo teste compila um NSIS x86 de fixture, executa o helper verdadeiro no host
x64, simula a remoção de UM debug.log fictício e confirma restauração com SHA-256
idêntico. São sete verificações reais de integração de filesystem/host, além das
oito regressões de ACL, conflito, caminhos e orçamento. Não é instalação do LSR.
Fixtures e seus journals são preservados. As capturas nesta pasta mostram a
única tentativa operacional, que falhou com segurança.

## Estado e continuação

- Não reutilizar r9 para implantação; seu hash continua preservado no histórico.
- As correções do helper estão em desenvolvimento. Falta incorporá-las à próxima
revisão de empacotamento da MESMA dev.9, inspecionar e homologar.
- A instrução posterior de retomada proíbe alterar instalações operacionais:
nenhuma nova tentativa de instalação será feita nesta fase.
- Fonte base consolidada: `9d4c115`; checkpoints anteriores preservados.
- Uma regressão chegou a ser recusada antes da execução por indisponibilidade
  da revisão automática (limite de uso); foi retomada posteriormente, sem bypass.

Rollback da tentativa: desnecessário, pois a versão anterior não foi removida.
Para atualização futura: conferir novos hashes, backup e perfil, preservar o
journal externo, instalar somente com autorização vigente e verificar hashes
antes da primeira abertura. Se houver falha, não repetir automaticamente.
