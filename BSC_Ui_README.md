# BSC UI Quick Guide

This document explains how the BSC Qt UI is structured and how to add new pages.

## Overview

The UI is built from three file types:
1. `.ui` files - visual layout created in Qt Designer
2. `.py` files - logic and wiring
3. `frontend/style.qss` - global styling for the app

## Frontend setup

1. Activate your virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
2. Install Qt Designer:
        - Windows or macOS standalone: https://www.pythonguis.com/installation/install-qt-designer-standalone/
        - macOS Homebrew: `brew install --cask qt-creator` (Designer is included)

Notes:
- Keep UI styling in `frontend/style.qss`.
- UI pages live under `frontend/` as `.ui` + `.py` pairs.

## Main window

- Main UI file: `frontend/BSCMainWindow.ui`
- Loader: `frontend/BSCMainWindow.py`
- Navigation: stacked widget `swPages` with child pages named `wgtYourPage`
- Menu actions are accessed via `findChild`

## Add a new page (summary)

1. Create `YourPage.ui` in `frontend/` using Qt Designer. Use Hungarian notation for object names (`btn*`, `lbl*`, `wgt*`, etc).
2. Create `YourPage.py` with a `QWidget` subclass that loads the `.ui` via `uic.loadUi` and exposes a `changePage` signal if needed.
3. In `BSCMainWindow.ui`, add a page to `swPages`, drop a widget inside, and promote it to your class. Name it `wgtYourPage`.
4. In `BSCMainWindow.py`, `findChild` your page and connect signals like `changePage` to `switch_to_page`.

## Implementation notes

- Keep styling in `frontend/style.qss` only; avoid inline styles.
- Use `self.findChild(YourPageClass, 'wgtYourPage')` for page references.
- For standalone page testing, add a small `if __name__ == "__main__":` block.

## Minimal page template

```python
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSignal
import os

class YourPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), "YourPage.ui")
        uic.loadUi(ui_path, self)
```

###Creating your page

When you want to create a page you need to create a .ui file and a .py file. both should be named the same, but this is not a requirement.

Every class requires the following imports

	from PyQt6 import QtWidgets, uic
	from PyQt6.QtGui import QAction
	
A page can be created either by using a .ui file or simply hardcoding it in Python [see ShotGraph.py] This approach is not recommended as it makes it harder to visualize

####UI file tips
1. **Ensure you name everything using Hungarian notation.** This is critical for two reasons:
   - **Code reference:** To locate elements in Python using `findChild()` with the correct object name
   - **Styling:** To apply specific styles from `style.qss` using CSS selectors (e.g., `QPushButton#btnClear`)
   
   Standard prefixes: Buttons: `btn*`, Labels: `lbl*`, Spinboxes: `spn*` (int) or `dsb*` (double), Combos: `cbo*`, Dialogs: `dlg*`, Menus: `mnu*`, Actions: `act*`, Widgets/Containers: `wgt*`, Stacked widgets: `sw*`, Progress bars: `pgb*`, Tables: `tbl*`, Dialog button boxes: `dbb*`, Graphs/Plots: `grph*`. If there is no Hungarian equivalent, use a descriptive name.
2. Wait until all items are in a page before applying formatting. Widgets can get stuck inside each other if you don't wait.
3. Imported/promoted widgets won't be visible in the editor, so ensure you are looking at the right item
4. **Do not apply custom styling in Qt Designer** - use the `style.qss` file instead for all visual customizations

####Python file tips
1. If you are using an element, locate it using `findChild` with the Hungarian notation name:

	self.btnMyButton = self.findChild(QtWidgets.QPushButton, 'btnMyButton')
	self.lblMyLabel = self.findChild(QtWidgets.QLabel, 'lblMyLabel')

1. If something needs to be accessed on the page make an accessor method. If you are unsure make one anyway
2. Make a main method within your page for testing purposes

		if __name__ == "__main__":
	    import sys
	    app = QtWidgets.QApplication(sys.argv)
	    window = [your class]()
	    window.show()
	    sys.exit(app.exec())

###Styling with style.qss
All styling changes should be defined in the centralized **`style.qss`** file located in the `frontend/` directory. This ensures consistent theming across the entire application and makes it easy to update styles globally.

**Why Hungarian notation matters for styling:**
Object names follow Hungarian notation specifically so they can be referenced in the `.qss` file. For example:
- A button named `btnClear` can be styled with `QPushButton#btnClear { ... }`
- A label named `lblTitle` can be styled with `QLabel#lblTitle { ... }`
- A widget named `wgtFrontPage` can be styled with `QWidget#wgtFrontPage { ... }`

**Best practices for styling:**
1. **Always add styles to `style.qss`** unless it's a very specific, one-off case that will never be reused
2. **Use specific selectors** in `.qss` for custom styles (e.g., `QPushButton#btnClear` instead of `QPushButton`)
3. **Never hardcode colors or styles in Python** - use the `.qss` file instead
4. **Reference the style.qss file** in your main window initialization to apply styles globally
5. **Use custom properties** in Qt Designer (e.g., `accent="text"`) to apply pre-defined style classes to multiple widgets

###Importing Widgets
In order to avoid recreating UI elements it is best practice to create a widget for it and import it within your page.

To import a widget, the first step is to place a QWidget in your page. left-click on the widget and select "promote to...". Once you are on the page enter the name of the Python file (excluding the .py) into both the class name and header file fields. After that click add. Finally select the option you just created in the promoted widgets box. If you already created the widget previously you can just select it from the box and click promote.

