"""Armazenamento dos dados: Firebase (Firestore) de verdade e uma versão em memória para os testes.

O resto do programa (repositórios) só conversa com a interface `Armazenamento` abaixo; ele não sabe
se os dados estão na nuvem ou na memória.

Vocabulário (Firestore -> este arquivo):
  * coleção  = "tabela" (usuarios, turmas, pesquisas, ...)
  * documento = "linha": um dicionário com um id de texto
  * lote      = várias gravações que valem juntas (tudo ou nada), como uma transação

O Firestore não tem chave estrangeira nem UNIQUE. Por isso:
  * o que precisa ser único (e-mail, código da turma, matrícula...) usa um id de documento
    determinístico e a operação `criar`, que falha se o documento já existe;
  * apagar algo apaga também o que depende dele, feito pelos repositórios (ver repository/cascata.py).
"""
import copy
import hashlib
import os
import threading
import time
from datetime import datetime, timezone

LIMITE_DO_LOTE = 500  # o Firestore aceita até 500 operações por lote
FILTRO_IN_MAXIMO = 30  # e até 30 valores num filtro "in"


class ErroDeIntegridade(Exception):
    """Dado que fere uma regra de integridade (valor inválido, documento que não existe...)."""


class Duplicado(ErroDeIntegridade):
    """Tentativa de criar um documento que já existe (e-mail, código de turma, matrícula...)."""


class ErroDeConfiguracao(RuntimeError):
    """O Firebase não está configurado (falta o arquivo de credenciais, por exemplo)."""


def agora():
    """Data/hora atual do computador (sem fuso), como os campos de data do programa."""
    return datetime.now()


def chave_unica(tipo, valor):
    """Id do documento da coleção 'unicos' que garante que um valor (e-mail, código) não se repita."""
    return f"{tipo}-{hashlib.sha256(valor.encode('utf-8')).hexdigest()[:40]}"


def normalizar_ids(dados):
    """Campos que terminam em _id são sempre texto (no Firestore o id do documento é texto)."""
    return {
        k: (str(v) if k.endswith("_id") and v is not None else v) for k, v in dados.items()
    }


class Lote:
    """Acumula gravações e as aplica de uma vez em `confirmar()` (tudo ou nada, até 500 operações)."""

    def __init__(self, loja):
        self._loja = loja
        self.operacoes = []

    def criar(self, colecao, id_, dados):
        """Cria o documento; no `confirmar`, levanta Duplicado se ele já existir."""
        self.operacoes.append(("criar", colecao, str(id_), normalizar_ids(dados)))
        return self

    def gravar(self, colecao, id_, dados):
        """Grava o documento inteiro (cria ou substitui)."""
        self.operacoes.append(("gravar", colecao, str(id_), normalizar_ids(dados)))
        return self

    def atualizar(self, colecao, id_, campos):
        """Muda só estes campos de um documento que já existe."""
        self.operacoes.append(("atualizar", colecao, str(id_), normalizar_ids(campos)))
        return self

    def apagar(self, colecao, id_):
        self.operacoes.append(("apagar", colecao, str(id_), None))
        return self

    def __len__(self):
        return len(self.operacoes)

    def confirmar(self):
        operacoes, self.operacoes = self.operacoes, []
        if operacoes:
            self._loja._aplicar(operacoes)


class Armazenamento:
    """Interface. Todo documento devolvido é um dicionário que já traz a chave 'id'."""

    def novo_id(self):
        raise NotImplementedError

    def obter(self, colecao, id_):
        raise NotImplementedError

    def obter_varios(self, colecao, ids):
        """{id: documento} dos ids que existem."""
        raise NotImplementedError

    def consultar(self, colecao, **igual):
        """Documentos em que cada campo é igual ao valor dado (sem ordem garantida)."""
        raise NotImplementedError

    def consultar_em(self, colecao, campo, valores, **igual):
        """Como `consultar`, mas `campo` pode ser qualquer um dos `valores`."""
        raise NotImplementedError

    def _aplicar(self, operacoes):
        raise NotImplementedError

    # -- atalhos
    def lote(self):
        return Lote(self)

    def criar(self, colecao, id_, dados):
        self.lote().criar(colecao, id_, dados).confirmar()

    def atualizar(self, colecao, id_, campos):
        self.lote().atualizar(colecao, id_, campos).confirmar()

    def apagar(self, colecao, id_):
        self.lote().apagar(colecao, id_).confirmar()


