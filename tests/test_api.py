"""A API de ponta a ponta (sem navegador): o mesmo fluxo que o front faz, via HTTP."""
import pytest
from fastapi.testclient import TestClient

from api import sessoes
from api.main import app


@pytest.fixture
def http():
    sessoes.limpar_tudo()
    return TestClient(app)


class Pessoa:
    def __init__(self, http, nome, email, tipo):
        self.http = http
        r = http.post("/api/auth/cadastro", json={"nome": nome, "email": email, "senha": "senha123", "tipo": tipo})
        assert r.status_code == 201, r.text
        self.id = r.json()["usuario"]["id"]
        r = http.post("/api/auth/entrar", json={"email": email, "senha": "senha123"})
        assert r.status_code == 200, r.text
        self.token = r.json()["token"]

    def _h(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, url, **kw):
        return self.http.get(url, headers=self._h(), **kw)

    def post(self, url, json=None):
        return self.http.post(url, headers=self._h(), json=json)

    def put(self, url, json=None):
        return self.http.put(url, headers=self._h(), json=json)

    def delete(self, url):
        return self.http.delete(url, headers=self._h())


@pytest.fixture
def cenario(http):
    prof = Pessoa(http, "Profa. Marina", "marina@x.com", "professor")
    ana = Pessoa(http, "Ana Souza", "ana@x.com", "aluno")
    bia = Pessoa(http, "Bia Ferreira", "bia@x.com", "aluno")
    turma = prof.post("/api/professor/turmas", {"nome": "Projeto 1", "permite_grupos": True}).json()
    for aluna in (ana, bia):
        assert aluna.post("/api/aluno/turmas/entrar", {"codigo": turma["codigo"].lower()}).status_code == 201
    return prof, ana, bia, turma


def test_sem_token_devolve_401(http):
    r = http.get("/api/aluno/turmas")
    assert r.status_code == 401
    assert "Entre na sua conta" in r.json()["detail"]


def test_token_invalido_devolve_401(http):
    r = http.get("/api/aluno/turmas", headers={"Authorization": "Bearer nada"})
    assert r.status_code == 401


def test_cadastro_login_e_sair(http):
    p = Pessoa(http, "Caio", "caio@x.com", "aluno")
    assert p.get("/api/auth/eu").json()["nome"] == "Caio"
    r = http.post("/api/auth/entrar", json={"email": "CAIO@x.com", "senha": "senha123"})
    assert r.status_code == 200 and r.json()["usuario"]["tipo"] == "aluno"
    assert http.post("/api/auth/sair", headers=p._h()).status_code == 204
    assert p.get("/api/auth/eu").status_code == 401


def test_erros_de_regra_chegam_como_400_com_a_mensagem(http):
    r = http.post("/api/auth/entrar", json={"email": "x@x.com", "senha": "errada"})
    assert r.status_code == 400 and r.json()["detail"] == "E-mail ou senha incorretos."
    r = http.post("/api/auth/cadastro", json={"nome": "", "email": "a@a.com", "senha": "123456", "tipo": "aluno"})
    assert r.status_code == 400 and r.json()["detail"] == "Informe seu nome."


def test_perfil_errado_nao_alcanca_a_rota(cenario):
    prof, ana, _, turma = cenario
    r = ana.get("/api/professor/turmas")
    assert r.status_code == 400 and "exclusiva de professores" in r.json()["detail"]
    r = prof.get("/api/aluno/turmas")
    assert r.status_code == 400 and "exclusiva de alunos" in r.json()["detail"]


def test_professor_ve_turma_com_alunos(cenario):
    prof, _, _, turma = cenario
    lista = prof.get("/api/professor/turmas").json()
    assert lista[0]["n_alunos"] == 2 and lista[0]["codigo"] == turma["codigo"]
    completa = prof.get(f"/api/professor/turmas/{turma['id']}").json()
    assert [a["nome"] for a in completa["alunos"]] == ["Ana Souza", "Bia Ferreira"]


def test_entrar_com_codigo_errado(cenario, http):
    caio = Pessoa(http, "Caio", "caio@x.com", "aluno")
    r = caio.post("/api/aluno/turmas/entrar", {"codigo": "ZZZZZZ"})
    assert r.status_code == 400 and "Não existe turma" in r.json()["detail"]


