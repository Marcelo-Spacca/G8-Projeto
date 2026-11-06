"""Regras de negócio. Não conhecem a interface; usam os repositórios para acessar o banco."""

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from repository.models import Fonte, Interacao, Pesquisa, Relatorio, Trecho, Usuario
from repository.repositories import (
    FonteRepository,
    InteracaoRepository,
    PesquisaRepository,
    RelatorioRepository,
    UsuarioRepository,
)


class RegraViolada(Exception):
    """Erro de regra de negócio; a interface mostra a mensagem sem encerrar o programa."""


def _obrigatorio(valor: str | None, campo: str) -> str:
    valor = (valor or "").strip()
    if not valor:
        raise RegraViolada(f"O campo '{campo}' é obrigatório.")
    return valor


def _sessao_padrao() -> sessionmaker:
    from repository.database import Session

    return Session


class _ServicoBase:
    def __init__(self, session_factory: sessionmaker | None = None):
        self._sf = session_factory or _sessao_padrao()


# --------------------------------------------------------------------------- usuários


def _hash_senha(senha: str) -> str:
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(senha.encode(), salt=sal, n=2**14, r=8, p=1)
    return f"{sal.hex()}${h.hex()}"


def _confere_senha(senha: str, armazenado: str) -> bool:
    sal_hex, h_hex = armazenado.split("$", 1)
    h = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal_hex), n=2**14, r=8, p=1)
    return hmac.compare_digest(h.hex(), h_hex)


class UsuarioService(_ServicoBase):
    def cadastrar(self, nome: str, email: str, senha: str, tipo: str) -> Usuario:
        nome = _obrigatorio(nome, "nome")
        email = _obrigatorio(email, "e-mail").lower()
        if "@" not in email:
            raise RegraViolada("E-mail inválido.")
        if len(senha or "") < 6:
            raise RegraViolada("A senha precisa ter pelo menos 6 caracteres.")
        if tipo not in ("aluno", "professor"):
            raise RegraViolada("Tipo deve ser 'aluno' ou 'professor'.")
        with self._sf.begin() as s:
            repo = UsuarioRepository(s)
            if repo.por_email(email):
                raise RegraViolada("Já existe um usuário com esse e-mail.")
            return repo.salvar(
                Usuario(nome=nome, email=email, senha_hash=_hash_senha(senha), tipo=tipo)
            )

    def entrar(self, email: str, senha: str) -> Usuario:
        with self._sf() as s:
            usuario = UsuarioRepository(s).por_email((email or "").strip().lower())
            if not usuario or not _confere_senha(senha or "", usuario.senha_hash):
                raise RegraViolada("E-mail ou senha incorretos.")
            return usuario


# --------------------------------------------------------------------------- pesquisas


def _pesquisa_do_aluno(s, pesquisa_id: int, aluno_id: int) -> Pesquisa:
    pesquisa = PesquisaRepository(s).por_id(pesquisa_id)
    if not pesquisa or pesquisa.aluno_id != aluno_id:
        raise RegraViolada("Pesquisa não encontrada.")
    return pesquisa


class PesquisaService(_ServicoBase):
    def criar(self, aluno_id: int, titulo: str, objetivo: str) -> Pesquisa:
        titulo = _obrigatorio(titulo, "título")
        objetivo = _obrigatorio(objetivo, "objetivo")
        with self._sf.begin() as s:
            pesquisa = PesquisaRepository(s).salvar(
                Pesquisa(titulo=titulo, objetivo=objetivo, aluno_id=aluno_id)
            )
            # RF20/RF22: o relatório nasce junto com a pesquisa, ligado só a ela
            RelatorioRepository(s).salvar(Relatorio(pesquisa_id=pesquisa.id))
            return pesquisa

    def listar_do_aluno(self, aluno_id: int) -> list[Pesquisa]:
        with self._sf() as s:
            return PesquisaRepository(s).do_aluno(aluno_id)

    def listar_todas(self) -> list[Pesquisa]:
        """Para o professor escolher de qual pesquisa quer ver o relatório."""
        with self._sf() as s:
            return PesquisaRepository(s).todas()


# --------------------------------------------------------------------------- interações


