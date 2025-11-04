from .iSmartDot import iSmartDot
class SimSmartDot(iSmartDot):
    def __init__(self):
        self.connected = False

    def connect(self, MAC_Address):
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False
        return True

    def startMag(self):
        pass

    def stopMag(self):
        pass

    def startAccel(self):
        pass

    def stopAccel(self):
        pass

    def startGyro(self):
        pass

    def stopGyro(self):
        pass

    def startLight(self):
        pass

    def stopLight(self):
        pass

    def UUID(self):
        return "SimSmartDot"