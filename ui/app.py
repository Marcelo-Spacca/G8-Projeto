"""Abre o programa."""
import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from repository import armazenamento
from ui import estilo
from ui.janela_principal import JanelaPrincipal


def _avisar_erro_nao_tratado(tipo, erro, rastro):
    """Erro que nenhuma tela tratou: mostra um aviso em vez de o programa só "ficar sem reagir"."""
    traceback.print_exception(tipo, erro, rastro)
    QMessageBox.critical(
        None,
        "Algo deu errado",
        f"{tipo.__name__}: {str(erro)[:300]}\n\n"
        "Se o problema for de conexão, confira a internet, o arquivo .env e se o banco Firestore "
        "foi criado no Firebase (veja o README).",
    )


def executar(argv=None):
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("Registro verificável do uso de IA")
    estilo.aplicar(app)
    try:
        armazenamento.loja()  # confere já na abertura se o Firebase está configurado
    except armazenamento.ErroDeConfiguracao as erro:
        QMessageBox.critical(None, "Firebase não configurado", str(erro))
        return 1
    sys.excepthook = _avisar_erro_nao_tratado
    janela = JanelaPrincipal()
    janela.show()
    return app.exec()
