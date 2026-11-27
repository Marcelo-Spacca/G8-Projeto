import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { plural } from "../formato";
import type { TurmaProfessor } from "../tipos";
import { Btn, Cabecalho, Confirmar, DialogoCampos, Estado, Pagina, Selo, Vazio, useAviso, useCarga } from "../ui";

export default function ProfTurmas() {
  const { dados, erro, recarregar } = useCarga(() => api.profTurmas(), []);
  const [nova, setNova] = useState(false);
  const [excluir, setExcluir] = useState<TurmaProfessor | null>(null);
  const navegar = useNavigate();
  const aviso = useAviso();

  async function copiar(t: TurmaProfessor) {
    try { await navigator.clipboard.writeText(t.codigo); aviso(`Código ${t.codigo} copiado.`); }
    catch { aviso(`Não consegui copiar. O código é ${t.codigo}.`, "info"); }
  }
  const botaoNova = <Btn tipo="primary" icone="plus" onClick={() => setNova(true)}>Nova turma</Btn>;
  return (
    <Pagina nav="turmas" tutorial="prof_turmas" migalhas={[{ texto: "Minhas turmas", para: "/professor/turmas" }]}>
      <Cabecalho titulo="Minhas turmas" subtitulo="Crie uma turma para cada cadeira e passe o código aos alunos. Dentro dela você vê os alunos, os grupos e as pesquisas."
        acoes={<><Btn icone="file" onClick={() => navegar("/professor/pesquisas")}>Pesquisas de todas as turmas</Btn>{botaoNova}</>} />
      <Estado erro={erro} carregando={!dados} voltarPara="/" />
      {dados && dados.length === 0 && <Vazio acao={botaoNova}>Você ainda não criou nenhuma turma. Crie a primeira: o sistema gera o código de entrada para os alunos.</Vazio>}
      {dados && dados.length > 0 && (
        <div className="card list">
          {dados.map((t) => {
            const partes = [plural(t.n_alunos, "aluno", "alunos"), plural(t.n_pesquisas, "pesquisa", "pesquisas")];
            if (t.permite_grupos) partes.push(plural(t.n_grupos, "grupo", "grupos"));
            return (
              <div key={t.id} className="row link" role="link" tabIndex={0} style={{ gridTemplateColumns: "minmax(0,1fr) auto auto" }}
                onClick={() => navegar(`/professor/turmas/${t.id}`)} onKeyDown={(e) => { if (e.key === "Enter") navegar(`/professor/turmas/${t.id}`); }}>
                <div>
                  <div className="t">{t.nome}{t.permite_grupos ? <Selo tipo="info">Grupos permitidos</Selo> : <Selo tipo="plain">Só individuais</Selo>}</div>
                  <div className="m">{partes.join("  ·  ")}</div>
                  {t.aguardando_revisao > 0 && <div style={{ marginTop: 8 }}><Selo tipo="warn">{t.aguardando_revisao} aguardando revisão</Selo></div>}
                </div>
                <div><div className="m" style={{ margin: "0 0 4px", fontSize: ".78rem", fontWeight: 600 }}>Código de entrada</div><span className="code">{t.codigo}</span></div>
                <div className="actions" onClick={(e) => e.stopPropagation()}>
                  <Btn sm icone="copy" onClick={() => copiar(t)}>Copiar código</Btn>
                  <Btn sm tipo="danger" icone="trash" onClick={() => setExcluir(t)}>Excluir</Btn>
                </div>
              </div>
            );
          })}
        </div>
      )}
      {nova && (
        <DialogoCampos titulo="Nova turma" subtitulo="Ao criar, o sistema gera um código de entrada. Quem tiver o código entra na turma." rotuloOk="Criar turma" onFechar={() => setNova(false)}
          campos={[{ nome: "nome", rotulo: "Nome da turma (a cadeira)", placeholder: "Ex.: Projeto 1, SI 26.2" }, { nome: "permite_grupos", rotulo: "Permitir que os alunos criem grupos nesta turma", tipo: "caixa" }]}
          onEnviar={async (v) => {
            const t = await api.profCriarTurma(v.nome, v.permite_grupos);
            setNova(false);
            aviso(`Turma criada. Código de entrada: ${t.codigo}. Passe-o aos alunos.`);
            navegar(`/professor/turmas/${t.id}`);
          }} />
      )}
      {excluir && (
        <Confirmar titulo="Excluir esta turma?" rotuloOk="Excluir turma" perigo onFechar={() => setExcluir(null)}
          texto={`A turma “${excluir.nome}”, com ${plural(excluir.n_alunos, "aluno matriculado", "alunos matriculados")}, ${plural(excluir.n_pesquisas, "pesquisa", "pesquisas")} e os grupos, será apagada com todas as interações, fontes e relatórios. O código deixa de valer. Isso não pode ser desfeito.`}
          onConfirmar={async () => { await api.profExcluirTurma(excluir.id); setExcluir(null); aviso("Turma excluída."); recarregar(); }} />
      )}
    </Pagina>
  );
}
