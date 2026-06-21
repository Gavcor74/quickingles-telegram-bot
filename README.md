# Quickingles Telegram Bot

Bot de Telegram para generar borradores de contenido de Quickingles y enviarlos al canal de revision `@quickingles_test`.

## Version Vercel

Esta version evita depender del VPS, EasyPanel, n8n, Redis u Ollama. Funciona con:

- `/api/telegram`: webhook de Telegram para comandos como `/post_now`.
- `/api/daily-post`: endpoint para Vercel Cron.
- Anthropic Claude u OpenAI como proveedor de IA.

Flujo actual recomendado:

```text
@quickinglesbot
  -> /post_now o Vercel Cron
  -> genera contenido con Claude u OpenAI
  -> publica en @quickingles_test
  -> revision manual
  -> copiar/pegar al canal final
```

## Variables en Vercel para Claude

```env
TELEGRAM_BOT_TOKEN=token_nuevo_de_botfather
TELEGRAM_CHANNEL_ID=@quickingles_test
TELEGRAM_ADMIN_USER_ID=tu_user_id_telegram
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=tu_api_key_de_claude
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-sonnet-4-5
MAX_TOKENS=1200
DAILY_POST_DAYS=mon,wed,fri
DAILY_POST_HOUR=9
DAILY_POST_MINUTE=0
TZ=Europe/Madrid
BRAND_SIGNATURE=- Jesus | Quickingles
POST_LENGTH=medium
TOPIC_POOL=phrasal verbs,collocations,slang,idioms,false friends,pronunciation tips,common mistakes,business english,travel english,listening hacks,small talk,email writing,interview english,grammar in context,vocabulary builder
CUSTOM_PROMPT=
CRON_SECRET=
```

Si Anthropic te muestra otro identificador de modelo disponible en la consola, puedes sustituir solo `ANTHROPIC_MODEL` sin tocar codigo.

## Variables alternativas para OpenAI

```env
AI_PROVIDER=openai
OPENAI_API_KEY=tu_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
MAX_TOKENS=1200
```

Regenera el `TELEGRAM_BOT_TOKEN` en BotFather antes de desplegar, porque el token anterior aparecio en capturas.

## Configurar webhook de Telegram

Despues de desplegar en Vercel, ejecuta en el navegador o terminal:

```text
https://api.telegram.org/botTELEGRAM_BOT_TOKEN/setWebhook?url=https://TU-PROYECTO.vercel.app/api/telegram
```

Comprueba el estado con:

```text
https://api.telegram.org/botTELEGRAM_BOT_TOKEN/getWebhookInfo
```

## Cron

`vercel.json` incluye una ejecucion lunes, miercoles y viernes a las `07:00 UTC`, que en horario de verano corresponde a las `09:00` en Madrid.

```json
{
  "crons": [
    {
      "path": "/api/daily-post",
      "schedule": "0 7 * * 1,3,5"
    }
  ]
}
```

Si quieres evitar cualquier desfase horario, deja el cron desactivado al principio y usa solo `/post_now`.

## Version VPS antigua

`telegram_agent.py` queda como version legacy para VPS/EasyPanel. Usa polling, SQLite local y Ollama, por lo que no es la ruta recomendada tras cancelar el VPS.
