import { ReactNode, useCallback } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { ProvedorAuth, useAuth } from "./auth";
import { ProvedorAvisos, Sprite, useAviso } from "./ui";
import type { Tipo } from "./tipos";
import Acesso from "./paginas/Acesso";
import AlunoTurmas from "./paginas/AlunoTurmas";
import AlunoTurma from "./paginas/AlunoTurma";
import AlunoPesquisa from "./paginas/AlunoPesquisa";
import AlunoInteracao from "./paginas/AlunoInteracao";
import ProfTurmas from "./paginas/ProfTurmas";
import ProfTurma from "./paginas/ProfTurma";
import ProfPesquisas from "./paginas/ProfPesquisas";
import ProfRevisao from "./paginas/ProfRevisao";
import ProfInteracao from "./paginas/ProfInteracao";
import Relatorio from "./paginas/Relatorio";

const inicio = (tipo: Tipo) => (tipo === "professor" ? "/professor/turmas" : "/aluno/turmas");

function Protegida({ tipo, children }: { tipo?: Tipo; children: ReactNode }) {
  const { usuario, carregando } = useAuth();
  if (carregando) return <div className="loading">Carregando…</div>;
  if (!usuario) return <Navigate to="/" replace />;
  if (tipo && usuario.tipo !== tipo) return <Navigate to={inicio(usuario.tipo)} replace />;
  return <>{children}</>;
}

function Entrada() {
  const { usuario, carregando } = useAuth();
  if (carregando) return <div className="loading">Carregando…</div>;
  return usuario ? <Navigate to={inicio(usuario.tipo)} replace /> : <Acesso />;
}

function Rotas() {
  return (
    <Routes>
      <Route path="/" element={<Entrada />} />
      <Route path="/aluno/turmas" element={<Protegida tipo="aluno"><AlunoTurmas /></Protegida>} />
      <Route path="/aluno/turmas/:id" element={<Protegida tipo="aluno"><AlunoTurma /></Protegida>} />
      <Route path="/aluno/pesquisas/:id" element={<Protegida tipo="aluno"><AlunoPesquisa /></Protegida>} />
      <Route path="/aluno/interacoes/:id" element={<Protegida tipo="aluno"><AlunoInteracao /></Protegida>} />
      <Route path="/professor/turmas" element={<Protegida tipo="professor"><ProfTurmas /></Protegida>} />
      <Route path="/professor/turmas/:id" element={<Protegida tipo="professor"><ProfTurma /></Protegida>} />
      <Route path="/professor/pesquisas" element={<Protegida tipo="professor"><ProfPesquisas /></Protegida>} />
      <Route path="/professor/pesquisas/:id" element={<Protegida tipo="professor"><ProfRevisao /></Protegida>} />
      <Route path="/professor/interacoes/:id" element={<Protegida tipo="professor"><ProfInteracao /></Protegida>} />
      <Route path="/pesquisas/:id/relatorio" element={<Protegida><Relatorio /></Protegida>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function ComSessao() {
  const navegar = useNavigate();
  const aviso = useAviso();
  const aoExpirar = useCallback(() => { navegar("/"); aviso("Sua sessão expirou. Entre de novo.", "erro"); }, [navegar, aviso]);
  return <ProvedorAuth aoExpirar={aoExpirar}><Rotas /></ProvedorAuth>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Sprite />
      <ProvedorAvisos><ComSessao /></ProvedorAvisos>
    </BrowserRouter>
  );
}
