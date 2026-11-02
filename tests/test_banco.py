import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from repository.database import Session, engine
from repository.interacao_repository import InteracaoRepository
from repository.models import Fonte, Interacao, Pesquisa, Relatorio, Trecho, Usuario
from repository.pesquisa_repository import PesquisaRepository
from repository.usuario_repository import UsuarioRepository


def novo_aluno(email="ana@x.com"):
    return UsuarioRepository().salvar(Usuario(nome="Ana", email=email, senha_hash="h", tipo="aluno"))


def nova_pesquisa(aluno, titulo="Tema"):
    return PesquisaRepository().salvar(Pesquisa(titulo=titulo, objetivo="Obj", aluno_id=aluno.id))


def nova_interacao(pesquisa, pergunta="q"):
    return InteracaoRepository().salvar(
        Interacao(ferramenta_ia="IA", pergunta=pergunta, resposta="r", pesquisa_id=pesquisa.id)
    )


def contar(modelo):
    with Session() as s:
        return s.scalar(select(func.count()).select_from(modelo))


# ---------------------------------------------------------------- estrutura
def test_as_7_tabelas_existem():
    esperadas = {"usuario", "turma", "pesquisa", "interacao", "fonte", "trecho", "relatorio"}
    assert esperadas <= set(inspect(engine).get_table_names())


# ---------------------------------------------------------------- usuário
def test_salvar_e_buscar_usuario_por_email():
    salvo = novo_aluno()
    assert salvo.id is not None
    achado = UsuarioRepository().buscar_por_email("ana@x.com")
    assert achado.id == salvo.id and achado.nome == "Ana"
    assert UsuarioRepository().buscar_por_email("nao@x.com") is None


def test_banco_barra_email_repetido():
    novo_aluno("a@x.com")
    with pytest.raises(IntegrityError):
        novo_aluno("a@x.com")


def test_banco_barra_tipo_de_usuario_invalido():
    with pytest.raises(IntegrityError):
        UsuarioRepository().salvar(Usuario(nome="X", email="x@x.com", senha_hash="h", tipo="admin"))


# ---------------------------------------------------------------- pesquisa
def test_pesquisa_nasce_em_andamento_com_data():
    p = nova_pesquisa(novo_aluno())
    assert p.status == "em_andamento" and p.data_criacao is not None and p.data_conclusao is None


def test_banco_barra_status_de_pesquisa_invalido():
    aluno = novo_aluno()
    with pytest.raises(IntegrityError):
        PesquisaRepository().salvar(Pesquisa(titulo="T", objetivo="O", status="pausada", aluno_id=aluno.id))


def test_banco_barra_pesquisa_de_aluno_inexistente():
    with pytest.raises(IntegrityError):
        PesquisaRepository().salvar(Pesquisa(titulo="T", objetivo="O", aluno_id=999))


def test_listar_pesquisas_do_aluno_mais_recente_primeiro():
    ana, bia = novo_aluno("a@x.com"), novo_aluno("b@x.com")
    nova_pesquisa(ana, "primeira")
    nova_pesquisa(bia, "da bia")
    nova_pesquisa(ana, "segunda")
    titulos = [p.titulo for p in PesquisaRepository().listar_por_aluno(ana.id)]
    assert titulos == ["segunda", "primeira"]


def test_buscar_pesquisa_por_id():
    p = nova_pesquisa(novo_aluno())
    assert PesquisaRepository().buscar_por_id(p.id).titulo == "Tema"
    assert PesquisaRepository().buscar_por_id(999) is None


# ---------------------------------------------------------------- interação
def test_banco_barra_interacao_de_pesquisa_inexistente():
    with pytest.raises(IntegrityError):
        InteracaoRepository().salvar(Interacao(ferramenta_ia="IA", pergunta="q", resposta="r", pesquisa_id=999))


