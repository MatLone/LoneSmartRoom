# Lone Smart Room v1.4 — Integração Wake-on-LAN Android

**Mudança principal:** a funcionalidade **Ligar PC** agora possui implementação **real no projeto Android nativo**. O aplicativo envia diretamente pela rede local um pacote UDP Wake-on-LAN. O PC já despertou pelo WolOn durante teste do usuário, mas **esta nova versão Android ainda precisa ser compilada e testada no Galaxy S25 FE**.

## Arquivos

- `index.html`, `styles.css`, `app.js` — mesma interface, com Controles, Monitoramento PC e Gamer Launcher; configuração WoL agora acessível no pop-up **Controle remoto**.
- `main.cjs`, `preload.cjs`, `package.json` — widget Electron para Windows, com controles demonstrativos (o PC não acorda a si próprio enquanto dorme).
- `Android-LoneSmartRoom/` — projeto de aplicativo Android Studio. A interface é carregada a partir dos mesmos 3 arquivos HTML/CSS/JS, e uma ponte Kotlin envia UDP WoL real.
- `Android-LoneSmartRoom/LEIA-ME-ANDROID.md` — instruções de compilação e primeiro teste.

## Instruções rápidas Android

1. No Windows, instale o Android Studio, SDK 35 e JDK 17.
2. Abra a pasta `Android-LoneSmartRoom` como projeto Android Studio.
3. Sincronize Gradle e execute no Galaxy S25 FE.
4. Conecte o celular ao Wi-Fi da mesma rede do PC (mesma sub-rede, sem isolamento).
5. Entre em **Controles** > **Meu computador** > **Controle remoto** e confirme os campos MAC, broadcast e UDP.
6. Suspenda o computador e toque em **Enviar Wake-on-LAN**. Verifique fisicamente se ele despertou.

O projeto Android não contém APK pronto nem Gradle Wrapper JAR; consulte as instruções do arquivo Android.

## Rede já testada com WolOn

- Ethernet Intel I225-V
- MAC `02:00:00:C7:AC:53`
- IP Windows `172.31.250.8`
- broadcast `172.31.250.255`
- UDP porta `9`

IP e broadcast devem ser revistos se o roteador ou a rede mudar. O Android envia diretamente para o broadcast; não exige servidor separado dentro da mesma LAN.

## Escopo real x simulação

| Recurso | Android nativo | Navegador / Windows |
| --- | --- | --- |
| Wake-on-LAN | Pacote UDP real | Simulação |
| Verificar se o PC está online | Não implementado | Simulação |
| Suspender / reiniciar / desligar | Simulação, sem agente Windows | Simulação |
| Steam, CS2, RGB, sensores, FPS | Simulação | Simulação |
| Voz e efeito de onda vermelha | Efeito demonstrativo, sem captação | Efeito demonstrativo |

**Importante:** a mensagem "Pacote enviado" só confirma a transmissão do celular; não verifica se o PC acordou. O teste anterior comprovou apenas a retomada de suspensão, não a inicialização após desligamento completo. Não abra portas de automação do PC para a Internet. Acesso fora de casa exigirá projeto adicional de comunicação autenticada e emissor WoL confiável.

## Segurança

A ponte Android possui uma única capacidade nativa (emitir magic packet). Ela está ligada à interface local fornecida pelo aplicativo, não navega para sites externos e valida formato de MAC, broadcast IPv4 e porta 7/9. Não executa shell nem comandos arbitrários.

## Próxima etapa

Depois de testar o Android, adicionar um **agente de presença autenticado no PC** para confirmar os estados online/offline, e só depois implementar ações de desligar, suspender, reiniciar e abrir aplicativos com autorização explícita.
