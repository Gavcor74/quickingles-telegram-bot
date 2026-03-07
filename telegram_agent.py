import json
import os
import random
import re
import sqlite3
import asyncio
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().strip("\"").strip("'")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
TIMEZONE = os.getenv("TZ", "Europe/Madrid")
DAILY_POST_HOUR = int(os.getenv("DAILY_POST_HOUR", "9"))
DAILY_POST_MINUTE = int(os.getenv("DAILY_POST_MINUTE", "0"))
DAILY_POST_DAYS = os.getenv("DAILY_POST_DAYS", "mon,wed,fri").lower()
AUTHORIZED_USER_ID = os.getenv("TELEGRAM_ADMIN_USER_ID", "")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))

SYSTEM_PROMPT = "Eres un asistente util y conciso."
CONTENT_SYSTEM_PROMPT = (
    "Eres copywriter experto para un canal de Telegram de ingles para hispanohablantes. "
    "Escribes con voz personal del profesor, directo, cercano y claro. "
    "Tu salida SIEMPRE debe seguir una plantilla fija estilo Notion con emojis, "
    "sin frases de asistente ni texto meta."
)

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

MEMORY_FILE = Path("telegram_memory.json")
DB_FILE = Path("content.db")
MAX_HISTORY_MESSAGES = 20
MAX_GENERATION_ATTEMPTS = 2
DAILY_JOB_NAME = "daily_post"


def load_memory() -> dict[str, list[dict[str, str]]]:
    if not MEMORY_FILE.exists():
        return {}

    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {}


def save_memory(memory: dict[str, list[dict[str, str]]]) -> None:
    MEMORY_FILE.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS published_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                topic TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                normalized TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

    ensure_column_exists("published_posts", "topic", "TEXT NOT NULL DEFAULT ''")

    set_default_setting("daily_enabled", "0")
    set_default_setting("topic_mode", "rotate")
    set_default_setting("fixed_topic", "")
    set_default_setting("topic_pool", ",".join(TOPIC_CATALOG))
    set_default_setting("post_length", "medium")
    set_default_setting("brand_signature", "- Jesus | Quickingles")



def ensure_column_exists(table: str, column: str, column_def: str) -> None:
    conn = get_db()
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    names = {row[1] for row in cols}
    if column not in names:
        with conn:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")


def set_default_setting(key: str, value: str) -> None:
    conn = get_db()
    with conn:
        conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)", (key, value))


