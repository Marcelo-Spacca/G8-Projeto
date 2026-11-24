"""O mesmo conjunto de testes roda contra o MemoryStore e contra o FirestoreStore.

O FirestoreStore roda contra um cliente falso (FirestoreFalso, abaixo) que imita a parte da
biblioteca google-cloud-firestore que o programa usa, inclusive os limites reais (500 operações por
lote, 30 valores no filtro 'in', lote tudo-ou-nada, datas com fuso, erros AlreadyExists/NotFound).

Para rodar também contra o emulador oficial do Firebase (precisa de Java e firebase-tools):
    firebase emulators:start --only firestore        (em outro terminal)
    FIRESTORE_EMULATOR_HOST=localhost:8080 pytest tests/test_armazenamento_contrato.py
"""
import os
import uuid
from datetime import datetime, timezone

import pytest
from google.api_core import exceptions as erros

from repository.armazenamento import Duplicado, ErroDeIntegridade, FirestoreStore, MemoryStore


# ---------------------------------------------------------------------------- cliente falso
class _Snap:
    def __init__(self, id_, dados):
        self.id, self._dados = id_, dados

    @property
    def exists(self):
        return self._dados is not None

    def to_dict(self):
        return None if self._dados is None else dict(self._dados)


class _Ref:
    def __init__(self, banco, colecao, id_):
        self.banco, self.colecao, self.id = banco, colecao, id_

    def get(self):
        return _Snap(self.id, self.banco.docs.get(self.colecao, {}).get(self.id))


class _Consulta:
    def __init__(self, banco, colecao, filtros=()):
        self.banco, self.colecao, self.filtros = banco, colecao, tuple(filtros)

    def where(self, *, filter):  # só a forma nova (filter=FieldFilter) é aceita, como no uso real
        if filter.op_string == "in" and len(filter.value) > 30:
            raise erros.InvalidArgument("'in' aceita no máximo 30 valores")
        return _Consulta(self.banco, self.colecao, self.filtros + (filter,))

    def document(self, id_):
        return _Ref(self.banco, self.colecao, id_)

    def stream(self):
        for id_, dados in list(self.banco.docs.get(self.colecao, {}).items()):
            if all(_confere(dados, f) for f in self.filtros):
                yield _Snap(id_, dados)


def _confere(dados, filtro):
    valor = dados.get(filtro.field_path)
    if filtro.op_string == "==":
        return valor == filtro.value
    if filtro.op_string == "in":
        return valor in filtro.value
    raise AssertionError(f"operador não usado pelo programa: {filtro.op_string}")


def _guardar(dados):
    """O Firestore guarda datas em UTC; uma data sem fuso é tratada como UTC."""
    return {
        k: (v.replace(tzinfo=timezone.utc) if isinstance(v, datetime) and v.tzinfo is None else v)
        for k, v in dados.items()
    }


class _Lote:
    def __init__(self, banco):
        self.banco, self.ops = banco, []

    def create(self, ref, dados):
        self.ops.append(("create", ref, dados))

    def set(self, ref, dados):
        self.ops.append(("set", ref, dados))

    def update(self, ref, dados):
        self.ops.append(("update", ref, dados))

    def delete(self, ref):
        self.ops.append(("delete", ref, None))

    def commit(self):
        if len(self.ops) > 500:
            raise erros.InvalidArgument("lote com mais de 500 operações")
        copia = {c: dict(d) for c, d in self.banco.docs.items()}
        for tipo, ref, dados in self.ops:
            docs = copia.setdefault(ref.colecao, {})
            if tipo == "create":
                if ref.id in docs:
                    raise erros.AlreadyExists(f"{ref.colecao}/{ref.id}")
                docs[ref.id] = _guardar(dados)
            elif tipo == "set":
                docs[ref.id] = _guardar(dados)
            elif tipo == "update":
                if ref.id not in docs:
                    raise erros.NotFound(f"{ref.colecao}/{ref.id}")
                docs[ref.id] = {**docs[ref.id], **_guardar(dados)}
            else:
                docs.pop(ref.id, None)
        self.banco.docs = copia  # tudo ou nada
        self.banco.lotes.append(len(self.ops))


