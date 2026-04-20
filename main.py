import json
import os
from pathlib import Path

import requests


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
SYSTEM_PROMPT = "Eres un asistente útil y conciso."
MEMORY_FILE = Path("memory.json")
MAX_HISTORY_MESSAGES = 20


def load_memory() -> list[dict]:
    if not MEMORY_FILE.exists():
        return []

    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        pass

    return []


def save_memory(messages: list[dict]) -> None:
    MEMORY_FILE.write_text(
        json.dumps(messages[-MAX_HISTORY_MESSAGES:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_agent(user_input: str, history: list[dict]) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": user_input}
    ]

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()

    return data["message"]["content"]


def main() -> None:
    print(
        f"Agente local listo con Ollama ({MODEL}). "
        "Escribe tu mensaje (o 'salir', '/reset')."
    )
    history = load_memory()

    while True:
        user_input = input("Tu> ").strip()

        if not user_input:
            continue

        if user_input.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break

        if user_input.lower() == "/reset":
            history = []
            save_memory(history)
            print("Memoria reiniciada.\n")
            continue

        try:
            answer = run_agent(user_input, history)
            history.extend(
                [
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": answer},
                ]
            )
            save_memory(history)
            print(f"Agente> {answer}\n")
        except Exception as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    main()
