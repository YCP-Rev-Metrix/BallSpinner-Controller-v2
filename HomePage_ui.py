# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'HomePage.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QMainWindow,
    QMenuBar, QSizePolicy, QStatusBar, QTabWidget,
    QVBoxLayout, QWidget)

from AnalysisModePage import AnalysisModePage
from CloudTest import CloudTest
from DiagnosticModePage import DiagnosticModePage
from InteractiveSineWave import InteractiveSineWave

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(930, 828)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_4 = QGridLayout(self.centralwidget)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabDiagnosticMode = QWidget()
        self.tabDiagnosticMode.setObjectName(u"tabDiagnosticMode")
        self.gridLayout_2 = QGridLayout(self.tabDiagnosticMode)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.widget_2 = DiagnosticModePage(self.tabDiagnosticMode)
        self.widget_2.setObjectName(u"widget_2")

        self.gridLayout_2.addWidget(self.widget_2, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tabDiagnosticMode, "")
        self.tabShotMode = QWidget()
        self.tabShotMode.setObjectName(u"tabShotMode")
        self.verticalLayout_2 = QVBoxLayout(self.tabShotMode)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(self.tabShotMode)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.BrandonWidget_2 = InteractiveSineWave(self.tabShotMode)
        self.BrandonWidget_2.setObjectName(u"BrandonWidget_2")

        self.gridLayout_3.addWidget(self.BrandonWidget_2, 0, 0, 1, 1)

        self.BrandonWidget_3 = InteractiveSineWave(self.tabShotMode)
        self.BrandonWidget_3.setObjectName(u"BrandonWidget_3")

        self.gridLayout_3.addWidget(self.BrandonWidget_3, 0, 1, 1, 1)

        self.BrandonWidget = InteractiveSineWave(self.tabShotMode)
        self.BrandonWidget.setObjectName(u"BrandonWidget")

        self.gridLayout_3.addWidget(self.BrandonWidget, 0, 2, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_3)

        self.tabWidget.addTab(self.tabShotMode, "")
        self.tabCloud = QWidget()
        self.tabCloud.setObjectName(u"tabCloud")
        self.gridLayout = QGridLayout(self.tabCloud)
        self.gridLayout.setObjectName(u"gridLayout")
        self.cloudTest = CloudTest(self.tabCloud)
        self.cloudTest.setObjectName(u"cloudTest")

        self.gridLayout.addWidget(self.cloudTest, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tabCloud, "")
        self.tabAnalysisMode = QWidget()
        self.tabAnalysisMode.setObjectName(u"tabAnalysisMode")
        self.widget = AnalysisModePage(self.tabAnalysisMode)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(10, 10, 891, 811))
        self.tabWidget.addTab(self.tabAnalysisMode, "")

        self.gridLayout_4.addWidget(self.tabWidget, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 930, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabDiagnosticMode), QCoreApplication.translate("MainWindow", u"Diagnostic Mode", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Prototype Shot Page", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabShotMode), QCoreApplication.translate("MainWindow", u"Shot Mode", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCloud), QCoreApplication.translate("MainWindow", u"Page", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabAnalysisMode), QCoreApplication.translate("MainWindow", u"Analysis mode", None))
    # retranslateUi

