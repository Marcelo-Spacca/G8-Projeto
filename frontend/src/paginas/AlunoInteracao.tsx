import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { dataHora, plural } from "../formato";
import type { Fonte } from "../tipos";
import { Btn, Cabecalho, Confirmar, ContagemSelos, DialogoCampos, Estado, Icone, Pagina, Recado, Selo, useAviso, useCarga } from "../ui";
import { CartaoFonte, DialogoVerificacao } from "./fonte";

export default function AlunoInteracao() {
  const { id = "" } = useParams();
  const { dados: i, erro, recarregar } = useCarga(() => api.alunoInteracao(id), [id]);
  type D = null | { t: "editar" } | { t: "excluir" } | { t: "fonte" } | { t: "editarFonte"; f: Fonte } | { t: "verificar"; f: Fonte } | { t: "trecho"; f: Fonte };
  const [d, setD] = useState<D>(null);
  const navegar = useNavigate();
  const aviso = useAviso();
  const comAluno = i?.pesquisa.status === "em_andamento";
  const editavel = !!i && comAluno && !i.confirmada;
  const pesquisaPara = `/aluno/pesquisas/${i?.pesquisa.id ?? ""}`;
  const fechar = () => setD(null);
  const pronto = (texto: string) => { fechar(); aviso(texto); recarregar(); };

  return (
    <Pagina nav="turmas" tutorial="aluno_interacao" migalhas={[
      { texto: "Minhas turmas", para: "/aluno/turmas" },
      { texto: i?.pesquisa.turma ?? "Turma", para: `/aluno/turmas/${i?.pesquisa.turma_id ?? ""}` },
      { texto: i?.pesquisa.titulo ?? "Pesquisa", para: pesquisaPara },
      { texto: i ? `Interação com ${i.ferramenta}` : "Interação", para: `/aluno/interacoes/${id}` },
    ]}>
      <Estado erro={erro} carregando={!i} voltarPara="/aluno/turmas" />
      {i && (
        <>
          <Cabecalho
            selo={<div className="tally"><Selo tipo="plain">{i.ferramenta}</Selo>{i.confirmada && <Selo tipo="ok">Confirmada pelo professor</Selo>}</div>}
            titulo={`Interação com ${i.ferramenta}`} subtitulo={`Registrada em ${dataHora(i.data_registro)}`}
            acoes={editavel && <><Btn icone="edit" onClick={() => setD({ t: "editar" })}>Editar</Btn><Btn tipo="danger" icone="trash" onClick={() => setD({ t: "excluir" })}>Excluir</Btn></>}
          />
          {!comAluno && <Recado tipo="info" icone="lock" titulo="Esta interação não pode ser alterada">A pesquisa está com o professor ou já foi concluída: esta interação e suas fontes não podem ser alteradas.</Recado>}
          {comAluno && i.confirmada && <Recado tipo="info" icone="lock" titulo="Interação confirmada">O professor confirmou esta interação e ela não pode mais ser alterada. Se precisar ajustar algo, crie uma nova interação na pesquisa.</Recado>}
          {i.comentario && <Recado tipo="prof" icone="chat" titulo={`Comentário do professor · ${dataHora(i.data_comentario)}`} citacao>{i.comentario}</Recado>}
          <div className="card panel"><h3>Pergunta</h3><p className="doc" style={{ fontFamily: "var(--sans)", fontSize: "1rem" }}>{i.pergunta}</p></div>
          <div className="card panel"><h3><Icone nome="spark" />Resposta da IA</h3><p className="doc">{i.resposta}</p></div>
          <div className="sec" style={{ marginTop: 6 }}>
            <h2>Fontes citadas pela IA</h2>
            {editavel && <Btn tipo="primary" icone="plus" onClick={() => setD({ t: "fonte" })}>Adicionar fonte</Btn>}
          </div>
          <ContagemSelos c={i.contagem} />
          {i.fontes.length === 0
            ? <div className="empty"><p>{editavel ? "Nenhuma fonte cadastrada. Se a IA citou livros, artigos ou sites, cadastre cada um para poder conferi-los depois." : "Nenhuma fonte foi cadastrada nesta interação."}</p></div>
            : <div className="card">
                {i.fontes.map((f) => (
                  <CartaoFonte key={f.id} f={f} visao="aluno" botoes={editavel && <>
                    <Btn sm tipo={f.status === "nao_verificada" ? "primary" : ""} onClick={() => setD({ t: "verificar", f })}>{f.status === "nao_verificada" ? "Verificar" : "Alterar verificação"}</Btn>
                    {f.status === "verificada" && <Btn sm onClick={() => setD({ t: "trecho", f })}>Ligar outro trecho</Btn>}
                    <Btn sm icone="edit" onClick={() => setD({ t: "editarFonte", f })}>Editar fonte</Btn>
                  </>} />
                ))}
              </div>}
        </>
      )}

      {i && d?.t === "editar" && (
        <DialogoCampos titulo="Editar interação" subtitulo="As fontes cadastradas continuam as mesmas." rotuloOk="Salvar" onFechar={fechar}
          campos={[{ nome: "ferramenta", rotulo: "Ferramenta de IA usada", valor: i.ferramenta }, { nome: "pergunta", rotulo: "Pergunta feita", tipo: "area", altura: 100, valor: i.pergunta }, { nome: "resposta", rotulo: "Resposta obtida", tipo: "area", altura: 140, valor: i.resposta }]}
          onEnviar={async (v) => { await api.alunoEditarInteracao(i.id, v.ferramenta, v.pergunta, v.resposta); pronto("Interação atualizada."); }} />
      )}
      {i && d?.t === "excluir" && (
        <Confirmar titulo="Excluir esta interação?" rotuloOk="Excluir" perigo onFechar={fechar}
          texto={`A pergunta, a resposta${i.fontes.length ? ` e ${plural(i.fontes.length, "fonte cadastrada", "fontes cadastradas")}, com os trechos ligados,` : ""} serão apagadas. Isso não pode ser desfeito.`}
          onConfirmar={async () => { await api.alunoExcluirInteracao(i.id); fechar(); navegar(pesquisaPara); aviso("Interação excluída."); }} />
      )}
      {i && d?.t === "fonte" && (
        <DialogoCampos titulo="Adicionar fonte" subtitulo="A fonte entra como “não verificada” até você conferi-la." rotuloOk="Adicionar fonte" onFechar={fechar}
          campos={[{ nome: "referencia", rotulo: "Referência citada pela IA", tipo: "area", altura: 80, placeholder: "Ex.: SILVA, J. A educação na era da IA. 2023." }, { nome: "link", rotulo: "Link (opcional)", placeholder: "https://" }]}
          onEnviar={async (v) => { await api.alunoAdicionarFonte(i.id, v.referencia, v.link); pronto("Fonte adicionada como não verificada."); }} />
      )}
      {d?.t === "editarFonte" && (
        <DialogoCampos titulo="Editar fonte" rotuloOk="Salvar fonte" onFechar={fechar}
          subtitulo={d.f.status !== "nao_verificada"
            ? "Atenção: esta fonte já foi conferida. Se você mudar a referência ou o link, ela volta a “não verificada” e os trechos ligados a ela são removidos, para você conferir de novo."
            : "Corrija a referência ou o link. A fonte continua “não verificada”."}
          campos={[{ nome: "referencia", rotulo: "Referência citada pela IA", tipo: "area", altura: 80, valor: d.f.referencia }, { nome: "link", rotulo: "Link (opcional)", placeholder: "https://", valor: d.f.link ?? "" }]}
          onEnviar={async (v) => {
            const nova = await api.alunoEditarFonte(d.f.id, v.referencia, v.link);
            pronto(nova.voltou_a_nao_verificada ? "Fonte atualizada. Como o conteúdo mudou, ela voltou a “não verificada”." : "Fonte atualizada.");
          }} />
      )}
      {d?.t === "verificar" && (
        <DialogoVerificacao fonte={d.f} onFechar={fechar}
          onSalvar={async (v) => { await api.alunoVerificarFonte(d.f.id, v.resultado, v.anotacao, v.trecho, v.localizacao); pronto("Verificação salva."); }} />
      )}
      {d?.t === "trecho" && (
        <DialogoCampos titulo="Ligar trecho do seu texto" subtitulo={d.f.referencia} rotuloOk="Ligar trecho" onFechar={fechar}
          campos={[{ nome: "trecho", rotulo: "Trecho do seu texto em que usou esta fonte", tipo: "area", altura: 110 }, { nome: "localizacao", rotulo: "Onde fica (opcional)", placeholder: "Ex.: parágrafo 3" }]}
          onEnviar={async (v) => { await api.alunoLigarTrecho(d.f.id, v.trecho, v.localizacao); pronto("Trecho ligado à fonte."); }} />
      )}
    </Pagina>
  );
}
