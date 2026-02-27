import ErrorHandling
import sys
import traceback

def ValueErrorTest():
    raise ValueError("This is a test ValueError")

def TypeErrorTest():
    raise TypeError("This is a test TypeError")

def KeyErrorTest():
    raise KeyError("This is a test KeyError")

if __name__ == "__main__":
    sys.excepthook = ErrorHandling.ErrorWindow
    ValueErrorTest()
    print("All tests completed.")