def test_fluxo_completo_do_aluno_e_da_revisao(cenario):
    prof, ana, _, turma = cenario
    turmas = ana.get("/api/aluno/turmas").json()
    assert turmas[0]["professor"] == "Profa. Marina" and turmas[0]["permite_grupos"] is True

    p = ana.post(f"/api/aluno/turmas/{turma['id']}/pesquisas", {"titulo": "IA e educação", "objetivo": "Entender riscos"}).json()
    assert p["status"] == "em_andamento"
    assert [x["titulo"] for x in ana.get(f"/api/aluno/turmas/{turma['id']}/pesquisas").json()] == ["IA e educação"]

    i = ana.post(f"/api/aluno/pesquisas/{p['id']}/interacoes", {"ferramenta": "ChatGPT", "pergunta": "Quais riscos?", "resposta": "Autoria e fontes."}).json()
    f1 = ana.post(f"/api/aluno/interacoes/{i['id']}/fontes", {"referencia": "SILVA. Avaliação. 2023.", "link": "https://exemplo.org"}).json()
    f2 = ana.post(f"/api/aluno/interacoes/{i['id']}/fontes", {"referencia": "OLIVEIRA. Plágio. 2022."}).json()
    assert f1["status"] == "nao_verificada"

    v = ana.post(f"/api/aluno/fontes/{f1['id']}/verificacao", {"resultado": "verificada", "anotacao": "Conferi", "trecho": "A autoria muda.", "localizacao": "parágrafo 3"})
    assert v.status_code == 200 and v.json()["trechos"][0]["trecho"] == "A autoria muda."
    r = ana.post(f"/api/aluno/fontes/{f1['id']}/trechos", {"trecho": "Outro trecho"})
    assert r.status_code == 201 and len(r.json()["trechos"]) == 2
    assert ana.post(f"/api/aluno/fontes/{f2['id']}/verificacao", {"resultado": "incorreta"}).json()["status"] == "incorreta"

    # editar fonte já julgada volta a não verificada e avisa
    e = ana.put(f"/api/aluno/fontes/{f1['id']}", {"referencia": "SILVA. Avaliação (corrigida). 2023.", "link": "https://exemplo.org"}).json()
    assert e["status"] == "nao_verificada" and e["voltou_a_nao_verificada"] is True and e["trechos"] == []
    ana.post(f"/api/aluno/fontes/{f1['id']}/verificacao", {"resultado": "verificada", "trecho": "Trecho novo"})

    detalhe = ana.get(f"/api/aluno/interacoes/{i['id']}").json()
    assert detalhe["contagem"] == {"verificada": 1, "incorreta": 1, "nao_verificada": 0}
    assert detalhe["pesquisa"]["titulo"] == "IA e educação"

    previa = ana.get(f"/api/pesquisas/{p['id']}/relatorio").json()
    assert previa["situacao"] == "previa" and previa["n_fontes"] == 2

    # o professor não alcança a pesquisa antes da entrega no relatório
    assert prof.get(f"/api/pesquisas/{p['id']}/relatorio").status_code == 400

    ent = ana.post(f"/api/aluno/pesquisas/{p['id']}/entrega").json()
    assert ent["status"] == "entregue"
    # entregue: aluno não altera mais
    r = ana.post(f"/api/aluno/interacoes/{i['id']}/fontes", {"referencia": "X"})
    assert r.status_code == 400 and "entregue ao professor" in r.json()["detail"]

    # professor
    lista = prof.get("/api/professor/pesquisas").json()
    assert lista["pesquisas"][0]["status"] == "entregue" and lista["turmas"][0]["nome"] == "Projeto 1"
    rev = prof.get(f"/api/professor/pesquisas/{p['id']}").json()
    assert rev["interacoes"][0]["ferramenta"] == "ChatGPT"
    assert prof.get(f"/api/pesquisas/{p['id']}/relatorio").json()["situacao"] == "entregue"

    j = prof.post(f"/api/professor/fontes/{f2['id']}/julgamento", {"resultado": "incorreta", "anotacao": "Não achei."}).json()
    assert j["julgada_pelo_professor"] is True and j["anotacao"] == "Não achei."
    c = prof.put(f"/api/professor/interacoes/{i['id']}/comentario", {"comentario": "Boa pergunta."}).json()
    assert c["comentario"] == "Boa pergunta."
    assert prof.post(f"/api/professor/interacoes/{i['id']}/confirmacao").json()["confirmada"] is True
    assert prof.delete(f"/api/professor/interacoes/{i['id']}/confirmacao").json()["confirmada"] is False

    d = prof.post(f"/api/professor/pesquisas/{p['id']}/devolucao", {"mensagem": ""})
    assert d.status_code == 400 and "mensagem" in d.json()["detail"]
    dev = prof.post(f"/api/professor/pesquisas/{p['id']}/devolucao", {"mensagem": "Ligue as fontes."}).json()
    assert dev["status"] == "em_andamento" and dev["devolvida"] is True and dev["mensagem_devolucao"] == "Ligue as fontes."
    vista = ana.get(f"/api/aluno/pesquisas/{p['id']}").json()
    assert vista["devolvida"] is True

    ana.post(f"/api/aluno/pesquisas/{p['id']}/entrega")
    ok = prof.post(f"/api/professor/pesquisas/{p['id']}/aceite").json()
    assert ok["status"] == "concluida"
    assert ana.get(f"/api/pesquisas/{p['id']}/relatorio").json()["situacao"] == "concluida"


