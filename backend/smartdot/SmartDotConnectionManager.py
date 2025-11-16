#The purpose of this file is to manage two connections to a SmartDot
#It will also prevent two connections from being made to the same SmartDot
from .iSmartDot import iSmartDot
class SmartDotConnectionManager:
    def __init__(self):
        self.connections = []
        self.max_connections = 2
        self.smartdots = []

    def add_connection(self, MAC_Address, smartdot):
        if len(self.connections) < self.max_connections:
            if MAC_Address in self.connections:
                return False
            else:
                self.connections.append(MAC_Address)
                self.smartdots.append(smartdot)
                print(f"Connections: {self.connections}")
                print(f"SmartDots: {smartdot._MAC_ADDRESS}")
                print(f"SmartDots: {self.smartdots}")
                return True
        else:
            return False

    def remove_connection(self, MAC_Address, smartdot):
        if MAC_Address in self.connections:
            self.connections.remove(MAC_Address)
            self.smartdots.remove(smartdot)
            print(f"Connections: {self.connections}")
            print(f"SmartDots: {smartdot._MAC_ADDRESS}")
            print(f"SmartDots: {self.smartdots}")
            return True
        else:
            return False

    def get_connections(self):
        return self.connections
    def get_smartdots(self):
        return self.smartdots
        
    def get_smartdot(self, MAC_Address):
        for smartdot in self.smartdots:
            if smartdot._MAC_ADDRESS == MAC_Address:
                return smartdot
        return None
