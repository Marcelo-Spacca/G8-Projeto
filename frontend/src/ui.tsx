import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useNavigate } from "react-router-dom";
import { api, ErroApi } from "./api";
import { useAuth } from "./auth";
import { SPRITE } from "./sprite";
import TUTORIAIS from "./tutoriais.json";
import type { Contagem, Pesquisa, StatusFonte } from "./tipos";

// ------------------------------------------------------------------ ícones
export function Sprite() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
      <defs dangerouslySetInnerHTML={{ __html: SPRITE }} />
    </svg>
  );
}
export function Icone({ nome, className = "" }: { nome: string; className?: string }) {
  return (
    <svg className={`ic ${className}`} aria-hidden="true">
      <use href={`#i-${nome}`} />
    </svg>
  );
}

// ------------------------------------------------------------------ selos
export function Selo({ tipo = "", children }: { tipo?: string; children: ReactNode }) {
  return <span className={`chip ${tipo}`}>{children}</span>;
}
export function SeloPesquisa({ p, visao = "aluno" }: { p: Pick<Pesquisa, "status" | "devolvida">; visao?: "aluno" | "professor" }) {
  if (p.devolvida) return <Selo tipo="bad">Devolvida para ajustes</Selo>;
  if (p.status === "entregue") return visao === "professor" ? <Selo tipo="warn">Aguardando sua revisão</Selo> : <Selo tipo="warn">Entregue ao professor</Selo>;
  if (p.status === "concluida") return <Selo tipo="ok">Concluída</Selo>;
  return <Selo tipo="info">Em andamento</Selo>;
}
export function SeloFonte({ status }: { status: StatusFonte }) {
  if (status === "verificada") return <Selo tipo="ok">Verificada</Selo>;
  if (status === "incorreta") return <Selo tipo="bad">Incorreta</Selo>;
  return <Selo tipo="warn dotted">Não verificada</Selo>;
}
export function ContagemSelos({ c }: { c: Contagem }) {
  const itens: [string, string][] = [];
  if (c.verificada) itens.push(["ok", `${c.verificada} ${c.verificada === 1 ? "verificada" : "verificadas"}`]);
  if (c.incorreta) itens.push(["bad", `${c.incorreta} ${c.incorreta === 1 ? "incorreta" : "incorretas"}`]);
  if (c.nao_verificada) itens.push(["warn dotted", `${c.nao_verificada} ${c.nao_verificada === 1 ? "não verificada" : "não verificadas"}`]);
  if (!itens.length) return null;
  return <div className="tally">{itens.map(([k, t]) => <Selo key={k} tipo={k}>{t}</Selo>)}</div>;
}

// ------------------------------------------------------------------ botões
interface BtnProps {
  children: ReactNode; onClick?: () => void; tipo?: "primary" | "danger" | "ghost" | ""; sm?: boolean;
  icone?: string; desabilitado?: boolean; dica?: string; submit?: boolean; solido?: boolean;
}
export function Btn({ children, onClick, tipo = "", sm, icone, desabilitado, dica, submit, solido }: BtnProps) {
  return (
    <button
      type={submit ? "submit" : "button"}
      className={`btn ${tipo} ${solido ? "solid" : ""} ${sm ? "sm" : ""}`}
      onClick={onClick}
      disabled={desabilitado}
      title={dica}
    >
      {icone && <Icone nome={icone} />}
      {children}
    </button>
  );
}

// ------------------------------------------------------------------ avisos (toast)
type TipoAviso = "ok" | "info" | "erro";
const ContextoAviso = createContext<(texto: string, tipo?: TipoAviso) => void>(() => {});
export const useAviso = () => useContext(ContextoAviso);

export function ProvedorAvisos({ children }: { children: ReactNode }) {
  const [aviso, setAviso] = useState<{ texto: string; tipo: TipoAviso } | null>(null);
  const timer = useRef<number>();
  const mostrar = useCallback((texto: string, tipo: TipoAviso = "ok") => {
    setAviso({ texto, tipo });
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setAviso(null), tipo === "erro" ? 9000 : 6000);
  }, []);
  return (
    <ContextoAviso.Provider value={mostrar}>
      {children}
      {aviso && (
        <div className="toast" role={aviso.tipo === "erro" ? "alert" : "status"} style={aviso.tipo === "erro" ? { background: "var(--bad)", color: "#fff" } : undefined}>
          <Icone nome={aviso.tipo === "erro" ? "alert" : "check"} />
          {aviso.texto}
        </div>
      )}
    </ContextoAviso.Provider>
  );
}

