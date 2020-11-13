# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Equi.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog


class EquiDialog(QDialog):
    def __init__(self, parent=None):
        super(EquiDialog, self).__init__(parent)

        self.setObjectName("Dialog")
        self.resize(400, 300)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(130, 30, 111, 16))
        self.label.setObjectName("label")
        self.buy = QtWidgets.QPushButton(self)
        self.buy.setGeometry(QtCore.QRect(70, 230, 75, 23))
        self.buy.setObjectName("buy")
        self.exit = QtWidgets.QPushButton(self)
        self.exit.setGeometry(QtCore.QRect(200, 230, 75, 23))
        self.exit.setObjectName("exit")
        self.widget = QtWidgets.QWidget(self)
        self.widget.setGeometry(QtCore.QRect(90, 70, 191, 61))
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.label_3 = QtWidgets.QLabel(self.widget)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.thing = QtWidgets.QLineEdit(self.widget)
        self.thing.setObjectName("thing")
        self.verticalLayout.addWidget(self.thing)
        self.price = QtWidgets.QLineEdit(self.widget)
        self.price.setObjectName("price")
        self.verticalLayout.addWidget(self.price)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.exit.clicked.connect(self.quit)
        self.buy.clicked.connect(self.add_equi)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "Новое оборудование"))
        self.buy.setText(_translate("Dialog", "Закупить"))
        self.exit.setText(_translate("Dialog", "Отмена"))
        self.label_2.setText(_translate("Dialog", "Название"))
        self.label_3.setText(_translate("Dialog", "Стоимость"))
