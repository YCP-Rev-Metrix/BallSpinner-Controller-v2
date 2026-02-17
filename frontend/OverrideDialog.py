from PyQt6 import QtWidgets, QtCore, uic
import os

class OverrideDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, *, current_enabled: bool = False):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'OverrideDialog.ui'), self, package='frontend')
        
        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, 'dbbMain')
        self.chkEnableOverride = self.findChild(QtWidgets.QCheckBox, 'chkEnableOverride')
        self.lblOverrideStatus = self.findChild(QtWidgets.QLabel, 'lblOverrideStatus')
        self.lblWarning = self.findChild(QtWidgets.QLabel, 'lblWarning')
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        # Update label when checkbox changes
        self.chkEnableOverride.stateChanged.connect(self.update_status_label)
        
        self.setWindowTitle("Override Mode Settings")
        self.setModal(True)
        self.resize(800, 500)

        # Reflect current state and messaging
        self.chkEnableOverride.setChecked(current_enabled)
        self._update_action_text(current_enabled)
        self.update_status_label()

    def _update_action_text(self, currently_enabled: bool):
        """Update the warning text to reflect enable/disable intent."""
        if currently_enabled:
            self.lblWarning.setText("⚠ WARNING: You are about to DISABLE override mode. Motors will return to safe limits.")
        else:
            self.lblWarning.setText("⚠ WARNING: Override mode will allow motors to exceed safe operating limits!")
    
    def update_status_label(self):
        """Update the status label based on checkbox state."""
        if self.chkEnableOverride.isChecked():
            self.lblOverrideStatus.setText("Status: Override Mode will be ENABLED")
            self.lblOverrideStatus.setProperty("status", "enabled")
        else:
            self.lblOverrideStatus.setText("Status: Override Mode will be DISABLED")
            self.lblOverrideStatus.setProperty("status", "disabled")

        self.lblOverrideStatus.style().unpolish(self.lblOverrideStatus)
        self.lblOverrideStatus.style().polish(self.lblOverrideStatus)
    
    def is_override_enabled(self):
        """Return whether override mode is enabled."""
        return self.chkEnableOverride.isChecked()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    dialog = OverrideDialog()
    result = dialog.exec()
    if result == QtWidgets.QDialog.DialogCode.Accepted:
        print(f"Override enabled: {dialog.is_override_enabled()}")
