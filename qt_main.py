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
        self.databaseUpdateUnderway=False

        self.programci = QtWidgets.QApplication(sys.argv)
        self.ui = ui.Ui_MainWindow()
        self.ui.show()
        self.initDbConnection()
        self.initDepCodeComboBoxes()
        self.connectHandlers()

        sys.exit(self.programci.exec_())
        return

    def initDbConnection(self):
        if not os.path.isfile('classdb.sqlite'):
            self.createDatabaseUpdateThread(self.ui.statusbar)
        self.conn=sqlite3.connect('classdb.sqlite',check_same_thread=False)
        self.db=self.conn.cursor()

    def createDatabaseUpdateThread(self,statusbar):
        databaseUpdateThread = threading.Thread(target=self.updateDatabase, args=(statusbar,))
        self.databaseUpdateUnderway=True
        databaseUpdateThread.start()

    def updateDatabase(self,statusbar):
        ITUSIS_Parser(statusbar).getClasses()
        self.databaseUpdateUnderway=False
        self.initDepCodeComboBoxes()

    def initDepCodeComboBoxes(self):
        if self.databaseUpdateUnderway:
            print('db update')
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
        print('depCodeSelectedHandler')
        pass

    def classCodeSelectedHandler(self):
        print('classCodeSelectedHandler')
        pass

    def classSelectedHandler(self):
        print('classSelectedHandler')
        pass


ITU_Programci()






'''
class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

'''
