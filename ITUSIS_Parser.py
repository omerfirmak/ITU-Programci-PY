import sqlite3
import os
import requests
import re
from bs4 import BeautifulSoup

class ITUSIS_Parser:
    days=['Pa','Sa','Ça','Pe','Cu']
    def __init__(self):
        try:
            os.remove('classdb.sqlite')
        except:
            pass
        self.db=sqlite3.connect('classdb.sqlite')
        self.cur=self.db.cursor()
        self.cur.execute('''CREATE TABLE classes
        (Depcode TEXT, CRN TEXT, Code TEXT, Title TEXT, Inst TEXT ,Build TEXT, ClassTime TEXT,Restr TEXT )''')


    def getDepartmentCodes(self):
        list=[]
        html = requests.get('http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php').text
        soup = BeautifulSoup(html,'html.parser')
        for depCode in soup.findAll('option',{ 'value' : True}):
            val=depCode.get('value')
            if val != '':
                list.append(val)
        return list

    def getClasses(self):
        for dep in self.getDepartmentCodes():
            classList=[]
            classEntry=[]
            cellEntry=[]
            html = requests.get('http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php?fb='+dep).text
            soup = BeautifulSoup(html,'html.parser')
            for rows in soup.findAll('tr', {'onmouseover': True , 'onmouseout': True}):
                for cells in rows.findAll('td'):
                    for elem in cells.descendants:
                        if(isinstance(elem,str)):
                            cellEntry.append(elem)
                    classEntry.append(cellEntry)
                    cellEntry=[]
                classList.append(classEntry)
                classEntry=[]
            self.addToDatabase(classList,dep)

    def addToDatabase(self,data,dep):
        for classEntry in data:
            insert_query="INSERT INTO classes VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}')".format(dep,classEntry[0][0],classEntry[1][0],
            classEntry[2][0].replace('\'',''),classEntry[3][0],classEntry[4][0],self.calcClassTime(classEntry[5],classEntry[6]),classEntry[11][0])
            self.cur.execute(insert_query)
        self.db.commit()

    def calcClassTime(self,day,hour):
        list =[]
        if day[0][0] == '-':
            return "Undefined"

        for i in range(0,len(day)):
            hourasd = hour[i].split('/')
            start_t = ITUSIS_Parser.days.index(day[i][:2])*14+(int(hourasd[0][:2])-8);
            stop_t = start_t + int(hourasd[1][:2]) - int(hourasd[0][:2])
            list.append(str(start_t) +'-' + str(stop_t))
        return ','.join(list)
