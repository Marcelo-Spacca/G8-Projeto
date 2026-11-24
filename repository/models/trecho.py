from repository.models.base import Modelo


class Trecho(Modelo):
    COLECAO = "trechos"
    CAMPOS = {
        "trecho_citado": None,
        "localizacao": None,  # parágrafo/linha, opcional
        "fonte_id": None,
    }
    RELACOES = {"fonte": None}