# ---------------------------------------------------------------------------------- memória
class MemoryStore(Armazenamento):
    """Tudo na memória: usado nos testes (rápido, sem internet) e serve de modelo do comportamento
    esperado do Firestore. Os ids são "1", "2", ... na ordem de criação."""

    def __init__(self):
        self._dados = {}
        self._contador = 0
        self._trava = threading.RLock()

    def novo_id(self):
        with self._trava:
            self._contador += 1
            return str(self._contador)

    def obter(self, colecao, id_):
        with self._trava:
            doc = self._dados.get(colecao, {}).get(str(id_))
            return None if doc is None else {**copy.deepcopy(doc), "id": str(id_)}

    def obter_varios(self, colecao, ids):
        achados = {}
        for id_ in dict.fromkeys(str(i) for i in ids if i is not None):
            doc = self.obter(colecao, id_)
            if doc is not None:
                achados[id_] = doc
        return achados

    def consultar(self, colecao, **igual):
        igual = normalizar_ids(igual)
        with self._trava:
            return [
                {**copy.deepcopy(doc), "id": id_}
                for id_, doc in self._dados.get(colecao, {}).items()
                if all(doc.get(k) == v for k, v in igual.items())
            ]

    def consultar_em(self, colecao, campo, valores, **igual):
        valores = {str(v) if campo.endswith("_id") else v for v in valores}
        return [d for d in self.consultar(colecao, **igual) if d.get(campo) in valores]

    def _aplicar(self, operacoes):
        with self._trava:
            # 1) confere tudo; se algo falhar, nada é gravado (como num lote do Firestore)
            existentes = {(c, i) for c, docs in self._dados.items() for i in docs}
            for tipo, colecao, id_, _ in operacoes:
                chave = (colecao, id_)
                if tipo == "criar":
                    if chave in existentes:
                        raise Duplicado(f"{colecao}/{id_} já existe")
                    existentes.add(chave)
                elif tipo == "gravar":
                    existentes.add(chave)
                elif tipo == "atualizar":
                    if chave not in existentes:
                        raise ErroDeIntegridade(f"{colecao}/{id_} não existe")
                elif tipo == "apagar":
                    existentes.discard(chave)
            # 2) aplica
            for tipo, colecao, id_, dados in operacoes:
                docs = self._dados.setdefault(colecao, {})
                if tipo in ("criar", "gravar"):
                    docs[id_] = copy.deepcopy(dados)
                elif tipo == "atualizar":
                    docs[id_].update(copy.deepcopy(dados))
                else:
                    docs.pop(id_, None)

    def contar(self, colecao):
        """Quantos documentos há na coleção (útil nos testes)."""
        with self._trava:
            return len(self._dados.get(colecao, {}))


# ---------------------------------------------------------------------------------- Firestore
def _para_nuvem(dados):
    """Datas sem fuso (horário do computador) viram UTC ao gravar."""
    return {
        k: (v.astimezone(timezone.utc) if isinstance(v, datetime) and v.tzinfo is None else v)
        for k, v in dados.items()
    }


def _da_nuvem(dados):
    """E voltam a ser datas sem fuso, no horário do computador, ao ler."""
    return {
        k: (v.astimezone().replace(tzinfo=None) if isinstance(v, datetime) and v.tzinfo else v)
        for k, v in dados.items()
    }


