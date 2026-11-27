import type {
  Contagem, Convite, Fonte, Grupo, Interacao, Pesquisa, Pessoa, Relatorio, TurmaAluno, TurmaProfessor, Usuario,
} from "./tipos";

const CHAVE = "registro-ia:token";

export function lerToken(): string | null {
  try { return localStorage.getItem(CHAVE); } catch { return null; }
}
export function guardarToken(token: string | null) {
  try {
    if (token) localStorage.setItem(CHAVE, token); else localStorage.removeItem(CHAVE);
  } catch { /* navegador sem armazenamento: a sessão vale só até recarregar */ }
}

/** Erro com a mensagem pronta para o usuário (vem da regra de negócio no servidor). */
export class ErroApi extends Error {
  constructor(mensagem: string, public status: number) { super(mensagem); }
}

let aoExpirar: () => void = () => {};
export function quandoSessaoExpirar(f: () => void) { aoExpirar = f; }

async function pedir<T>(metodo: string, url: string, corpo?: unknown): Promise<T> {
  const cabecalhos: Record<string, string> = {};
  const token = lerToken();
  if (token) cabecalhos["Authorization"] = `Bearer ${token}`;
  if (corpo !== undefined) cabecalhos["Content-Type"] = "application/json";
  let resposta: Response;
  try {
    resposta = await fetch(url, { method: metodo, headers: cabecalhos, body: corpo === undefined ? undefined : JSON.stringify(corpo) });
  } catch {
    throw new ErroApi("Não consegui falar com o servidor. Confira se ele está rodando e tente de novo.", 0);
  }
  if (resposta.status === 204) return undefined as T;
  let dados: any = null;
  try { dados = await resposta.json(); } catch { /* sem corpo */ }
  if (!resposta.ok) {
    const texto = typeof dados?.detail === "string" ? dados.detail : "Não foi possível concluir. Tente de novo.";
    if (resposta.status === 401 && token) aoExpirar();
    throw new ErroApi(texto, resposta.status);
  }
  return dados as T;
}
const get = <T,>(u: string) => pedir<T>("GET", u);
const post = <T,>(u: string, c?: unknown) => pedir<T>("POST", u, c ?? {});
const put = <T,>(u: string, c: unknown) => pedir<T>("PUT", u, c);
const del = <T,>(u: string) => pedir<T>("DELETE", u);

