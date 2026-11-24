"""Testes da camada de dados (repositórios + armazenamento), sem passar pelos services.

Rodam contra o MemoryStore. O Firestore não tem chave estrangeira nem UNIQUE, então aqui se
confere o que o programa garante por conta própria: unicidade por id de documento, regras de
valor (status, tipo, dono da pesquisa) e exclusão em cascata."""
import uuid

import pytest

from repository import armazenamento
from repository.armazenamento import Duplicado, ErroDeIntegridade, MemoryStore
from repository.fonte_repository import FonteRepository
from repository.grupo_repository import GrupoRepository
from repository.interacao_repository import InteracaoRepository
from repository.models import Fonte, Interacao, Pesquisa, Relatorio, Trecho, Turma, Usuario
from repository.pesquisa_repository import PesquisaRepository
from repository.relatorio_repository import RelatorioRepository
from repository.turma_repository import TurmaRepository
from repository.usuario_repository import UsuarioRepository
from tests.apoio import contar


def novo_aluno(email="ana@x.com", nome="Ana"):
    return UsuarioRepository().salvar(Usuario(nome=nome, email=email, senha_hash="h", tipo="aluno"))


def nova_turma(nome="Cálculo", codigo=None, permite_grupos=False):
    codigo = codigo or uuid.uuid4().hex[:6].upper()
    repo = UsuarioRepository()
    professor = repo.buscar_por_email("prof@x.com") or repo.salvar(
        Usuario(nome="Prof", email="prof@x.com", senha_hash="h", tipo="professor")
    )
    return TurmaRepository().salvar(
        Turma(nome=nome, codigo=codigo, permite_grupos=permite_grupos, professor_id=professor.id)
    )


def nova_pesquisa(aluno, titulo="Tema", turma=None):
    turma = turma or nova_turma()
    return PesquisaRepository().salvar(
        Pesquisa(titulo=titulo, objetivo="Obj", aluno_id=aluno.id, turma_id=turma.id)
    )


def nova_interacao(pesquisa, pergunta="q"):
    return InteracaoRepository().salvar(
        Interacao(ferramenta_ia="IA", pergunta=pergunta, resposta="r", pesquisa_id=pesquisa.id)
    )


# ---------------------------------------------------------------- armazenamento (MemoryStore)
def test_lote_e_tudo_ou_nada():
    loja = MemoryStore()
    loja.criar("x", "1", {"a": 1})
    lote = loja.lote().criar("x", "2", {"a": 2}).criar("x", "1", {"a": 3})  # o segundo já existe
    with pytest.raises(Duplicado):
        lote.confirmar()
    assert loja.obter("x", "2") is None and loja.obter("x", "1")["a"] == 1


def test_atualizar_documento_que_nao_existe_falha():
    with pytest.raises(ErroDeIntegridade):
        MemoryStore().atualizar("x", "9", {"a": 1})


def test_consultas_por_igualdade_e_por_varios_valores():
    loja = MemoryStore()
    for i, cor in enumerate(["azul", "verde", "azul"], start=1):
        loja.criar("x", str(i), {"cor": cor, "dono_id": str(i)})
    assert {d["id"] for d in loja.consultar("x", cor="azul")} == {"1", "3"}
    assert {d["id"] for d in loja.consultar_em("x", "dono_id", [1, "2"])} == {"1", "2"}  # int vira texto
    assert loja.obter_varios("x", ["1", "9"]).keys() == {"1"}


def test_documentos_devolvidos_sao_copias():
    loja = MemoryStore()
    loja.criar("x", "1", {"lista": [1]})
    loja.obter("x", "1")["lista"].append(2)
    assert loja.obter("x", "1")["lista"] == [1]


def test_datas_de_firestore_viram_datas_sem_fuso():
    from datetime import datetime, timezone

    from repository.armazenamento import _da_nuvem, _para_nuvem

    local = datetime(2026, 3, 1, 10, 30, 15, 123456)
    nuvem = _para_nuvem({"d": local})["d"]
    assert nuvem.tzinfo is not None and nuvem.astimezone(timezone.utc) == nuvem
    assert _da_nuvem({"d": nuvem})["d"] == local  # ida e volta sem perder nada