class InteracaoService(_ServicoBase):
    def registrar(
        self,
        aluno_id: int,
        pesquisa_id: int,
        ferramenta_ia: str,
        pergunta: str,
        resposta: str,
        fontes: list[str] | None = None,
    ) -> Interacao:
        ferramenta_ia = _obrigatorio(ferramenta_ia, "ferramenta de IA")
        pergunta = _obrigatorio(pergunta, "pergunta")
        resposta = _obrigatorio(resposta, "resposta")
        with self._sf.begin() as s:
            _pesquisa_do_aluno(s, pesquisa_id, aluno_id)
            interacao = Interacao(
                ferramenta_ia=ferramenta_ia,
                pergunta=pergunta,
                resposta=resposta,
                pesquisa_id=pesquisa_id,
                fontes=[Fonte(referencia=r.strip()) for r in (fontes or []) if r.strip()],
            )
            return InteracaoRepository(s).salvar(interacao)

    def listar(self, aluno_id: int, pesquisa_id: int) -> list[Interacao]:
        with self._sf() as s:
            _pesquisa_do_aluno(s, pesquisa_id, aluno_id)
            return InteracaoRepository(s).da_pesquisa(pesquisa_id)

    def obter(self, aluno_id: int, interacao_id: int) -> Interacao:
        """Interação com suas fontes e os trechos ligados a cada fonte (RF27)."""
        with self._sf() as s:
            return self._da_aluno(s, aluno_id, interacao_id)

    def editar(
        self,
        aluno_id: int,
        interacao_id: int,
        ferramenta_ia: str | None = None,
        pergunta: str | None = None,
        resposta: str | None = None,
    ) -> Interacao:
        """RF13: corrige os textos da interação. As fontes ligadas não são tocadas.

        Campos None ou vazios mantêm o valor atual.
        """
        with self._sf.begin() as s:
            interacao = self._da_aluno(s, aluno_id, interacao_id)
            if ferramenta_ia and ferramenta_ia.strip():
                interacao.ferramenta_ia = ferramenta_ia.strip()
            if pergunta and pergunta.strip():
                interacao.pergunta = pergunta.strip()
            if resposta and resposta.strip():
                interacao.resposta = resposta.strip()
            return InteracaoRepository(s).salvar(interacao)

    def excluir(self, aluno_id: int, interacao_id: int) -> None:
        """RF14: apaga a interação; fontes e trechos dela saem junto (cascade).

        A confirmação com o usuário é feita pela interface antes de chamar este método.
        """
        with self._sf.begin() as s:
            interacao = self._da_aluno(s, aluno_id, interacao_id)
            InteracaoRepository(s).excluir(interacao)

    @staticmethod
    def _da_aluno(s, aluno_id: int, interacao_id: int) -> Interacao:
        interacao = InteracaoRepository(s).por_id(interacao_id)
        if not interacao or interacao.pesquisa.aluno_id != aluno_id:
            raise RegraViolada("Interação não encontrada.")
        return interacao


# --------------------------------------------------------------------------- fontes


STATUS_VERIFICACAO = ("verificada", "incorreta")


class FonteService(_ServicoBase):
    def adicionar(self, aluno_id: int, interacao_id: int, referencia: str) -> Fonte:
        referencia = _obrigatorio(referencia, "referência")
        with self._sf.begin() as s:
            InteracaoService._da_aluno(s, aluno_id, interacao_id)
            return FonteRepository(s).salvar(Fonte(referencia=referencia, interacao_id=interacao_id))

    def verificar(
        self,
        aluno_id: int,
        fonte_id: int,
        status: str,
        anotacao: str | None = None,
        trecho: str | None = None,
        localizacao: str | None = None,
    ) -> Fonte:
        """Marca a fonte como verificada ou incorreta.

        RF18: a anotação do que o aluno encontrou fica salva na fonte.
        RF26: se a fonte foi verificada, o aluno pode informar o trecho do texto
        em que a usou; o trecho fica salvo ligado à fonte.
        """
        if status not in STATUS_VERIFICACAO:
            raise RegraViolada("Status deve ser 'verificada' ou 'incorreta'.")
        trecho = (trecho or "").strip()
        if trecho and status != "verificada":
            raise RegraViolada("Só é possível ligar um trecho a uma fonte verificada.")
        with self._sf.begin() as s:
            repo = FonteRepository(s)
            fonte = self._da_aluno(s, aluno_id, fonte_id)
            fonte.status = status
            fonte.data_verificacao = datetime.now()
            if anotacao is not None and anotacao.strip():
                fonte.anotacao_correcao = anotacao.strip()
            if trecho:
                repo.adicionar_trecho(
                    Trecho(
                        trecho_citado=trecho,
                        localizacao=(localizacao or "").strip() or None,
                        fonte_id=fonte.id,
                    )
                )
            repo.salvar(fonte)
            s.refresh(fonte, ["trechos"])
            return fonte

    def vincular_trecho(
        self, aluno_id: int, fonte_id: int, trecho: str, localizacao: str | None = None
    ) -> Trecho:
        """RF26: liga mais um trecho a uma fonte já verificada."""
        trecho = _obrigatorio(trecho, "trecho")
        with self._sf.begin() as s:
            fonte = self._da_aluno(s, aluno_id, fonte_id)
            if fonte.status != "verificada":
                raise RegraViolada("Só é possível ligar um trecho a uma fonte verificada.")
            return FonteRepository(s).adicionar_trecho(
                Trecho(
                    trecho_citado=trecho,
                    localizacao=(localizacao or "").strip() or None,
                    fonte_id=fonte.id,
                )
            )

    @staticmethod
    def _da_aluno(s, aluno_id: int, fonte_id: int) -> Fonte:
        fonte = FonteRepository(s).por_id(fonte_id)
        if not fonte or fonte.interacao.pesquisa.aluno_id != aluno_id:
            raise RegraViolada("Fonte não encontrada.")
        return fonte