class FirestoreStore(Armazenamento):
    """Os dados no Firestore (Firebase), pela biblioteca oficial google-cloud-firestore."""

    def __init__(self, cliente):
        self._cliente = cliente
        self._ultimo_id = 0
        self._trava = threading.Lock()

    def novo_id(self):
        """Id que cresce com o tempo (19 dígitos), para que "mais novo" seja também "id maior".
        O Firestore sortearia um id aleatório; assim a ordem de criação é preservada no desempate."""
        with self._trava:
            self._ultimo_id = max(self._ultimo_id + 1, time.time_ns())
            return f"{self._ultimo_id:019d}"

    def _doc(self, snap):
        return {**_da_nuvem(snap.to_dict() or {}), "id": snap.id}

    def obter(self, colecao, id_):
        snap = self._cliente.collection(colecao).document(str(id_)).get()
        return self._doc(snap) if snap.exists else None

    def obter_varios(self, colecao, ids):
        ids = list(dict.fromkeys(str(i) for i in ids if i is not None))
        if not ids:
            return {}
        refs = [self._cliente.collection(colecao).document(i) for i in ids]
        return {s.id: self._doc(s) for s in self._cliente.get_all(refs) if s.exists}

    def _consulta(self, colecao, igual, extra=None):
        from google.cloud.firestore_v1.base_query import FieldFilter

        consulta = self._cliente.collection(colecao)
        for campo, valor in igual.items():
            consulta = consulta.where(filter=FieldFilter(campo, "==", valor))
        if extra is not None:
            consulta = consulta.where(filter=FieldFilter(*extra))
        return [self._doc(s) for s in consulta.stream()]

    def consultar(self, colecao, **igual):
        return self._consulta(colecao, normalizar_ids(igual))

    def consultar_em(self, colecao, campo, valores, **igual):
        valores = list(dict.fromkeys((str(v) if campo.endswith("_id") else v) for v in valores if v is not None))
        igual = normalizar_ids(igual)
        achados = []
        for i in range(0, len(valores), FILTRO_IN_MAXIMO):
            achados += self._consulta(colecao, igual, (campo, "in", valores[i : i + FILTRO_IN_MAXIMO]))
        return achados

    def _aplicar(self, operacoes):
        from google.api_core import exceptions as erros

        for inicio in range(0, len(operacoes), LIMITE_DO_LOTE):
            lote = self._cliente.batch()
            for tipo, colecao, id_, dados in operacoes[inicio : inicio + LIMITE_DO_LOTE]:
                ref = self._cliente.collection(colecao).document(id_)
                if tipo == "criar":
                    lote.create(ref, _para_nuvem(dados))
                elif tipo == "gravar":
                    lote.set(ref, _para_nuvem(dados))
                elif tipo == "atualizar":
                    lote.update(ref, _para_nuvem(dados))
                else:
                    lote.delete(ref)
            try:
                lote.commit()
            except erros.AlreadyExists as erro:
                raise Duplicado(str(erro)) from erro
            except erros.NotFound as erro:
                raise ErroDeIntegridade(str(erro)) from erro


def conectar():
    """Cria o cliente do Firestore a partir do .env:

    FIREBASE_CREDENCIAIS  caminho do arquivo JSON da conta de serviço (baixado no console do Firebase)
    FIREBASE_PROJETO      (opcional) id do projeto; se faltar, é lido do próprio JSON

    Se FIRESTORE_EMULATOR_HOST estiver definido, usa o emulador local do Firebase, sem credenciais.
    Se REGISTRO_IA_BANCO=memoria, não usa o Firebase: os dados ficam só na memória (para demonstração)."""
    from dotenv import load_dotenv

    load_dotenv()
    if os.getenv("REGISTRO_IA_BANCO", "").strip().lower() == "memoria":
        # modo de demonstração: tudo fica só na memória e some ao fechar o servidor
        return MemoryStore()
    from google.cloud import firestore

    projeto = os.getenv("FIREBASE_PROJETO") or None
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        return FirestoreStore(firestore.Client(project=projeto or "projeto-local"))

    caminho = os.getenv("FIREBASE_CREDENCIAIS", "").strip()
    if not caminho:
        raise ErroDeConfiguracao(
            "O Firebase não está configurado. No arquivo .env, preencha FIREBASE_CREDENCIAIS com o "
            "caminho do arquivo JSON da conta de serviço (veja o README, seção 'Firebase')."
        )
    caminho = os.path.expanduser(caminho)
    if not os.path.isfile(caminho):
        raise ErroDeConfiguracao(
            f"Não encontrei o arquivo de credenciais do Firebase em: {caminho}\n"
            "Confira o caminho em FIREBASE_CREDENCIAIS no arquivo .env."
        )
    return FirestoreStore(firestore.Client.from_service_account_json(caminho, project=projeto))


_loja = None


def loja():
    """O armazenamento em uso (conecta ao Firebase na primeira vez)."""
    global _loja
    if _loja is None:
        _loja = conectar()
    return _loja


def usar(nova):
    """Troca o armazenamento em uso (os testes colocam um MemoryStore aqui)."""
    global _loja
    _loja = nova
