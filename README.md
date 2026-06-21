# Quickingles Content Bot

Bot serverless para Vercel. Usa una unica funcion Node.js en `api/telegram.js`.

## Variables en Vercel

```env
TELEGRAM_BOT_TOKEN=token_nuevo_de_botfather
TELEGRAM_CHANNEL_ID=@quickingles_test
TELEGRAM_ADMIN_USER_ID=tu_user_id_telegram
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=tu_api_key_de_claude
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-sonnet-4-5
MAX_TOKENS=1200
APP_TIMEZONE=Europe/Madrid
BRAND_SIGNATURE=- Jesus | Quickingles
POST_LENGTH=medium
```

No uses `TZ`; Vercel la reserva.

## Proyecto Vercel limpio

- Repo: `Gavcor74/quickingles-telegram-bot`
- Nombre recomendado: `quickingles-content-bot`
- Preset: Other o Node.js
- Root: `./`
- Build command: vacio/default
- Output: vacio/default

## Webhook

```text
https://api.telegram.org/botTELEGRAM_BOT_TOKEN/setWebhook?url=https://TU-PROYECTO.vercel.app/api/telegram
```

Prueba en Telegram:

```text
/post_now
```
