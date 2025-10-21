# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'POC.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDial, QGridLayout,
    QLabel, QMainWindow, QMenuBar, QSizePolicy,
    QStatusBar, QTabWidget, QWidget)

from CloudTest import CloudTest
from InteractiveSineWave import InteractiveSineWave
from pyqtgraph import PlotWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(930, 828)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayout_2 = QGridLayout(self.tab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.graph1 = PlotWidget(self.tab)
        self.graph1.setObjectName(u"graph1")

        self.gridLayout_2.addWidget(self.graph1, 1, 0, 1, 1)

        self.dial = QDial(self.tab)
        self.dial.setObjectName(u"dial")

        self.gridLayout_2.addWidget(self.dial, 3, 0, 1, 1)

        self.dial_3 = QDial(self.tab)
        self.dial_3.setObjectName(u"dial_3")

        self.gridLayout_2.addWidget(self.dial_3, 3, 5, 1, 1)

        self.dial_2 = QDial(self.tab)
        self.dial_2.setObjectName(u"dial_2")

        self.gridLayout_2.addWidget(self.dial_2, 3, 3, 1, 1)

        self.graph2 = PlotWidget(self.tab)
        self.graph2.setObjectName(u"graph2")

        self.gridLayout_2.addWidget(self.graph2, 1, 3, 1, 1)

        self.graph3 = PlotWidget(self.tab)
        self.graph3.setObjectName(u"graph3")

        self.gridLayout_2.addWidget(self.graph3, 1, 5, 1, 1)

        self.label_2 = QLabel(self.tab)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 0, 3, 1, 1)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.chkLockTab = QCheckBox(self.tab_2)
        self.chkLockTab.setObjectName(u"chkLockTab")
        self.chkLockTab.setGeometry(QRect(70, 50, 731, 31))
        self.horizontalLayoutWidget = QWidget(self.tab_2)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(50, 120, 801, 351))
        self.gridLayout_3 = QGridLayout(self.horizontalLayoutWidget)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.BrandonWidget_2 = InteractiveSineWave(self.horizontalLayoutWidget)
        self.BrandonWidget_2.setObjectName(u"BrandonWidget_2")

        self.gridLayout_3.addWidget(self.BrandonWidget_2, 0, 0, 1, 1)

        self.BrandonWidget = InteractiveSineWave(self.horizontalLayoutWidget)
        self.BrandonWidget.setObjectName(u"BrandonWidget")

        self.gridLayout_3.addWidget(self.BrandonWidget, 0, 2, 1, 1)

        self.BrandonWidget_3 = InteractiveSineWave(self.horizontalLayoutWidget)
        self.BrandonWidget_3.setObjectName(u"BrandonWidget_3")

        self.gridLayout_3.addWidget(self.BrandonWidget_3, 0, 1, 1, 1)

        self.label = QLabel(self.tab_2)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(350, 20, 211, 20))
        self.tabWidget.addTab(self.tab_2, "")
        self.AnalysisMode = QWidget()
        self.AnalysisMode.setObjectName(u"AnalysisMode")
        self.label_3 = QLabel(self.AnalysisMode)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(280, 30, 341, 16))
        self.tabWidget.addTab(self.AnalysisMode, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.cloudTest = CloudTest(self.tab_3)
        self.cloudTest.setObjectName(u"cloudTest")
        self.cloudTest.setGeometry(QRect(100, 110, 441, 331))
        self.label_31 = QLabel(self.tab_3)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setGeometry(QRect(320, 70, 57, 14))
        self.tabWidget.addTab(self.tab_3, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 930, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Prototype Diagnostic Mode", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Tab 1", None))
        self.chkLockTab.setText(QCoreApplication.translate("MainWindow", u"LockTab", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Prototype Shot Page", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Tab 2", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Happy AnalysiMode", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.AnalysisMode), QCoreApplication.translate("MainWindow", u"Page", None))
        self.label_31.setText(QCoreApplication.translate("MainWindow", u"Hello", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Page", None))
    # retranslateUi

