# Lone Smart Room — Android v1.4 / Wake-on-LAN real

Este projeto abre **a mesma interface das 3 abas** que a demonstração de Windows. O único recurso integrado a hardware é o botão **Ligar PC**, que utiliza um pacote mágico de Wake-on-LAN sobre **UDP, pela rede local**.

## Compilar e instalar no Galaxy S25 FE

1. No Windows 11, instale o **Android Studio** com Android SDK 35 e JDK 17. Use uma versão de Android Studio compatível com o Android Gradle Plugin 8.7.3.
2. Extraia o ZIP e abra a pasta `Android-LoneSmartRoom` no Android Studio (`File` → `Open`).
3. Sincronize o projeto. **Este pacote contém os arquivos Gradle, mas não inclui o binário `gradle-wrapper.jar` nem um APK compilado.** Se o IDE exigir um wrapper, gere-o com uma instalação local do Gradle 8.9 executando `gradle wrapper --gradle-version 8.9` na pasta do projeto. Isso gera `gradlew.bat` e `gradle-wrapper.jar`.
4. Conecte seu Samsung via USB com depuração USB habilitada ou use o modo Wi-Fi do Android Studio e clique em `Run`.
5. Abra a aba **Controles**, depois **Meu computador** → **Controle remoto**. Confirme MAC, broadcast e porta. Toque em **Ligar** ou no botão principal **Enviar Wake-on-LAN**.

## Configuração inicial

- MAC da Ethernet: `02:00:00:C7:AC:53`
- Broadcast: `172.31.250.255`
- Porta: `9`
- Celular e computador na mesma LAN, sem isolamento dos clientes Wi-Fi. Se for usado o Wi-Fi convidado ou uma rede secundária em modo roteador/NAT, o broadcast pode não alcançar o PC.
- Testar primeiro com o Windows **suspenso**, estado já validado usando WolOn. O despertar a partir de desligamento completo ainda não foi comprovado.

## Importante

- A mensagem **Pacote WoL enviado** significa que o Android transmitiu o pacote; **não prova que o Windows iniciou**. O monitoramento real de estado exige um agente ou verificação adicional.
- **Desligar, reiniciar, suspender, Steam, CS2, RGB e sensores continuam em simulação** nesta versão. Não há conexões reais ao Windows, Home Assistant ou SignalRGB.
- O app usa uma WebView com conteúdo HTML local, bloqueia a navegação externa e só expõe a operação de enviar pacotes WoL (sem shell/comandos arbitrários).
- Não funciona fora de casa automaticamente. Não abra portas de controle do Windows no roteador. Para acesso remoto serão necessários VPN e um emissor remoto autorizado.
- A integração do Android **não é necessária no Windows para acordar o PC**: se o PC está dormindo, o widget dentro dele não está executando.
