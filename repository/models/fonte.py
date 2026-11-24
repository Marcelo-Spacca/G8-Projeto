from repository.models.base import Modelo


class Fonte(Modelo):
    COLECAO = "fontes"
    CAMPOS = {
        "referencia": None,
        "link": None,  # RF15: endereço da fonte, opcional
        "status": "nao_verificada",  # nao_verificada | verificada | incorreta
        "anotacao_correcao": None,
        "data_verificacao": None,
        "julgada_pelo_professor": False,
        "interacao_id": None,
    }
    RELACOES = {"interacao": None, "trechos": list}
