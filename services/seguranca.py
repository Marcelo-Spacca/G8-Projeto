import hashlib
import hmac
import os

# Parâmetros do scrypt (biblioteca padrão do Python). Mudar estes valores
# invalida as senhas já guardadas.
_N, _R, _P = 2**14, 8, 1


def gerar_hash(senha):
    sal = os.urandom(16)
    h = hashlib.scrypt(senha.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P)
    return f"{sal.hex()}${h.hex()}"


def confere_senha(senha, guardado):
    try:
        sal_hex, h_hex = guardado.split("$")
        esperado = bytes.fromhex(h_hex)
        h = hashlib.scrypt(
            senha.encode("utf-8"), salt=bytes.fromhex(sal_hex), n=_N, r=_R, p=_P
        )
    except ValueError:
        return False
    return hmac.compare_digest(h, esperado)
