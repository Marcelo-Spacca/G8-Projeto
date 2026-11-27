import { useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ErroApi } from "../api";
import { dia, nomes, plural } from "../formato";
import type { Convite, Grupo, Pessoa } from "../tipos";
import { Btn, Cabecalho, Dialogo, DialogoCampos, DialogoForm, Estado, Icone, Pagina, Selo, SeloPesquisa, Vazio, useAviso, useCarga } from "../ui";

export default function AlunoTurma() {
  const { id = "" } = useParams();
  const [busca, setBusca] = useSearchParams();
  const turma = useCarga(() => api.alunoTurma(id), [id]);
  const permite = !!turma.dados?.permite_grupos;
  const aba = busca.get("aba") === "grupos" && permite ? "grupos" : "individuais";
  const lista = useCarga(
    async () => (aba === "grupos" ? { grupos: await api.alunoGruposDaTurma(id), pesquisas: [] } : { pesquisas: await api.alunoPesquisasDaTurma(id), grupos: [] }),
    [id, aba],
  );
  const [dialogo, setDialogo] = useState<null | "nova" | "grupo" | "convites">(null);
  const [convidar, setConvidar] = useState<Grupo | null>(null);
  const navegar = useNavigate();
  const aviso = useAviso();
  const convites = turma.dados?.convites ?? [];

  function recarregar() { turma.recarregar(); lista.recarregar(); }
  const irPara = (a: string) => setBusca(a === "grupos" ? { aba: "grupos" } : {});

  return (
    <Pagina nav="turmas" tutorial="aluno_pesquisas" migalhas={[{ texto: "Minhas turmas", para: "/aluno/turmas" }, { texto: turma.dados?.nome ?? "Turma", para: `/aluno/turmas/${id}` }]}>
      <Estado erro={turma.erro} carregando={!turma.dados} voltarPara="/aluno/turmas" />
      {turma.dados && (
        <>
          <Cabecalho titulo={turma.dados.nome} subtitulo={`Professor: ${turma.dados.professor}`} />
          <div className="tabs" role="tablist">
            <button className="tab" role="tab" type="button" aria-current={aba === "individuais"} onClick={() => irPara("individuais")}>Individuais</button>
            <button className="tab" role="tab" type="button" aria-current={aba === "grupos"} disabled={!permite} title={permite ? undefined : "O professor não habilitou grupos nesta turma."} onClick={() => irPara("grupos")}>Grupos</button>
            <span className="grow" />
            <div className="tools">
              <Btn sm desabilitado={!permite} dica={permite ? undefined : "O professor não habilitou grupos nesta turma."} onClick={() => setDialogo("convites")}>
                Convites {convites.length > 0 && <span className="chip warn plain" style={{ marginLeft: 2 }}>{convites.length}</span>}
              </Btn>
            </div>
          </div>
          <div className="sec">
            <p className="sub" style={{ margin: 0 }}>
              {aba === "grupos" ? "Pesquisas feitas em grupo: todos os integrantes trabalham na mesma pesquisa." : "Cada pesquisa reúne as interações com IA de um trabalho seu."}
            </p>
            {aba === "grupos"
              ? <Btn tipo="primary" icone="plus" onClick={() => setDialogo("grupo")}>Criar grupo</Btn>
              : <Btn tipo="primary" icone="plus" onClick={() => setDialogo("nova")}>Nova pesquisa</Btn>}
          </div>
          <Estado erro={lista.erro} carregando={!lista.dados} voltarPara="/aluno/turmas" />
          {lista.dados && aba === "individuais" && (
            lista.dados.pesquisas.length === 0
              ? <Vazio>Você ainda não criou nenhuma pesquisa nesta turma. Crie a primeira para começar a registrar o uso de IA do seu trabalho.</Vazio>
              : <div className="card list">
                  {lista.dados.pesquisas.map((p) => (
                    <Link key={p.id} className="row link" to={`/aluno/pesquisas/${p.id}`}>
                      <div><div className="t">{p.titulo}</div><div className="m">{p.objetivo.length > 120 ? p.objetivo.slice(0, 119) + "…" : p.objetivo}</div></div>
                      <div className="side-r"><SeloPesquisa p={p} /><small>Criada em {dia(p.data_criacao)}</small></div>
                    </Link>
                  ))}
                </div>
          )}
          {lista.dados && aba === "grupos" && (
            lista.dados.grupos.length === 0
              ? <Vazio>Você ainda não faz parte de nenhum grupo nesta turma. Crie um grupo e convide colegas, ou aceite um convite.</Vazio>
              : <div className="card list">
                  {lista.dados.grupos.map((g) => <LinhaGrupo key={g.id} g={g} onConvidar={() => setConvidar(g)} />)}
                </div>
          )}
        </>
      )}

      {dialogo === "nova" && (
        <DialogoCampos
          titulo="Nova pesquisa" subtitulo={`Turma: ${turma.dados?.nome}`} rotuloOk="Criar pesquisa"
          campos={[
            { nome: "titulo", rotulo: "Título", placeholder: "Ex.: Impactos da IA na educação" },
            { nome: "objetivo", rotulo: "Objetivo: o que você quer descobrir?", tipo: "area", altura: 100 },
          ]}
          onFechar={() => setDialogo(null)}
          onEnviar={async (v) => {
            const p = await api.alunoCriarPesquisa(id, v.titulo, v.objetivo);
            setDialogo(null);
            aviso("Pesquisa criada. Registre a primeira interação com a IA.");
            navegar(`/aluno/pesquisas/${p.id}`);
          }}
        />
      )}
      {dialogo === "grupo" && (
        <DialogoCampos
          titulo="Criar grupo" subtitulo="Depois de criar, você convida colegas da turma. A pesquisa é do grupo, não de um aluno só." rotuloOk="Criar grupo"
          campos={[
            { nome: "nome", rotulo: "Nome do grupo", placeholder: "Ex.: Time Alfa" },
            { nome: "titulo", rotulo: "Título da pesquisa do grupo", placeholder: "Ex.: Impactos da IA na educação" },
            { nome: "objetivo", rotulo: "Objetivo: o que o grupo quer descobrir?", tipo: "area", altura: 100 },
          ]}
          onFechar={() => setDialogo(null)}
          onEnviar={async (v) => {
            const g = await api.alunoCriarGrupo(id, v.nome, v.titulo, v.objetivo);
            setDialogo(null);
            setBusca({ aba: "grupos" });
            recarregar();
            const candidatos = await api.alunoConvidaveis(g.id).catch(() => [] as Pessoa[]);
            if (candidatos.length === 0) aviso("Grupo criado. Ainda não há outros alunos na turma para convidar.", "info");
            else { aviso("Grupo criado. Agora convide os colegas."); setConvidar(g); }
          }}
        />
      )}
      {convidar && <DialogoConvidar grupo={convidar} onFechar={() => setConvidar(null)} onEnviado={() => { setConvidar(null); aviso("Convites enviados. Quando alguém aceitar, a pesquisa do grupo aparece aqui."); recarregar(); }} />}
      {dialogo === "convites" && (
        <DialogoConvites convites={convites} onFechar={() => setDialogo(null)}
          onRespondido={(aceito, grupo) => {
            recarregar();
            if (aceito) { setBusca({ aba: "grupos" }); aviso(`Você entrou no grupo ${grupo}. A pesquisa do grupo já está na lista.`); } else aviso("Convite recusado.", "info");
          }} />
      )}
    </Pagina>
  );
}

