#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import ui
import sys
import sqlite3
import threading
import os
import math
import random
import functools

from PyQt5 import QtCore, QtGui, QtWidgets

from ITUSIS_Parser import ITUSIS_Parser

class ITU_Programci():
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.ui = ui.Ui_MainWindow()
        self.ui.show()
        self.resizeWidgets()
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

        self.ui.action_Reset.triggered.connect(self.reset)
        self.ui.action_Update_database.triggered.connect(functools.partial(self.createDatabaseUpdateThread, self.ui.statusbar))
        self.ui.action_Save.triggered.connect(self.save)

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
        senderComboBox = self.ui.sender()
        timeSlots=['' for x in range(0,70)]
        colorArr = ['' for x in range(0,70)]
        for i in range(0,10):
            availClassComboBox = self.ui.findChild(QtWidgets.QComboBox,'availClassComboBox_%d' % i)
            classInfo = availClassComboBox.currentText()
            if classInfo == '':
                continue
            CRN = classInfo[:5]
            self.db.execute(('select ClassTime  from classes where CRN=\'%s\'' % CRN))
            for block in self.db.fetchone()[0].split(','):
                if block == 'Undefined':
                    continue
                start_stop = block.split('-')
                for j in range(int(start_stop[0]),int(start_stop[1])):
                    if timeSlots[j] == '':
                        timeSlots[j] = self.ui.findChild(QtWidgets.QComboBox,'classCodeComboBox_%d' % i).currentText()
                        colorArr[j] = rand_col[i]
                    else:
                        msgbox = QtWidgets.QMessageBox(self.ui)
                        msgbox.setText('Sectiginiz ders baska bir dersinizle cakismaktadir!')
                        msgbox.setWindowTitle('Hata!')
                        msgbox.show()
                        senderComboBox.setCurrentIndex(0)
                        return
        for i in range(0,70):
            item = self.ui.schedule.item(i%14,math.floor(i/14))
            item.setText(timeSlots[i])
            if timeSlots[i] != '':
                item.setBackground(colorArr[i])
            else:
                item.setBackground(QtGui.QColor('white'))

    def save(self):
        classList=[]
        fileName = QtWidgets.QFileDialog.getSaveFileName(self.ui,'Kayıt dosyasını aç');
        saveFile = open(fileName[0],'w')
        for i in range(0,10):
            classEntry = self.ui.findChild(QtWidgets.QComboBox,'availClassComboBox_%d' % i).currentText()
            if classEntry != '':
                classList.append(classEntry[:5])
        saveFile.write(','.join(classList))
        saveFile.close()

    def reset(self):
        name = ['depCodeComboBox_%d','classCodeComboBox_%d','availClassComboBox_%d']
        for i in range(0,10):
            for j in range(0,3):
                obj = self.ui.findChild(QtWidgets.QComboBox, name[j] % i)
                if j == 0:
                    obj.setCurrentIndex(0)
                else:
                    obj.clear()

    def clearAndChangeStateOfComboBoxes(self):
        name = ['depCodeComboBox_%d','classCodeComboBox_%d','availClassComboBox_%d']
        for i in range(0,10):
            for j in range(0,3):
                obj = self.ui.findChild(QtWidgets.QComboBox, name[j] % i)
                obj.clear()
                obj.setEnabled(not obj.isEnabled())

    def resizeWidgets(self):
        #TableWidget
        width = 0
        for i in range(self.ui.schedule.columnCount()):
            width += self.ui.schedule.columnWidth(i)
        width += self.ui.schedule.verticalHeader().sizeHint().width()
        width += self.ui.schedule.verticalScrollBar().sizeHint().width()/6
        height=0
        for i in range(self.ui.schedule.rowCount()):
            height += self.ui.schedule.rowHeight(i)
        height += self.ui.schedule.horizontalHeader().sizeHint().height()
        height += self.ui.schedule.horizontalScrollBar().sizeHint().height()/6
        self.ui.schedule.resize(width,height)

        #MainWindow
        self.ui.setFixedHeight(self.ui.schedule.geometry().bottom()+40)

rand_col=[]
for i in range(0,10):
    rand_col.append(QtGui.QColor.fromRgbF(random.randint(150,255)/255.0,random.randint(150,255)/255.0,random.randint(150,255)/255.0))
ITU_Programci()



'''
import math

class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)



    for i in range(0,70):
        self.schedule.setItem(i%14,math.floor(i/14),QtWidgets.QTableWidgetItem())

'''
