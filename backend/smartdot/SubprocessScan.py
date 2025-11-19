from PyQt6.QtCore import QObject, QProcess, pyqtSignal, QByteArray, QCoreApplication
import sys

class ProcessRunner(QObject):
    """
    Runs an external process asynchronously using QProcess.
    Emits signals for stdout, stderr, and when finished.
    """

    outputReceived = pyqtSignal(str)       # stdout
    errorReceived = pyqtSignal(str)        # stderr
    finished = pyqtSignal(int, int)        # exitCode, exitStatus

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)

    def start(self, program: str, args: list[str] = []):
        """
        Starts the given process asynchronously.
        Example: start("python3", ["-u", "script.py"])
        """
        self.process.start(program, args)

    def _handle_stdout(self):
        data: QByteArray = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8").strip()
        if text:
            self.outputReceived.emit(text)

    def _handle_stderr(self):
        data: QByteArray = self.process.readAllStandardError()
        text = bytes(data).decode("utf-8").strip()
        if text:
            self.errorReceived.emit(text)

    def _handle_finished(self, exitCode, exitStatus):
        # Send any remaining buffered output
        self._handle_stdout()
        self._handle_stderr()
        self.finished.emit(exitCode, exitStatus)


# -------------------------------------------------------------------------
# Debugging entry point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app = QCoreApplication(sys.argv)

    runner = ProcessRunner()

    def on_output(text):
        print("[stdout]", text)

    def on_error(text):
        print("[stderr]", text)

    def on_finished(code, status):
        print(f"Process finished: code={code}, status={status}")
        app.quit()

    runner.outputReceived.connect(on_output)
    runner.errorReceived.connect(on_error)
    runner.finished.connect(on_finished)

    # Example command for debugging:
    # Replace with any process you want to test
    runner.start("python3", ["ScanSmartDots.py"])

    sys.exit(app.exec())
