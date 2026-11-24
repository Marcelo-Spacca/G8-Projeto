from repository.models.base import Modelo, agora


class Relatorio(Modelo):
    """1:1 com a pesquisa: o id do documento é o id da pesquisa."""

    COLECAO = "relatorios"
    CAMPOS = {"data_geracao": agora, "pesquisa_id": None}
    RELACOES = {"pesquisa": None}