def test_ids_do_firestore_crescem_com_o_tempo():
    from repository.armazenamento import FirestoreStore

    loja = FirestoreStore(cliente=None)
    ids = [loja.novo_id() for _ in range(2000)]
    assert ids == sorted(ids) and len(set(ids)) == 2000 and all(len(i) == 19 for i in ids)


# ---------------------------------------------------------------- usuário
def test_salvar_e_buscar_usuario_por_email():
    salvo = novo_aluno()
    assert salvo.id is not None
    achado = UsuarioRepository().buscar_por_email("ana@x.com")
    assert achado.id == salvo.id and achado.nome == "Ana"
    assert UsuarioRepository().buscar_por_id(salvo.id).email == "ana@x.com"
    assert UsuarioRepository().buscar_por_email("nao@x.com") is None


def test_email_repetido_e_barrado():
    novo_aluno("a@x.com")
    with pytest.raises(Duplicado):
        novo_aluno("a@x.com")
    assert contar("usuarios") == 1  # e a segunda tentativa não deixou nada pela metade


def test_tipo_de_usuario_invalido_e_barrado():
    with pytest.raises(ErroDeIntegridade):
        UsuarioRepository().salvar(Usuario(nome="X", email="x@x.com", senha_hash="h", tipo="admin"))
    assert contar("usuarios") == 0


def test_campo_desconhecido_no_modelo_e_erro():
    with pytest.raises(TypeError):
        Usuario(nome="X", emial="x@x.com")


# ---------------------------------------------------------------- pesquisa
def test_pesquisa_nasce_em_andamento_com_data():
    p = nova_pesquisa(novo_aluno())
    assert p.status == "em_andamento" and p.data_criacao is not None and p.data_conclusao is None


def test_status_de_pesquisa_invalido_e_barrado():
    aluno = novo_aluno()
    with pytest.raises(ErroDeIntegridade):
        PesquisaRepository().salvar(Pesquisa(titulo="T", objetivo="O", status="pausada", aluno_id=aluno.id))


def test_listar_pesquisas_do_aluno_mais_recente_primeiro():
    ana, bia = novo_aluno("a@x.com"), novo_aluno("b@x.com")
    turma = nova_turma()
    nova_pesquisa(ana, "primeira", turma)
    nova_pesquisa(bia, "da bia", turma)
    nova_pesquisa(ana, "segunda", turma)
    titulos = [p.titulo for p in PesquisaRepository().listar_por_aluno(ana.id, turma.id)]
    assert titulos == ["segunda", "primeira"]


def test_buscar_pesquisa_por_id():
    p = nova_pesquisa(novo_aluno())
    assert PesquisaRepository().buscar_por_id(p.id).titulo == "Tema"
    assert PesquisaRepository().buscar_por_id("999") is None
    assert PesquisaRepository().buscar_por_id(999) is None  # número também serve


def test_pesquisa_precisa_de_um_dono_aluno_ou_grupo():
    turma, ana = nova_turma(permite_grupos=True), novo_aluno()
    grupo_id = GrupoRepository().criar(turma.id, ana.id, "G", "T", "O")
    with pytest.raises(ErroDeIntegridade):  # sem dono
        PesquisaRepository().salvar(Pesquisa(titulo="T", objetivo="O", turma_id=turma.id))
    with pytest.raises(ErroDeIntegridade):  # dois donos
        PesquisaRepository().salvar(
            Pesquisa(titulo="T", objetivo="O", turma_id=turma.id, aluno_id=ana.id, grupo_id=grupo_id)
        )
    PesquisaRepository().salvar(Pesquisa(titulo="T", objetivo="O", turma_id=turma.id, grupo_id=grupo_id))
    with pytest.raises(Duplicado):  # um grupo só tem uma pesquisa
        PesquisaRepository().salvar(Pesquisa(titulo="T2", objetivo="O", turma_id=turma.id, grupo_id=grupo_id))


