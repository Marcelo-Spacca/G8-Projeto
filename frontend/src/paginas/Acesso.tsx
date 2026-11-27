import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ErroApi } from "../api";
import { useAuth } from "../auth";
import { Icone, Selo } from "../ui";

export default function Acesso() {
  const [cadastro, setCadastro] = useState(false);
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState("aluno");
  const [erro, setErro] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const { entrou } = useAuth();
  const navegar = useNavigate();

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      if (cadastro) {
        await api.cadastrar(nome, email, senha, tipo);
        setCadastro(false);
        setSenha("");
        setOk("Conta criada. Digite sua senha para entrar.");
      } else {
        const r = await api.entrar(email, senha);
        entrou(r.token, r.usuario);
        navegar(r.usuario.tipo === "professor" ? "/professor/turmas" : "/aluno/turmas");
      }
    } catch (x) {
      setErro(x instanceof ErroApi ? x.message : "Não foi possível concluir.");
    } finally {
      setEnviando(false);
    }
  }
  function trocar(paraCadastro: boolean) { setCadastro(paraCadastro); setErro(null); setOk(null); }

  return (
    <div className="auth">
      <section className="auth-hero">
        <div className="brand">
          <div className="brand-mark"><span className="mk">IA</span></div>
          <div><b>VerifIA<br /></b></div>
        </div>
        <div>
          <h1>Cada resposta da IA, conferida e documentada.</h1>
          <p>Registre suas conversas, confira as fontes citadas e entregue ao professor um relatório que mostra o que foi verificado.</p>
        </div>
        <div className="auth-demo" aria-hidden="true">
          <div className="q2">“A avaliação precisa ser repensada quando a produção textual deixa de ser <span className="mark">prova de autoria</span>.”</div>
          <div className="row-s"><Selo tipo="ok">Fonte verificada</Selo><Selo tipo="plain">Trecho ligado ao seu texto</Selo></div>
        </div>
      </section>
      <section className="auth-form">
        <form onSubmit={enviar} style={{ display: "grid", gap: 18 }} noValidate>
          <div>
            <h1>{cadastro ? "Criar conta" : "Entrar"}</h1>
            <p className="sub">{cadastro
              ? "Com a conta de aluno você registra o uso de IA; com a de professor, recebe os relatórios."
              : "Registre o que a IA respondeu, confira cada fonte e entregue o relatório ao professor."}</p>
          </div>
          {ok && <div className="callout ok"><Icone nome="check" /><div><b>{ok}</b></div></div>}
          {cadastro && (
            <div className="f"><label htmlFor="nome">Nome</label>
              <input className="in" id="nome" value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Como você quer ser chamado" autoComplete="name" /></div>
          )}
          <div className="f"><label htmlFor="email">E-mail</label>
            <input className="in" id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="voce@exemplo.com" autoComplete="email" autoFocus /></div>
          <div className="f"><label htmlFor="senha">Senha</label>
            <input className="in" id="senha" type="password" value={senha} onChange={(e) => setSenha(e.target.value)}
              placeholder={cadastro ? "Pelo menos 6 caracteres" : ""} autoComplete={cadastro ? "new-password" : "current-password"} /></div>
          {cadastro && (
            <div className="f"><span className="lb">Você é</span>
              <div className="seg" role="group" aria-label="Tipo de conta">
                <button type="button" aria-pressed={tipo === "aluno"} onClick={() => setTipo("aluno")}>Aluno</button>
                <button type="button" aria-pressed={tipo === "professor"} onClick={() => setTipo("professor")}>Professor</button>
              </div></div>
          )}
          {erro && <p className="err" role="alert">{erro}</p>}
          <button className="btn primary" type="submit" disabled={enviando}>{enviando ? "Aguarde…" : cadastro ? "Criar conta" : "Entrar"}</button>
          <p style={{ textAlign: "center" }}>
            <button type="button" className="linkbtn" onClick={() => trocar(!cadastro)}>
              {cadastro ? "Já tem conta? Entrar" : "Ainda não tem conta? Criar conta"}
            </button>
          </p>
        </form>
      </section>
    </div>
  );
}
