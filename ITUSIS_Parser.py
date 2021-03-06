# -*- coding: utf-8 -*-
import sqlite3
import os
import requests
import re
from bs4 import BeautifulSoup
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

class ITUSIS_Parser(QtCore.QThread):
    days=['Pa','Sa','Ça','Pe','Cu']

    updateStatusBarSignal = QtCore.pyqtSignal(str)

    def __init__(self):
        super(ITUSIS_Parser, self).__init__()
        reload(sys)
        sys.setdefaultencoding('utf-8')
        self.db=sqlite3.connect('classdb.sqlite',check_same_thread=False)
        self.cur=self.db.cursor()
        try:
            self.cur.execute('DROP TABLE classes')
        except:
            pass
        self.cur.execute('CREATE TABLE classes (Depcode TEXT, CRN TEXT, Code TEXT, Title TEXT, Inst TEXT ,Build TEXT, ClassTime TEXT,Restr TEXT,Day TEXT, Time TEXT )')

    def run(self):
        self.getClasses()

    def getDepartmentCodes(self):
        list=[]
        r=requests.get('http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php')
        r.encoding='windows-1254'
        html = r.text
        soup = BeautifulSoup(html,'html.parser')
        for depCode in soup.findAll('option',{ 'value' : True}):
            val=depCode.get('value')
            if val != '':
                list.append(val)
        return list

    def getClasses(self):
        for dep in self.getDepartmentCodes():
            self.updateStatusBarSignal.emit(dep)
            classList=[]
            classEntry=[]
            cellEntry=[]
            r=requests.get('http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php?fb='+dep)
            r.encoding='windows-1254'
            html = r.text
            soup = BeautifulSoup(html,'html.parser')
            for rows in soup.findAll('tr', {'onmouseover': True , 'onmouseout': True}):
                for cells in rows.findAll('td'):
                    for elem in cells.descendants:
                        if(isinstance(elem,basestring)):
                            cellEntry.append(elem)
                    if cellEntry == []:
                        cellEntry.append("")
                    classEntry.append(cellEntry)
                    cellEntry=[]
                classList.append(classEntry)
                classEntry=[]
            self.addToDatabase(classList,dep)
        self.updateStatusBarSignal.emit('end')
        self.db.close()

    def addToDatabase(self,data,dep):
        for classEntry in data:
            insert_query="INSERT INTO classes VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}')".format(dep,classEntry[0][0],classEntry[1][0],
            classEntry[2][0].replace('\'',''),classEntry[3][0].replace('\'',''),','.join(classEntry[4]),self.calcClassTime(classEntry[5],classEntry[6]),
            classEntry[11][0],','.join(classEntry[5]),','.join(classEntry[6]))
            self.cur.execute(insert_query)
        self.db.commit()

    def calcClassTime(self,day,hour):
        list =[]
        if day[0][0] == '-':
            return "Undefined"

        for i in range(0,len(day)):
            hourasd = hour[i].split('/')
            if hourasd[0] == '':
                return "Undefined"

            try:
                start_t = ITUSIS_Parser.days.index(day[i][:2])*14+(int(hourasd[0][:2])-8);
            except:
                if len(day) == 1:
                    return "Undefined"
                else:
                    continue

            stop_t = start_t + int(hourasd[1][:2]) - int(hourasd[0][:2])

            if hourasd[0][-2:] == "00":
                start_t-=0.5

            if hourasd[1][-3:-1] == "59":
                stop_t+=0.5

            start_t*=2
            stop_t*=2

            list.append(str(int(start_t)) +'-' + str(int(stop_t)))
        return ','.join(list)