# --------------------------------------------------------------------------- relatório


@dataclass
class TrechoRel:
    texto: str
    localizacao: str | None


@dataclass
class FonteRel:
    referencia: str
    status: str
    anotacao: str | None
    data_verificacao: datetime | None
    trechos: list[TrechoRel] = field(default_factory=list)


@dataclass
class InteracaoRel:
    ferramenta_ia: str
    pergunta: str
    resposta: str
    data_registro: datetime
    fontes: list[FonteRel] = field(default_factory=list)


@dataclass
class ConteudoRelatorio:
    relatorio_id: int
    pesquisa_id: int
    titulo: str
    objetivo: str
    aluno: str
    data_geracao: datetime
    interacoes: list[InteracaoRel] = field(default_factory=list)

    @property
    def total_fontes(self) -> int:
        return sum(len(i.fontes) for i in self.interacoes)

    def contagem_status(self) -> dict[str, int]:
        cont = {"verificada": 0, "incorreta": 0, "nao_verificada": 0}
        for i in self.interacoes:
            for f in i.fontes:
                cont[f.status] = cont.get(f.status, 0) + 1
        return cont


class RelatorioService(_ServicoBase):
    def gerar(self, usuario: Usuario, pesquisa_id: int) -> ConteudoRelatorio:
        """RF20: monta o relatório a partir do que já está registrado, sem digitação extra.
        RF22: o relatório é sempre o único ligado a esta pesquisa.

        Professor vê qualquer pesquisa; aluno só as próprias.
        """
        with self._sf.begin() as s:
            pesquisa = PesquisaRepository(s).completa(pesquisa_id)
            if not pesquisa or (usuario.tipo != "professor" and pesquisa.aluno_id != usuario.id):
                raise RegraViolada("Pesquisa não encontrada.")

            relatorio = pesquisa.relatorio or RelatorioRepository(s).salvar(
                Relatorio(pesquisa_id=pesquisa.id)
            )
            relatorio.data_geracao = datetime.now()
            RelatorioRepository(s).salvar(relatorio)

            return ConteudoRelatorio(
                relatorio_id=relatorio.id,
                pesquisa_id=pesquisa.id,
                titulo=pesquisa.titulo,
                objetivo=pesquisa.objetivo,
                aluno=pesquisa.aluno.nome,
                data_geracao=relatorio.data_geracao,
                interacoes=[
                    InteracaoRel(
                        ferramenta_ia=i.ferramenta_ia,
                        pergunta=i.pergunta,
                        resposta=i.resposta,
                        data_registro=i.data_registro,
                        fontes=[
                            FonteRel(
                                referencia=f.referencia,
                                status=f.status,
                                anotacao=f.anotacao_correcao,
                                data_verificacao=f.data_verificacao,
                                trechos=[
                                    TrechoRel(t.trecho_citado, t.localizacao) for t in f.trechos
                                ],
                            )
                            for f in sorted(i.fontes, key=lambda f: f.id)
                        ],
                    )
                    for i in sorted(pesquisa.interacoes, key=lambda i: i.id)
                ],
            )