// ------------------------------------------------------------------ diálogos
export function Dialogo(props: {
  titulo: string; subtitulo?: string; largura?: number; onFechar: () => void; children: ReactNode; rodape: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const alvo = ref.current?.querySelector<HTMLElement>("input:not([type=radio]):not([type=checkbox]),textarea,select");
    (alvo ?? ref.current?.querySelector<HTMLElement>("button.btn"))?.focus();
    const tecla = (e: KeyboardEvent) => { if (e.key === "Escape") props.onFechar(); };
    document.addEventListener("keydown", tecla);
    const antes = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", tecla); document.body.style.overflow = antes; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return createPortal(
    <div className="scrim">
      <div className="dlg" role="dialog" aria-modal="true" aria-label={props.titulo} style={{ width: `min(${props.largura ?? 540}px,100%)` }} ref={ref}>
        <div className="dlg-h">
          <div>
            <h2 style={{ fontSize: "1.2rem", letterSpacing: "-.015em" }}>{props.titulo}</h2>
            {props.subtitulo && <p>{props.subtitulo}</p>}
          </div>
          <button className="xbtn" type="button" onClick={props.onFechar} aria-label="Fechar"><Icone nome="x" /></button>
        </div>
        {props.children}
        <div className="dlg-f">{props.rodape}</div>
      </div>
    </div>,
    document.body,
  );
}

/** Caixa de diálogo com um formulário: cuida do envio, do "carregando" e do erro mostrado dentro dela. */
export function DialogoForm(props: {
  titulo: string; subtitulo?: string; largura?: number; rotuloOk: string; perigo?: boolean; somenteFechar?: boolean;
  onFechar: () => void; onEnviar?: () => Promise<void>; children: ReactNode; desabilitarOk?: boolean;
}) {
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  async function enviar(e?: React.FormEvent) {
    e?.preventDefault();
    if (enviando || !props.onEnviar) return;
    setEnviando(true);
    setErro(null);
    try { await props.onEnviar(); } catch (x) {
      setErro(x instanceof ErroApi ? x.message : "Não foi possível concluir. Tente de novo.");
      setEnviando(false);
    }
  }
  return (
    <Dialogo
      titulo={props.titulo} subtitulo={props.subtitulo} largura={props.largura} onFechar={props.onFechar}
      rodape={
        <>
          {!props.somenteFechar && <Btn onClick={props.onFechar}>Cancelar</Btn>}
          <button
            type="submit" form="form-dialogo" disabled={enviando || props.desabilitarOk}
            className={`btn ${props.perigo ? "danger solid" : "primary"}`}
          >
            {enviando ? "Aguarde…" : props.rotuloOk}
          </button>
        </>
      }
    >
      <form id="form-dialogo" className="dlg-b" onSubmit={enviar}>
        {props.children}
        {erro && <p className="err" role="alert">{erro}</p>}
      </form>
    </Dialogo>
  );
}

export interface CampoDef {
  nome: string; rotulo: string; tipo?: "texto" | "area" | "caixa" | "codigo"; dica?: string; altura?: number;
  valor?: string | boolean; placeholder?: string;
}
/** Diálogo só com campos de texto (a maioria dos formulários do programa). */
export function DialogoCampos(props: {
  titulo: string; subtitulo?: string; campos: CampoDef[]; rotuloOk: string; perigo?: boolean;
  onFechar: () => void; onEnviar: (v: Record<string, any>) => Promise<void>;
}) {
  const [v, setV] = useState<Record<string, any>>(() => Object.fromEntries(props.campos.map((c) => [c.nome, c.valor ?? (c.tipo === "caixa" ? false : "")])));
  return (
    <DialogoForm titulo={props.titulo} subtitulo={props.subtitulo} rotuloOk={props.rotuloOk} perigo={props.perigo} onFechar={props.onFechar} onEnviar={() => props.onEnviar(v)}>
      {props.campos.map((c) => {
        const id = `campo-${c.nome}`;
        if (c.tipo === "caixa") {
          return (
            <label key={c.nome} className="chk">
              <input type="checkbox" checked={!!v[c.nome]} onChange={(e) => setV({ ...v, [c.nome]: e.target.checked })} />
              <span>{c.rotulo}</span>
            </label>
          );
        }
        return (
          <div className="f" key={c.nome}>
            <label htmlFor={id}>{c.rotulo}</label>
            {c.tipo === "area" ? (
              <textarea id={id} className="ta" style={{ minHeight: c.altura ?? 96 }} value={v[c.nome]} placeholder={c.placeholder} onChange={(e) => setV({ ...v, [c.nome]: e.target.value })} />
            ) : (
              <input id={id} className={`in ${c.tipo === "codigo" ? "codein" : ""}`} value={v[c.nome]} placeholder={c.placeholder} maxLength={c.tipo === "codigo" ? 12 : undefined}
                onChange={(e) => setV({ ...v, [c.nome]: e.target.value })} autoComplete="off" />
            )}
            {c.dica && <small>{c.dica}</small>}
          </div>
        );
      })}
    </DialogoForm>
  );
}

