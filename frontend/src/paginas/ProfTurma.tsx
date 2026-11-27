import { useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { plural } from "../formato";
import type { Grupo } from "../tipos";
import { Btn, Confirmar, DialogoForm, Estado, Icone, Pagina, Selo, Vazio, iniciais, useAviso, useCarga } from "../ui";
import { LinhaPesquisaProf } from "./linhas";

export default function ProfTurma() {
  const { id = "" } = useParams();
  const [busca, setBusca] = useSearchParams();
  const { dados: t, erro, recarregar } = useCarga(() => api.profTurma(id), [id]);
  const aba = busca.get("aba") === "grupos" && t?.permite_grupos ? "grupos" : "alunos";
  const [atribuir, setAtribuir] = useState<Grupo | null>(null);
  const [remover, setRemover] = useState<{ g: Grupo; aluno: { id: string; nome: string } } | null>(null);
  const navegar = useNavigate();
  const aviso = useAviso();
  const copiar = async () => {
    if (!t) return;
    try { await navigator.clipboard.writeText(t.codigo); aviso(`Código ${t.codigo} copiado.`); } catch { aviso(`O código é ${t.codigo}.`, "info"); }
  };
  return (
    <Pagina nav="turmas" tutorial="prof_turma" largo migalhas={[{ texto: "Minhas turmas", para: "/professor/turmas" }, { texto: t?.nome ?? "Turma", para: `/professor/turmas/${id}` }]}>
      <Estado erro={erro} carregando={!t} voltarPara="/professor/turmas" />
      {t && (
        <>
          <div className="head">
            <div>
              <h1>{t.nome}</h1>
              <div className="codebox" style={{ marginTop: 10 }}>
                <small>Código de entrada</small><span className="code">{t.codigo}</span>
                <Btn sm icone="copy" onClick={copiar}>Copiar</Btn>
                {t.permite_grupos ? <Selo tipo="info">Grupos permitidos</Selo> : <Selo tipo="plain">Grupos desativados</Selo>}
              </div>
            </div>
            <div className="actions"><Btn icone="file" onClick={() => navegar(`/professor/pesquisas?turma=${t.id}`)}>Lista de pesquisas</Btn></div>
          </div>
          <div className="tabs" role="tablist">
            <button className="tab" role="tab" type="button" aria-current={aba === "alunos"} onClick={() => setBusca({})}><Icone nome="users" />Alunos</button>
            <button className="tab" role="tab" type="button" aria-current={aba === "grupos"} disabled={!t.permite_grupos}
              title={t.permite_grupos ? undefined : "Você não habilitou grupos ao criar esta turma."} onClick={() => setBusca({ aba: "grupos" })}>Grupos</button>
          </div>

          {aba === "alunos" && ((t.alunos ?? []).length === 0
            ? <Vazio>Nenhum aluno entrou ainda. Passe o código {t.codigo} para a turma.</Vazio>
            : <>
                <p className="sub" style={{ margin: 0 }}>{plural(t.alunos!.length, "aluno matriculado", "alunos matriculados")}. Cada um aparece com as próprias pesquisas.</p>
                {t.alunos!.map((a) => (
                  <div className="block card" key={a.id}>
                    <div className="bh">
                      <h2><span className="avatar" style={{ width: 34, height: 34, fontSize: ".82rem" }}>{iniciais(a.nome)}</span>{a.nome}
                        <span style={{ color: "var(--muted)", fontWeight: 500, fontSize: ".9rem" }}>{plural(a.pesquisas.length, "pesquisa", "pesquisas")}</span></h2>
                      {a.grupos.length > 0 && <Selo tipo="info">Em grupos: {a.grupos.join(", ")}</Selo>}
                    </div>
                    {a.pesquisas.length > 0
                      ? <div className="list" style={{ border: "1px solid var(--line)", borderRadius: 12, overflow: "hidden" }}>{a.pesquisas.map((p) => <LinhaPesquisaProf key={p.id} p={p} mostrarAutor={false} />)}</div>
                      : <p className="m" style={{ color: "var(--faint)", margin: 0 }}>Ainda não criou pesquisa individual.</p>}
                  </div>
                ))}
              </>)}

          {aba === "grupos" && ((t.grupos ?? []).length === 0
            ? <Vazio>Nenhum grupo foi criado ainda. Os alunos criam grupos na turma e convidam os colegas; você também pode atribuir alunos depois.</Vazio>
            : <>
                {(t.sem_grupo ?? []).length > 0 && <p className="sub" style={{ margin: 0 }}>Alunos sem grupo: {t.sem_grupo!.map((a) => a.nome).join(", ")}.</p>}
                {t.grupos!.map((g) => (
                  <div className="block card" key={g.id}>
                    <div className="bh"><h2>Grupo {g.nome}</h2><Btn sm icone="plus" onClick={() => setAtribuir(g)}>Atribuir aluno</Btn></div>
                    <p className="m" style={{ margin: 0, color: "var(--muted)" }}>Pesquisa do grupo: {g.titulo}</p>
                    <div className="members">
                      {g.alunos.map((a) => (
                        <div className="member" key={a.id}><span className="avatar">{iniciais(a.nome)}</span><span className="n">{a.nome}</span>
                          <Btn sm tipo="danger" onClick={() => setRemover({ g, aluno: a })}>Remover</Btn></div>
                      ))}
                    </div>
                    {g.pesquisa
                      ? <div className="list" style={{ border: "1px solid var(--line)", borderRadius: 12, overflow: "hidden" }}><LinhaPesquisaProf p={g.pesquisa} mostrarAutor={false} /></div>
                      : <p className="m" style={{ margin: 0, color: "var(--faint)", fontSize: ".86rem" }}>Ainda sem pesquisa: ela é criada quando o grupo tiver dois integrantes.</p>}
                  </div>
                ))}
              </>)}
        </>
      )}
      {t && atribuir && (
        <Atribuir grupo={atribuir} candidatos={(t.alunos_lista ?? []).filter((a) => !atribuir.alunos.some((m) => m.id === a.id))}
          onFechar={() => setAtribuir(null)} onFeito={() => { setAtribuir(null); aviso("Aluno atribuído ao grupo."); recarregar(); }} />
      )}
      {remover && (
        <Confirmar titulo="Remover aluno do grupo?" rotuloOk="Remover do grupo" perigo onFechar={() => setRemover(null)}
          texto={`${remover.aluno.nome} deixa o grupo ${remover.g.nome} e perde o acesso à pesquisa dele. O que o grupo já registrou continua com o grupo.`}
          onConfirmar={async () => { await api.profRemover(remover.g.id, remover.aluno.id); setRemover(null); aviso(`${remover.aluno.nome} foi removido do grupo.`); recarregar(); }} />
      )}
    </Pagina>
  );
}

function Atribuir({ grupo, candidatos, onFechar, onFeito }: { grupo: Grupo; candidatos: { id: string; nome: string }[]; onFechar: () => void; onFeito: () => void }) {
  const [aluno, setAluno] = useState(candidatos[0]?.id ?? "");
  if (candidatos.length === 0) {
    return <DialogoForm titulo="Atribuir aluno ao grupo" somenteFechar rotuloOk="Fechar" onFechar={onFechar} onEnviar={async () => onFechar()}><p>Todos os alunos da turma já estão neste grupo.</p></DialogoForm>;
  }
  return (
    <DialogoForm titulo="Atribuir aluno ao grupo" subtitulo={`Grupo ${grupo.nome}`} rotuloOk="Atribuir" onFechar={onFechar} onEnviar={async () => { await api.profAtribuir(grupo.id, aluno); onFeito(); }}>
      <div className="f"><label htmlFor="at-aluno">Aluno</label>
        <select id="at-aluno" className="sel" value={aluno} onChange={(e) => setAluno(e.target.value)}>
          {candidatos.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
        </select></div>
    </DialogoForm>
  );
}