function LinhaGrupo({ g, onConvidar }: { g: Grupo; onConvidar: () => void }) {
  const corpo = (
    <>
      <div>
        <div className="t">{g.titulo}</div>
        <div className="m">Grupo {g.nome} · {nomes(g.alunos)}</div>
        {!g.pesquisa && (
          <div className="m" style={{ color: "var(--faint)", fontSize: ".82rem" }}>
            A pesquisa do grupo é criada quando o primeiro convidado aceitar.{g.convites_pendentes > 0 && ` ${plural(g.convites_pendentes, "convite pendente", "convites pendentes")}.`}
          </div>
        )}
      </div>
      <div className="side-r">
        {g.pesquisa ? <><SeloPesquisa p={g.pesquisa} /><small>Criada em {dia(g.pesquisa.data_criacao)}</small></>
          : <><Selo tipo="warn dotted">Aguardando integrantes</Selo><Btn sm onClick={onConvidar}>Convidar alunos</Btn></>}
      </div>
    </>
  );
  return g.pesquisa
    ? <Link className="row link" to={`/aluno/pesquisas/${g.pesquisa.id}`}>{corpo}</Link>
    : <div className="row">{corpo}</div>;
}

export function DialogoConvidar({ grupo, onFechar, onEnviado }: { grupo: { id: string; nome: string }; onFechar: () => void; onEnviado: () => void }) {
  const cand = useCarga(() => api.alunoConvidaveis(grupo.id), [grupo.id]);
  const [marcados, setMarcados] = useState<string[]>([]);
  if (cand.erro) return <Dialogo titulo="Convidar alunos" onFechar={onFechar} rodape={<Btn onClick={onFechar}>Fechar</Btn>}><div className="dlg-b"><p className="err">{cand.erro}</p></div></Dialogo>;
  if (!cand.dados) return null;
  if (cand.dados.length === 0) {
    return <Dialogo titulo="Convidar alunos" onFechar={onFechar} rodape={<Btn tipo="primary" onClick={onFechar}>Fechar</Btn>}>
      <div className="dlg-b"><p>Não há mais colegas da turma para convidar: todos já estão no grupo ou têm convite pendente.</p></div></Dialogo>;
  }
  return (
    <DialogoForm titulo="Convidar alunos" subtitulo={`Grupo ${grupo.nome}. Quem aceitar entra na pesquisa do grupo.`} rotuloOk="Enviar convites" onFechar={onFechar}
      onEnviar={async () => { await api.alunoConvidar(grupo.id, marcados); onEnviado(); }}>
      {cand.dados.map((a) => (
        <label key={a.id} className="chk">
          <input type="checkbox" checked={marcados.includes(a.id)} onChange={(e) => setMarcados(e.target.checked ? [...marcados, a.id] : marcados.filter((x) => x !== a.id))} />
          <span>{a.nome}</span>
        </label>
      ))}
    </DialogoForm>
  );
}

