# Quickingles Content Bot

Bot serverless para generar borradores de contenido de Quickingles desde Telegram y enviarlos al canal de revision `@quickingles_test`.

Este repo esta preparado para Vercel con un unico entrypoint Python:

```toml
[tool.vercel]
entrypoint = "api.app:handler"
```

## Flujo

```text
@quickinglesbot
  -> /post_now
  -> Vercel /api/telegram
  -> Claude genera el borrador
  -> se envia a @quickingles_test
  -> revision manual
  -> copiar/pegar al canal final
```

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
TOPIC_POOL=phrasal verbs,collocations,slang,idioms,false friends,pronunciation tips,common mistakes,business english,travel english,listening hacks,small talk,email writing,interview english,grammar in context,vocabulary builder
CUSTOM_PROMPT=
```

No uses `TZ` en Vercel; esta reservada. Usa `APP_TIMEZONE`.

## Crear proyecto limpio en Vercel

1. Importa `Gavcor74/quickingles-telegram-bot`.
2. Nombre recomendado: `quickingles-content-bot`.
3. Preset: Python.
4. Root Directory: `./`.
5. Build/Output: valores por defecto.
6. Anade las variables anteriores.
7. Deploy.

## Configurar webhook

Cuando Vercel despliegue bien, registra el webhook:

```text
https://api.telegram.org/botTELEGRAM_BOT_TOKEN/setWebhook?url=https://TU-PROYECTO.vercel.app/api/telegram
```

Comprueba:

```text
https://api.telegram.org/botTELEGRAM_BOT_TOKEN/getWebhookInfo
```

## Pendiente

La programacion automatica queda fuera del primer despliegue para evitar ruido. Primero dejamos estable `/post_now`; despues anadimos cron si hace falta.