def test_pesquisa_salva_com_relatorio_cria_os_dois_juntos():
    aluno, turma = novo_aluno(), nova_turma()
    p = PesquisaRepository().salvar(
        Pesquisa(titulo="T", objetivo="O", aluno_id=aluno.id, turma_id=turma.id, relatorio=Relatorio())
    )
    assert RelatorioRepository().buscar_por_pesquisa(p.id).pesquisa_id == p.id
    assert contar("relatorios") == 1


def test_aceitar_pesquisa_fecha_interacoes_e_carimba_relatorio():
    p = nova_pesquisa(novo_aluno())
    nova_interacao(p)
    nova_interacao(p, "outra")
    PesquisaRepository().entregar(p.id)
    aceita = PesquisaRepository().aceitar(p.id)  # sem relatório: o aceitar cria
    assert aceita.status == "concluida" and aceita.data_conclusao is not None
    assert all(i.confirmada for i in InteracaoRepository().listar_por_pesquisa(p.id))
    assert RelatorioRepository().buscar_por_pesquisa(p.id) is not None


def test_garantir_relatorio_e_idempotente():
    p = nova_pesquisa(novo_aluno())
    r1, r2 = RelatorioRepository().garantir(p.id), RelatorioRepository().garantir(p.id)
    assert r1.id == r2.id and contar("relatorios") == 1


# ---------------------------------------------------------------- interação
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
    p = PesquisaRepository().salvar(
        Pesquisa(titulo="Ação ✓", objetivo="Objetivo com acentuação", aluno_id=aluno.id, turma_id="1")
    )
    longo = "áéíóú ção " * 3000
    nova = InteracaoRepository().salvar(Interacao(ferramenta_ia="IA", pergunta=longo, resposta=longo, pesquisa_id=p.id))
    assert InteracaoRepository().listar_por_pesquisa(p.id)[0].resposta == longo
    assert PesquisaRepository().buscar_por_id(p.id).titulo == "Ação ✓"
    assert nova.id is not None


# ---------------------------------------------------------------- fonte, trecho
def test_fonte_nasce_nao_verificada():
    i = nova_interacao(nova_pesquisa(novo_aluno()))
    f = FonteRepository().salvar(Fonte(referencia="Silva (2023)", interacao_id=i.id))
    achada = FonteRepository().buscar_por_id(f.id)
    assert achada.status == "nao_verificada" and achada.data_verificacao is None and not achada.julgada_pelo_professor
    assert achada.interacao.id == i.id and achada.trechos == []


def test_verificar_fonte_grava_trecho_e_perder_a_verificacao_apaga_o_trecho():
    i = nova_interacao(nova_pesquisa(novo_aluno()))
    f = FonteRepository().salvar(Fonte(referencia="x", interacao_id=i.id))
    repo = FonteRepository()
    repo.registrar_verificacao(f.id, "verificada", "ok", Trecho(trecho_citado="t", localizacao="§1"))
    assert [t.trecho_citado for t in repo.buscar_por_id(f.id).trechos] == ["t"]
    assert repo.buscar_por_id(f.id).data_verificacao is not None
    repo.registrar_verificacao(f.id, "incorreta", "não existe", None)
    achada = repo.buscar_por_id(f.id)
    assert achada.status == "incorreta" and achada.trechos == [] and contar("trechos") == 0


# ---------------------------------------------------------------- exclusão em cascata
def _montar_arvore():
    aluno = novo_aluno()
    p = nova_pesquisa(aluno)
    i = nova_interacao(p)
    f = FonteRepository().salvar(Fonte(referencia="ref", interacao_id=i.id))
    FonteRepository().adicionar_trecho(Trecho(trecho_citado="trecho", fonte_id=f.id))
    RelatorioRepository().garantir(p.id)
    return aluno, p


def _contagens():
    return [contar(c) for c in ("interacoes", "fontes", "trechos", "relatorios")]


def test_apagar_pesquisa_apaga_tudo_que_depende_dela():
    _, p = _montar_arvore()
    assert _contagens() == [1, 1, 1, 1]
    PesquisaRepository().excluir(p.id)
    assert _contagens() == [0, 0, 0, 0] and contar("pesquisas") == 0


