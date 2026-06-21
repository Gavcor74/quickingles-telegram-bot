import json
import os
from http.server import BaseHTTPRequestHandler

from api._bot import TELEGRAM_CHANNEL_ID, generate_post, local_schedule_matches_now, send_message


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_GET(self) -> None:
        cron_secret = os.getenv("CRON_SECRET", "").strip()
        auth = self.headers.get("authorization", "")
        provided = auth.removeprefix("Bearer ").strip()
        if cron_secret and provided != cron_secret:
            self._send_json(401, {"ok": False, "error": "unauthorized"})
            return

        if os.getenv("STRICT_DAILY_SCHEDULE", "0") == "1" and not local_schedule_matches_now():
            self._send_json(200, {"ok": True, "skipped": "outside configured local schedule"})
            return

        if not TELEGRAM_CHANNEL_ID:
            self._send_json(500, {"ok": False, "error": "missing TELEGRAM_CHANNEL_ID"})
            return

        try:
            content, topic = generate_post()
            send_message(TELEGRAM_CHANNEL_ID, content)
            self._send_json(200, {"ok": True, "topic": topic})
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})