class FirestoreFalso:
    def __init__(self):
        self.docs, self.lotes = {}, []

    def collection(self, nome):
        return _Consulta(self, nome)

    def get_all(self, refs):
        return [r.get() for r in refs]

    def batch(self):
        return _Lote(self)


# ---------------------------------------------------------------------------- as duas lojas
def _opcoes():
    opcoes = ["memoria", "firestore_falso"]
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        opcoes.append("emulador")
    return opcoes


@pytest.fixture(params=_opcoes())
def loja(request):
    if request.param == "memoria":
        return MemoryStore()
    if request.param == "firestore_falso":
        return FirestoreStore(FirestoreFalso())
    from google.cloud import firestore

    return FirestoreStore(firestore.Client(project="projeto-local"))


@pytest.fixture
def col(loja):
    """Nome de coleção exclusivo do teste (no emulador, evita misturar com outros testes)."""
    return f"t{uuid.uuid4().hex[:10]}"


def test_criar_obter_e_apagar(loja, col):
    loja.criar(col, "a", {"n": 1, "txt": "ação ✓"})
    assert loja.obter(col, "a") == {"n": 1, "txt": "ação ✓", "id": "a"}
    assert loja.obter(col, "b") is None
    loja.apagar(col, "a")
    assert loja.obter(col, "a") is None
    loja.apagar(col, "a")  # apagar o que não existe não é erro


def test_criar_repetido_e_duplicado(loja, col):
    loja.criar(col, "a", {"n": 1})
    with pytest.raises(Duplicado):
        loja.criar(col, "a", {"n": 2})
    assert loja.obter(col, "a")["n"] == 1


def test_atualizar_muda_so_os_campos_dados(loja, col):
    loja.criar(col, "a", {"n": 1, "m": 2})
    loja.atualizar(col, "a", {"n": 10, "m": None})
    assert loja.obter(col, "a") == {"n": 10, "m": None, "id": "a"}
    with pytest.raises(ErroDeIntegridade):
        loja.atualizar(col, "naoexiste", {"n": 1})


def test_lote_e_tudo_ou_nada(loja, col):
    loja.criar(col, "a", {"n": 1})
    with pytest.raises(Duplicado):
        loja.lote().criar(col, "b", {"n": 2}).criar(col, "a", {"n": 3}).confirmar()
    assert loja.obter(col, "b") is None and loja.obter(col, "a")["n"] == 1
    with pytest.raises(ErroDeIntegridade):
        loja.lote().criar(col, "c", {"n": 2}).atualizar(col, "x", {"n": 3}).confirmar()
    assert loja.obter(col, "c") is None


def test_gravar_substitui_o_documento_inteiro(loja, col):
    loja.criar(col, "a", {"n": 1, "m": 2})
    loja.lote().gravar(col, "a", {"n": 5}).confirmar()
    assert loja.obter(col, "a") == {"n": 5, "id": "a"}


def test_consultar_por_igualdade(loja, col):
    for i, cor in enumerate(["azul", "verde", "azul"]):
        loja.criar(col, f"d{i}", {"cor": cor, "grupo_id": "g" if i < 2 else "h"})
    assert {d["id"] for d in loja.consultar(col, cor="azul")} == {"d0", "d2"}
    assert {d["id"] for d in loja.consultar(col, cor="azul", grupo_id="g")} == {"d0"}
    assert len(loja.consultar(col)) == 3


def test_campos_terminados_em_id_aceitam_numero_e_texto(loja, col):
    loja.criar(col, "a", {"dono_id": "7"})
    assert [d["id"] for d in loja.consultar(col, dono_id=7)] == ["a"]
    assert [d["id"] for d in loja.consultar_em(col, "dono_id", [7, 8])] == ["a"]
    loja.atualizar(col, "a", {"dono_id": 9})
    assert loja.obter(col, "a")["dono_id"] == "9"