export const api = {
  // acesso
  entrar: (email: string, senha: string) => post<{ token: string; usuario: Usuario }>("/api/auth/entrar", { email, senha }),
  cadastrar: (nome: string, email: string, senha: string, tipo: string) =>
    post<{ usuario: Usuario }>("/api/auth/cadastro", { nome, email, senha, tipo }),
  eu: () => get<Usuario>("/api/auth/eu"),
  sair: () => post<void>("/api/auth/sair"),

  // aluno
  alunoTurmas: () => get<TurmaAluno[]>("/api/aluno/turmas"),
  alunoEntrarNaTurma: (codigo: string) => post<TurmaAluno>("/api/aluno/turmas/entrar", { codigo }),
  alunoTurma: (id: string) => get<TurmaAluno>(`/api/aluno/turmas/${id}`),
  alunoPesquisasDaTurma: (id: string) => get<Pesquisa[]>(`/api/aluno/turmas/${id}/pesquisas`),
  alunoGruposDaTurma: (id: string) => get<Grupo[]>(`/api/aluno/turmas/${id}/grupos`),
  alunoCriarPesquisa: (turma: string, titulo: string, objetivo: string) =>
    post<Pesquisa>(`/api/aluno/turmas/${turma}/pesquisas`, { titulo, objetivo }),
  alunoCriarGrupo: (turma: string, nome: string, titulo: string, objetivo: string) =>
    post<Grupo>(`/api/aluno/turmas/${turma}/grupos`, { nome, titulo, objetivo }),
  alunoConvidaveis: (grupo: string) => get<Pessoa[]>(`/api/aluno/grupos/${grupo}/convidaveis`),
  alunoConvidar: (grupo: string, alunos_ids: string[]) => post<{ enviados: number }>(`/api/aluno/grupos/${grupo}/convites`, { alunos_ids }),
  alunoResponderConvite: (id: string, aceitar: boolean) =>
    post<{ grupo: { id: string; nome: string }; aceito: boolean }>(`/api/aluno/convites/${id}/resposta`, { aceitar }),
  alunoPesquisa: (id: string) => get<Pesquisa>(`/api/aluno/pesquisas/${id}`),
  alunoEditarPesquisa: (id: string, titulo: string, objetivo: string) => put<Pesquisa>(`/api/aluno/pesquisas/${id}`, { titulo, objetivo }),
  alunoEntregar: (id: string) => post<Pesquisa>(`/api/aluno/pesquisas/${id}/entrega`),
  alunoExcluirPesquisa: (id: string) => del<void>(`/api/aluno/pesquisas/${id}`),
  alunoRegistrarInteracao: (pesquisa: string, ferramenta: string, pergunta: string, resposta: string) =>
    post<Interacao>(`/api/aluno/pesquisas/${pesquisa}/interacoes`, { ferramenta, pergunta, resposta }),
  alunoInteracao: (id: string) => get<Interacao>(`/api/aluno/interacoes/${id}`),
  alunoEditarInteracao: (id: string, ferramenta: string, pergunta: string, resposta: string) =>
    put<Interacao>(`/api/aluno/interacoes/${id}`, { ferramenta, pergunta, resposta }),
  alunoExcluirInteracao: (id: string) => del<void>(`/api/aluno/interacoes/${id}`),
  alunoAdicionarFonte: (interacao: string, referencia: string, link: string) =>
    post<Fonte>(`/api/aluno/interacoes/${interacao}/fontes`, { referencia, link }),
  alunoEditarFonte: (id: string, referencia: string, link: string) => put<Fonte>(`/api/aluno/fontes/${id}`, { referencia, link }),
  alunoVerificarFonte: (id: string, resultado: string, anotacao: string, trecho: string, localizacao: string) =>
    post<Fonte>(`/api/aluno/fontes/${id}/verificacao`, { resultado, anotacao, trecho, localizacao }),
  alunoLigarTrecho: (id: string, trecho: string, localizacao: string) =>
    post<Fonte>(`/api/aluno/fontes/${id}/trechos`, { trecho, localizacao }),

  // relatório (aluno e professor)
  relatorio: (pesquisa: string) => get<Relatorio>(`/api/pesquisas/${pesquisa}/relatorio`),

  // professor
  profTurmas: () => get<TurmaProfessor[]>("/api/professor/turmas"),
  profCriarTurma: (nome: string, permite_grupos: boolean) => post<TurmaProfessor>("/api/professor/turmas", { nome, permite_grupos }),
  profTurma: (id: string) => get<TurmaProfessor>(`/api/professor/turmas/${id}`),
  profExcluirTurma: (id: string) => del<void>(`/api/professor/turmas/${id}`),
  profAtribuir: (grupo: string, aluno_id: string) => post<Grupo>(`/api/professor/grupos/${grupo}/alunos`, { aluno_id }),
  profRemover: (grupo: string, aluno: string) => del<Grupo>(`/api/professor/grupos/${grupo}/alunos/${aluno}`),
  profPesquisas: (turma?: string | null) =>
    get<{ turmas: Pessoa[]; turma_id: string | null; pesquisas: Pesquisa[] }>(`/api/professor/pesquisas${turma ? `?turma_id=${encodeURIComponent(turma)}` : ""}`),
  profPesquisa: (id: string) => get<Pesquisa>(`/api/professor/pesquisas/${id}`),
  profAceitar: (id: string) => post<Pesquisa>(`/api/professor/pesquisas/${id}/aceite`),
  profDevolver: (id: string, mensagem: string) => post<Pesquisa>(`/api/professor/pesquisas/${id}/devolucao`, { mensagem }),
  profInteracao: (id: string) => get<Interacao>(`/api/professor/interacoes/${id}`),
  profComentar: (id: string, comentario: string) => put<Interacao>(`/api/professor/interacoes/${id}/comentario`, { comentario }),
  profConfirmar: (id: string) => post<Interacao>(`/api/professor/interacoes/${id}/confirmacao`),
  profReabrir: (id: string) => del<Interacao>(`/api/professor/interacoes/${id}/confirmacao`),
  profJulgar: (id: string, resultado: string, anotacao: string) =>
    post<Fonte>(`/api/professor/fontes/${id}/julgamento`, { resultado, anotacao }),
};

export type { Contagem, Convite };
