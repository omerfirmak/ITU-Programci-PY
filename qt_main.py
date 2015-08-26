#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import ui
import sys
import sqlite3
import threading
import os
from PyQt5 import QtCore, QtGui, QtWidgets

from ITUSIS_Parser import ITUSIS_Parser

class ITU_Programci():
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.ui = ui.Ui_MainWindow()
        self.ui.show()
        self.initDbConnection()
        self.initDepCodeComboBoxes()
        self.connectHandlers()

        sys.exit(self.app.exec_())
        return

    def initDbConnection(self):
        if not os.path.isfile('classdb.sqlite'):
            self.firstBoot = True
            self.createDatabaseUpdateThread(self.ui.statusbar)
        else:
            self.firstBoot = False

        self.conn=sqlite3.connect('classdb.sqlite',check_same_thread=False)
        self.db=self.conn.cursor()

    def createDatabaseUpdateThread(self,statusbar):
        databaseUpdateThread = threading.Thread(target=self.updateDatabase, args=(statusbar,))
        self.clearAndChangeStateOfComboBoxes()
        databaseUpdateThread.start()

    def updateDatabase(self,statusbar):
        ITUSIS_Parser(statusbar).getClasses()
        self.clearAndChangeStateOfComboBoxes()
        self.firstBoot = False
        self.initDepCodeComboBoxes()

    def initDepCodeComboBoxes(self):
        if self.firstBoot:
            return
        depCodeList=['']
        for code in self.db.execute('select distinct Depcode from classes'):
            depCodeList.append(code[0])
        for i in range(0,10):
            obj = self.ui.findChild(QtWidgets.QComboBox,'depCodeComboBox_%d' % i)
            obj.clear()
            obj.addItems(depCodeList)

    def connectHandlers(self):
        name = ['depCodeComboBox_%d','classCodeComboBox_%d','availClassComboBox_%d']
        handlers = [self.depCodeSelectedHandler,self.classCodeSelectedHandler,self.classSelectedHandler]
        for i in range(0,10):
            for j in range(0,3):
                obj = self.ui.findChild(QtWidgets.QComboBox, name[j] % i)
                obj.currentIndexChanged.connect(handlers[j])

    def depCodeSelectedHandler(self):
        senderComboBox = self.ui.sender()
        index = senderComboBox.objectName().split('_')[1]
        depCode = senderComboBox.currentText()

        nextComboBox = self.ui.findChild(QtWidgets.QComboBox,'classCodeComboBox_%s' % index)

        if depCode == '':
            nextComboBox.clear()
            return

        self.db.execute('select distinct Code from classes where Depcode=\'%s\'' % depCode)
        classCodeList = ['']
        for elem in self.db.fetchall():
            classCodeList.append(elem[0])

        nextComboBox.clear()
        nextComboBox.addItems(classCodeList)

    def classCodeSelectedHandler(self):
        senderComboBox = self.ui.sender()
        index = senderComboBox.objectName().split('_')[1]
        classCode = senderComboBox.currentText()
        nextComboBox = self.ui.findChild(QtWidgets.QComboBox,'availClassComboBox_%s' % index)

        if classCode == '':
            nextComboBox.clear()
            return

        self.db.execute('select CRN , Title , Inst  ,Build , Day ,Time  from classes where Code=\'%s\'' % classCode)
        availClassList =['']
        for elem in self.db.fetchall():
            availClassList.append('%s :: %s :: %s :: %s :: %s :: %s' % (elem[0],elem[1],elem[2],elem[4],elem[5],elem[3]))

        nextComboBox.clear()
        nextComboBox.addItems(availClassList)

    def classSelectedHandler(self):
        pass


    def clearAndChangeStateOfComboBoxes(self):
        name = ['depCodeComboBox_%d','classCodeComboBox_%d','availClassComboBox_%d']
        for i in range(0,10):
            for j in range(0,3):
                obj = self.ui.findChild(QtWidgets.QComboBox, name[j] % i)
                obj.clear()
                obj.setEnabled(not obj.isEnabled())


ITU_Programci()




'''
class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

'''
