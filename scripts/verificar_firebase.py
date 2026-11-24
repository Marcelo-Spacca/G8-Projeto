"""Confere se o programa consegue falar com o Firebase (Firestore).

    python -m scripts.verificar_firebase

Grava, lê e apaga um documento de teste na coleção 'diagnostico'. Não mexe em nenhum dado real.
Não há tabelas para criar: o Firestore cria as coleções sozinho na primeira gravação.
"""
import sys

from repository import armazenamento


def verificar():
    loja = armazenamento.loja()
    id_ = loja.novo_id()
    loja.lote().gravar("diagnostico", id_, {"mensagem": "ok", "quando": armazenamento.agora()}).confirmar()
    doc = loja.obter("diagnostico", id_)
    loja.apagar("diagnostico", id_)
    if not doc or doc.get("mensagem") != "ok":
        raise RuntimeError("O documento de teste não voltou como foi gravado.")


def main():
    try:
        verificar()
    except armazenamento.ErroDeConfiguracao as erro:
        print(f"Configuração incompleta:\n  {erro}")
        return 1
    except Exception as erro:  # credencial inválida, Firestore não criado, sem internet...
        print(f"Não consegui usar o Firestore: {type(erro).__name__}: {erro}")
        print("Confira o passo a passo do README (seção Firebase): projeto, banco Firestore e chave JSON.")
        return 1
    print("Tudo certo: o programa conseguiu gravar, ler e apagar um documento no Firestore.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
