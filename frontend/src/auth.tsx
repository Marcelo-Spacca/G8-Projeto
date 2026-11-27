import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { api, guardarToken, lerToken, quandoSessaoExpirar } from "./api";
import type { Usuario } from "./tipos";

interface Auth {
  usuario: Usuario | null; carregando: boolean;
  entrou: (token: string, u: Usuario) => void; sair: () => void;
}
const Ctx = createContext<Auth>({ usuario: null, carregando: true, entrou: () => {}, sair: () => {} });
export const useAuth = () => useContext(Ctx);

export function ProvedorAuth({ children, aoExpirar }: { children: ReactNode; aoExpirar: () => void }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);

  const sair = useCallback(() => { guardarToken(null); setUsuario(null); }, []);
  const entrou = useCallback((token: string, u: Usuario) => { guardarToken(token); setUsuario(u); }, []);

  useEffect(() => {
    quandoSessaoExpirar(() => { sair(); aoExpirar(); });
    if (!lerToken()) { setCarregando(false); return; }
    api.eu().then(setUsuario).catch(() => guardarToken(null)).finally(() => setCarregando(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <Ctx.Provider value={{ usuario, carregando, entrou, sair }}>{children}</Ctx.Provider>;
}