export function Confirmar(props: { titulo: string; texto: string; rotuloOk: string; perigo?: boolean; onFechar: () => void; onConfirmar: () => Promise<void> }) {
  return (
    <DialogoForm titulo={props.titulo} rotuloOk={props.rotuloOk} perigo={props.perigo} onFechar={props.onFechar} onEnviar={props.onConfirmar}>
      <p>{props.texto}</p>
    </DialogoForm>
  );
}

export function Tutorial({ chave, onFechar }: { chave: string; onFechar: () => void }) {
  const t = (TUTORIAIS as Record<string, { titulo: string; abertura: string; secoes: { titulo: string; itens: string[] }[] }>)[chave];
  if (!t) return null;
  return (
    <Dialogo titulo={t.titulo} largura={620} onFechar={onFechar} rodape={<Btn tipo="primary" onClick={onFechar}>Entendi</Btn>}>
      <div className="dlg-b tut">
        <p>{t.abertura}</p>
        {t.secoes.map((s) => (
          <div key={s.titulo}>
            <h3>{s.titulo}</h3>
            <ul>{s.itens.map((i) => <li key={i}>{i}</li>)}</ul>
          </div>
        ))}
      </div>
    </Dialogo>
  );
}

// ------------------------------------------------------------------ estrutura da página
export interface Migalha { texto: string; para: string }

export function Pagina(props: {
  migalhas: Migalha[]; tutorial?: string; largo?: boolean; children: ReactNode; nav?: "turmas" | "pesquisas";
}) {
  const { usuario, sair } = useAuth();
  const navegar = useNavigate();
  const [tutorialAberto, setTutorialAberto] = useState(false);
  const aluno = usuario?.tipo === "aluno";
  const aviso = useAviso();
  const m = props.migalhas;
  const voltar = m.length > 1 ? m[m.length - 2] : null;

  async function sairDaConta() {
    try { await api.sair(); } catch { /* já estava sem sessão */ }
    sair();
    navegar("/");
    aviso("Você saiu da conta.", "info");
  }

  return (
    <div className="app">
      <aside className="side">
        <Link to="/" className="brand" style={{ textDecoration: "none" }}>
          <div className="brand-mark"><span className="mk">IA</span></div>
          <div><b>VerifIA<br /></b></div>
        </Link>
        <nav className="nav" aria-label="Principal">
          <div className="nav-label">{aluno ? "Área do aluno" : "Área do professor"}</div>
          <Link to={aluno ? "/aluno/turmas" : "/professor/turmas"} aria-current={props.nav === "turmas" ? "page" : undefined}>
            <Icone nome="book" />Minhas turmas
          </Link>
          {!aluno && (
            <Link to="/professor/pesquisas" aria-current={props.nav === "pesquisas" ? "page" : undefined}>
              <Icone nome="file" />Pesquisas dos alunos
            </Link>
          )}
          {props.tutorial && <button type="button" onClick={() => setTutorialAberto(true)}><Icone nome="help" />Tutorial</button>}
        </nav>
        <div className="me">
          <div className="me-row">
            <div className="avatar">{iniciais(usuario?.nome ?? "")}</div>
            <div><b>{usuario?.nome}</b><span>{aluno ? "Aluno" : "Professor"}</span></div>
          </div>
          <button type="button" className="out" onClick={sairDaConta}><Icone nome="out" />Sair</button>
        </div>
      </aside>
      <main className="main">
        <div className="top">
          <div className="crumbs">
            {voltar && (
              <button type="button" className="back" onClick={() => navegar(voltar.para)} aria-label={`Voltar para ${voltar.texto}`}>
                <Icone nome="left" />Voltar
              </button>
            )}
            {m.map((x, i) =>
              i === m.length - 1 ? (
                <span key={i} className="here">{x.texto}</span>
              ) : (
                <span key={i} style={{ display: "contents" }}>
                  <Link to={x.para}>{x.texto}</Link><Icone nome="right" />
                </span>
              ),
            )}
          </div>
          {props.tutorial && (
            <button type="button" className="btn sm ghost" onClick={() => setTutorialAberto(true)}><Icone nome="help" />Tutorial</button>
          )}
        </div>
        <div className={`page ${props.largo ? "wide" : ""}`}>{props.children}</div>
      </main>
      {tutorialAberto && props.tutorial && <Tutorial chave={props.tutorial} onFechar={() => setTutorialAberto(false)} />}
    </div>
  );
}

