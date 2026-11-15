"""Abre o programa."""
import sys

from PySide6.QtWidgets import QApplication

from ui import estilo
from ui.janela_principal import JanelaPrincipal


def executar(argv=None):
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("Registro verificável do uso de IA")
    estilo.aplicar(app)
    janela = JanelaPrincipal()
    janela.show()
    return app.exec()