def test_apagar_interacao_apaga_fontes_e_trechos():
    _, p = _montar_arvore()
    outra = nova_interacao(p, "fica")
    InteracaoRepository().excluir(InteracaoRepository().listar_por_pesquisa(p.id)[0].id)
    assert [i.id for i in InteracaoRepository().listar_por_pesquisa(p.id)] == [outra.id]
    assert contar("fontes") == 0 and contar("trechos") == 0


def test_apagar_usuario_apaga_suas_pesquisas_e_libera_o_email():
    aluno, _ = _montar_arvore()
    UsuarioRepository().excluir(aluno.id)
    assert contar("pesquisas") == 0 and _contagens() == [0, 0, 0, 0]
    assert UsuarioRepository().buscar_por_email("ana@x.com") is None
    novo_aluno("ana@x.com")  # o e-mail voltou a ficar livre


def test_apagar_cascata_grande_passa_de_500_operacoes():
    """Mais de 500 documentos: o lote é gravado em pedaços e nada fica para trás."""
    p = nova_pesquisa(novo_aluno())
    for n in range(260):
        FonteRepository().salvar(Fonte(referencia=f"f{n}", interacao_id=nova_interacao(p, f"q{n}").id))
    assert contar("fontes") == 260
    PesquisaRepository().excluir(p.id)
    assert contar("interacoes") == 0 and contar("fontes") == 0


# ---------------------------------------------------------------- turma, grupo
def test_codigo_de_turma_repetido_e_barrado_e_libera_ao_apagar():
    t = nova_turma(codigo="AAA111")
    assert TurmaRepository().codigo_existe("AAA111")
    with pytest.raises(Duplicado):
        nova_turma(nome="Outra", codigo="AAA111")
    assert contar("turmas") == 1
    TurmaRepository().excluir(t.id)
    assert not TurmaRepository().codigo_existe("AAA111")
    nova_turma(nome="Outra", codigo="AAA111")


def test_matricula_repetida_e_barrada():
    ana, turma = novo_aluno(), nova_turma()
    TurmaRepository().matricular(turma.id, ana.id)
    assert TurmaRepository().aluno_esta_na_turma(turma.id, ana.id)
    with pytest.raises(Duplicado):
        TurmaRepository().matricular(turma.id, ana.id)
    assert [a.nome for a in TurmaRepository().listar_alunos(turma.id)] == ["Ana"]


def test_pesquisa_do_grupo_nasce_com_o_segundo_integrante_e_so_uma_vez():
    turma, ana, bia, caio = nova_turma(permite_grupos=True), novo_aluno("a@x.com"), novo_aluno("b@x.com"), novo_aluno("c@x.com")
    repo = GrupoRepository()
    grupo_id = repo.criar(turma.id, ana.id, "G", "Título", "Objetivo")
    assert repo.buscar_por_id(grupo_id).pesquisa is None  # sozinha, a Ana não tem pesquisa do grupo
    repo.adicionar_integrante(grupo_id, bia.id)
    pesquisa = repo.buscar_por_id(grupo_id).pesquisa
    assert pesquisa.titulo == "Título" and pesquisa.de_grupo and contar("relatorios") == 1
    repo.adicionar_integrante(grupo_id, caio.id)  # o terceiro não cria outra
    assert contar("pesquisas") == 1
    with pytest.raises(Duplicado):  # integrante repetido
        repo.adicionar_integrante(grupo_id, caio.id)


def test_convite_aceito_entra_no_grupo_e_recusado_pode_ser_reaberto():
    turma, ana, bia = nova_turma(permite_grupos=True), novo_aluno("a@x.com"), novo_aluno("b@x.com")
    repo = GrupoRepository()
    grupo_id = repo.criar(turma.id, ana.id, "G", "T", "O")
    repo.convidar(grupo_id, [bia.id], ana.id)
    (convite,) = repo.convites_pendentes(bia.id, turma.id)
    assert convite.grupo.nome == "G" and convite.convidado_por.nome == "Ana"
    repo.responder_convite(convite.id, False)
    assert repo.convites_pendentes(bia.id, turma.id) == []
    repo.convidar(grupo_id, [bia.id], ana.id)  # reabre o recusado, sem duplicar
    assert contar("convites") == 1
    (convite,) = repo.convites_pendentes(bia.id, turma.id)
    repo.responder_convite(convite.id, True)
    assert repo.aluno_e_integrante(grupo_id, bia.id) and repo.buscar_por_id(grupo_id).pesquisa is not None
    assert [g.id for g in repo.listar_do_aluno(bia.id, turma.id)] == [grupo_id]


