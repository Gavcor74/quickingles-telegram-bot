# Agente local en Python (sin API de OpenAI)

Este proyecto usa **Ollama** en local, asi que no necesitas `OPENAI_API_KEY` ni consumes tokens de OpenAI.

## 1) Instalar Ollama (una vez)
Descarga e instala desde [https://ollama.com/download](https://ollama.com/download)

## 2) Descargar un modelo local (una vez)
```powershell
ollama pull llama3.2
```

## 3) Crear entorno virtual
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 4) Instalar dependencias Python
```powershell
pip install -r requirements.txt
```

## 5) Configurar variables
```powershell
Copy-Item .env.example .env
```

Edita `.env` y rellena:
- `TELEGRAM_BOT_TOKEN`: token de `@BotFather`
- `TELEGRAM_CHANNEL_ID`: `@tu_canal` o id numerico del canal
- `TELEGRAM_ADMIN_USER_ID`: tu user id de Telegram (opcional pero recomendado)
- `DAILY_POST_DAYS`: dias en formato `mon,wed,fri`
- `DAILY_POST_HOUR` y `DAILY_POST_MINUTE`: hora de publicacion

## 6) Lanzar bot de Telegram
```powershell
python telegram_agent.py
```

## Comandos del bot
- `/start`: ayuda rapida
- `/reset`: borra memoria de chat
- `/status`: estado de automatizacion, temas, longitud y firma
- `/start_daily`: activa publicacion programada
- `/stop_daily`: desactiva publicacion programada
- `/post_now`: publica un post al instante

### Comandos para tipo de contenido y estilo
- `/topics`: muestra catalogo y temas activos
- `/set_topics phrasal verbs, collocations, slang`: define mezcla de temas
- `/set_mode rotate`: rota temas para cubrir variedad
- `/set_mode random`: elige tema aleatorio del pool
- `/set_focus phrasal verbs`: fija un solo tipo de contenido
- `/clear_focus`: vuelve al modo mezcla
- `/set_length short|medium|long`: cambia longitud de los posts
- `/set_signature - Jesus | Quickingles`: fija firma al final de cada post

Catalogo incluido:
- phrasal verbs
- collocations
- slang
- idioms
- false friends
- pronunciation tips
- common mistakes
- business english
- travel english
- listening hacks
- small talk
- email writing
- interview english
- grammar in context
- vocabulary builder

## Publicacion programada original
- El bot genera contenido de ingles para hispanohablantes.
- Guarda historial en `content.db`.
- Antes de publicar, compara con posts anteriores para evitar repeticiones.

## Memoria y datos locales
- Conversaciones: `telegram_memory.json`
- Historial de posts, temas y estado: `content.db`

## Opcional: cambiar modelo
```powershell
$env:OLLAMA_MODEL="mistral"
python telegram_agent.py
```