Remember if you are creating a widget to be used within a page the widget needs its own class and UI files.

###Signals and using imported widgets
A widget can communicate to its child widget by simply calling methods from its class, and that widget can respond with the return values. If an interaction requires the child widget to initiate something that's where signals come in. A signal allows the parent to receive a message from its child. Some elements have built-in signals you can use

Note: although I'm using the term parent and child widget, there is no inheritance

to create a signal

	[YourSignal] = pyqtSignal([DataTypes you want to pass])

to send the signal 

	self.[YourSignal].emit([data])

to receive a signal, in the parent

	[child widget].[YourSignal].connect([your code here])
You need to either have a function with the same parameters as the signal in the parent, or just use a lambda function to do something else

###Menu bar
To add something to the menubar

In Qt Designer you can either click on the "type here" text to create a new menu and/or click on the existing menu to add to it by selecting the "type here" text. You can also create submenus by clicking on the page+ icon. **Take note of the name in the object inspector**

In the .py simply instantiate the action. Remember it's a QAction rather than a QWidget 

	 self.[YourAction] = self.findChild(QAction, '[YourAction]')
	


## Part 2: Tutorial
This tutorial is going to assume you already have your development environment set up. If not follow that tutorial first. If you already know how to make a page go to step 3

###Step 1: Making the UI file

Open Qt Designer

If you are on macOS I highly recommend you create a new desktop and keep the designer in windowed mode there. On Windows use the default combined view.

In the widget box (If you don't see it, go into the menu bar and click View then make sure it's checked) you can grab elements and bring them onto the screen. Follow the practices above for best results

###Step 2: Creating the Python file
In the project create a new Python file named for your page.
Import the following alongside whatever you need for your page

	from PyQt6 import QtWidgets, uic
	from PyQt6.QtGui import QAction
	
From there create your page's class, use the following code as a template

	class YourPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object) 
    # Insert your other signals here if applicable
    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (name matches file in repo)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'YourPage.ui'), self, package='frontend')
        
        
Add relevant logic to the page, more detail above

Make sure you create a main in your Python file to test that your page works

###Step 3: Implementing the page into the rest of the navigation.

####Step 3a: Qt Designer
1. Open *BSCMainWindow.ui* in Qt Designer and go to the stacked widget named `swPages`.
2. Within the pages in the stacked widget, left-click on the last one
3. Right-click on the stacked widget to open the menu. Ensure it says "Page N out of N", if not retry step 2 
4. Click on "Insert page after current"
5. Ensure the new page is at the bottom. If not delete it and retry from step 3
6. Rename the page to `wgtYourNewPageName` (use Hungarian notation with `wgt` prefix for widget containers)
7. Drag a QWidget into that page; you should see it inside the page in the object inspector
8. Rename that widget to your class name (e.g., `YourNewPage`)
9. Left-click on the widget and select "Promote to..."
10. Enter the Python file you just created (e.g., `YourNewPage`) into the **Class Name** field and `frontend.YourNewPage` into the **Header File** field, then click **Add**
11. Select the option you just created in the promoted widgets box and click **Promote**
12. Once that is done, save *BSCMainWindow.ui*


####Step 3b: Python
1. Open *BSCMainWindow.py*
2. Go to the part of the `__init__` method declaring all of the pages and declare your page in the following form:
    
        # previous page declaration
        self.wgtYourNewPage = self.findChild(YourNewPageClass, 'wgtYourNewPage')
        
3. Connect to your new page's `changePage` signal in the following form:

        # previous page declaration
        self.wgtYourNewPage.changePage.connect(self.switch_to_page)
        # Any additional signal connections
        
4. Add an entry to the match case in `switch_to_page()` with your new page index and any incoming data it may need

###Step 4: Navigating to your new page

There are 2 methods of creating navigation to the new page: menu bar actions and page buttons.

For both methods, take note of the index of the page you created (see the page order listed above). Remember: page count in Qt Designer starts at 1, but page indexes are 0-based.

####Step 4a: Button (Primary Method)
This is the main method for navigating to your widget.

1. Open the .ui file of the page you want to navigate from (e.g., `FrontPage.ui`)
2. Add a QPushButton to the page and name it following Hungarian notation (e.g., `btnGoToNewPage`)
3. Open the Python file of the page (e.g., `FrontPage.py`)
4. Declare the button variable and connect it:

        self.btnGoToNewPage = self.findChild(QtWidgets.QPushButton, 'btnGoToNewPage')
        self.btnGoToNewPage.clicked.connect(lambda: self.changePage.emit([PageIndex], "[Data if applicable]"))

####Step 4b: Menu Bar (Secondary Method)
This navigation method is for static references such as Home or main sections.

1. Open *BSCMainWindow.ui* in Qt Designer
2. Click on the menu bar and select the appropriate menu (e.g., `mnuNavigation`)
3. Click on the "type here" text within the menu
4. Type in the action name **Take note of the objectName in the object inspector (use `act*` prefix)**
5. Open *BSCMainWindow.py*
6. Instantiate your action:

        self.actYourNewPage = self.findChild(QAction, 'actYourNewPage')
    
7. Connect your action to the `switch_to_page` method:

        self.actYourNewPage.triggered.connect(lambda: self.switch_to_page([PageIndex], "[Data if applicable]"))
    
     
    





