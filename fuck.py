# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pk10.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from caiapi import CaiPiaoApi


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(110, 290, 121, 51))
        self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(30, 20, 31, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(70, 20, 54, 16))
        self.label_2.setObjectName("label_2")
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(370, 60, 381, 431))
        self.textBrowser.setObjectName("textBrowser")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(20, 60, 311, 20))
        self.lineEdit.setObjectName("lineEdit")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(110, 210, 121, 51))
        self.pushButton_2.setObjectName("pushButton_2")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.cnbt()
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "开始投注"))
        self.label.setText(_translate("MainWindow", "余额"))
        self.label_2.setText(_translate("MainWindow", "9999"))
        self.pushButton_2.setText(_translate("MainWindow", "登录"))

    def cnbt(self):
        self.pushButton_2.clicked.connect(self.login)
        self.pushButton.clicked.connect(self.start)

    def login(self):
        file = open('./10pk.txt', 'w')
        file.write('----10分pk投注记录----')
        self.cp = CaiPiaoApi(token=self.lineEdit.text())
        yuer = self.cp.getyuer()
        self.label_2.setText(str(yuer))

    def starttozhu(self):
        res = self.cp.touzhu()
        print("sss")
        self.textBrowser.append(res[3])
        newline = "当前投注期数:%s,投注模式：%s" % (res[1], res[2])
        self.textBrowser.append(newline)
        with open("./10pk.txt", mode='a') as file:
            file.write("\n"+res[3]+newline)
        self.textBrowser.moveCursor(self.textBrowser.textCursor().End)
        self.label_2.setText(str(res[0]))

    def start(self):  # 投注函数  根据上两期的结果进行投注 开完奖就投注 处理各种逻辑
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.starttozhu, 'cron', day_of_week='*', hour='*', minute="*", second=20,
                          id="666")  # 每分钟20秒的时候跑一次
        scheduler.start()