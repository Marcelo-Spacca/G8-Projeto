import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { Btn, Cabecalho, DialogoCampos, Estado, Pagina, Selo, Vazio, useAviso, useCarga } from "../ui";

export default function AlunoTurmas() {
  const { dados, erro } = useCarga(() => api.alunoTurmas(), []);
  const [entrar, setEntrar] = useState(false);
  const navegar = useNavigate();
  const aviso = useAviso();
  const abrirEntrar = <Btn tipo="primary" icone="plus" onClick={() => setEntrar(true)}>Entrar em uma turma</Btn>;
  return (
    <Pagina nav="turmas" migalhas={[{ texto: "Minhas turmas", para: "/aluno/turmas" }]} tutorial="aluno_turmas">
      <Cabecalho titulo="Minhas turmas" subtitulo="Cada turma é uma cadeira. As suas pesquisas ficam dentro da turma a que pertencem." acoes={abrirEntrar} />
      <Estado erro={erro} carregando={!dados} voltarPara="/" />
      {dados && dados.length === 0 && (
        <Vazio acao={abrirEntrar}>Você ainda não entrou em nenhuma turma. Peça o código ao seu professor e use “Entrar em uma turma”.</Vazio>
      )}
      {dados && dados.length > 0 && (
        <div className="card list">
          {dados.map((t) => (
            <Link key={t.id} className="row link" to={`/aluno/turmas/${t.id}`}>
              <div><div className="t">{t.nome}</div><div className="m">Professor: {t.professor}</div></div>
              <div className="side-r">{t.permite_grupos ? <Selo tipo="info">Grupos permitidos</Selo> : <Selo tipo="plain">Só pesquisas individuais</Selo>}</div>
            </Link>
          ))}
        </div>
      )}
      {entrar && (
        <DialogoCampos
          titulo="Entrar em uma turma" subtitulo="Peça o código de 6 caracteres ao professor." rotuloOk="Entrar na turma"
          campos={[{ nome: "codigo", rotulo: "Código da turma", tipo: "codigo", placeholder: "PROJ01" }]}
          onFechar={() => setEntrar(false)}
          onEnviar={async (v) => {
            const t = await api.alunoEntrarNaTurma(v.codigo);
            setEntrar(false);
            aviso(`Você entrou na turma ${t.nome}.`);
            navegar(`/aluno/turmas/${t.id}`);
          }}
        />
      )}
    </Pagina>
  );
}
