from coolerwidget.core.services import compute


class MainController:
    def __init__(self, window) -> None:
        self.window = window
        self.window.runClicked.connect(self.on_run_clicked)

    def on_run_clicked(self) -> None:
        x = self.window.getInputValue()
        y = compute(x)
        self.window.setOutputValue(y)
