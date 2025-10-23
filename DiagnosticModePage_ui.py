# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DiagnosticModePage.ui'
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
from PySide6.QtWidgets import (QApplication, QDial, QGridLayout, QLabel,
    QPushButton, QSizePolicy, QWidget)

from pyqtgraph import PlotWidget

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(757, 419)
        self.gridLayout_2 = QGridLayout(Form)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.graph2 = PlotWidget(Form)
        self.graph2.setObjectName(u"graph2")

        self.gridLayout.addWidget(self.graph2, 1, 1, 1, 1)

        self.graph1 = PlotWidget(Form)
        self.graph1.setObjectName(u"graph1")

        self.gridLayout.addWidget(self.graph1, 1, 0, 1, 1)

        self.graph3 = PlotWidget(Form)
        self.graph3.setObjectName(u"graph3")

        self.gridLayout.addWidget(self.graph3, 1, 2, 1, 1)

        self.dial_3 = QDial(Form)
        self.dial_3.setObjectName(u"dial_3")

        self.gridLayout.addWidget(self.dial_3, 2, 2, 1, 1)

        self.dial_2 = QDial(Form)
        self.dial_2.setObjectName(u"dial_2")

        self.gridLayout.addWidget(self.dial_2, 2, 1, 1, 1)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)

        self.dial = QDial(Form)
        self.dial.setObjectName(u"dial")

        self.gridLayout.addWidget(self.dial, 2, 0, 1, 1)

        self.btnStart = QPushButton(Form)
        self.btnStart.setObjectName(u"btnStart")
        self.btnStart.setCheckable(False)

        self.gridLayout.addWidget(self.btnStart, 3, 0, 1, 1)

        self.btnClear = QPushButton(Form)
        self.btnClear.setObjectName(u"btnClear")

        self.gridLayout.addWidget(self.btnClear, 3, 1, 1, 1)

        self.btnStop = QPushButton(Form)
        self.btnStop.setObjectName(u"btnStop")

        self.gridLayout.addWidget(self.btnStop, 3, 2, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"<html><head/><body><p align=\"center\">Prototype Diagnostic Mode</p></body></html>", None))
        self.btnStart.setText(QCoreApplication.translate("Form", u"Start", None))
        self.btnClear.setText(QCoreApplication.translate("Form", u"Clear", None))
        self.btnStop.setText(QCoreApplication.translate("Form", u"Stop", None))
    # retranslateUi

