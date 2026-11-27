"""API do Registro verificável do uso de IA.

É só uma casca fina: cada rota chama um service (as regras continuam em services/) e devolve JSON.
Rodar:  uvicorn api.main:app --port 8000      (documentação interativa em /docs)
"""
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api import serializadores as ser
from api import sessoes
from repository.armazenamento import ErroDeConfiguracao, ErroDeIntegridade
from services.erros import RegraViolada
from services.fonte_service import FonteService
from services.grupo_service import GrupoService
from services.interacao_service import InteracaoService
from services.pesquisa_service import PesquisaService
from services.relatorio_service import RelatorioService
from services.revisao_service import RevisaoService
from services.turma_service import TurmaService
from services.usuario_service import UsuarioService

log = logging.getLogger("api")
app = FastAPI(title="Registro verificável do uso de IA", docs_url="/docs", redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

usuarios = UsuarioService()
turmas = TurmaService()
pesquisas = PesquisaService()
interacoes = InteracaoService()
fontes = FonteService()
grupos = GrupoService()
relatorios = RelatorioService()
revisoes = RevisaoService()


# ---------------------------------------------------------------------------------- erros
@app.exception_handler(RegraViolada)
async def _regra_violada(_req, erro):
    texto = str(erro)
    sem_login = texto.startswith("Entre na sua conta") or texto.startswith("Sua sessão expirou")
    return JSONResponse({"detail": texto}, status_code=401 if sem_login else 400)


@app.exception_handler(ErroDeIntegridade)
async def _integridade(_req, erro):
    return JSONResponse({"detail": "Esta ação conflita com dados que já existem. Atualize a página e tente de novo."}, status_code=409)


@app.exception_handler(ErroDeConfiguracao)
async def _configuracao(_req, erro):
    return JSONResponse({"detail": str(erro)}, status_code=503)


@app.exception_handler(Exception)
async def _inesperado(_req, erro):
    log.exception("erro inesperado", exc_info=erro)
    return JSONResponse(
        {"detail": "Algo deu errado do nosso lado. Tente de novo; se continuar, avise o grupo do projeto."},
        status_code=500,
    )


# ---------------------------------------------------------------------------------- sessão
def _token(autorizacao: Optional[str] = Header(default=None, alias="Authorization")):
    if autorizacao and autorizacao.lower().startswith("bearer "):
        return autorizacao[7:].strip()
    return None


def logado(token: Optional[str] = Depends(_token)):
    """Roda a rota com o usuário do token na sessão global dos services (veja api/sessoes.py)."""
    if token is None:
        raise RegraViolada("Entre na sua conta para continuar.")
    with sessoes.Contexto(token) as usuario:
        yield usuario


def anonimo():
    with sessoes.Contexto(None):
        yield None


# ---------------------------------------------------------------------------------- corpos
class Cadastro(BaseModel):
    nome: str = ""
    email: str = ""
    senha: str = ""
    tipo: str = ""


class Login(BaseModel):
    email: str = ""
    senha: str = ""


class Codigo(BaseModel):
    codigo: str = ""


class TituloObjetivo(BaseModel):
    titulo: str = ""
    objetivo: str = ""


class NovoGrupo(BaseModel):
    nome: str = ""
    titulo: str = ""
    objetivo: str = ""


class NovaTurma(BaseModel):
    nome: str = ""
    permite_grupos: bool = False


class Convidar(BaseModel):
    alunos_ids: List[str] = []


class Resposta(BaseModel):
    aceitar: bool


class NovaInteracao(BaseModel):
    ferramenta: str = ""
    pergunta: str = ""
    resposta: str = ""


class NovaFonte(BaseModel):
    referencia: str = ""
    link: Optional[str] = None


class Verificacao(BaseModel):
    resultado: str = ""
    anotacao: Optional[str] = None
    trecho: Optional[str] = None
    localizacao: Optional[str] = None


class NovoTrecho(BaseModel):
    trecho: str = ""
    localizacao: Optional[str] = None


class Julgamento(BaseModel):
    resultado: str = ""
    anotacao: Optional[str] = None


class Comentario(BaseModel):
    comentario: Optional[str] = None


class Devolucao(BaseModel):
    mensagem: str = ""


class AlunoId(BaseModel):
    aluno_id: str


# ---------------------------------------------------------------------------------- acesso
@app.post("/api/auth/cadastro", status_code=201)
def cadastrar(corpo: Cadastro, _=Depends(anonimo)):
    novo = usuarios.cadastrar(corpo.nome, corpo.email, corpo.senha, corpo.tipo)
    return {"usuario": ser.usuario(novo)}


@app.post("/api/auth/entrar")
def entrar(corpo: Login, _=Depends(anonimo)):
    usuario = usuarios.entrar(corpo.email, corpo.senha)
    return {"token": sessoes.criar_token(usuario.id), "usuario": ser.usuario(usuario)}


@app.get("/api/auth/eu")
def quem_sou(usuario=Depends(logado)):
    return ser.usuario(usuario)


@app.post("/api/auth/sair", status_code=204)
def sair(token: Optional[str] = Depends(_token)):
    if token:
        sessoes.revogar(token)


# ---------------------------------------------------------------------------------- aluno: turmas
@app.get("/api/aluno/turmas")
def aluno_turmas(_=Depends(logado)):
    return [ser.turma_aluno(t) for t in turmas.listar_do_aluno()]


@app.post("/api/aluno/turmas/entrar", status_code=201)
def aluno_entrar_na_turma(corpo: Codigo, _=Depends(logado)):
    return ser.turma_aluno(turmas.entrar(corpo.codigo))


@app.get("/api/aluno/turmas/{turma_id}")
def aluno_turma(turma_id: str, _=Depends(logado)):
    turma = turmas.obter_do_aluno(turma_id)
    dados = ser.turma_aluno(turma)
    dados["convites"] = [ser.convite(c) for c in grupos.convites_pendentes(turma.id)]
    return dados


@app.get("/api/aluno/turmas/{turma_id}/pesquisas")
def aluno_pesquisas_da_turma(turma_id: str, _=Depends(logado)):
    return [ser.pesquisa(p) for p in pesquisas.listar_minhas(turma_id)]


@app.post("/api/aluno/turmas/{turma_id}/pesquisas", status_code=201)
def aluno_criar_pesquisa(turma_id: str, corpo: TituloObjetivo, _=Depends(logado)):
    return ser.pesquisa(pesquisas.criar(turma_id, corpo.titulo, corpo.objetivo))


@app.get("/api/aluno/turmas/{turma_id}/grupos")
def aluno_grupos_da_turma(turma_id: str, _=Depends(logado)):
    return [ser.grupo(g) for g in grupos.listar_do_aluno(turma_id)]


@app.post("/api/aluno/turmas/{turma_id}/grupos", status_code=201)
def aluno_criar_grupo(turma_id: str, corpo: NovoGrupo, _=Depends(logado)):
    return ser.grupo(grupos.criar(turma_id, corpo.nome, corpo.titulo, corpo.objetivo))


@app.get("/api/aluno/grupos/{grupo_id}/convidaveis")
def aluno_convidaveis(grupo_id: str, _=Depends(logado)):
    return [{"id": a.id, "nome": a.nome} for a in grupos.convidaveis(grupo_id)]


@app.post("/api/aluno/grupos/{grupo_id}/convites", status_code=201)
def aluno_convidar(grupo_id: str, corpo: Convidar, _=Depends(logado)):
    return {"enviados": grupos.convidar(grupo_id, corpo.alunos_ids)}


@app.post("/api/aluno/convites/{convite_id}/resposta")
def aluno_responder_convite(convite_id: str, corpo: Resposta, _=Depends(logado)):
    grupo = grupos.responder_convite(convite_id, corpo.aceitar)
    return {"grupo": {"id": grupo.id, "nome": grupo.nome}, "aceito": corpo.aceitar}


# ---------------------------------------------------------------------------------- aluno: pesquisa
def _pesquisa_do_aluno(pesquisa_id):
    p = pesquisas.obter(pesquisa_id)
    p.interacoes = interacoes.listar(p.id)
    return ser.pesquisa(p, com_interacoes=True)


@app.get("/api/aluno/pesquisas/{pesquisa_id}")
def aluno_pesquisa(pesquisa_id: str, _=Depends(logado)):
    return _pesquisa_do_aluno(pesquisa_id)


@app.put("/api/aluno/pesquisas/{pesquisa_id}")
def aluno_editar_pesquisa(pesquisa_id: str, corpo: TituloObjetivo, _=Depends(logado)):
    pesquisas.editar(pesquisa_id, corpo.titulo, corpo.objetivo)
    return _pesquisa_do_aluno(pesquisa_id)


@app.post("/api/aluno/pesquisas/{pesquisa_id}/entrega")
def aluno_entregar(pesquisa_id: str, _=Depends(logado)):
    pesquisas.entregar(pesquisa_id)
    return _pesquisa_do_aluno(pesquisa_id)


@app.delete("/api/aluno/pesquisas/{pesquisa_id}", status_code=204)
def aluno_excluir_pesquisa(pesquisa_id: str, _=Depends(logado)):
    pesquisas.excluir(pesquisa_id)


@app.post("/api/aluno/pesquisas/{pesquisa_id}/interacoes", status_code=201)
def aluno_registrar_interacao(pesquisa_id: str, corpo: NovaInteracao, _=Depends(logado)):
    return ser.interacao(interacoes.registrar(pesquisa_id, corpo.ferramenta, corpo.pergunta, corpo.resposta))


# ---------------------------------------------------------------------------------- aluno: interação e fontes
def _interacao_do_aluno(interacao_id):
    i = interacoes.obter(interacao_id)
    dados = ser.interacao(i)
    p = pesquisas.obter(i.pesquisa_id)
    dados["pesquisa"] = {"id": p.id, "titulo": p.titulo, "status": p.status, "turma_id": p.turma_id,
                         "turma": None if p.turma is None else p.turma.nome}
    return dados


@app.get("/api/aluno/interacoes/{interacao_id}")
def aluno_interacao(interacao_id: str, _=Depends(logado)):
    return _interacao_do_aluno(interacao_id)


@app.put("/api/aluno/interacoes/{interacao_id}")
def aluno_editar_interacao(interacao_id: str, corpo: NovaInteracao, _=Depends(logado)):
    interacoes.editar(interacao_id, corpo.ferramenta, corpo.pergunta, corpo.resposta)
    return _interacao_do_aluno(interacao_id)


@app.delete("/api/aluno/interacoes/{interacao_id}", status_code=204)
def aluno_excluir_interacao(interacao_id: str, _=Depends(logado)):
    interacoes.excluir(interacao_id)


@app.post("/api/aluno/interacoes/{interacao_id}/fontes", status_code=201)
def aluno_adicionar_fonte(interacao_id: str, corpo: NovaFonte, _=Depends(logado)):
    return ser.fonte(fontes.adicionar(interacao_id, corpo.referencia, corpo.link))


@app.put("/api/aluno/fontes/{fonte_id}")
def aluno_editar_fonte(fonte_id: str, corpo: NovaFonte, _=Depends(logado)):
    antes = fontes.obter(fonte_id)
    nova = fontes.editar(fonte_id, corpo.referencia, corpo.link)
    dados = ser.fonte(nova)
    dados["voltou_a_nao_verificada"] = antes.status != "nao_verificada" and nova.status == "nao_verificada"
    return dados


@app.post("/api/aluno/fontes/{fonte_id}/verificacao")
def aluno_verificar_fonte(fonte_id: str, corpo: Verificacao, _=Depends(logado)):
    return ser.fonte(fontes.verificar(fonte_id, corpo.resultado, corpo.anotacao, corpo.trecho, corpo.localizacao))


@app.post("/api/aluno/fontes/{fonte_id}/trechos", status_code=201)
def aluno_ligar_trecho(fonte_id: str, corpo: NovoTrecho, _=Depends(logado)):
    fontes.ligar_trecho(fonte_id, corpo.trecho, corpo.localizacao)
    return ser.fonte(fontes.obter(fonte_id))


# ---------------------------------------------------------------------------------- relatório (aluno e professor)
@app.get("/api/pesquisas/{pesquisa_id}/relatorio")
def relatorio(pesquisa_id: str, _=Depends(logado)):
    return ser.relatorio(relatorios.gerar(pesquisa_id))


# ---------------------------------------------------------------------------------- professor: turmas
@app.get("/api/professor/turmas")
def prof_turmas(_=Depends(logado)):
    return [ser.turma_professor(t) for t in turmas.listar_do_professor()]


@app.post("/api/professor/turmas", status_code=201)
def prof_criar_turma(corpo: NovaTurma, _=Depends(logado)):
    criada = turmas.criar(corpo.nome, corpo.permite_grupos)
    return ser.turma_professor(turmas.obter_do_professor(criada.id))


@app.get("/api/professor/turmas/{turma_id}")
def prof_turma(turma_id: str, _=Depends(logado)):
    return ser.turma_professor(turmas.obter_do_professor(turma_id), completa=True)


@app.delete("/api/professor/turmas/{turma_id}", status_code=204)
def prof_excluir_turma(turma_id: str, _=Depends(logado)):
    turmas.excluir(turma_id)


@app.post("/api/professor/grupos/{grupo_id}/alunos", status_code=201)
def prof_atribuir(grupo_id: str, corpo: AlunoId, _=Depends(logado)):
    return ser.grupo(grupos.atribuir_aluno(grupo_id, corpo.aluno_id))


@app.delete("/api/professor/grupos/{grupo_id}/alunos/{aluno_id}")
def prof_remover(grupo_id: str, aluno_id: str, _=Depends(logado)):
    return ser.grupo(grupos.remover_aluno(grupo_id, aluno_id))


# ---------------------------------------------------------------------------------- professor: pesquisas
@app.get("/api/professor/pesquisas")
def prof_pesquisas(turma_id: Optional[str] = None, _=Depends(logado)):
    todas = [t for t in turmas.listar_do_professor()]
    if turma_id is not None and turma_id not in {t.id for t in todas}:
        turma_id = None
    return {
        "turmas": [{"id": t.id, "nome": t.nome} for t in todas],
        "turma_id": turma_id,
        "pesquisas": [ser.pesquisa(p) for p in revisoes.listar_todas(turma_id)],
    }


def _revisao_da_pesquisa(pesquisa_id):
    return ser.pesquisa(revisoes.obter_pesquisa(pesquisa_id), com_interacoes=True)


@app.get("/api/professor/pesquisas/{pesquisa_id}")
def prof_pesquisa(pesquisa_id: str, _=Depends(logado)):
    return _revisao_da_pesquisa(pesquisa_id)


@app.post("/api/professor/pesquisas/{pesquisa_id}/aceite")
def prof_aceitar(pesquisa_id: str, _=Depends(logado)):
    revisoes.aceitar(pesquisa_id)
    return _revisao_da_pesquisa(pesquisa_id)


@app.post("/api/professor/pesquisas/{pesquisa_id}/devolucao")
def prof_devolver(pesquisa_id: str, corpo: Devolucao, _=Depends(logado)):
    revisoes.devolver(pesquisa_id, corpo.mensagem)
    return _revisao_da_pesquisa(pesquisa_id)


def _interacao_do_professor(interacao_id):
    i = revisoes.obter_interacao(interacao_id)
    p = revisoes.obter_pesquisa(i.pesquisa_id)
    dados = ser.interacao(i)
    dados["pesquisa"] = {
        "id": p.id, "titulo": p.titulo, "status": p.status,
        "turma_id": p.turma_id, "turma": None if p.turma is None else p.turma.nome,
        "autor": f"Grupo {p.grupo.nome}" if p.de_grupo else f"Aluno: {p.aluno.nome}",
    }
    return dados


@app.get("/api/professor/interacoes/{interacao_id}")
def prof_interacao(interacao_id: str, _=Depends(logado)):
    return _interacao_do_professor(interacao_id)


@app.put("/api/professor/interacoes/{interacao_id}/comentario")
def prof_comentar(interacao_id: str, corpo: Comentario, _=Depends(logado)):
    revisoes.comentar_interacao(interacao_id, corpo.comentario)
    return _interacao_do_professor(interacao_id)


@app.post("/api/professor/interacoes/{interacao_id}/confirmacao")
def prof_confirmar(interacao_id: str, _=Depends(logado)):
    revisoes.confirmar_interacao(interacao_id)
    return _interacao_do_professor(interacao_id)


@app.delete("/api/professor/interacoes/{interacao_id}/confirmacao")
def prof_reabrir(interacao_id: str, _=Depends(logado)):
    revisoes.reabrir_interacao(interacao_id)
    return _interacao_do_professor(interacao_id)


@app.post("/api/professor/fontes/{fonte_id}/julgamento")
def prof_julgar(fonte_id: str, corpo: Julgamento, _=Depends(logado)):
    return ser.fonte(revisoes.julgar_fonte(fonte_id, corpo.resultado, corpo.anotacao))


# ---------------------------------------------------------------------------------- front-end (build do React)
_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/api/saude")
def saude():
    return {"ok": True}


if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{caminho:path}", include_in_schema=False)
    def front(caminho: str):
        if caminho.startswith("api/"):
            return JSONResponse({"detail": "Rota não encontrada."}, status_code=404)
        arquivo = (_DIST / caminho).resolve()
        if caminho and arquivo.is_file() and _DIST in arquivo.parents:
            return FileResponse(arquivo)
        return FileResponse(_DIST / "index.html")
