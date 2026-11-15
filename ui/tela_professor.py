"""Área do professor: relatórios recebidos (RF23). O professor só vê pesquisas já concluídas (RF03)."""
from PySide6.QtWidgets import QVBoxLayout

from ui import componentes as c


class TelaProfessor(c.TelaBase):
    def carregar(self):
        entregues = self.janela.relatorios.listar_entregues()
        self.reiniciar()
        self.corpo.addWidget(c.rotulo("Relatórios recebidos", "titulo"))
        self.corpo.addWidget(c.rotulo("Pesquisas que os alunos concluíram e entregaram.", "mudo"))
        self.linhas = []
        if not entregues:
            self.corpo.addWidget(self.vazio("Nenhum relatório recebido ainda. Quando um aluno concluir uma pesquisa, ela aparece aqui."))
        else:
            lista = c.Lista()
            for p in entregues:
                self.linhas.append(lista.adicionar(self._linha(p)))
            lista.fechar()
            self.corpo.addWidget(lista)
        self.corpo.addStretch(1)

    def _linha(self, pesquisa):
        contagem = self.janela.relatorios.contagem_fontes(pesquisa)
        total = sum(contagem.values())
        linha = c.Linha(clicavel=True)
        linha.pesquisa_id = pesquisa.id
        esquerda = QVBoxLayout()
        esquerda.setSpacing(3)
        esquerda.addWidget(c.rotulo(pesquisa.aluno.nome, "item", quebra=False))
        esquerda.addWidget(c.rotulo(c.cortar(pesquisa.titulo, 90), "documento"))
        direita = QVBoxLayout()
        direita.setSpacing(4)
        if total == 0:
            selos = [c.selo("Sem fontes", "neutro")]
        else:
            selos = [c.selo(f"{contagem['verificada']}/{total} verificadas", "verificada" if contagem["verificada"] == total else "neutro")]
            if contagem["incorreta"]:
                selos.append(c.selo(c.plural(contagem["incorreta"], "incorreta", "incorretas"), "incorreta"))
            if contagem["nao_verificada"]:
                selos.append(c.selo(c.plural(contagem["nao_verificada"], "pendente", "pendentes"), "pendente"))
        direita.addLayout(c.linha_horizontal(None, *selos, espaco=6))
        direita.addWidget(c.rotulo(f"Entregue em {c.formatar_data(pesquisa.data_conclusao)}", "dica", quebra=False))
        linha.selos = selos
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addLayout(direita)
        linha.setLayout(conteudo)
        linha.clicado.connect(lambda pid=pesquisa.id: self.janela.abrir_relatorio(pid, "‹ Relatórios recebidos", self.janela.abrir_professor))
        return linha
