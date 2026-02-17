```markdown
# Creating a new page in the BSC

## Part 1: How does the UI work

The BSC UI consists of 2 kinds of files
# BSC UI Quick Guide

This document explains how the BSC Qt UI is structured and how to add new pages.

Key points
- **Main UI:** `BSCMainWindow.ui` (loaded by `BSCMainWindow.py`)
- **Pages:** Each page should have a `.ui` file and a corresponding `.py` file
- **Navigation:** `BSCMainWindow` contains a stacked widget (`swPages`) where each page is a child widget

How to add a page (summary)
1. Create `YourPage.ui` in `frontend/` using Qt Designer with Hungarian notation for all object names
2. Create `YourPage.py` with a QWidget subclass that loads the `.ui` via `uic.loadUi` and exposes a `changePage` signal if needed
3. Promote the widget in `BSCMainWindow.ui` to use your new class (objectName should follow pattern `wgtYourPage`)
4. Wire the `changePage` signal to `BSCMainWindow.switch_to_page` in `BSCMainWindow.py`

Notes
- Use `self.findChild(YourPageClass, 'wgtYourPageName')` in `BSCMainWindow` to obtain references to pages defined in the UI file
- Use Hungarian notation for all object names: buttons (`btn*`), labels (`lbl*`), spinboxes (`spn*`, `dsb*`), combos (`cbo*`), dialogs (`dlg*`), menus (`mnu*`), actions (`act*`), widgets/containers (`wgt*`), stacked widgets (`sw*`), progress bars (`pgb*`), tables (`tbl*`), dialog button boxes (`dbb*`), graphs (`grph*`). This is essential for both code reference and styling.
- **All styling should be defined in `frontend/style.qss`** - never hardcode styles in Python or Qt Designer
- Update `BSCMainWindow.ui` in Qt Designer and save it after promoting widgets

If you want, I can restore additional tutorial sections from the previous file, but this smaller guide keeps the repo references consistent with the new `BSCMainWindow` name.
1. .py files, the script component

The .ui files are XML-based files that should be edited in the *Qt Designer* almost exclusively. If you are going to edit the files manually, only adjust values within the objects rather than trying to restructure the objects themselves. **Make a backup before manually editing the files**. All Ui files are made of widgets. There are some premade widgets within the designer, or you can create UI files to function as widgets within your application.

The .py files are what allow us to have any functionality whatsoever on a page, turning the .ui file into a class that can be used.

### The HomePage

The main UI file in the BSC is called *HomePage.ui*. This file contains an E-stop button and a QStackedWidget. This QStackedWidget contains a set of header widgets labeled in the form of *page[Your Page Name]*. Within these widgets should only be a single widget, promoted to the class of the screen you want to create. 

	HomePage
		btnEStop (QPushButton)
		StackedWidget (QStackedWidget)
			Page[SamplePage1] (Qwidget)
				[samplePage1]([SamplePage1])
			Page[SamplePage2] (Qwidget)
				[samplePage2]([SamplePage2])
			

*HomePage.py* is the Python file that loads and draws *HomePage.ui* and handles navigation. This Widget exsists to contain and manage the various pages in the app. All pages added should be properly defined in the HomePage. Below is a piece of example code.

	self.[Page name] = self.findChild([Class of new page], '[name of page in HomePage.ui]')
	
Page navigation is handeled by the signal changePage connected to the method `switch_to_page(self, index, data):`(see tutorial)

index is the page you want to go to. The following is an example list of indexes. if you create a page, add its index to the list at the bottom of *HomePage.py*

	Order of pages in stackedWidget:
	0 - FrontPage
	1 - DiagnosticModePage
	2 - ShotModePage
	3 - AnalysisModePage
	4 - Cloud Test 
	5 - SmartDotViewer (Currently not used, can be replaced)
	
data is used if additional data needs to be sent to another page. Any object can be passed

Use the match case in the `switch_to_page()` method for the index to call the approprate method for collecting data.

###Creating your page

When you want to to create a page you need to create a .ui file and a .py file. both should be named the same, but this is not a requirement.

Every class requires the following imports

	from PyQt6 import QtWidgets, uic
	from PyQt6.QtGui import QAction
	
A page can be created either by using a .ui file or simply hardcoding it in Python [see ShotGraph.py] This approach is not recommended as it makes it harder to visualize

####UI file tips
1. Ensure you name everything. Use Hungarian notation for the names. If there is no Hungarian equivalent than you can simply leave the name in front of the element
2. Wait untill all items are in a page before applying formating. Widgets can get stuck inside eachother if you don't wait.
3. Imported/promoted widgets won't be visible in the editor, so ensure you are looking at the right item

####Python file tips
1. If you are using an element, it needs to be imported

		self.[elementName] = self.findChild([elementType], '[elementName]')

1. If something needs to be accessed on the page make an accessor method. If you are unsure make one anyway
2. Make a main method within your page for testing purposes

		if __name__ == "__main__":
	    import sys
	    app = QtWidgets.QApplication(sys.argv)
	    window = [your class]()
	    window.show()
	    sys.exit(app.exec())

###Importing Widgets
In order to avoid recreating ui elemets it is best practice to create a widget for it and import it withibn your page.

To import a widget, the first step is to place a Qwidget in your page. leftclick on the widget and select "promote to...". Once you are on the page enter the name of the Python file (excluding the .py) into both the class name and header file fields. After that click add. Finnaly select the option you just created in the promoted widgets box. If you already created the widget previously you can just select it from the box and click promote.

Remember if you are creating a widget to be used within a page the widget needs it's own class and ui files.

###Signals and using imported widgets
A widget can communicate to it's child widget by simply calling methods from its class, and that widget can respond with the return values. If an interaction requires the child widget to initiate something thats where signals come in. A signal allows the parent to recieve a message from its child. Some elements have baked in signals you can use

-note: although im using the term parent and child widget, there is no inheritance

to create a signal

	[YourSignal] = pyqtSignal([DataTypes you want to pass])

to send the signal 

	self.[YourSignal].emit([data])

to recive a signal, in the parent

	[child widget].[YourSignal].connect([your code here])
You need to either have a function with the same parameters as the signal in the parent, or just use a lamda function to do something else

###Menu bar
To add something to the menubar

In Qtdesigner you can either click on the "type here" text to create a new menu and/or click on the exsisting menu to add to it by selecting the "type here" text. You can also create submenus bly cliking on the page+ icon. **Take note of the name in the object inspector**

In the .py simply instantiante the action. Remember its a QAction rather than a Qwidget 
	
	 self.[YourAction] = self.findChild(QAction, '[YourAction]')
	



## Part 2: Tutorial
This tutorial is going to assume you already have your delelopment enironment set up. If not follow that tutorial first. If you alreay know how to make a page go to step 3

###Step 1: Making the Ui file

Open Qt designer

If you are on Macos I highly recomend you create a new desktop and keep the designer in windowed mode there. On windows use the default combined view.

In the widget box (If you dont see it, go into the menu bar and click view then make sure its checked) you can grab elements and bring them on to the screen. Follow the practices above for best results

###Step 2: Creating the Python file
In the project create a new Python file named for your page.
Import the following alongside whatever you need for your page

	from PyQt6 import QtWidgets, uic
	from PyQt6.QtGui import QAction
	
From there create your pages class, use the following code as a template

	class [YourPage](QtWidgets.QWidget):
    changePage = pyqtSignal(int, object) 
	 #Insert Your other signals here if aplicable
    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (name matches file in repo)
        uic.loadUi(os.path.join(os.path.dirname(__file__), '[YourUiFile]'), self, package='frontend')
        
    
        
        
Add Relevant logic to page, more detail above

Make sure you create a main in your Python file to test that your page works

###Step 3: Implementing the page into the rest of the naviagation.

####Step 3a: Qt designer
1. open *HomePage.ui* in Qt designer and go to the QStackedWidget named stackedWidget.
2. within the pages in the QStackedWidget left click on the last one
2. right click on the stacked widget to open the menu. Ensure it says Page N out of N, if not retry step 2 
3. click on insert page after current
4. Ensure the new page is at the bottem. If not delete it and retry from step 2
5. If it is the rename the page to page[YourNewPageName]
6. then drag a wiget into that page, you should see it inside the page you just made in the inspector
7. Rename that wiget to you new page name
8. left click on the widget and select "promote to..."
9. Python file you just created (excluding the .py) into both the class name and header file fields and click add
11. select the option you just created in the promoted widgets box and click promote
12. once that is done save *HomePage.ui*


####Step 3b: Python
1. Open *HomePage.py*
2. Go to the part of the file declairing all of the pages and declare your page in the following form
	
		#previous page decalration
		self.[YourNewPage] = self.findChild([ClassOfYourNewPage], '[NameOfYourNewPageInUiFile]')
		
1. connect to your new pages changePageSignal in the following form

		#previous page decalration
		self.[YourNewPage].changePage.connect(self.switch_to_page)
		#Any additional signal connections
1. Add an entry to the match case in `switch_to_page()` with your new page and any incoming data it may need

###Step 4: Navigating to you new page

# Creating a new page in the BSC

## Part 1: How does the UI work

The BSC UI consists of 3 kinds of files

1. `.ui` files - the visual component (structure and layout)
2. `.py` files - the script component (functionality and logic)
3. `.qss` file - the style component (theming and appearance)

The .ui files are XML-based files that should be edited in the *Qt Designer* almost exclusively. If you are going to edit the files manually, only adjust values within the objects rather than trying to restructure the objects themselves. **Make a backup before manually editing the files**. All UI files are made of widgets. There are some premade widgets within the designer, or you can create UI files to function as widgets within your application.

The .py files are what allow us to have any functionality whatsoever on a page, turning the .ui file into a class that can be used.

The `.qss` file (Qt Style Sheet) is a CSS-like file that handles all visual styling of the application. This includes colors, fonts, borders, padding, and other appearance properties. All style customizations should be made in this file rather than hardcoding styles in Python code or applying them in Qt Designer. This ensures consistent theming across the entire application and makes it easy to make global style changes.


### The BSCMainWindow

The main UI file in the BSC is called *BSCMainWindow.ui*. This file contains a menu bar and a stacked widget (`swPages`). The stacked widget contains a set of header widgets (pages) with objectNames following the pattern `wgt[PageName]`. Within each page should only be a single widget, promoted to the class of the screen you want to create. 

	BSCMainWindow (wndMain)
		Menu Bar (mnuNavigation)
			Actions: actHome, actDiagnosticMode, actAnalysisMode, actCloudTest, actExitApplication
		Stacked Widget (swPages)
			Page 0 (wgtFrontPage)
			Page 1 (wgtDiagnosticModePage)
			Page 2 (wgtShotModePage)
			Page 3 (wgtAnalysisModePage)
			Page 4 (wgtCloudTestPage)
			Page 5 (wgtSmartDotViewer)
			Page 6 (wgtShotViewPage)
			Page 7 (wgtDataViewPage)
					


*BSCMainWindow.py* is the Python file that loads and draws *BSCMainWindow.ui* and handles navigation. This Widget exists to contain and manage the various pages in the app. All pages added should be properly defined in the BSCMainWindow. Below is a piece of example code.

	self.wgtYourNewPage = self.findChild(YourNewPageClass, 'wgtYourNewPage')
	
Page navigation is handled by the signal `changePage` connected to the method `switch_to_page(self, index, data)` in BSCMainWindow.py (see tutorial).

index is the page you want to go to. The following is the order of pages in `swPages`:

	Order of pages in swPages:
	0 - wgtFrontPage (FrontPage)
	1 - wgtDiagnosticModePage (DiagnosticModePage)
	2 - wgtShotModePage (ShotModePage)
	3 - wgtAnalysisModePage (AnalysisModePage)
	4 - wgtCloudTestPage (CloudTest)
	5 - wgtSmartDotViewer (SmartDotViewer)
	6 - wgtShotViewPage (ShotViewPage)
	7 - wgtDataViewPage (DataViewPage)
	
data is used if additional data needs to be sent to another page.

use the match case in the `switch_to_page()` method for the index to call the appropriate method for collecting data.

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
    
     
    