def test_consultar_em_com_mais_de_30_valores(loja, col):
    for i in range(75):
        loja.criar(col, f"d{i}", {"k": f"v{i}", "par": i % 2 == 0})
    achados = loja.consultar_em(col, "k", [f"v{i}" for i in range(75)])
    assert len(achados) == 75 and len({d["id"] for d in achados}) == 75
    so_pares = loja.consultar_em(col, "k", [f"v{i}" for i in range(75)], par=True)
    assert len(so_pares) == 38
    assert loja.consultar_em(col, "k", []) == []


def test_obter_varios(loja, col):
    loja.criar(col, "a", {"n": 1})
    loja.criar(col, "b", {"n": 2})
    achados = loja.obter_varios(col, ["a", "b", "z", None, "a"])
    assert {k: v["n"] for k, v in achados.items()} == {"a": 1, "b": 2}
    assert loja.obter_varios(col, []) == {}


def test_datas_voltam_como_foram_gravadas(loja, col):
    momento = datetime(2026, 3, 1, 10, 30, 15, 123456)  # sem fuso, horário do computador
    loja.criar(col, "a", {"quando": momento, "nunca": None})
    lido = loja.obter(col, "a")
    assert lido["quando"] == momento and lido["quando"].tzinfo is None and lido["nunca"] is None


def test_lote_grande_passa_de_500_operacoes(loja, col):
    lote = loja.lote()
    for i in range(1234):
        lote.criar(col, f"d{i:04d}", {"i": i})
    lote.confirmar()
    assert len(loja.consultar(col)) == 1234
    lote = loja.lote()
    for i in range(1234):
        lote.apagar(col, f"d{i:04d}")
    lote.confirmar()
    assert loja.consultar(col) == []


def test_lote_vazio_nao_faz_nada(loja, col):
    loja.lote().confirmar()


def test_firestore_falso_divide_o_lote_em_pedacos_de_500():
    falso = FirestoreFalso()
    loja = FirestoreStore(falso)
    lote = loja.lote()
    for i in range(1234):
        lote.criar("x", str(i), {"i": i})
    lote.confirmar()
    assert falso.lotes == [500, 500, 234]


def test_programa_inteiro_roda_sobre_o_firestore_falso():
    """Os dados de exemplo passam por todos os services e repositórios, agora gravando pelo
    FirestoreStore (ids de 19 dígitos, datas com fuso, lotes) em vez do MemoryStore."""
    from repository import armazenamento
    from scripts import popular_exemplo
    from services.revisao_service import RevisaoService
    from services.sessao import sessao
    from services.turma_service import TurmaService
    from services.usuario_service import UsuarioService

    armazenamento.usar(FirestoreStore(FirestoreFalso()))
    popular_exemplo.popular()
    UsuarioService().entrar("marina@exemplo.com", "senha123")
    turmas = TurmaService().listar_do_professor()
    assert [t.nome for t in turmas] == ["Banco de Dados", "Projeto 1, SI 26.2"]  # mais nova primeiro
    pesquisas = RevisaoService().listar_todas()
    assert {p.status for p in pesquisas} == {"em_andamento", "entregue", "concluida"}
    assert pesquisas[0].data_entrega is None or pesquisas[0].data_entrega.tzinfo is None  # datas sem fuso
    completa = TurmaService().obter_do_professor(next(t.id for t in turmas if t.codigo == "PROJ01"))
    assert len(completa.alunos) == 5 and len(completa.grupos) == 2
    sessao.encerrar()
    popular_exemplo.limpar()
    assert armazenamento.loja().consultar("usuarios") == []
    assert armazenamento.loja().consultar("pesquisas") == [] and armazenamento.loja().consultar("unicos") == []
