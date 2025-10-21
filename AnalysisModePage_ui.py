# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'AnalysisModePage.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QSizePolicy,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(910, 892)
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(30, 20, 71, 16))
        self.btnIncrease = QPushButton(Form)
        self.btnIncrease.setObjectName(u"btnIncrease")
        self.btnIncrease.setGeometry(QRect(110, 80, 113, 32))
        self.btnDecrease = QPushButton(Form)
        self.btnDecrease.setObjectName(u"btnDecrease")
        self.btnDecrease.setGeometry(QRect(110, 120, 113, 32))
        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(120, 20, 60, 16))

        self.retranslateUi(Form)
        self.btnDecrease.clicked.connect(self.label_2.update)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.btnIncrease.setText(QCoreApplication.translate("Form", u"Increase", None))
        self.btnDecrease.setText(QCoreApplication.translate("Form", u"Decrease", None))
        self.label_2.setText("")
    # retranslateUi

