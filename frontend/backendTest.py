from PySide6.QtCore import QObject, Signal, Slot, Property

class Backend(QObject):
    messageChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self._message = "Hello from Python"

    @Property(str, notify=messageChanged)
    def message(self):
        return self._message

    @Slot()
    def doSomething(self):
        #print("Python slot called!")
        self._message = "Updated from Python"
        self.messageChanged.emit(self._message)

