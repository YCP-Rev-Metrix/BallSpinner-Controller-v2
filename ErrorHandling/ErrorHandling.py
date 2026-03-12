import sys
import traceback
from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtGui import QPixmap
import json

def ErrorWindow(exctype, value, tb):
    # Log the exception or perform other actions
    try:
        traceback_format = "".join(traceback.format_exception(exctype, value, tb))

        # Show a message box with the error details
        app = QApplication.instance() or QApplication(sys.argv)  # Ensure we have a QApplication instance
    
        error_message = f"An unexpected error occurred:\n{str(value)}\n\nDetails:\n{traceback_format}"
        ErrorBox = QMessageBox()
        ErrorBox.setIcon(QMessageBox.Icon.Critical)
        ErrorBox.setWindowTitle("Error")
        ErrorBox.setDetailedText(error_message)
        ErrorBox.setText("An unexpected error occurred. Please check the details for more information.")
        ErrorBox.raise_()  # Bring the message box to the front
        ErrorBox.exec()
        # Call the default excepthook to ensure the program exits after showing the message box
        sys.__excepthook__(exctype, value, tb)
    except Exception as e:
        # If an error occurs while trying to show the error message, log it to the console
        print(f"Failed to display error message: {e}")
        print(f"Original exception: {traceback_format}")

    
    

def LoadErrorDatabase():
    try:
        with open("ErrorHandling/error_database.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load error database: {e}")
        return {}
    
def GetErrorSolution(exception):
    error_db = LoadErrorDatabase()
    exception_type = type(exception).__name__
    return error_db.get(exception_type, "No specific solution found. Please check the logs for details.")

#Plan:
# Create a database of common exceptions and their solutions
# Implement a function that takes an exception as input and checks it against the database
# If a match is found, display the solution to the user
# If no match is found, display a generic error message and log the exception for further analysis
#  



