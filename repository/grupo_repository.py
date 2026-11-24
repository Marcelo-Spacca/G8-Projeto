from repository import armazenamento
from repository.carga import carregar_grupos, mais_recentes_primeiro, usuarios_por_id
from repository.models import ConviteGrupo, Grupo, GrupoAluno, Pesquisa, Relatorio
from repository.armazenamento import agora
from repository.pesquisa_repository import id_da_pesquisa_do_grupo


def _criar_pesquisa_do_grupo(loja, lote, grupo, integrantes):
    """A pesquisa do grupo nasce quando ele chega a 2 integrantes. Só existe uma por grupo (o id
    do documento é derivado do id do grupo)."""
    pesquisa_id = id_da_pesquisa_do_grupo(grupo["id"])
    if integrantes < 2 or loja.obter("pesquisas", pesquisa_id) is not None:
        return
    pesquisa = Pesquisa(
        titulo=grupo["titulo"], objetivo=grupo["objetivo"], grupo_id=grupo["id"], turma_id=grupo["turma_id"]
    )
    lote.criar("pesquisas", pesquisa_id, pesquisa.para_dict())
    # RF20/RF22: o relatório nasce junto, como nas pesquisas individuais
    lote.criar("relatorios", pesquisa_id, Relatorio(pesquisa_id=pesquisa_id).para_dict())


def _integrantes(loja, grupo_id):
    return {m["aluno_id"] for m in loja.consultar("grupo_alunos", grupo_id=grupo_id)}


class GrupoRepository:
    def criar(self, turma_id, criador_id, nome, titulo, objetivo):
        """Cria o grupo já com o criador como primeiro integrante (ainda sem pesquisa)."""
        loja = armazenamento.loja()
        grupo = Grupo(nome=nome, titulo=titulo, objetivo=objetivo, turma_id=turma_id, criador_id=criador_id)
        grupo.id = loja.novo_id()
        integrante = GrupoAluno(grupo_id=grupo.id, aluno_id=criador_id)
        lote = loja.lote()
        lote.criar("grupos", grupo.id, grupo.para_dict())
        lote.criar("grupo_alunos", f"{grupo.id}_{criador_id}", integrante.para_dict())
        lote.confirmar()
        return grupo.id

    def buscar_por_id(self, grupo_id):
        doc = armazenamento.loja().obter("grupos", grupo_id)
        return carregar_grupos([doc], turma=True, pesquisa=True, convites=True)[0] if doc else None

    def aluno_e_integrante(self, grupo_id, aluno_id):
        return armazenamento.loja().obter("grupo_alunos", f"{grupo_id}_{aluno_id}") is not None

    def listar_do_aluno(self, aluno_id, turma_id):
        """Grupos da turma de que o aluno participa, do mais recente para o mais antigo."""
        loja = armazenamento.loja()
        ids = [m["grupo_id"] for m in loja.consultar("grupo_alunos", aluno_id=aluno_id)]
        docs = [d for d in loja.obter_varios("grupos", ids).values() if d["turma_id"] == str(turma_id)]
        grupos = carregar_grupos(docs, turma=True, pesquisa=True, convites=True)
        return mais_recentes_primeiro(grupos, lambda g: g.data_criacao)

    # ---------------------------------------------------------------- integrantes
    def adicionar_integrante(self, grupo_id, aluno_id):
        loja = armazenamento.loja()
        grupo = loja.obter("grupos", grupo_id)
        lote = loja.lote()
        lote.criar("grupo_alunos", f"{grupo_id}_{aluno_id}", GrupoAluno(grupo_id=grupo_id, aluno_id=aluno_id).para_dict())
        _criar_pesquisa_do_grupo(loja, lote, grupo, len(_integrantes(loja, grupo_id) | {str(aluno_id)}))
        lote.confirmar()

    def remover_integrante(self, grupo_id, aluno_id):
        armazenamento.loja().apagar("grupo_alunos", f"{grupo_id}_{aluno_id}")

    # ---------------------------------------------------------------- convites
    def convidar(self, grupo_id, convidados_ids, por_id):
        """Cria os convites (ou reabre o que foi recusado) num único lote."""
        loja = armazenamento.loja()
        lote = loja.lote()
        for aluno_id in convidados_ids:
            id_convite = f"{grupo_id}_{aluno_id}"
            if loja.obter("convites", id_convite) is None:
                convite = ConviteGrupo(grupo_id=grupo_id, aluno_id=aluno_id, convidado_por_id=por_id)
                lote.criar("convites", id_convite, convite.para_dict())
            else:
                lote.atualizar(
                    "convites",
                    id_convite,
                    {"status": "pendente", "data_resposta": None, "convidado_por_id": por_id, "data_criacao": agora()},
                )
        lote.confirmar()

    def buscar_convite(self, convite_id):
        loja = armazenamento.loja()
        doc = loja.obter("convites", convite_id)
        if doc is None:
            return None
        convite = ConviteGrupo.de_dict(doc)
        grupo = loja.obter("grupos", convite.grupo_id)
        convite.grupo = Grupo.de_dict(grupo) if grupo else None
        return convite

    def convites_pendentes(self, aluno_id, turma_id):
        """Convites que o aluno ainda não respondeu nesta turma, do mais recente para o mais antigo."""
        loja = armazenamento.loja()
        convites = [ConviteGrupo.de_dict(d) for d in loja.consultar("convites", aluno_id=aluno_id, status="pendente")]
        docs = loja.obter_varios("grupos", [c.grupo_id for c in convites])
        grupos = {g.id: g for g in carregar_grupos([d for d in docs.values() if d["turma_id"] == str(turma_id)])}
        quem = usuarios_por_id([c.convidado_por_id for c in convites])
        daqui = []
        for convite in convites:
            if convite.grupo_id in grupos:
                convite.grupo = grupos[convite.grupo_id]
                convite.convidado_por = quem.get(convite.convidado_por_id)
                daqui.append(convite)
        return mais_recentes_primeiro(daqui, lambda c: c.data_criacao)

    def responder_convite(self, convite_id, aceitar):
        """Aceitar entra no grupo e, se for o caso, cria a pesquisa dele, tudo no mesmo lote."""
        loja = armazenamento.loja()
        convite = loja.obter("convites", convite_id)
        lote = loja.lote()
        lote.atualizar(
            "convites", convite_id,
            {"status": "aceito" if aceitar else "recusado", "data_resposta": agora()},
        )
        if aceitar:
            grupo_id, aluno_id = convite["grupo_id"], convite["aluno_id"]
            integrantes = _integrantes(loja, grupo_id)
            if aluno_id not in integrantes:
                lote.criar("grupo_alunos", f"{grupo_id}_{aluno_id}", GrupoAluno(grupo_id=grupo_id, aluno_id=aluno_id).para_dict())
            _criar_pesquisa_do_grupo(loja, lote, loja.obter("grupos", grupo_id), len(integrantes | {aluno_id}))
        lote.confirmar()
