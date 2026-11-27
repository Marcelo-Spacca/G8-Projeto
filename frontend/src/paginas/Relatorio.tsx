import { useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { dataHora } from "../formato";
import type { Fonte, Interacao } from "../tipos";
import { Btn, Cabecalho, ContagemSelos, Estado, Pagina, Selo, SeloFonte, useCarga } from "../ui";

function TabelaFontes({ fontes }: { fontes: Fonte[] }) {
  return (
    <div className="scroll-x" style={{ marginTop: 12 }}>
      <table>
        <thead><tr><th style={{ width: "38%" }}>Fonte</th><th style={{ width: "22%" }}>Status</th><th>Trecho no texto do aluno</th></tr></thead>
        <tbody>
          {fontes.map((f) => (
            <tr key={f.id}>
              <td>
                <b>{f.referencia}</b>
                {f.link && <><br /><span style={{ color: "#2547D0", overflowWrap: "anywhere" }}>{f.link}</span></>}
                {f.julgada_pelo_professor && <><br /><span style={{ color: "#2547D0", fontWeight: 600 }}>Julgada pelo professor</span></>}
                {f.anotacao && <><br /><span style={{ color: "#5A6680" }}>Anotação do {f.julgada_pelo_professor ? "professor" : "aluno"}: {f.anotacao}</span></>}
              </td>
              <td><SeloFonte status={f.status} /></td>
              <td>
                {f.trechos.length === 0
                  ? <span style={{ color: "#8590A6" }}>{f.status === "incorreta" ? "— sem trecho (fonte descartada)" : "— sem trecho ligado"}</span>
                  : f.trechos.map((t) => <p key={t.id} style={{ margin: "0 0 8px" }}><span className="mark">“{t.trecho}”</span>{t.localizacao && <small style={{ color: "#5A6680" }}> ({t.localizacao})</small>}</p>)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BlocoInteracao({ n, i }: { n: number; i: Interacao }) {
  return (
    <div>
      <h3>Interação {n}: {i.ferramenta} <span style={{ fontWeight: 400, color: "#5A6680", fontSize: ".9rem" }}>{dataHora(i.data_registro)}</span>
        {i.confirmada && <span style={{ color: "#107A57", fontSize: ".85rem", marginLeft: 8 }}>✓ confirmada pelo professor</span>}</h3>
      <span className="lab">Pergunta</span><p style={{ whiteSpace: "pre-line", margin: 0 }}>{i.pergunta}</p>
      <span className="lab" style={{ marginTop: 8 }}>Resposta da IA</span><p style={{ whiteSpace: "pre-line", margin: 0 }}>{i.resposta}</p>
      {i.fontes.length > 0 ? <TabelaFontes fontes={i.fontes} /> : <p style={{ color: "#8590A6" }}>Nenhuma fonte citada nesta interação.</p>}
      {i.comentario && <div className="coment"><b>Comentário do professor</b><br />{i.comentario}</div>}
    </div>
  );
}

export default function RelatorioPagina() {
  const { id = "" } = useParams();
  const { usuario } = useAuth();
  const prof = usuario?.tipo === "professor";
  const { dados: r, erro } = useCarga(() => api.relatorio(id), [id]);
  const tutorial = prof ? "relatorio_professor" : "relatorio_aluno";
  const migalhas = prof
    ? [{ texto: "Minhas turmas", para: "/professor/turmas" }, { texto: r?.pesquisa.titulo ?? "Pesquisa", para: `/professor/pesquisas/${id}` }, { texto: "Relatório", para: `/pesquisas/${id}/relatorio` }]
    : [{ texto: "Minhas turmas", para: "/aluno/turmas" }, { texto: r?.pesquisa.titulo ?? "Pesquisa", para: `/aluno/pesquisas/${id}` }, { texto: "Relatório", para: `/pesquisas/${id}/relatorio` }];
  let nota = "";
  if (r) {
    if (r.situacao === "concluida") nota = "Pesquisa concluída: o professor aceitou este relatório.";
    else if (r.situacao === "entregue") nota = prof ? "O aluno entregou esta pesquisa para a sua verificação." : "Este relatório foi entregue ao professor, que está revisando.";
    else if (!prof) nota = "Isto é uma prévia. Ao entregar a pesquisa, o relatório fica disponível para o professor.";
  }
  const sit = r && (r.situacao === "concluida"
    ? [`#107A57`, `Concluída: aceita pelo professor em ${dataHora(r.pesquisa.data_conclusao)}`]
    : r.situacao === "entregue" ? ["#9A5B05", `Entregue em ${dataHora(r.pesquisa.data_entrega)}, aguardando a revisão do professor`]
    : ["#9A5B05", "Prévia: a pesquisa ainda não foi entregue ao professor"]);
  return (
    <Pagina nav="turmas" tutorial={tutorial} migalhas={migalhas}>
      <Estado erro={erro} carregando={!r} voltarPara={prof ? "/professor/turmas" : "/aluno/turmas"} />
      {r && sit && (
        <>
          <div className="no-print"><Cabecalho titulo="Relatório" subtitulo={nota} acoes={<Btn icone="down" onClick={() => window.print()}>Salvar como PDF</Btn>} /></div>
          <div className="paper">
            <div><h1>Relatório de uso de IA</h1><p className="sit" style={{ color: sit[0], marginTop: 6 }}>{sit[1]}</p></div>
            <dl>
              <dt>Pesquisa</dt><dd>{r.pesquisa.titulo}</dd>
              {r.pesquisa.turma && <><dt>Turma</dt><dd>{r.pesquisa.turma}</dd></>}
              {r.pesquisa.grupo ? <><dt>Grupo</dt><dd>{r.pesquisa.grupo.nome}</dd><dt>Integrantes</dt><dd>{r.pesquisa.grupo.alunos.join(", ")}</dd></> : <><dt>Aluno</dt><dd>{r.pesquisa.aluno}</dd></>}
              <dt>Objetivo</dt><dd style={{ whiteSpace: "pre-line" }}>{r.pesquisa.objetivo}</dd>
            </dl>
            <div className="tally">
              <Selo tipo="plain">{r.n_interacoes} {r.n_interacoes === 1 ? "interação" : "interações"}</Selo>
              <Selo tipo="plain">{r.n_fontes} {r.n_fontes === 1 ? "fonte" : "fontes"}</Selo>
            </div>
            <ContagemSelos c={r.contagem} />
            {r.interacoes.length === 0
              ? <p style={{ color: "#8590A6" }}>Nenhuma interação registrada nesta pesquisa.</p>
              : r.interacoes.map((i, n) => <BlocoInteracao key={i.id} n={n + 1} i={i} />)}
          </div>
        </>
      )}
    </Pagina>
  );
}
