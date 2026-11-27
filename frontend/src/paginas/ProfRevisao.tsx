import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { dataHora, nomes, plural, resumoFontes } from "../formato";
import { Andamento, Btn, Cabecalho, Confirmar, DialogoCampos, Estado, Pagina, Recado, Selo, SeloPesquisa, Vazio, useAviso, useCarga } from "../ui";

export default function ProfRevisao() {
  const { id = "" } = useParams();
  const { dados: p, erro, recarregar } = useCarga(() => api.profPesquisa(id), [id]);
  const [d, setD] = useState<null | "aceitar" | "devolver">(null);
  const navegar = useNavigate();
  const aviso = useAviso();
  const emRevisao = p?.status === "entregue";
  const entregue = p?.status === "entregue" || p?.status === "concluida";
  const interacoes = p?.interacoes ?? [];
  return (
    <Pagina nav="turmas" tutorial="prof_pesquisa" migalhas={[
      { texto: "Minhas turmas", para: "/professor/turmas" },
      { texto: p?.turma?.nome ?? "Turma", para: `/professor/turmas/${p?.turma?.id ?? ""}` },
      { texto: p?.titulo ?? "Pesquisa", para: `/professor/pesquisas/${id}` },
    ]}>
      <Estado erro={erro} carregando={!p} voltarPara="/professor/pesquisas" />
      {p && (
        <>
          <Cabecalho selo={<SeloPesquisa p={p} visao="professor" />} titulo={p.titulo}
            subtitulo={<>{p.de_grupo && p.grupo ? `Grupo ${p.grupo.nome} · integrantes: ${nomes(p.grupo.alunos)}` : `Aluno: ${p.aluno?.nome}`}  ·  Turma: {p.turma?.nome}<br />{p.objetivo}</>} />
          <Andamento p={p} />
          {emRevisao && <Recado tipo="warn" icone="clock" titulo={`Entregue em ${dataHora(p.data_entrega)}: aguardando a sua revisão`}>Abra cada interação para julgar as fontes, comentar e confirmar. Depois, aceite a pesquisa ou devolva-a ao aluno com uma mensagem.</Recado>}
          {p.status === "concluida" && <Recado tipo="ok" icone="check" titulo={`Concluída em ${dataHora(p.data_conclusao)}`}>Você aceitou esta pesquisa. Ela não pode mais ser alterada.</Recado>}
          {p.devolvida && <Recado tipo="bad" icone="undo" titulo={`Devolvida ao aluno em ${dataHora(p.data_devolucao)}`}>Sua mensagem: {p.mensagem_devolucao}{"\n\n"}O aluno está ajustando. Você acompanha o que ele faz; a revisão volta quando ele entregar de novo.</Recado>}
          {p.status === "em_andamento" && !p.devolvida && <Recado tipo="info" icone="eye" titulo="Em andamento com o aluno">Você pode acompanhar o que ele registrou, mas só consegue revisar depois que ele entregar a pesquisa.</Recado>}
          <div className="actions">
            <Btn icone="file" desabilitado={!entregue} dica={entregue ? undefined : "O relatório fica disponível quando o aluno entregar a pesquisa."} onClick={() => navegar(`/pesquisas/${p.id}/relatorio`)}>Ver relatório</Btn>
            <span style={{ flex: 1 }} />
            {emRevisao && <><Btn tipo="danger" icone="undo" onClick={() => setD("devolver")}>Devolver ao aluno</Btn><Btn tipo="primary" icone="check" onClick={() => setD("aceitar")}>Aceitar pesquisa</Btn></>}
          </div>
          <div className="sec" style={{ marginTop: 6 }}><h2>Interações com IA</h2></div>
          {interacoes.length === 0 ? <Vazio>O aluno ainda não registrou nenhuma interação.</Vazio> : (
            <div className="card list">
              {interacoes.map((i) => (
                <Link key={i.id} className="row link" to={`/professor/interacoes/${i.id}`}>
                  <div>
                    <div className="t"><Selo tipo="plain">{i.ferramenta}</Selo><span style={{ fontWeight: 400, color: "var(--faint)", fontSize: ".84rem" }}>{dataHora(i.data_registro)}</span></div>
                    <div className="m" style={{ color: "var(--ink)", fontFamily: "var(--serif)", fontSize: ".98rem", marginTop: 6 }}>{i.pergunta.length > 140 ? i.pergunta.slice(0, 139) + "…" : i.pergunta}</div>
                  </div>
                  <div className="side-r">
                    <span className="m" style={{ margin: 0 }}>{resumoFontes(i.contagem)}</span>
                    <div className="actions" style={{ justifyContent: "flex-end" }}>{i.confirmada && <Selo tipo="ok">Confirmada</Selo>}{i.tem_comentario && <Selo tipo="info">Comentada</Selo>}</div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
      {p && d === "aceitar" && (() => {
        const pendentes = p.contagem.nao_verificada;
        const abertas = interacoes.filter((i) => !i.confirmada).length;
        let texto = "A pesquisa ficará concluída e não poderá mais ser alterada pelo aluno nem por você.";
        if (abertas) texto = `${plural(abertas, "interação ainda não confirmada será fechada", "interações ainda não confirmadas serão fechadas")}. ` + texto;
        if (pendentes) texto = `Ainda há ${plural(pendentes, "fonte", "fontes")} sem julgamento. ` + texto;
        return <Confirmar titulo="Aceitar esta pesquisa?" texto={texto} rotuloOk="Aceitar pesquisa" onFechar={() => setD(null)}
          onConfirmar={async () => { await api.profAceitar(p.id); setD(null); aviso("Pesquisa aceita e concluída."); recarregar(); }} />;
      })()}
      {p && d === "devolver" && (
        <DialogoCampos titulo="Devolver pesquisa ao aluno" rotuloOk="Devolver ao aluno" perigo onFechar={() => setD(null)}
          subtitulo="A pesquisa volta a “em andamento” para o aluno ajustar, e ele lê esta mensagem no sistema. Interações que você confirmou continuam fechadas."
          campos={[{ nome: "mensagem", rotulo: "Mensagem para o aluno", tipo: "area", altura: 130, dica: "Explique por que a pesquisa não foi aceita e o que ajustar." }]}
          onEnviar={async (v) => { await api.profDevolver(p.id, v.mensagem); setD(null); aviso("Pesquisa devolvida ao aluno com a sua mensagem."); recarregar(); }} />
      )}
    </Pagina>
  );
}