def test_editar_e_excluir_pesquisa_e_interacao(cenario):
    _, ana, _, turma = cenario
    p = ana.post(f"/api/aluno/turmas/{turma['id']}/pesquisas", {"titulo": "A", "objetivo": "B"}).json()
    e = ana.put(f"/api/aluno/pesquisas/{p['id']}", {"titulo": "Novo", "objetivo": "Obj"}).json()
    assert e["titulo"] == "Novo"
    i = ana.post(f"/api/aluno/pesquisas/{p['id']}/interacoes", {"ferramenta": "Claude", "pergunta": "p", "resposta": "r"}).json()
    ed = ana.put(f"/api/aluno/interacoes/{i['id']}", {"ferramenta": "Gemini", "pergunta": "p2", "resposta": "r2"}).json()
    assert ed["ferramenta"] == "Gemini"
    assert ana.delete(f"/api/aluno/interacoes/{i['id']}").status_code == 204
    assert ana.get(f"/api/aluno/interacoes/{i['id']}").status_code == 400
    assert ana.delete(f"/api/aluno/pesquisas/{p['id']}").status_code == 204
    assert ana.get(f"/api/aluno/turmas/{turma['id']}/pesquisas").json() == []


def test_grupos_convites_e_professor_atribui(cenario, http):
    prof, ana, bia, turma = cenario
    g = ana.post(f"/api/aluno/turmas/{turma['id']}/grupos", {"nome": "Alfa", "titulo": "IA em grupo", "objetivo": "Obj"}).json()
    assert g["pesquisa"] is None and [a["nome"] for a in g["alunos"]] == ["Ana Souza"]
    cand = ana.get(f"/api/aluno/grupos/{g['id']}/convidaveis").json()
    assert [c["nome"] for c in cand] == ["Bia Ferreira"]
    assert ana.post(f"/api/aluno/grupos/{g['id']}/convites", {"alunos_ids": [bia.id]}).json() == {"enviados": 1}

    convites = bia.get(f"/api/aluno/turmas/{turma['id']}").json()["convites"]
    assert convites[0]["grupo"]["nome"] == "Alfa"
    r = bia.post(f"/api/aluno/convites/{convites[0]['id']}/resposta", {"aceitar": True}).json()
    assert r["aceito"] is True

    grupos = ana.get(f"/api/aluno/turmas/{turma['id']}/grupos").json()
    assert grupos[0]["pesquisa"]["titulo"] == "IA em grupo" and len(grupos[0]["alunos"]) == 2

    caio = Pessoa(http, "Caio", "caio@x.com", "aluno")
    caio.post("/api/aluno/turmas/entrar", {"codigo": turma["codigo"]})
    completa = prof.get(f"/api/professor/turmas/{turma['id']}").json()
    assert [a["nome"] for a in completa["sem_grupo"]] == ["Caio"]
    assert completa["grupos"][0]["pesquisa"]["id"] == grupos[0]["pesquisa"]["id"]
    ag = prof.post(f"/api/professor/grupos/{g['id']}/alunos", {"aluno_id": caio.id}).json()
    assert len(ag["alunos"]) == 3
    rm = prof.delete(f"/api/professor/grupos/{g['id']}/alunos/{caio.id}").json()
    assert len(rm["alunos"]) == 2


def test_excluir_turma_e_ver_o_que_sobra(cenario):
    prof, ana, _, turma = cenario
    ana.post(f"/api/aluno/turmas/{turma['id']}/pesquisas", {"titulo": "A", "objetivo": "B"})
    assert prof.delete(f"/api/professor/turmas/{turma['id']}").status_code == 204
    assert prof.get("/api/professor/turmas").json() == []
    assert ana.get("/api/aluno/turmas").json() == []


def test_aluno_nao_ve_pesquisa_de_outro(cenario):
    _, ana, bia, turma = cenario
    p = ana.post(f"/api/aluno/turmas/{turma['id']}/pesquisas", {"titulo": "A", "objetivo": "B"}).json()
    r = bia.get(f"/api/aluno/pesquisas/{p['id']}")
    assert r.status_code == 400 and "não encontrada" in r.json()["detail"]
    assert bia.get(f"/api/pesquisas/{p['id']}/relatorio").status_code == 400


def test_sessoes_nao_se_misturam(cenario):
    prof, ana, bia, turma = cenario
    for _ in range(3):
        assert ana.get("/api/auth/eu").json()["nome"] == "Ana Souza"
        assert bia.get("/api/auth/eu").json()["nome"] == "Bia Ferreira"
        assert prof.get("/api/auth/eu").json()["tipo"] == "professor"
