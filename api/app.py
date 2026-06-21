import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from api._bot import TELEGRAM_CHANNEL_ID, generate_post, is_authorized, send_message


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in {"", "/", "/api", "/api/telegram"}:
            self._send_json(200, {"ok": True, "service": "quickingles-content-bot"})
            return
        self._send_json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path != "/api/telegram":
            self._send_json(404, {"ok": False, "error": "not_found"})
            return

        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        chat_id = None

        try:
            update = json.loads(raw)
            message = update.get("message") or update.get("edited_message") or {}
            chat = message.get("chat") or {}
            user = message.get("from") or {}
            text = (message.get("text") or "").strip()
            chat_id = chat.get("id")

            if not chat_id or not text:
                self._send_json(200, {"ok": True})
                return

            if not is_authorized(user.get("id")):
                send_message(chat_id, "No autorizado para este comando.")
                self._send_json(200, {"ok": True})
                return

            command = text.split(maxsplit=1)[0].split("@", 1)[0].lower()

            if command == "/start":
                send_message(chat_id, "Bot listo. Comandos: /post_now /status")
            elif command == "/status":
                channel = TELEGRAM_CHANNEL_ID or "(sin configurar)"
                send_message(chat_id, f"Vercel activo. Canal de revision: {channel}")
            elif command == "/post_now":
                if not TELEGRAM_CHANNEL_ID:
                    send_message(chat_id, "Falta TELEGRAM_CHANNEL_ID en variables de entorno.")
                else:
                    send_message(chat_id, "Generando post... te aviso en cuanto se envie al canal de revision.")
                    content, topic = generate_post()
                    send_message(TELEGRAM_CHANNEL_ID, content)
                    send_message(chat_id, f"Post enviado a revision. Tema: {topic}")
            else:
                send_message(chat_id, "Comando disponible: /post_now")

            self._send_json(200, {"ok": True})
        except Exception as exc:
            try:
                if chat_id:
                    send_message(chat_id, f"Error: {exc}")
            finally:
                self._send_json(200, {"ok": False, "error": str(exc)})