function DialogoConvites({ convites, onFechar, onRespondido }: { convites: Convite[]; onFechar: () => void; onRespondido: (aceito: boolean, grupo: string) => void }) {
  const [restantes, setRestantes] = useState(convites);
  const [erro, setErro] = useState<string | null>(null);
  async function responder(c: Convite, aceitar: boolean) {
    setErro(null);
    try {
      await api.alunoResponderConvite(c.id, aceitar);
      setRestantes((r) => r.filter((x) => x.id !== c.id));
      onRespondido(aceitar, c.grupo?.nome ?? "");
    } catch (x) { setErro(x instanceof ErroApi ? x.message : "Não foi possível responder."); }
  }
  return (
    <Dialogo titulo="Convites pendentes" onFechar={onFechar} rodape={<Btn tipo="primary" onClick={onFechar}>Fechar</Btn>}>
      <div className="dlg-b">
        {restantes.length === 0 && <p style={{ color: "var(--muted)" }}>Nenhum convite pendente.</p>}
        {restantes.map((c) => (
          <div className="invite" key={c.id}>
            <b>Grupo {c.grupo?.nome}</b>
            <p style={{ color: "var(--muted)" }}>{c.convidado_por} convidou você para a pesquisa “{c.titulo}”.</p>
            <small style={{ color: "var(--faint)" }}>Integrantes até agora: {c.integrantes.join(", ")}</small>
            <div className="btns"><Btn tipo="primary" sm onClick={() => responder(c, true)}>Aceitar</Btn><Btn sm onClick={() => responder(c, false)}>Recusar</Btn></div>
          </div>
        ))}
        {erro && <p className="err" role="alert"><Icone nome="alert" /> {erro}</p>}
      </div>
    </Dialogo>
  );
}
