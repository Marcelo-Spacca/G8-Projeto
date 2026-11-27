import { ReactNode, useState } from "react";
import { DialogoForm, Icone, Selo, SeloFonte } from "../ui";
import type { Fonte } from "../tipos";

const GLIFO: Record<string, [string, string]> = {
  verificada: ["ok", "check"], incorreta: ["bad", "x"], nao_verificada: ["warn", "clock"],
};

/** Cartão de uma fonte: referência, link, status, anotação e trechos ligados. */
export function CartaoFonte({ f, visao, botoes }: { f: Fonte; visao: "aluno" | "professor"; botoes?: ReactNode }) {
  const [cor, icone] = GLIFO[f.status];
  const dele = visao === "professor" ? "no texto do aluno" : "no seu texto";
  const quem = f.julgada_pelo_professor ? "Anotação do professor" : visao === "professor" ? "Anotação do aluno" : "Anotação";
  const http = f.link && /^https?:\/\//i.test(f.link);
  return (
    <div className="src" data-fonte={f.id}>
      <div className={`glyph ${cor}`}><Icone nome={icone} /></div>
      <div>
        <div className="head-s">
          <div>
            <div className="ref">{f.referencia}</div>
            {f.link && (http
              ? <a className="lnk" href={f.link} target="_blank" rel="noreferrer"><Icone nome="link" />{f.link}</a>
              : <span className="lnk" style={{ color: "var(--muted)" }}>{f.link}</span>)}
          </div>
          <div className="tally">
            <SeloFonte status={f.status} />
            {f.julgada_pelo_professor && <Selo tipo="info">Julgada pelo professor</Selo>}
          </div>
        </div>
        {f.anotacao && <p className="note"><b>{quem}:</b> {f.anotacao}</p>}
        {f.trechos.length > 0 ? (
          <div className="used">
            <small>Usada {dele} em:</small>
            {f.trechos.map((t) => (
              <p className="quote" key={t.id}>
                <span className="mark">“{t.trecho}”</span>{t.localizacao && <> <small>({t.localizacao})</small></>}
              </p>
            ))}
          </div>
        ) : (
          <p className="none">{f.status === "incorreta" ? `Fonte descartada: sem trecho ${dele}.` : "Ainda sem trecho vinculado."}</p>
        )}
        {botoes && <div className="btns">{botoes}</div>}
      </div>
    </div>
  );
}

const OPCOES: [string, string, string, string][] = [
  ["verificada", "ok", "check", "Verificada: existe e confirma o que a IA disse"],
  ["incorreta", "bad", "x", "Incorreta ou inventada"],
  ["nao_verificada", "warn", "clock", "Ainda não verificada"],
];

/** RF17/RF18/RF26 (aluno) e julgamento do professor: mesma caixa, o professor não liga trecho. */
export function DialogoVerificacao(props: {
  fonte: Fonte; professor?: boolean; onFechar: () => void;
  onSalvar: (v: { resultado: string; anotacao: string; trecho: string; localizacao: string }) => Promise<void>;
}) {
  const { fonte, professor } = props;
  const [resultado, setResultado] = useState<string>(fonte.status);
  const [anotacao, setAnotacao] = useState(fonte.anotacao ?? "");
  const [trecho, setTrecho] = useState("");
  const [localizacao, setLocalizacao] = useState("");
  const ligados = fonte.trechos.length;
  const verificada = resultado === "verificada";
  const rotuloAnotacao =
    resultado === "incorreta" ? "Anotação de correção: o que está errado nesta fonte? (opcional)"
      : professor ? "Sua anotação para o aluno (opcional)" : "O que você encontrou (opcional)";
  const aviso = professor
    ? ligados === 1 ? "O trecho que o aluno ligou a esta fonte será removido." : `Os ${ligados} trechos que o aluno ligou a esta fonte serão removidos.`
    : ligados === 1 ? "O trecho ligado a esta fonte será removido." : `Os ${ligados} trechos ligados a esta fonte serão removidos.`;
  return (
    <DialogoForm
      titulo={professor ? "Julgar fonte" : "Verificar fonte"} largura={600} rotuloOk="Salvar verificação" onFechar={props.onFechar}
      subtitulo={professor ? "Confira a fonte e registre o seu julgamento. O aluno lê a sua anotação." : "Confira a fonte por conta própria, fora da IA."}
      onEnviar={() => props.onSalvar({ resultado, anotacao, trecho: verificada && !professor ? trecho : "", localizacao })}
    >
      <div>
        <div className="ref" style={{ fontFamily: "var(--serif)", fontWeight: 600 }}>{fonte.referencia}</div>
        {fonte.link && <div className="m" style={{ color: "var(--muted)", fontSize: ".84rem", overflowWrap: "anywhere" }}>{fonte.link}</div>}
      </div>
      <div className="f">
        <span className="lb">{professor ? "Qual é o seu julgamento?" : "Qual é o resultado da sua conferência?"}</span>
        <div className="opts">
          {OPCOES.map(([v, cor, ic, texto]) => (
            <label className="opt" key={v}>
              <input type="radio" name="resultado" value={v} checked={resultado === v} onChange={() => setResultado(v)} />
              <span className={`glyph ${cor}`}><Icone nome={ic} /></span>
              <span><b>{texto}</b></span>
            </label>
          ))}
        </div>
      </div>
      <div className="f">
        <label htmlFor="v-anot">{rotuloAnotacao}</label>
        <textarea id="v-anot" className="ta" style={{ minHeight: 80 }} value={anotacao} onChange={(e) => setAnotacao(e.target.value)}
          placeholder={professor ? "Ex.: não encontrei este artigo em nenhuma base." : "Ex.: o artigo existe, mas o ano é 2021 e não 2023."} />
      </div>
      {!professor && (
        <div className={`f ${verificada ? "" : "fieldset-off"}`}>
          <label htmlFor="v-trecho">{ligados ? `Ligar outro trecho do seu texto (opcional). Já há ${ligados} ligado(s).` : "Em que trecho do seu texto você usou esta fonte? (opcional)"}</label>
          <textarea id="v-trecho" className="ta" style={{ minHeight: 80 }} value={trecho} onChange={(e) => setTrecho(e.target.value)} placeholder="Cole aqui a frase ou o parágrafo do seu trabalho." disabled={!verificada} />
          <input className="in" value={localizacao} onChange={(e) => setLocalizacao(e.target.value)} placeholder="Onde fica: parágrafo ou linha (opcional)" disabled={!verificada} aria-label="Onde fica" />
        </div>
      )}
      {!verificada && ligados > 0 && <p className="err">{aviso}</p>}
    </DialogoForm>
  );
}
