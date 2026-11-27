"""Abre o programa: sobe o servidor e o navegador.

    python main.py

Precisa do front já compilado (cd frontend && npm install && npm run build). Para mexer no front
com recarga automática, veja o README (npm run dev)."""
import threading
import webbrowser
from pathlib import Path

import uvicorn

PORTA = 8000


def main():
    if not (Path(__file__).parent / "frontend" / "dist" / "index.html").is_file():
        print("O front ainda não foi compilado. Rode:  cd frontend  &&  npm install  &&  npm run build")
        return 1
    threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{PORTA}")).start()
    uvicorn.run("api.main:app", host="127.0.0.1", port=PORTA, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
