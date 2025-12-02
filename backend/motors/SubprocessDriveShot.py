from PyQt6.QtCore import QObject, QProcess, pyqtSignal, QByteArray, QCoreApplication
import sys

class MotorRunner(QObject):

    def __init__(self):
        super().__init__()
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)
    
    def start(self, program: str, args: list[str] = []):
        self.process.start(program, args)
    def _handle_stdout(self):
        data: QByteArray = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8").strip()
        if text:
            print("[stdout]", text)
    def _handle_stderr(self):
        data: QByteArray = self.process.readAllStandardError()
        text = bytes(data).decode("utf-8").strip()
        if text:
            print("[stderr]", text)
    def _handle_finished(self, exitCode, exitStatus):
        self._handle_stdout()
        self._handle_stderr()
        print(f"Process finished with exit code {exitCode} and status {exitStatus}")
    