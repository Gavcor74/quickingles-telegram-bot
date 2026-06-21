import json
import os
import random
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().strip('"').strip("'")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
TELEGRAM_ADMIN_USER_ID = os.getenv("TELEGRAM_ADMIN_USER_ID", "").strip()

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5").strip()
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1200"))

TIMEZONE = os.getenv("APP_TIMEZONE") or os.getenv("TZ", "Europe/Madrid")
DAILY_POST_DAYS = os.getenv("DAILY_POST_DAYS", "mon,wed,fri").lower()
DAILY_POST_HOUR = int(os.getenv("DAILY_POST_HOUR", "9"))
BRAND_SIGNATURE = os.getenv("BRAND_SIGNATURE", "- Jesus | Quickingles").strip()
POST_LENGTH = os.getenv("POST_LENGTH", "medium").strip().lower()
CUSTOM_PROMPT = os.getenv("CUSTOM_PROMPT", "").strip()

TOPIC_CATALOG = [
    "phrasal verbs",
    "collocations",
    "slang",
    "idioms",
    "false friends",
    "pronunciation tips",
    "common mistakes",
    "business english",
    "travel english",
    "listening hacks",
    "small talk",
    "email writing",
    "interview english",
    "grammar in context",
    "vocabulary builder",
]

CONTENT_SYSTEM_PROMPT = (
    "Eres copywriter experto para un canal de Telegram de ingles para hispanohablantes. "
    "Escribes con voz personal del profesor, directo, cercano y claro. "
    "Tu salida SIEMPRE debe seguir una plantilla fija estilo Notion con emojis, "
    "sin frases de asistente ni texto meta."
)


def topic_pool() -> list[str]:
    raw = os.getenv("TOPIC_POOL", "").strip()
    if not raw:
        return TOPIC_CATALOG[:]
    cleaned = [item.strip().lower() for item in raw.split(",") if item.strip()]
    return cleaned or TOPIC_CATALOG[:]


def choose_topic() -> str:
    pool = topic_pool()
    fixed = os.getenv("FIXED_TOPIC", "").strip().lower()
    if fixed:
        return fixed

    day_index = datetime.now(ZoneInfo(TIMEZONE)).toordinal()
    return pool[day_index % len(pool)] if pool else random.choice(TOPIC_CATALOG)


def length_instruction() -> str:
    if POST_LENGTH == "short":
        return "70 a 110 palabras"
    if POST_LENGTH == "long":
        return "150 a 210 palabras"
    return "100 a 150 palabras"


def topic_specific_guidance(topic: str) -> str:
    guidance = {
        "slang": (
            "Para slang: evita explicar lo obvio. Ensena uso real, matiz, registro y contexto. "
            "Cada ejemplo debe incluir una frase natural en ingles y una traduccion/adaptacion util en espanol."
        ),
        "phrasal verbs": (
            "Para phrasal verbs: no des definiciones abstractas. Prioriza verbo + contexto real + traduccion natural."
        ),
        "collocations": (
            "Para collocations: centra el post en combinaciones naturales que un hispanohablante suele decir mal."
        ),
        "common mistakes": (
            "Para common mistakes: compara error comun vs forma natural correcta de manera muy clara."
        ),
        "pronunciation tips": (
            "Para pronunciation tips: incluye contraste de sonido o palabra concreta para practicar."
        ),
        "grammar in context": (
            "Para grammar in context: explica la estructura con ejemplos cotidianos, no con teoria larga."
        ),
    }
    return guidance.get(
        topic,
        "Haz el contenido practico, especifico y util para hispanohablantes adultos que quieren sonar mas naturales.",
    )


