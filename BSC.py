from backend.smartdot.SmartDotConnectionManager import SmartDotConnectionManager

smartdotConnectionManager = SmartDotConnectionManager()

class MotorData:
    def __init__(self, dx, length, spin, tilt, angle):
        self.spin = spin
        self.tilt = tilt
        self.angle = angle
        self.dx = dx
        self.length = length