def test_apagar_turma_leva_tudo_junto():
    turma, ana, bia = nova_turma(permite_grupos=True), novo_aluno("a@x.com"), novo_aluno("b@x.com")
    p = nova_pesquisa(ana, turma=turma)
    nova_interacao(p)
    repo = GrupoRepository()
    grupo_id = repo.criar(turma.id, ana.id, "G", "T", "O")
    repo.convidar(grupo_id, [bia.id], ana.id)
    repo.adicionar_integrante(grupo_id, bia.id)  # nasce a pesquisa do grupo (com relatório)
    TurmaRepository().matricular(turma.id, ana.id)
    interacao_do_grupo = nova_interacao(repo.buscar_por_id(grupo_id).pesquisa)
    FonteRepository().salvar(Fonte(referencia="r", interacao_id=interacao_do_grupo.id))
    TurmaRepository().excluir(turma.id)
    for colecao in (
        "turmas", "matriculas", "grupos", "grupo_alunos", "convites", "pesquisas", "interacoes", "fontes", "relatorios",
    ):
        assert contar(colecao) == 0, colecao
    assert contar("usuarios") == 3  # ana, bia e o professor continuam existindo
    assert contar("unicos") == 3  # só os e-mails; o código da turma foi liberado


def test_listar_do_professor_traz_so_as_pesquisas_das_turmas_dele_mais_recente_primeiro():
    ana = novo_aluno()
    t1 = nova_turma("A", "AAAAAA")
    p1 = nova_pesquisa(ana, "antiga", t1)
    outro = UsuarioRepository().salvar(Usuario(nome="Outro", email="o@x.com", senha_hash="h", tipo="professor"))
    t_outro = TurmaRepository().salvar(Turma(nome="X", codigo="XXXXXX", professor_id=outro.id))
    nova_pesquisa(ana, "de outro professor", t_outro)
    p2 = nova_pesquisa(ana, "nova", t1)
    prof = UsuarioRepository().buscar_por_email("prof@x.com")
    assert [p.titulo for p in PesquisaRepository().listar_do_professor(prof.id)] == ["nova", "antiga"]
    PesquisaRepository().entregar(p1.id)  # a entregue sobe: conta a data de entrega
    lista = PesquisaRepository().listar_do_professor(prof.id)
    assert [p.titulo for p in lista] == ["antiga", "nova"] and lista[0].aluno.nome == "Ana" and lista[0].turma.nome == "A"
    assert [p.titulo for p in PesquisaRepository().listar_do_professor(prof.id, t1.id)] == ["antiga", "nova"]
    assert PesquisaRepository().listar_do_professor(prof.id, t_outro.id) == []  # turma que não é dele
    assert p2.id != p1.id


# ---------------------------------------------------------------- dados de exemplo
def test_script_de_dados_de_exemplo_cria_e_limpa_sem_tocar_nos_dados_reais():
    from scripts import popular_exemplo

    real = novo_aluno("real@x.com")
    popular_exemplo.popular()
    pesquisas = armazenamento.loja().consultar("pesquisas")
    assert {p["status"] for p in pesquisas} >= {"em_andamento", "entregue", "concluida"}
    assert contar("grupos") == 2 and contar("convites") >= 5 and contar("turmas") == 3
    assert popular_exemplo.ja_existe()
    popular_exemplo.limpar()
    assert not popular_exemplo.ja_existe()
    assert contar("turmas") == 0 and contar("pesquisas") == 0 and contar("grupos") == 0
    assert contar("matriculas") == 0 and contar("convites") == 0 and contar("fontes") == 0
    assert UsuarioRepository().buscar_por_email("real@x.com").id == real.id
    assert contar("usuarios") == 1 and contar("unicos") == 1