def test_listar_interacoes_em_ordem_de_registro():
    p = nova_pesquisa(novo_aluno())
    nova_interacao(p, "um")
    nova_interacao(p, "dois")
    nova_interacao(p, "tres")
    assert [i.pergunta for i in InteracaoRepository().listar_por_pesquisa(p.id)] == ["um", "dois", "tres"]


def test_interacoes_so_da_pesquisa_pedida():
    aluno = novo_aluno()
    p1, p2 = nova_pesquisa(aluno, "a"), nova_pesquisa(aluno, "b")
    nova_interacao(p1, "da a")
    nova_interacao(p2, "da b")
    assert [i.pergunta for i in InteracaoRepository().listar_por_pesquisa(p1.id)] == ["da a"]


def test_texto_longo_e_acentos_sao_preservados():
    aluno = novo_aluno()
    p = PesquisaRepository().salvar(Pesquisa(titulo="Ação ✓", objetivo="Objetivo com acentuação", aluno_id=aluno.id))
    longo = "áéíóú ção " * 3000
    nova = InteracaoRepository().salvar(Interacao(ferramenta_ia="IA", pergunta=longo, resposta=longo, pesquisa_id=p.id))
    assert InteracaoRepository().listar_por_pesquisa(p.id)[0].resposta == longo
    assert PesquisaRepository().buscar_por_id(p.id).titulo == "Ação ✓"
    assert nova.id is not None


# ---------------------------------------------------------------- fonte, trecho, relatório
def test_fonte_nasce_nao_verificada():
    i = nova_interacao(nova_pesquisa(novo_aluno()))
    with Session() as s:
        f = Fonte(referencia="Silva (2023)", interacao_id=i.id)
        s.add(f)
        s.commit()
        assert f.status == "nao_verificada" and f.data_verificacao is None


def test_banco_barra_status_de_fonte_invalido():
    i = nova_interacao(nova_pesquisa(novo_aluno()))
    with Session() as s:
        s.add(Fonte(referencia="x", status="talvez", interacao_id=i.id))
        with pytest.raises(IntegrityError):
            s.commit()


def test_so_um_relatorio_por_pesquisa():
    p = nova_pesquisa(novo_aluno())
    with Session() as s:
        s.add(Relatorio(pesquisa_id=p.id))
        s.commit()
    with Session() as s:
        s.add(Relatorio(pesquisa_id=p.id))
        with pytest.raises(IntegrityError):
            s.commit()


# ---------------------------------------------------------------- exclusão em cascata
def _montar_arvore():
    aluno = novo_aluno()
    p = nova_pesquisa(aluno)
    i = nova_interacao(p)
    with Session() as s:
        f = Fonte(referencia="ref", interacao_id=i.id)
        f.trechos.append(Trecho(trecho_citado="trecho"))
        s.add_all([f, Relatorio(pesquisa_id=p.id)])
        s.commit()
    return aluno, p


def _contagens():
    return [contar(m) for m in (Interacao, Fonte, Trecho, Relatorio)]


def test_apagar_pesquisa_pelo_orm_apaga_tudo_que_depende_dela():
    _, p = _montar_arvore()
    assert _contagens() == [1, 1, 1, 1]
    with Session() as s:
        s.delete(s.get(Pesquisa, p.id))
        s.commit()
    assert _contagens() == [0, 0, 0, 0] and contar(Pesquisa) == 0


def test_apagar_pesquisa_por_sql_puro_tambem_cascateia():
    """Prova que o ON DELETE CASCADE está no banco, não só no Python."""
    _, p = _montar_arvore()
    with engine.begin() as c:
        c.execute(text("DELETE FROM pesquisa WHERE id = :i"), {"i": p.id})
    assert _contagens() == [0, 0, 0, 0]


def test_apagar_usuario_apaga_suas_pesquisas():
    aluno, _ = _montar_arvore()
    with engine.begin() as c:
        c.execute(text("DELETE FROM usuario WHERE id = :i"), {"i": aluno.id})
    assert contar(Pesquisa) == 0 and _contagens() == [0, 0, 0, 0]
