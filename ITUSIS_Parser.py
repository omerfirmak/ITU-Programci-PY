import sqlite3
import os
import requests
import re
from bs4 import BeautifulSoup

class ITUSIS_Parser:
    def __init__(self):
        try:
            os.remove('classdb.sqlite')
            print('Deleted already existing DB')
        except:
            print('Creating DB')

        self.db=sqlite3.connect('classdb.sqlite')
        self.cur=self.db.cursor()
        self.cur.execute('''CREATE TABLE classes
        (CRN TEXT, Code TEXT, Title TEXT, Inst TEXT ,Build TEXT, ClassTime TEXT, Restr TEXT )''')


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
            html = requests.get('http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php?fb='+dep).text
            soup = BeautifulSoup(html,'html.parser')
            for rows in soup.findAll('tr', {'onmouseover': True , 'onmouseout': True}):
                for cells in rows.findAll('td'):
                    for elem in cells.descendants:
                        if(isinstance(elem,str)):
                            classEntry.append(elem)
                            break
                classList.append(classEntry)
                classEntry=[]
            self.addToDatabase(classList)

    def addToDatabase(self,data):
        for classEntry in data:
            self.cur.execute("INSERT INTO classes VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}')".format(classEntry[0],classEntry[1],
            classEntry[2].replace('\'',''),classEntry[3],classEntry[4],classEntry[6],classEntry[11]))
        self.db.commit()
