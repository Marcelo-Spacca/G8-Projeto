"""Sobe o programa em modo demonstração: sem Firebase, com dados de exemplo só na memória.

    python -m scripts.demo            # http://127.0.0.1:8000  (entre com ana@exemplo.com / senha123)

Tudo some quando você fecha o servidor. Serve para ver o programa funcionando em 1 minuto."""
import os
import sys

os.environ["REGISTRO_IA_BANCO"] = "memoria"

import uvicorn  # noqa: E402

from scripts import popular_exemplo  # noqa: E402


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    popular_exemplo.popular()
    print(f"\nModo demonstração: abra http://127.0.0.1:{porta}")
    print("  aluno:     ana@exemplo.com   /  senha123")
    print("  professor: marina@exemplo.com  /  senha123\n")
    uvicorn.run("api.main:app", host="127.0.0.1", port=porta, log_level="warning")


if __name__ == "__main__":
    main()
