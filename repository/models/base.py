"""Base das classes de dados (o que antes eram os models do SQLAlchemy).

Cada classe declara:
  COLECAO   nome da coleção no Firestore
  CAMPOS    {campo: valor padrão (ou função que o calcula)}  -> o que é gravado no documento
  RELACOES  {atributo: list | None}  -> objetos ligados, preenchidos pelos repositórios quando a
            tela precisa deles (nada é gravado; ficam vazios/None até alguém carregar)
"""
from repository.armazenamento import agora, normalizar_ids

__all__ = ["Modelo", "agora"]


class Modelo:
    COLECAO = ""
    CAMPOS = {}
    RELACOES = {}

    def __init__(self, **dados):
        self.id = dados.pop("id", None)
        for nome, padrao in self.CAMPOS.items():
            valor = dados.pop(nome) if nome in dados else (padrao() if callable(padrao) else padrao)
            setattr(self, nome, valor)
        for nome, tipo in self.RELACOES.items():
            setattr(self, nome, dados.pop(nome) if nome in dados else ([] if tipo is list else None))
        if dados:
            raise TypeError(f"{type(self).__name__}: campo(s) desconhecido(s): {', '.join(dados)}")

    def para_dict(self):
        """O que vai para o documento (sem o id, que é o nome do documento)."""
        return normalizar_ids({nome: getattr(self, nome) for nome in self.CAMPOS})

    @classmethod
    def de_dict(cls, doc):
        campos = {nome: doc[nome] for nome in cls.CAMPOS if nome in doc}
        return cls(id=doc["id"], **campos)

    def __repr__(self):
        return f"<{type(self).__name__} id={self.id!r}>"