def set_setting(key: str, value: str) -> None:
    conn = get_db()
    with conn:
        conn.execute(
            """
            INSERT INTO settings(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def get_setting(key: str, default: str = "") -> str:
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def is_daily_enabled() -> bool:
    return get_setting("daily_enabled", "0") == "1"


def get_topic_mode() -> str:
    mode = get_setting("topic_mode", "rotate").strip().lower()
    return mode if mode in {"rotate", "random"} else "rotate"


def get_fixed_topic() -> str:
    return get_setting("fixed_topic", "").strip().lower()


def get_topic_pool() -> list[str]:
    raw = get_setting("topic_pool", ",".join(TOPIC_CATALOG))
    items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    return items if items else TOPIC_CATALOG[:]


def set_topic_pool(pool: list[str]) -> None:
    cleaned = [p.strip().lower() for p in pool if p.strip()]
    if not cleaned:
        cleaned = TOPIC_CATALOG[:]
    set_setting("topic_pool", ",".join(cleaned))



def get_post_length() -> str:
    length = get_setting("post_length", "medium").strip().lower()
    return length if length in {"short", "medium", "long"} else "medium"


def get_brand_signature() -> str:
    return get_setting("brand_signature", "- Jesus | Quickingles").strip()


def get_length_instruction() -> str:
    length = get_post_length()
    if length == "short":
        return "70 a 110 palabras"
    if length == "long":
        return "150 a 210 palabras"
    return "100 a 150 palabras"


def sanitize_generated_post(content: str, topic: str) -> str:
    text = content.strip()

    # Remove unresolved placeholders like [GANCHO EN PREGUNTA]
    text = re.sub(r"\[[^\]]+\]", "", text)

    # If hook is left empty, inject a natural opening question.
    lines = [ln.rstrip() for ln in text.splitlines()]
    if lines:
        first_nonempty_idx = next((i for i, ln in enumerate(lines) if ln.strip()), None)
        if first_nonempty_idx is not None:
            first = lines[first_nonempty_idx].strip()
            if first in {"🧠", "🧠 ?", "🧠?", ""}:
                lines[first_nonempty_idx] = f"🧠 ¿Sabías que dominar {topic} te hace sonar más natural en inglés?"
            elif first.startswith("🧠") and len(first.replace("🧠", "").strip()) < 6:
                lines[first_nonempty_idx] = f"🧠 ¿Sabías que dominar {topic} te hace sonar más natural en inglés?"

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def apply_brand_signature(content: str) -> str:
    signature = get_brand_signature()
    text = content.rstrip()
    if not signature:
        return text
    if text.endswith(signature):
        return text
    return f"{text}\n\n{signature}"
def ask_ollama(messages: list[dict[str, str]]) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=OLLAMA_TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9áéíóúñü\s]", "", text)
    return text


def get_recent_normalized(limit: int = 50) -> list[str]:
    conn = get_db()
    rows = conn.execute(
        "SELECT normalized FROM published_posts ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [row["normalized"] for row in rows]


def get_recent_titles(limit: int = 20) -> list[str]:
    conn = get_db()
    rows = conn.execute("SELECT title FROM published_posts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [row["title"] for row in rows]


def get_recent_topics(limit: int = 10) -> list[str]:
    conn = get_db()
    rows = conn.execute(
        "SELECT topic FROM published_posts WHERE topic <> '' ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [row["topic"].lower() for row in rows if row["topic"]]


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def is_too_similar(candidate: str, previous: list[str], threshold: float = 0.88) -> bool:
    return any(similarity(candidate, item) >= threshold for item in previous)


def choose_topic() -> str:
    fixed = get_fixed_topic()
    if fixed:
        return fixed

    pool = get_topic_pool()
    recent = get_recent_topics(limit=max(3, len(pool) // 2))
    candidates = [topic for topic in pool if topic not in recent]
    if not candidates:
        candidates = pool

    if get_topic_mode() == "random":
        return random.choice(candidates)

    return candidates[0]


def build_content_prompt(previous_titles: list[str], attempt: int, topic: str) -> str:
    blacklist = "\n".join(f"- {title}" for title in previous_titles) or "- (sin historial)"
    target_length = get_length_instruction()
    signature = get_brand_signature()
    return (
        f"Crea UN post para canal de Telegram sobre '{topic}'.\n"
        "Salida obligatoria con esta plantilla exacta (sin cambiar encabezados):\n"
        "🧠 [GANCHO EN PREGUNTA]\n\n"
        "📌 [TITULO CORTO]\n"
        "[Very short explanation in ENGLISH only (1-2 lines max)]\n\n"
        "💬 English boost\n"
        "[One extra English line only, practical and natural]\n\n"
        "✨ 3 ejemplos utiles\n"
        "- [Ejemplo 1: 3 frases en ingles] -> [traduccion en espanol]\n"
        "- [Ejemplo 2: 3 frases en ingles] -> [traduccion en espanol]\n"
        "- [Ejemplo 3: 3 frases en ingles] -> [traduccion en espanol]\n\n"
        "📝 Mini reto\n"
        "[Un ejercicio corto de practica, pero NO incluyas la solucion]\n\n"
        "Reglas obligatorias:\n"
        "1) Prohibido empezar con: 'Aqui tienes', 'A continuacion', 'Te comparto', 'Como IA'.\n"
        "2) Escribir como profesor humano (yo/te), no como asistente.\n"
        "3) Explicacion principal en INGLES (muy corta). Prioriza ejemplos con frases en ingles + traduccion.\n"
        f"4) Longitud objetivo: {target_length}. Mantener texto corto y directo.\n"
        "5) Evitar repeticion con posts anteriores.\n"
        "6) Reemplaza TODO lo que este entre [corchetes] con contenido real.\n"
        f"7) Cierra siempre con esta firma exacta: {signature}\n"
        "8) PROHIBIDO incluir una seccion de solucion o respuesta del reto.\n"
        f"Intento: {attempt}.\n"
        "Titulos recientes prohibidos:\n"
        f"{blacklist}\n"
        "Devuelve SOLO el post final. No anadas comentarios extra."
    )


def follows_style_rules(content: str) -> bool:
    lower = content.lower().strip()
    forbidden_starts = ("aqui tienes", "a continuación", "a continuacion", "te comparto", "como ia")
    required_chunks = ("🧠", "📌", "💬 english boost", "✨ 3 ejemplos utiles", "📝 mini reto")
    if any(lower.startswith(x) for x in forbidden_starts):
        return False
    if "[" in content or "]" in content:
        return False
    if "✅ solucion" in lower or "solución" in lower or "solucion" in lower:
        return False
    if not all(chunk in lower for chunk in required_chunks):
        return False
    signature = get_brand_signature()
    return (not signature) or lower.endswith(signature.lower())

def extract_title(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else "Post diario"
    return first_line[:120]


def generate_unique_post() -> tuple[str, str, str]:
    previous = get_recent_normalized()
    previous_titles = get_recent_titles()
    best_fallback: tuple[str, str, str] | None = None

    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        topic = choose_topic()
        prompt = build_content_prompt(previous_titles, attempt, topic)
        messages = [
            {"role": "system", "content": CONTENT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        content = ask_ollama(messages).strip()
        content = sanitize_generated_post(content, topic)
        content = apply_brand_signature(content)
        normalized = normalize_text(content)

        if not normalized:
            continue

        if best_fallback is None:
            best_fallback = (extract_title(content), content, topic)

        if follows_style_rules(content):
            return extract_title(content), content, topic

    if best_fallback is not None:
        return best_fallback

    raise RuntimeError("No se pudo generar contenido util.")


def save_post(title: str, body: str, topic: str) -> None:
    conn = get_db()
    with conn:
        conn.execute(
            """
            INSERT INTO published_posts(created_at, topic, title, body, normalized)
            VALUES(?, ?, ?, ?, ?)
            """,
            (datetime.now().isoformat(timespec="seconds"), topic, title, body, normalize_text(body)),
        )


def is_authorized(update: Update) -> bool:
    if not AUTHORIZED_USER_ID:
        return True
    if not update.effective_user:
        return False
    return str(update.effective_user.id) == AUTHORIZED_USER_ID


async def ensure_authorized(update: Update) -> bool:
    if is_authorized(update):
        return True
    if update.message:
        await update.message.reply_text("No autorizado para este comando.")
    return False


def parse_command_text(update: Update) -> str:
    if not update.message or not update.message.text:
        return ""
    text = update.message.text.strip()
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Bot listo. Comandos: /reset /topics /set_topics /set_mode /set_focus /clear_focus /set_signature /set_length /start_daily /stop_daily /status /post_now"
    )


async def topics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    catalog = "\n".join(f"- {t}" for t in TOPIC_CATALOG)
    active = "\n".join(f"- {t}" for t in get_topic_pool())
    await update.message.reply_text(
        f"Catalogo disponible:\n{catalog}\n\nTemas activos:\n{active}"
    )


async def set_topics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    raw = parse_command_text(update)
    if not raw:
        await update.message.reply_text("Uso: /set_topics phrasal verbs, collocations, slang")
        return

    requested = [x.strip().lower() for x in raw.split(",") if x.strip()]
    if not requested:
        await update.message.reply_text("No detecte temas validos.")
        return

    valid = [t for t in requested if t in TOPIC_CATALOG]
    invalid = [t for t in requested if t not in TOPIC_CATALOG]

    if not valid:
        await update.message.reply_text("Ningun tema coincide con el catalogo. Usa /topics para ver opciones.")
        return

    set_topic_pool(valid)

    msg = "Temas activos actualizados:\n" + "\n".join(f"- {t}" for t in valid)
    if invalid:
        msg += "\n\nIgnorados (no existen en catalogo):\n" + "\n".join(f"- {t}" for t in invalid)

    await update.message.reply_text(msg)


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    mode = parse_command_text(update).lower()
    if mode not in {"rotate", "random"}:
        await update.message.reply_text("Uso: /set_mode rotate   o   /set_mode random")
        return

    set_setting("topic_mode", mode)
    await update.message.reply_text(f"Modo de tema actualizado a: {mode}")


async def set_focus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    topic = parse_command_text(update).lower()
    if topic not in TOPIC_CATALOG:
        await update.message.reply_text("Tema no valido. Usa /topics para ver el catalogo.")
        return

    set_setting("fixed_topic", topic)
    await update.message.reply_text(f"Foco fijo activado: {topic}")


async def clear_focus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    set_setting("fixed_topic", "")
    await update.message.reply_text("Foco fijo desactivado. Se usara rotacion o random.")



async def set_signature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    signature = parse_command_text(update)
    if not signature:
        await update.message.reply_text("Uso: /set_signature - Jesus | Quickingles")
        return

    set_setting("brand_signature", signature)
    await update.message.reply_text(f"Firma actualizada: {signature}")


async def set_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    length = parse_command_text(update).lower()
    if length not in {"short", "medium", "long"}:
        await update.message.reply_text("Uso: /set_length short   o   /set_length medium   o   /set_length long")
        return

    set_setting("post_length", length)
    await update.message.reply_text(f"Longitud de posts actualizada a: {length}")
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    memory = load_memory()
    chat_id = str(update.effective_chat.id)
    memory[chat_id] = []
    save_memory(memory)
    await update.message.reply_text("Memoria del chat reiniciada.")


async def start_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    if not CHANNEL_ID:
        await update.message.reply_text("Falta TELEGRAM_CHANNEL_ID en variables de entorno.")
        return
    set_setting("daily_enabled", "1")
    await update.message.reply_text("Publicacion programada activada.")


async def stop_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    set_setting("daily_enabled", "0")
    await update.message.reply_text("Publicacion programada desactivada.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) AS total FROM published_posts").fetchone()
    posts = row["total"] if row else 0

    enabled = "ON" if is_daily_enabled() else "OFF"
    channel = CHANNEL_ID or "(sin configurar)"
    mode = get_topic_mode()
    fixed = get_fixed_topic() or "(ninguno)"
    pool = ", ".join(get_topic_pool())
    post_length = get_post_length()
    signature = get_brand_signature() or "(sin firma)"
    await update.message.reply_text(
        "Estado diario: "
        f"{enabled}\nCanal: {channel}\nDias: {DAILY_POST_DAYS}\nHora: {DAILY_POST_HOUR:02d}:{DAILY_POST_MINUTE:02d} ({TIMEZONE})\n"
        f"Modo temas: {mode}\nFoco fijo: {fixed}\nLongitud: {post_length}\nFirma: {signature}\nPool activo: {pool}\nPosts guardados: {posts}"
    )



async def _post_now_background(context: ContextTypes.DEFAULT_TYPE, requester_chat_id: int) -> None:
    try:
        title, content, topic = await asyncio.to_thread(generate_unique_post)
        await context.bot.send_message(chat_id=CHANNEL_ID, text=content)
        save_post(title, content, topic)
        await context.bot.send_message(chat_id=requester_chat_id, text=f"Post publicado en canal. Tema: {topic}")
    except Exception as exc:
        await context.bot.send_message(chat_id=requester_chat_id, text=f"Error publicando: {exc}")
async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    if not CHANNEL_ID:
        await update.message.reply_text("Falta TELEGRAM_CHANNEL_ID en variables de entorno.")
        return

    await update.message.reply_text("Generando post... te aviso en cuanto se publique.")
    context.application.create_task(_post_now_background(context, update.effective_chat.id))


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_input = update.message.text.strip()
    if not user_input:
        return

    chat_id = str(update.effective_chat.id)
    memory = load_memory()
    history = memory.get(chat_id, [])

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
            {"role": "user", "content": user_input}
        ]
        answer = await asyncio.to_thread(ask_ollama, messages)
    except Exception as exc:
        await update.message.reply_text(f"Error con Ollama: {exc}")
        return

    history.extend(
        [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": answer},
        ]
    )
    memory[chat_id] = history[-MAX_HISTORY_MESSAGES:]
    save_memory(memory)

    await update.message.reply_text(answer)


async def scheduled_publish(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_daily_enabled() or not CHANNEL_ID:
        return

    try:
        title, content, topic = await asyncio.to_thread(generate_unique_post)
        await context.bot.send_message(chat_id=CHANNEL_ID, text=content)
        save_post(title, content, topic)
        print(f"Publicado tema: {topic}")
    except Exception as exc:
        print(f"Error en publicacion programada: {exc}")


def setup_daily_job(app: Application) -> None:
    if not app.job_queue:
        raise RuntimeError("JobQueue no disponible. Reinstala dependencias y prueba de nuevo.")

    for job in app.job_queue.get_jobs_by_name(DAILY_JOB_NAME):
        job.schedule_removal()

    tz = ZoneInfo(TIMEZONE)
    app.job_queue.run_custom(
        scheduled_publish,
        job_kwargs={
            "trigger": "cron",
            "day_of_week": DAILY_POST_DAYS,
            "hour": DAILY_POST_HOUR,
            "minute": DAILY_POST_MINUTE,
            "timezone": tz,
        },
        name=DAILY_JOB_NAME,
    )


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en variables de entorno.")

    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("topics", topics))
    app.add_handler(CommandHandler("set_topics", set_topics))
    app.add_handler(CommandHandler("set_mode", set_mode))
    app.add_handler(CommandHandler("set_focus", set_focus))
    app.add_handler(CommandHandler("clear_focus", clear_focus))
    app.add_handler(CommandHandler("set_signature", set_signature))
    app.add_handler(CommandHandler("set_length", set_length))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("start_daily", start_daily))
    app.add_handler(CommandHandler("stop_daily", stop_daily))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("post_now", post_now))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    setup_daily_job(app)

    print(f"Bot de Telegram activo con Ollama ({OLLAMA_MODEL}).")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()

























































