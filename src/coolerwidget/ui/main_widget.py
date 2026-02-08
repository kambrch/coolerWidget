from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QLabel, QLineEdit, QPushButton, QVBoxLayout,
                               QWidget)


class MainWindow(QWidget):
    runClicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MyApp")

        self._inp = QLineEdit()
        self._btn = QPushButton("Run")
        self._out = QLabel("…")

        layout = QVBoxLayout()
        layout.addWidget(self._inp)
        layout.addWidget(self._btn)
        layout.addWidget(self._out)
        self.setLayout(layout)

        self._btn.clicked.connect(self.runClicked.emit)

    def getInputValue(self) -> str:
        return self._inp.text()

    def setOutputValue(self, text: str) -> None:
        self._out.setText(text)
