import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { dataHora, nomes, plural, resumoFontes } from "../formato";
import type { Pesquisa } from "../tipos";
import { Andamento, Btn, Cabecalho, Confirmar, DialogoCampos, Estado, Pagina, Recado, SeloPesquisa, Selo, Vazio, useAviso, useCarga } from "../ui";
import { DialogoConvidar } from "./AlunoTurma";

export default function AlunoPesquisa() {
  const { id = "" } = useParams();
  const { dados: p, erro, recarregar } = useCarga(() => api.alunoPesquisa(id), [id]);
  const [dialogo, setDialogo] = useState<null | "editar" | "entregar" | "excluir" | "interacao" | "convidar">(null);
  const navegar = useNavigate();
  const aviso = useAviso();
  const turmaId = p?.turma?.id ?? "";
  const aberta = p?.status === "em_andamento";

  const migalhas = [
    { texto: "Minhas turmas", para: "/aluno/turmas" },
    { texto: p?.turma?.nome ?? "Turma", para: `/aluno/turmas/${turmaId}${p?.de_grupo ? "?aba=grupos" : ""}` },
    { texto: p?.titulo ?? "Pesquisa", para: `/aluno/pesquisas/${id}` },
  ];
  return (
    <Pagina nav="turmas" tutorial="aluno_pesquisa" migalhas={migalhas}>
      <Estado erro={erro} carregando={!p} voltarPara="/aluno/turmas" />
      {p && (
        <>
          <Cabecalho selo={<SeloPesquisa p={p} />} titulo={p.titulo}
            subtitulo={<>{p.de_grupo && p.grupo && <>Grupo {p.grupo.nome} · integrantes: {nomes(p.grupo.alunos)}<br /></>}{p.objetivo}</>} />
          <Andamento p={p} />
          <Aviso p={p} />
          <div className="actions">
            {aberta ? (
              <>
                <Btn icone="edit" onClick={() => setDialogo("editar")}>Editar título e objetivo</Btn>
                <Btn icone="file" onClick={() => navegar(`/pesquisas/${p.id}/relatorio`)}>Ver prévia do relatório</Btn>
                {p.de_grupo && <Btn icone="users" onClick={() => setDialogo("convidar")}>Convidar alunos</Btn>}
                <Btn tipo="primary" icone="send" onClick={() => setDialogo("entregar")}>Entregar para o professor</Btn>
                {!p.de_grupo && <Btn tipo="danger" icone="trash" onClick={() => setDialogo("excluir")}>Excluir pesquisa</Btn>}
              </>
            ) : <Btn icone="file" onClick={() => navegar(`/pesquisas/${p.id}/relatorio`)}>Ver relatório</Btn>}
          </div>
          <div className="sec" style={{ marginTop: 6 }}>
            <h2>Interações com IA</h2>
            {aberta && <Btn tipo="primary" icone="plus" onClick={() => setDialogo("interacao")}>Nova interação</Btn>}
          </div>
          {(p.interacoes ?? []).length === 0
            ? <Vazio>{aberta ? "Nenhuma interação registrada ainda. Anote a ferramenta, a pergunta e a resposta de cada conversa com a IA." : "Nenhuma interação foi registrada."}</Vazio>
            : <div className="card list">
                {p.interacoes!.map((i) => (
                  <Link key={i.id} className="row link" to={`/aluno/interacoes/${i.id}`}>
                    <div>
                      <div className="t"><Selo tipo="plain">{i.ferramenta}</Selo><span style={{ fontWeight: 400, color: "var(--faint)", fontSize: ".84rem" }}>{dataHora(i.data_registro)}</span></div>
                      <div className="m" style={{ color: "var(--ink)", fontFamily: "var(--serif)", fontSize: ".98rem", marginTop: 6 }}>{i.pergunta.length > 140 ? i.pergunta.slice(0, 139) + "…" : i.pergunta}</div>
                    </div>
                    <div className="side-r">
                      <span className="m" style={{ margin: 0 }}>{resumoFontes(i.contagem)}</span>
                      <div className="actions" style={{ justifyContent: "flex-end" }}>
                        {i.confirmada && <Selo tipo="ok">Confirmada</Selo>}{i.tem_comentario && <Selo tipo="info">Comentário do professor</Selo>}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>}
        </>
      )}

      {p && dialogo === "editar" && (
        <DialogoCampos titulo="Editar pesquisa" rotuloOk="Salvar" onFechar={() => setDialogo(null)}
          campos={[{ nome: "titulo", rotulo: "Título", valor: p.titulo }, { nome: "objetivo", rotulo: "Objetivo", tipo: "area", altura: 100, valor: p.objetivo }]}
          onEnviar={async (v) => { await api.alunoEditarPesquisa(p.id, v.titulo, v.objetivo); setDialogo(null); aviso("Pesquisa atualizada."); recarregar(); }} />
      )}
      {p && dialogo === "interacao" && (
        <DialogoCampos titulo="Nova interação" subtitulo="Anote a ferramenta, a pergunta e a resposta de uma conversa com a IA." rotuloOk="Salvar interação" onFechar={() => setDialogo(null)}
          campos={[
            { nome: "ferramenta", rotulo: "Ferramenta de IA usada", placeholder: "Ex.: ChatGPT, Claude, Gemini" },
            { nome: "pergunta", rotulo: "Pergunta feita", tipo: "area", altura: 100 },
            { nome: "resposta", rotulo: "Resposta obtida", tipo: "area", altura: 140 },
          ]}
          onEnviar={async (v) => {
            const i = await api.alunoRegistrarInteracao(p.id, v.ferramenta, v.pergunta, v.resposta);
            setDialogo(null); aviso("Interação registrada. Cadastre as fontes que a IA citou."); navegar(`/aluno/interacoes/${i.id}`);
          }} />
      )}
      {p && dialogo === "entregar" && <ConfirmarEntrega p={p} onFechar={() => setDialogo(null)} onFeito={() => { setDialogo(null); aviso("Pesquisa entregue. O professor vai revisar e você verá aqui se ele aceitar ou devolver."); recarregar(); }} />}
      {p && dialogo === "excluir" && (
        <Confirmar titulo="Excluir esta pesquisa?" rotuloOk="Excluir" perigo onFechar={() => setDialogo(null)}
          texto={`A pesquisa “${p.titulo}”${p.n_interacoes ? ` e ${plural(p.n_interacoes, "interação registrada", "interações registradas")}, com as fontes e os trechos,` : ""} serão apagadas. Isso não pode ser desfeito.`}
          onConfirmar={async () => { await api.alunoExcluirPesquisa(p.id); setDialogo(null); navegar(`/aluno/turmas/${turmaId}`); aviso("Pesquisa excluída."); }} />
      )}
      {p?.grupo && dialogo === "convidar" && (
        <DialogoConvidar grupo={p.grupo} onFechar={() => setDialogo(null)} onEnviado={() => { setDialogo(null); aviso("Convites enviados."); recarregar(); }} />
      )}
    </Pagina>
  );
}

function ConfirmarEntrega({ p, onFechar, onFeito }: { p: Pesquisa; onFechar: () => void; onFeito: () => void }) {
  const pendentes = p.contagem.nao_verificada;
  let texto = "Depois de entregar, você não poderá alterar a pesquisa até o professor aceitar ou devolver. O relatório fica disponível para ele.";
  if (pendentes) texto = `Ainda há ${plural(pendentes, "fonte", "fontes")} sem verificar. ` + texto;
  return <Confirmar titulo="Entregar esta pesquisa ao professor?" texto={texto} rotuloOk="Entregar para o professor" onFechar={onFechar}
    onConfirmar={async () => { await api.alunoEntregar(p.id); onFeito(); }} />;
}

function Aviso({ p }: { p: Pesquisa }) {
  if (p.devolvida) {
    return <Recado tipo="bad" icone="undo" titulo={`O professor devolveu esta pesquisa em ${dataHora(p.data_devolucao)}`}>
      {p.mensagem_devolucao}{"\n\n"}Ajuste o que ele pediu e use “Entregar para o professor” de novo. Interações que ele já confirmou continuam fechadas.
    </Recado>;
  }
  if (p.status === "entregue") return <Recado tipo="warn" icone="clock" titulo={`Entregue ao professor em ${dataHora(p.data_entrega)}`}>Ele está revisando. Você não pode alterar nada até ele aceitar ou devolver a pesquisa.</Recado>;
  if (p.status === "concluida") return <Recado tipo="ok" icone="check" titulo={`Concluída pelo professor em ${dataHora(p.data_conclusao)}`}>A pesquisa foi aceita. Ela e o relatório não podem mais ser alterados.</Recado>;
  return null;
}
