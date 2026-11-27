import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { dataHora } from "../formato";
import type { Fonte } from "../tipos";
import { Btn, Cabecalho, Confirmar, ContagemSelos, DialogoCampos, Estado, Icone, Pagina, Recado, Selo, useAviso, useCarga } from "../ui";
import { CartaoFonte, DialogoVerificacao } from "./fonte";

export default function ProfInteracao() {
  const { id = "" } = useParams();
  const { dados: i, erro, recarregar } = useCarga(() => api.profInteracao(id), [id]);
  const [d, setD] = useState<null | { t: "comentar" } | { t: "confirmar" } | { t: "julgar"; f: Fonte }>(null);
  const aviso = useAviso();
  const status = i?.pesquisa.status;
  const emRevisao = status === "entregue";
  const podeJulgar = emRevisao && !i?.confirmada;
  const fechar = () => setD(null);
  const pronto = (t: string) => { fechar(); aviso(t); recarregar(); };
  const pesquisaPara = `/professor/pesquisas/${i?.pesquisa.id ?? ""}`;

  return (
    <Pagina nav="turmas" tutorial="prof_interacao" migalhas={[
      { texto: "Minhas turmas", para: "/professor/turmas" },
      { texto: i?.pesquisa.titulo ?? "Pesquisa", para: pesquisaPara },
      { texto: i ? `Interação com ${i.ferramenta}` : "Interação", para: `/professor/interacoes/${id}` },
    ]}>
      <Estado erro={erro} carregando={!i} voltarPara="/professor/turmas" />
      {i && (
        <>
          <Cabecalho selo={<div className="tally"><Selo tipo="plain">{i.ferramenta}</Selo>{i.confirmada && <Selo tipo="ok">Confirmada</Selo>}</div>}
            titulo={`Interação com ${i.ferramenta}`} subtitulo={`${i.pesquisa.autor}  ·  registrada em ${dataHora(i.data_registro)}`}
            acoes={emRevisao && (i.confirmada
              ? <Btn icone="undo" onClick={async () => { try { await api.profReabrir(i.id); pronto("Interação reaberta."); } catch (e: any) { aviso(e.message, "erro"); } }}>Reabrir interação</Btn>
              : <Btn tipo="primary" icone="check" onClick={() => setD({ t: "confirmar" })}>Confirmar interação</Btn>)} />
          {status === "em_andamento" && <Recado tipo="info" icone="eye" titulo="A pesquisa ainda está com o aluno">Você acompanha, mas só pode julgar e comentar depois que ele entregar.</Recado>}
          {status === "concluida" && <Recado tipo="ok" icone="check" titulo="Pesquisa concluída">Nada mais pode ser alterado.</Recado>}
          <div className="card panel"><h3>Pergunta</h3><p className="doc" style={{ fontFamily: "var(--sans)", fontSize: "1rem" }}>{i.pergunta}</p></div>
          <div className="card panel"><h3><Icone nome="spark" />Resposta da IA</h3><p className="doc">{i.resposta}</p></div>
          <div className="sec" style={{ marginTop: 6 }}>
            <h2>Seu comentário</h2>
            {emRevisao && <Btn icone="edit" onClick={() => setD({ t: "comentar" })}>{i.comentario ? "Editar comentário" : "Comentar"}</Btn>}
          </div>
          {i.comentario
            ? <Recado tipo="prof" icone="chat" titulo={`Comentário · ${dataHora(i.data_comentario)}`} citacao>{i.comentario}</Recado>
            : <p className="m" style={{ color: "var(--faint)", margin: 0 }}>{emRevisao ? "Nenhum comentário. O aluno lê o que você escrever aqui, mas não responde." : "Nenhum comentário nesta interação."}</p>}
          <div className="sec" style={{ marginTop: 6 }}><h2>Fontes citadas pela IA</h2></div>
          <ContagemSelos c={i.contagem} />
          {i.fontes.length === 0
            ? <div className="empty"><p>O aluno não cadastrou fontes nesta interação.</p></div>
            : <div className="card">
                {i.fontes.map((f) => (
                  <CartaoFonte key={f.id} f={f} visao="professor" botoes={podeJulgar &&
                    <Btn sm tipo={f.status === "nao_verificada" ? "primary" : ""} onClick={() => setD({ t: "julgar", f })}>{f.status === "nao_verificada" ? "Julgar fonte" : "Alterar julgamento"}</Btn>} />
                ))}
              </div>}
        </>
      )}
      {i && d?.t === "comentar" && (
        <DialogoCampos titulo="Comentar a interação" subtitulo="O aluno lê este comentário, mas não pode responder. Deixe em branco para apagar." rotuloOk="Salvar comentário" onFechar={fechar}
          campos={[{ nome: "comentario", rotulo: "Comentário para o aluno", tipo: "area", altura: 130, valor: i.comentario ?? "" }]}
          onEnviar={async (v) => { await api.profComentar(i.id, v.comentario); pronto("Comentário salvo."); }} />
      )}
      {i && d?.t === "confirmar" && (
        <Confirmar titulo="Confirmar esta interação?" rotuloOk="Confirmar interação" onFechar={fechar}
          texto="O aluno não poderá mais alterar esta interação nem as fontes dela. Se precisar de ajustes, ele cria uma nova interação."
          onConfirmar={async () => { await api.profConfirmar(i.id); pronto("Interação confirmada e fechada para o aluno."); }} />
      )}
      {d?.t === "julgar" && (
        <DialogoVerificacao professor fonte={d.f} onFechar={fechar}
          onSalvar={async (v) => { await api.profJulgar(d.f.id, v.resultado, v.anotacao); pronto("Julgamento salvo. O aluno verá a sua decisão."); }} />
      )}
    </Pagina>
  );
}
