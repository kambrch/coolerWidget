from coolerwidget.controllers.main_controller import MainController
from coolerwidget.ui.main_widget import MainWindow
from PySide6.QtWidgets import QApplication


def main() -> None:
    app = QApplication([])
    window = MainWindow()
    _controller = MainController(window)
    window.show()
    app.exec()
