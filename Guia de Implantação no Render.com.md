# Guia de Implantação no Render.com

Este guia fornece instruções passo a passo para implantar o bot de reconhecimento facial no Render.com, uma plataforma que oferece hospedagem gratuita e contínua para aplicações Python.

## 1. Criar uma conta no Render.com

1. Acesse [render.com](https://render.com)
2. Clique em "Sign Up" no canto superior direito
3. Você pode se cadastrar usando sua conta do GitHub, GitLab ou Google, ou criar uma conta com e-mail
4. Complete o processo de registro e faça login na sua conta

## 2. Preparar os arquivos para deploy

Você precisará dos seguintes arquivos:
- `render_bot.py` (renomeie para `app.py`)
- `requirements.txt`
- `Procfile` (com o conteúdo: `web: python app.py`)

## 3. Criar um novo serviço no Render

1. No dashboard do Render, clique em "New +" no canto superior direito
2. Selecione "Web Service" na lista de opções

## 4. Configurar o serviço

### Opção 1: Deploy via GitHub (recomendado)

1. Selecione "Build and deploy from a Git repository"
2. Conecte sua conta GitHub se ainda não estiver conectada
3. Crie um repositório no GitHub e faça upload dos arquivos do bot
4. Selecione o repositório na lista

### Opção 2: Deploy manual

1. Selecione "Deploy from a local directory"
2. Siga as instruções para configurar o CLI do Render e fazer o deploy

## 5. Configurar as opções do serviço

1. Dê um nome ao seu serviço (ex: "recon-facial-bot")
2. Região: Escolha a mais próxima de você
3. Branch: `main` (ou a branch que contém seu código)
4. Runtime: `Python 3`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `python app.py`
7. Plano: Selecione "Free"

## 6. Configurar variáveis de ambiente (opcional)

Se você quiser manter o token do bot seguro, você pode configurá-lo como uma variável de ambiente:

1. Na seção "Environment", clique em "Add Environment Variable"
2. Nome: `TELEGRAM_TOKEN`
3. Valor: `7736951978:AAFheBfSTrvkgl40ALpR-_3Vdd80BL4yDHU`

Neste caso, você precisará modificar o código para ler o token da variável de ambiente:

```python
import os
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7736951978:AAFheBfSTrvkgl40ALpR-_3Vdd80BL4yDHU")
```

## 7. Iniciar o deploy

1. Clique em "Create Web Service"
2. Aguarde o processo de build e deploy (pode levar alguns minutos)
3. Quando o status mudar para "Live", seu bot estará online

## 8. Verificar o funcionamento

1. Abra o Telegram e acesse [@recon_facial_bot](https://t.me/recon_facial_bot)
2. Envie o comando `/start` para verificar se o bot está respondendo
3. Teste o fluxo completo com o comando `/reconhecimento`

## 9. Solução de problemas

### O bot não responde

1. Verifique os logs no dashboard do Render:
   - Acesse seu serviço no dashboard
   - Clique na aba "Logs"
   - Verifique se há erros ou mensagens de alerta

### Erros de dependências

1. Verifique se todas as dependências estão listadas corretamente no arquivo `requirements.txt`
2. Se necessário, atualize o arquivo e faça um novo deploy

### Serviço desligado após inatividade

O plano gratuito do Render pode desligar seu serviço após 15 minutos de inatividade. Para evitar isso:

1. Configure um serviço de "ping" para manter seu bot ativo
2. Use um serviço como UptimeRobot para enviar requisições periódicas ao seu bot

## 10. Vantagens do Render.com

- **Gratuito**: O plano gratuito é suficiente para bots de Telegram com tráfego moderado
- **Contínuo**: Mesmo no plano gratuito, o serviço pode funcionar 24/7 (com algumas limitações)
- **Fácil de usar**: Interface intuitiva e processo de deploy simplificado
- **Escalável**: Se necessário, você pode facilmente atualizar para planos pagos com mais recursos

## 11. Limitações do plano gratuito

- 512 MB de RAM
- Desligamento após 15 minutos de inatividade
- 750 horas de execução por mês
- Sem domínio personalizado

Para contornar a limitação de inatividade, você pode configurar um serviço de "ping" para manter seu bot ativo.

## 12. Manutenção

- Verifique regularmente os logs para garantir que o bot esteja funcionando corretamente
- Monitore o uso de recursos para evitar atingir os limites do plano gratuito
- Faça backup do código e configurações periodicamente

Para qualquer dúvida ou problema, consulte a documentação oficial do Render em [render.com/docs](https://render.com/docs).
