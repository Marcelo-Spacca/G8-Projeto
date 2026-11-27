import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { Cabecalho, Estado, Pagina, Vazio, useCarga } from "../ui";
import { LinhaPesquisaProf } from "./linhas";

const SECOES: [string, string][] = [["entregue", "Aguardando sua revisão"], ["em_andamento", "Em andamento com os alunos"], ["concluida", "Concluídas"]];

export default function ProfPesquisas() {
  const [busca, setBusca] = useSearchParams();
  const turma = busca.get("turma");
  const { dados, erro } = useCarga(() => api.profPesquisas(turma), [turma]);
  return (
    <Pagina nav="pesquisas" tutorial="prof_lista" largo migalhas={[{ texto: "Minhas turmas", para: "/professor/turmas" }, { texto: "Pesquisas dos alunos", para: "/professor/pesquisas" }]}>
      <Cabecalho titulo="Pesquisas dos alunos" subtitulo="Acompanhe o que os alunos estão fazendo e revise as pesquisas que eles entregaram." />
      <Estado erro={erro} carregando={!dados} voltarPara="/professor/turmas" />
      {dados && (
        <>
          <div className="f" style={{ maxWidth: 340 }}>
            <label htmlFor="filtro">Turma</label>
            <select id="filtro" className="sel" value={dados.turma_id ?? ""} onChange={(e) => setBusca(e.target.value ? { turma: e.target.value } : {})}>
              <option value="">Todas as turmas</option>
              {dados.turmas.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
            </select>
          </div>
          {dados.pesquisas.length === 0 && <Vazio>{dados.turma_id ? "Nenhuma pesquisa nesta turma ainda." : "Nenhum aluno criou uma pesquisa ainda. Quando criarem, elas aparecem aqui."}</Vazio>}
          {SECOES.map(([status, titulo]) => {
            const itens = dados.pesquisas.filter((p) => p.status === status);
            if (!itens.length) return null;
            return (
              <div key={status} style={{ display: "grid", gap: 12 }}>
                <div className="group-title"><h2>{titulo}</h2><span>{itens.length}</span></div>
                <div className="card list">{itens.map((p) => <LinhaPesquisaProf key={p.id} p={p} mostrarTurma={!dados.turma_id} />)}</div>
              </div>
            );
          })}
        </>
      )}
    </Pagina>
  );
}
