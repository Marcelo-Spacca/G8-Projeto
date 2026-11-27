import { Link, useNavigate } from "react-router-dom";
import { dataHora, dia, plural, resumoFontesProf } from "../formato";
import type { Pesquisa } from "../tipos";
import { Btn, Icone, SeloPesquisa } from "../ui";

function quando(p: Pesquisa): string {
  if (p.status === "concluida") return `Concluída em ${dataHora(p.data_conclusao)}`;
  if (p.status === "entregue") return `Entregue em ${dataHora(p.data_entrega)}`;
  if (p.devolvida) return `Devolvida em ${dia(p.data_devolucao)}`;
  return p.de_grupo ? "Ainda com o grupo" : "Ainda com o aluno";
}

/** Linha de pesquisa da área do professor: título, quem fez, andamento, entrega, data e relatório. */
export function LinhaPesquisaProf({ p, mostrarAutor = true, mostrarTurma = false }: { p: Pesquisa; mostrarAutor?: boolean; mostrarTurma?: boolean }) {
  const navegar = useNavigate();
  const entregue = p.status === "entregue" || p.status === "concluida";
  const autor = p.de_grupo && p.grupo ? `Grupo ${p.grupo.nome}` : p.aluno?.nome;
  const partes: string[] = [];
  if (mostrarAutor && autor) partes.push(autor);
  if (mostrarTurma && p.turma) partes.push(p.turma.nome);
  partes.push(`${plural(p.n_interacoes, "interação", "interações")} · ${resumoFontesProf(p.contagem)}`);
  return (
    <div className="row" style={{ gridTemplateColumns: "minmax(0,1fr) auto auto" }}>
      <Link to={`/professor/pesquisas/${p.id}`} style={{ textDecoration: "none", color: "inherit", minWidth: 0 }}>
        <div className="t">{p.titulo}<SeloPesquisa p={p} visao="professor" /></div>
        <div className="m">{partes.join("  ·  ")}</div>
      </Link>
      <div className="side-r">
        <span style={{ display: "flex", gap: 8, alignItems: "center", fontSize: ".88rem", fontWeight: 550, color: entregue ? "var(--ok)" : "var(--muted)" }}>
          <span style={{ width: 18, height: 18, borderRadius: 5, display: "grid", placeItems: "center", ...(entregue ? { background: "var(--ok)", color: "#fff" } : { border: "1.5px solid var(--line-strong)" }) }}>
            {entregue && <Icone nome="check" />}
          </span>
          Entregue para verificação
        </span>
        <small>{quando(p)}</small>
      </div>
      <Btn sm icone="file" desabilitado={!entregue} dica={entregue ? undefined : "O relatório fica disponível quando o aluno entregar a pesquisa."} onClick={() => navegar(`/pesquisas/${p.id}/relatorio`)}>Relatório</Btn>
    </div>
  );
}
