#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from Tkinter import *
from ttk import *
import tkMessageBox
import tkFileDialog

import sqlite3
import os
import math
import random

from ITUSIS_Parser import ITUSIS_Parser

class ITU_Programci():
    def __init__(self):
        if not os.path.isfile('classdb.sqlite'):
            self.conn=sqlite3.connect('classdb.sqlite')
            self.db=self.conn.cursor()
            self.updateDatabase(True)
        else:
            self.conn=sqlite3.connect('classdb.sqlite')
            self.db=self.conn.cursor()
        self.initUI()

    def initUI(self):
        self.root = Tk()
        self.initMenu()
        self.initFrame()
        self.initWidgets()
        self.root.mainloop()

    def initMenu(self):
        self.menuBar = Menu(self.root)
        self.root.config(menu=self.menuBar)

        #Dosya Menusu
        self.fileMenu=Menu(self.menuBar,tearoff=0)
        self.fileMenu.add_command(label='Ac',command=self.load)
        self.fileMenu.add_command(label='Kaydet',command=self.save)
        self.menuBar.add_cascade(label="Dosya", menu=self.fileMenu)

        #Program Menusu
        self.progMenu=Menu(self.menuBar,tearoff=0)
        self.progMenu.add_command(label='Sifirla', command=self.reset)
        self.progMenu.add_command(label='Veritabanini guncelle', command=self.updateDatabase)
        self.menuBar.add_cascade(label="Program", menu=self.progMenu)

    def initFrame(self):
        self.frame = Frame(self.root,height=565,width=840)
        self.frame.master.title('ITU Programci')
        self.frame.pack()

    def initWidgets(self):
        depCodeList=['']
        for code in self.db.execute('select distinct Depcode from classes'):
            depCodeList.append(code[0])

        #Bolum kodlari sutunu
        self.depLabel = Label(self.frame,text='Bolum')
        self.depLabel.place(x=15,y=3)

        self.depCodeSpinner=[]
        for i in range(0,10):
            self.depCodeSpinner.append(Combobox(self.frame,width=6,state='readonly'))
            self.depCodeSpinner[i]['values']=depCodeList
            self.depCodeSpinner[i].place(x=15,y=22*(i+1))
            self.depCodeSpinner[i].bind('<<ComboboxSelected>>',self.depCodeSelectedHandler)

        #Ders kodu sutunu
        self.classCodeLabel = Label(self.frame,text='Ders Kodu')
        self.classCodeLabel.place(x=95,y=3)

        self.classCodeSpinner=[]
        for i in range(0,10):
            self.classCodeSpinner.append(Combobox(self.frame,width=10,state='readonly'))
            self.classCodeSpinner[i]['values']=['']
            self.classCodeSpinner[i].place(x=95,y=22*(i+1))
            self.classCodeSpinner[i].bind('<<ComboboxSelected>>',self.classCodeSelectedHandler)

        #Acilan dersler sutunu
        self.availClassLabel = Label(self.frame,text='Acilan Dersler')
        self.availClassLabel.place(x=205,y=3)

        self.availClassSpinner=[]
        for i in range(0,10):
            self.availClassSpinner.append(Combobox(self.frame,width=75,state='readonly'))
            self.availClassSpinner[i]['values']=['']
            self.availClassSpinner[i].place(x=205,y=22*(i+1))
            self.availClassSpinner[i].bind('<<ComboboxSelected>>',self.updateSchedule)

        #Haftalik cizelge
        self.weekChart = []
        for i in range(0,14*5):
            self.weekChart.append(Label(self.frame,anchor='center',background='white',width=10))
            self.weekChart[i].place(x=(90+85*math.floor(i/14)), y=270+20*(i%14))
        self.chartLabels=[]
        days=['Pazartesi','Sali','Carsamba','Persembe','Cuma']
        for i in range(0,5):
            self.chartLabels.append(Label(self.frame,text=days[i],anchor='center',width=10))
            self.chartLabels[i].place(x=90+i*85, y=250)

        for i in range(0, 14):
            self.chartLabels.append(Label(self.frame,text='{0}:30-{1}:29'.format(8+i,9+i),width=10,anchor='center'))
            self.chartLabels[i+5].place(x=5, y=270+20*(i%14))

    def reset(self):
        for index in range(0,10):
            self.depCodeSpinner[index].current(0)
            self.classCodeSpinner[index]['values'] = ['']
            self.availClassSpinner[index]['values'] = ['']
            self.classCodeSpinner[index].current(0)
            self.availClassSpinner[index].current(0)
        self.updateSchedule(None,index)

    def updateDatabase(self,firstBoot=False):
        if firstBoot:
            root = Tk()
            root.withdraw()
            tkMessageBox.showinfo('Veritabani guncellemesi','Veritabani simdi guncellenecek. Bu islem yaklasik 1-2 dakika surecektir.')
        else:
            ans= tkMessageBox.askquestion('Veritabani guncellemesi','Veritabanini simdi guncellemek istiyor musunuz?. Bu islem yaklasik 1-2 dakika surecektir.')
            if ans=='no':
                return
        self.db.close()
        updater = ITUSIS_Parser()
        updater.getClasses()
        self.conn=sqlite3.connect('classdb.sqlite')
        self.db=self.conn.cursor()
        if not firstBoot:
            depCodeList=['']
            for code in self.db.execute('select distinct Depcode from classes'):
                depCodeList.append(code[0])
            for i in range(0,10):
                self.depCodeSpinner[i]['values']=depCodeList

    def depCodeSelectedHandler(self,event,_index=None):
        if _index != None:
            index = _index
            depCode = self.depCodeSpinner[index].get()
        else:
            index = int(event.widget.winfo_y()/22 -1)
            depCode = event.widget.get()

        if depCode == '':
            self.classCodeSpinner[index]['values'] = ['']
            self.availClassSpinner[index]['values'] = ['']
            self.classCodeSpinner[index].current(0)
            self.availClassSpinner[index].current(0)
            if event != None:
                self.updateSchedule(None,index)
            return

        self.db.execute('select distinct Code from classes where Depcode=\'%s\'' % depCode)
        classCodeList = ['']
        for elem in self.db.fetchall():
            classCodeList.append(elem[0])
        self.classCodeSpinner[index]['values'] = classCodeList
        self.classCodeSpinner[index].current(0)
        self.availClassSpinner[index]['values'] = ['']
        self.availClassSpinner[index].current(0)
        if event != None:
            self.updateSchedule(None,index)

    def classCodeSelectedHandler(self,event,_index=None):
        if _index != None:
            index = _index
            classCode = self.classCodeSpinner[index].get()
        else:
            classCode = event.widget.get()
            index = int(event.widget.winfo_y()/22 -1)

        if classCode == '':
            self.availClassSpinner[index]['values'] = ['']
            self.availClassSpinner[index].current(0)
            if event != None:
                self.updateSchedule(None,index)
            return

        self.db.execute('select CRN , Title , Inst  ,Build , Day ,Time  from classes where Code=\'%s\'' % classCode)
        availClassList =['']
        for elem in self.db.fetchall():
            availClassList.append('%s :: %s :: %s :: %s :: %s :: %s' % (elem[0],elem[1],elem[2],elem[4],elem[5],elem[3]))
        self.availClassSpinner[index]['values'] = availClassList
        self.availClassSpinner[index].current(0)
        if event != None:
            self.updateSchedule(None,index)

    def updateSchedule(self,event,index=None):
        temp = [0 for x in range(70)]
        temp2 = [0 for x in range(70)]
        for i in range(0,10):
            data = self.availClassSpinner[i].get()
            if data == '':
                continue
            CRN = data[:5]
            self.db.execute(('select ClassTime  from classes where CRN=\'%s\'' % CRN))
            for block in self.db.fetchone()[0].split(','):
                start_stop = block.split('-')
                for j in range(int(start_stop[0]),int(start_stop[1])):
                    if temp[j] == 0:
                        temp[j] = rand_col[i]
                        temp2[j] = self.classCodeSpinner[i].get()
                    else:
                        if event != None:
                            event.widget.current(0)
                        else:
                            self.availClassSpinner[index].current(0)
                        self.updateSchedule(event,index)
                        tkMessageBox.showinfo('Hata','Sectiginiz ders baska bir dersinizle cakismaktadir!')
                        return
        for i in range(0,70):
            self.weekChart[i]['background']= 'white'
            self.weekChart[i]['text']=''
            if temp[i] != 0:
                self.weekChart[i]['background']=temp[i]
                self.weekChart[i]['text']= temp2[i]

    def save(self):
        fileName=tkFileDialog.asksaveasfilename(defaultextension='.ipsf',filetypes=[('Itu Programci Save File', '.ipsf')])
        saveFile = open(fileName,'w')
        list =[]
        for i in range(0,10):
            if self.availClassSpinner[i].get() != '':
                list.append(self.availClassSpinner[i].get()[:5])

        saveFile.write(','.join(list))
        saveFile.close()

    def load(self):
        fileName=tkFileDialog.askopenfilename(defaultextension='.ipsf',filetypes=[('Itu Programci Save File', '.ipsf')])
        saveFile = open(fileName,'r')
        CrnList = saveFile.read().replace('\n','').split(',')
        i=0
        for CRN in CrnList:
            self.db.execute('select Depcode,Code from classes where CRN=%s' % CRN)
            query = self.db.fetchone()
            self.depCodeSpinner[i].set(query[0])
            self.depCodeSelectedHandler(None,i)
            self.classCodeSpinner[i].set(query[1])
            self.classCodeSelectedHandler(None,i)
            for class_entry in self.availClassSpinner[i]['values']:
                if class_entry[:5] == CRN:
                    self.availClassSpinner[i].set(class_entry)
                    break
            i+=1
        self.updateSchedule(None)



rand_col = ['#CE9090','#CE90CA','#B890CE','#9092CE','#90B9CE','#90CEB5','#90CE92','#C6CE90','#CEBC90','#919191']
programci = ITU_Programci()
