export type Tipo = "aluno" | "professor";
export type StatusPesquisa = "em_andamento" | "entregue" | "concluida";
export type StatusFonte = "verificada" | "incorreta" | "nao_verificada";

export interface Usuario { id: string; nome: string; email: string; tipo: Tipo }
export interface Contagem { verificada: number; incorreta: number; nao_verificada: number }
export interface Pessoa { id: string; nome: string }

export interface Trecho { id: string; trecho: string; localizacao: string | null }
export interface Fonte {
  id: string; interacao_id: string; referencia: string; link: string | null; status: StatusFonte;
  anotacao: string | null; data_verificacao: string | null; julgada_pelo_professor: boolean; trechos: Trecho[];
  voltou_a_nao_verificada?: boolean;
}
export interface InteracaoResumo {
  id: string; pesquisa_id: string; ferramenta: string; pergunta: string; data_registro: string;
  confirmada: boolean; tem_comentario: boolean; contagem: Contagem;
}
export interface Interacao extends InteracaoResumo {
  resposta: string; comentario: string | null; data_comentario: string | null; fontes: Fonte[];
  pesquisa: { id: string; titulo: string; status: StatusPesquisa; turma_id: string; turma: string | null; autor?: string };
}
export interface Pesquisa {
  id: string; titulo: string; objetivo: string; status: StatusPesquisa; devolvida: boolean; de_grupo: boolean;
  data_criacao: string; data_entrega: string | null; data_conclusao: string | null; data_devolucao: string | null;
  mensagem_devolucao: string | null;
  turma: { id: string; nome: string } | null; aluno: Pessoa | null;
  grupo: { id: string; nome: string; alunos: Pessoa[] } | null;
  n_interacoes: number; contagem: Contagem; interacoes?: InteracaoResumo[];
}
export interface Convite {
  id: string; grupo: { id: string; nome: string } | null; titulo: string | null;
  convidado_por: string | null; integrantes: string[];
}
export interface Grupo {
  id: string; nome: string; titulo: string; objetivo: string; turma_id: string; alunos: Pessoa[];
  convites_pendentes: number; pesquisa: Pesquisa | null;
}
export interface TurmaAluno {
  id: string; nome: string; permite_grupos: boolean; professor: string | null; convites?: Convite[];
}
export interface TurmaProfessor {
  id: string; nome: string; codigo: string; permite_grupos: boolean;
  n_alunos: number; n_pesquisas: number; n_grupos: number; aguardando_revisao: number;
  alunos?: { id: string; nome: string; grupos: string[]; pesquisas: Pesquisa[] }[];
  sem_grupo?: Pessoa[]; grupos?: Grupo[]; alunos_lista?: Pessoa[];
}
export interface Relatorio {
  situacao: "previa" | "entregue" | "concluida";
  pesquisa: {
    id: string; titulo: string; objetivo: string; status: StatusPesquisa; data_entrega: string | null;
    data_conclusao: string | null; turma: string | null; aluno: string | null;
    grupo: { nome: string; alunos: string[] } | null;
  };
  contagem: Contagem; n_interacoes: number; n_fontes: number; interacoes: Interacao[];
}