def build_content_prompt(topic: str) -> str:
    custom_block = (
        f"\nInstrucciones extra del dueno del canal (obligatorias):\n{CUSTOM_PROMPT}\n"
        if CUSTOM_PROMPT
        else ""
    )
    return (
        f"Crea UN post para canal de Telegram sobre '{topic}'.\n"
        "Salida obligatoria con esta plantilla exacta (sin cambiar encabezados):\n"
        "🧠 [GANCHO EN PREGUNTA]\n\n"
        "📌 [TITULO CORTO]\n"
        "[Very short explanation in ENGLISH only (1-2 lines max), useful and specific]\n\n"
        "💬 English boost\n"
        "[One extra English line only, practical, memorable and natural]\n\n"
        "✨ 3 ejemplos utiles\n"
        "- [Ejemplo 1: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]\n"
        "- [Ejemplo 2: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]\n"
        "- [Ejemplo 3: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]\n\n"
        "📝 Mini reto\n"
        "[Un ejercicio corto de practica, pero NO incluyas la solucion]\n\n"
        "Reglas obligatorias:\n"
        "1) Prohibido empezar con: 'Aqui tienes', 'A continuacion', 'Te comparto', 'Como IA'.\n"
        "2) Escribir como profesor humano (yo/te), no como asistente.\n"
        "3) Explicacion principal en INGLES, muy corta. Prioriza ejemplos con frases en ingles + traduccion.\n"
        f"4) Longitud objetivo: {length_instruction()}. Mantener texto corto y directo.\n"
        "5) Reemplaza TODO lo que este entre [corchetes] con contenido real.\n"
        f"6) Cierra siempre con esta firma exacta: {BRAND_SIGNATURE}\n"
        "7) PROHIBIDO incluir una seccion de solucion o respuesta del reto.\n"
        "8) No hagas definiciones obvias o demasiado escolares. Tiene que sonar util para adultos.\n"
        "9) Cada ejemplo debe ser concreto, idiomatico y listo para reutilizar en una conversacion real.\n"
        "10) El mini reto debe invitar a producir ingles de verdad, no a dar una opinion vaga.\n"
        "Guia especifica para este tema:\n"
        f"{topic_specific_guidance(topic)}\n"
        f"{custom_block}"
        "Devuelve SOLO el post final. No anadas comentarios extra."
    )


def sanitize_generated_post(content: str, topic: str) -> str:
    text = re.sub(r"\[[^\]]+\]", "", content.strip())
    lines = [line.rstrip() for line in text.splitlines()]
    if lines:
        first_idx = next((idx for idx, line in enumerate(lines) if line.strip()), None)
        if first_idx is not None:
            first = lines[first_idx].strip()
            if first in {"🧠", "🧠 ?", "🧠?", ""} or (first.startswith("🧠") and len(first.replace("🧠", "").strip()) < 6):
                lines[first_idx] = f"🧠 ¿Sabías que dominar {topic} te hace sonar más natural en inglés?"
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if BRAND_SIGNATURE and not text.lower().endswith(BRAND_SIGNATURE.lower()):
        text = f"{text}\n\n{BRAND_SIGNATURE}"
    return text


def call_openai(topic: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("Falta OPENAI_API_KEY en variables de entorno.")

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": CONTENT_SYSTEM_PROMPT},
            {"role": "user", "content": build_content_prompt(topic)},
        ],
        "temperature": 0.8,
        "max_tokens": MAX_TOKENS,
    }
    response = requests.post(
        f"{OPENAI_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=55,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_anthropic(topic: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("Falta ANTHROPIC_API_KEY en variables de entorno.")

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.8,
        "system": CONTENT_SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": build_content_prompt(topic)},
        ],
    }
    response = requests.post(
        f"{ANTHROPIC_BASE_URL}/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=55,
    )
    response.raise_for_status()
    data = response.json()
    return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")


def generate_post() -> tuple[str, str]:
    topic = choose_topic()
    if AI_PROVIDER == "anthropic":
        content = call_anthropic(topic)
    elif AI_PROVIDER == "openai":
        content = call_openai(topic)
    else:
        raise RuntimeError("AI_PROVIDER debe ser 'openai' o 'anthropic'.")

    return sanitize_generated_post(content, topic), topic


def telegram_api(method: str, payload: dict) -> dict:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en variables de entorno.")

    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def send_message(chat_id: str | int, text: str) -> dict:
    return telegram_api("sendMessage", {"chat_id": chat_id, "text": text})


def is_authorized(user_id: int | str | None) -> bool:
    return not TELEGRAM_ADMIN_USER_ID or str(user_id) == TELEGRAM_ADMIN_USER_ID


def local_schedule_matches_now() -> bool:
    days = {item.strip() for item in DAILY_POST_DAYS.split(",") if item.strip()}
    now = datetime.now(ZoneInfo(TIMEZONE))
    weekday = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][now.weekday()]
    return weekday in days and now.hour == DAILY_POST_HOUR


