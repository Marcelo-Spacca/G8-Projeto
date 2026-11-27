import type { Contagem } from "./tipos";

const dois = (n: number) => String(n).padStart(2, "0");

export function dia(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return `${dois(d.getDate())}/${dois(d.getMonth() + 1)}/${d.getFullYear()}`;
}
export function dataHora(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return `${dia(iso)} às ${dois(d.getHours())}:${dois(d.getMinutes())}`;
}
export const plural = (n: number, s: string, p: string) => `${n} ${n === 1 ? s : p}`;

/** '3 fontes · 1 verificada · 1 incorreta · 1 pendente' (aluno) */
export function resumoFontes(c: Contagem): string {
  const total = c.verificada + c.incorreta + c.nao_verificada;
  if (total === 0) return "Sem fontes";
  const partes = [plural(total, "fonte", "fontes")];
  if (c.verificada) partes.push(plural(c.verificada, "verificada", "verificadas"));
  if (c.incorreta) partes.push(plural(c.incorreta, "incorreta", "incorretas"));
  if (c.nao_verificada) partes.push(`${c.nao_verificada} ${c.nao_verificada === 1 ? "pendente" : "pendentes"}`);
  return partes.join(" · ");
}
/** '3 fontes (1 verificada, 1 pendente)' (professor) */
export function resumoFontesProf(c: Contagem): string {
  const total = c.verificada + c.incorreta + c.nao_verificada;
  if (total === 0) return "sem fontes";
  const partes: string[] = [];
  if (c.verificada) partes.push(plural(c.verificada, "verificada", "verificadas"));
  if (c.incorreta) partes.push(plural(c.incorreta, "incorreta", "incorretas"));
  if (c.nao_verificada) partes.push(plural(c.nao_verificada, "pendente", "pendentes"));
  return `${plural(total, "fonte", "fontes")} (${partes.join(", ")})`;
}
export function nomes(lista: { nome: string }[]): string {
  const n = lista.map((x) => x.nome);
  if (n.length <= 1) return n.join("");
  return `${n.slice(0, -1).join(", ")} e ${n[n.length - 1]}`;
}
export function cortar(texto: string, max: number): string {
  const t = texto.replace(/\s+/g, " ").trim();
  return t.length <= max ? t : t.slice(0, max - 1).trimEnd() + "…";
}
