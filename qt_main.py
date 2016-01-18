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
        self.finalizeWidgets()
        self.initDbConnection()
        self.initDepCodeComboBoxes()
        self.connectHandlers()
        self.cache = {}
        self.count=0
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
        self.cache = {}
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
        self.ui.action_Load.triggered.connect(self.load)
        self.ui.createSchedulesButton.clicked.connect(self.createPossibleSchedules)
        self.ui.scheduleCombobox.currentIndexChanged.connect(self.scheduleSelectedHandler)

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

        self.db.execute('select CRN , Title , Inst  ,Build , Day ,Time, Restr,ClassTime  from classes where Code=\'%s\'' % classCode)
        availClassList =['']
        for elem in self.db.fetchall():
            if not self.checkIfMeetsCriteria(elem):
                continue
            availClassList.append('%s :: %s :: %s :: %s :: %s :: %s' % (elem[0],elem[1],elem[2],elem[4],elem[5],elem[3]))

        nextComboBox.clear()
        if availClassList == ['']:
            availClassList = ['Kriterlerinize uygun grup yok']
        nextComboBox.addItems(availClassList)

    def checkIfMeetsCriteria(self,classInfo):
        studentDepCode = self.ui.depCodeInput.text()
        if self.ui.useDepCodeCheckbox.isChecked() and studentDepCode not in classInfo[6]:
            return False
        classTime = classInfo[7]
        freeDays=[]
        for i in range(0,5):
            obj = self.ui.findChild(QtWidgets.QCheckBox,'freeDaysCheckbox_%s' % i)
            if obj.isChecked():
                freeDays.append(i)

        for block in classTime.split(','):
            if block == 'Undefined':
                continue
            start_end = block.split('-')
            start = int(start_end[0])
            end = int(start_end[1])
            if math.floor(start/14) in freeDays:
                return False
            if self.ui.hourStartInput.text() != '' and self.ui.hourEndInput.text() != '' :
                if start%14+8 < int(self.ui.hourStartInput.text()) or  end%14+8 >= int(self.ui.hourEndInput.text()):
                    return False

        unwantedBuildList = self.ui.unwantedBuildInput.text()
        for building in classInfo[3].split(','):
            if building in unwantedBuildList:
                return False

        return True

    def classSelectedHandler(self):
        senderComboBox = self.ui.sender()
        crnList = []
        for i in range(0,10):
            availClassComboBox = self.ui.findChild(QtWidgets.QComboBox,'availClassComboBox_%d' % i)
            classInfo = availClassComboBox.currentText()
            if classInfo == '' or classInfo == 'Kriterlerinize uygun grup yok':
                continue
            CRN = classInfo[:5]
            crnList.append(CRN)

        response = self.isValidSchedule(crnList)
        if response[0]:
            self.fillSchedule(response[1],response[2])
        else:
            senderComboBox.setCurrentIndex(0)
            msgbox = QtWidgets.QMessageBox(self.ui)
            msgbox.setText('Sectiginiz ders baska bir dersinizle cakismaktadir!')
            msgbox.setWindowTitle('Hata!')
            msgbox.show()
            senderComboBox.setCurrentIndex(0)

    def scheduleSelectedHandler(self):
        index = self.ui.scheduleCombobox.currentIndex()
        if index <=0:
            return
        self.fillClassInfo(self.scheduleList[index-1])

    def isValidSchedule(self,crnList):
        timeSlots=['' for x in range(0,70)]
        colorArr=['' for x in range(0,70)]
        i=0
        for CRN in crnList:
            if CRN in self.cache:
                query = self.cache[CRN]
            else:
                self.db.execute(('select ClassTime,Code from classes where CRN=\'%s\'' % CRN))
                query = self.db.fetchone()
                self.cache[CRN] = query

            for block in query[0].split(','):
                if block == 'Undefined':
                    continue
                start_end = block.split('-')
                for j in range(int(start_end[0]),int(start_end[1])):
                    if timeSlots[j] == '':
                        timeSlots[j] = query[1]
                        colorArr[j] = rand_col[i]
                    else:
                        return (False,None,None)
            i+=1
        return (True,timeSlots,colorArr)

    def fillSchedule(self,timeSlots,colorArr):
        for i in range(0,70):
            item = self.ui.schedule.item(i%14,math.floor(i/14))
            item.setText(timeSlots[i])
            if timeSlots[i] != '':
                item.setBackground(colorArr[i])
            else:
                item.setBackground(QtGui.QColor('white'))

    def save(self):
        classList=[]
        fileName = QtWidgets.QFileDialog.getSaveFileName(self.ui,'Kayıt dosyasını sec');
        if fileName[0] == '':
            return
        saveFile = open(fileName[0],'w')
        for i in range(0,10):
            classEntry = self.ui.findChild(QtWidgets.QComboBox,'availClassComboBox_%d' % i).currentText()
            if classEntry != '':
                classList.append(classEntry[:5])
        saveFile.write(','.join(classList))
        saveFile.close()

    def load(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self.ui,'Kayıt dosyasını sec');
        if fileName[0] == '':
            return
        saveFile = open(fileName[0],'r')
        crnList = saveFile.read().replace('\n','').split(',')
        self.fillClassInfo(crnList)

    def fillClassInfo(self,crnList):
        for i in range(0,10):
            obj = self.ui.findChild(QtWidgets.QComboBox,'depCodeComboBox_%d' % i)
            obj.setCurrentIndex(0)

        i=0
        for CRN in crnList:
            self.db.execute('select Depcode,Code from classes where CRN=%s' % CRN)
            query = self.db.fetchone()
            if query == None:
                continue
            obj = self.ui.findChild(QtWidgets.QComboBox,'depCodeComboBox_%d' % i)
            obj.setCurrentText(query[0])
            obj = self.ui.findChild(QtWidgets.QComboBox,'classCodeComboBox_%d' % i)
            obj.setCurrentText(query[1])
            obj = self.ui.findChild(QtWidgets.QComboBox,'availClassComboBox_%d' % i)
            obj.setCurrentIndex(obj.findText(CRN,flags=QtCore.Qt.MatchStartsWith))
            i+=1

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

    def finalizeWidgets(self):
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

        #Otomatik program olusturma bolumu
        self.ui.depCodeInput.setText('BLGE')
        self.ui.hourStartInput.setText('8')
        self.ui.hourEndInput.setText('19')
        self.ui.unwantedBuildInput.setText('MKB,ISB,MMB,GDB')
        #MainWindow
        #self.ui.setHeight(self.ui.schedule.geometry().bottom()+40)

    def createPossibleSchedules(self,checked,crnList=[],timeSlots=[0 for x in range(0,70)],index=0):
        if index==10:
            self.scheduleList.append(crnList)
            self.ui.scheduleCombobox.addItem('%d. opsiyon' % self.ui.scheduleCombobox.count())
            return
        elif index==0:
            self.scheduleList = []
            self.ui.scheduleCombobox.clear()
            self.ui.scheduleCombobox.addItem('')
        comboBox = self.ui.findChild(QtWidgets.QComboBox,'availClassComboBox_%d' % index)
        if comboBox.count() <= 1:
            self.createPossibleSchedules(checked,crnList,timeSlots,index+1)
        else:
            if comboBox.currentIndex() > 0:
                CRN = comboBox.currentText()[:5]
                if not self.isValidSchedule(crnList+[CRN])[0]:
                    return
                self.createPossibleSchedules(checked,crnList+[CRN],timeSlots,index+1)
            else:
                for i in range(1,comboBox.count()):
                    CRN = comboBox.itemText(i)[:5]
                    if not self.isValidSchedule(crnList+[CRN])[0]:
                        continue
                    self.createPossibleSchedules(checked,crnList+[CRN],timeSlots,index+1)
count=0
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