export function iniciais(nome: string): string {
  const p = nome.replace(/^(Profa?\.)\s*/i, "").trim().split(/\s+/).filter(Boolean);
  return ((p[0]?.[0] ?? "") + (p.length > 1 ? p[p.length - 1][0] : "")).toUpperCase();
}

export function Cabecalho(props: { titulo: ReactNode; subtitulo?: ReactNode; acoes?: ReactNode; selo?: ReactNode }) {
  return (
    <div className="head">
      <div>
        {props.selo && <div style={{ marginBottom: 10 }}>{props.selo}</div>}
        <h1>{props.titulo}</h1>
        {props.subtitulo && <p className="sub">{props.subtitulo}</p>}
      </div>
      {props.acoes && <div className="actions">{props.acoes}</div>}
    </div>
  );
}

export function Vazio({ children, acao }: { children: ReactNode; acao?: ReactNode }) {
  return <div className="empty"><p>{children}</p>{acao}</div>;
}

export function Recado(props: { tipo: "warn" | "bad" | "ok" | "info" | "prof"; icone: string; titulo: string; children?: ReactNode; citacao?: boolean }) {
  return (
    <div className={`callout ${props.tipo}`}>
      <Icone nome={props.icone} />
      <div>
        <b>{props.titulo}</b>
        {props.children && <p className={props.citacao ? "q" : ""}>{props.children}</p>}
      </div>
    </div>
  );
}

export function Andamento({ p }: { p: Pesquisa }) {
  const feita = p.status === "entregue" || p.status === "concluida";
  const dev = p.devolvida;
  const e1 = feita ? "done" : "now";
  const e2 = p.status === "concluida" ? "done" : p.status === "entregue" ? "now" : "todo";
  const e3 = p.status === "concluida" ? "done" : "todo";
  return (
    <div className="card" style={{ padding: "20px 24px" }}>
      <div className="steps" aria-label="Andamento da pesquisa">
        <div className={`step ${e1} ${dev ? "flag" : ""}`}>
          <span className="dot"><Icone nome={feita ? "check" : dev ? "undo" : "edit"} /></span>
          <b>{dev ? "Devolvida para ajustes" : "Em andamento"}</b>
          <small>{feita ? "Registro finalizado" : dev ? `Devolvida em ${fmtDia(p.data_devolucao)}` : `Criada em ${fmtDia(p.data_criacao)}`}</small>
        </div>
        <div className={`step ${e2}`}>
          <span className="dot"><Icone nome={p.status === "concluida" ? "check" : "send"} /></span>
          <b>Entregue ao professor</b>
          <small>{feita ? `Em ${fmtDia(p.data_entrega)}` : "Ainda não entregue"}</small>
        </div>
        <div className={`step ${e3}`}>
          <span className="dot"><Icone nome="check" /></span>
          <b>Concluída</b>
          <small>{p.status === "concluida" ? `Aceita em ${fmtDia(p.data_conclusao)}` : "Aguardando o professor"}</small>
        </div>
      </div>
    </div>
  );
}
import { dia as fmtDia } from "./formato";

// ------------------------------------------------------------------ carregamento de dados
export function useCarga<T>(buscar: () => Promise<T>, deps: unknown[]) {
  const [dados, setDados] = useState<T | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [n, setN] = useState(0);
  useEffect(() => {
    let vivo = true;
    setErro(null);
    buscar().then((d) => vivo && setDados(d)).catch((e) => vivo && setErro(e instanceof ErroApi ? e.message : "Não foi possível carregar."));
    return () => { vivo = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, n]);
  return { dados, erro, recarregar: () => setN((x) => x + 1), setDados };
}

export function Estado({ erro, carregando, voltarPara }: { erro: string | null; carregando: boolean; voltarPara: string }) {
  if (erro) {
    return (
      <div className="callout bad" role="alert">
        <Icone nome="alert" />
        <div><b>Não foi possível abrir esta tela</b><p>{erro}</p><p style={{ marginTop: 8 }}><Link to={voltarPara}>Voltar</Link></p></div>
      </div>
    );
  }
  return carregando ? <div className="loading">Carregando…</div> : null;
}
