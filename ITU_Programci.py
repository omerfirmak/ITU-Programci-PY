#!/usr/bin/python3
from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
import sqlite3
import time
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
        self.fileMenu.add_command(label='Denem1')
        self.fileMenu.add_command(label='Denem2')
        self.menuBar.add_cascade(label="Dosya", menu=self.fileMenu)

        #Program Menusu
        self.progMenu=Menu(self.menuBar,tearoff=0)
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
        self.depLabel.pack()
        self.depLabel.place(x=15,y=3)

        self.depCodeSpinner=[]
        for i in range(0,10):
            self.depCodeSpinner.append(Combobox(self.frame,width=6,state='readonly'))
            self.depCodeSpinner[i]['values']=depCodeList
            self.depCodeSpinner[i].pack()
            self.depCodeSpinner[i].place(x=15,y=22*(i+1))
            self.depCodeSpinner[i].bind('<<ComboboxSelected>>',self.depCodeSelectedHandler)

        #Ders kodu sutunu
        self.classCodeLabel = Label(self.frame,text='Ders Kodu')
        self.classCodeLabel.pack()
        self.classCodeLabel.place(x=95,y=3)

        self.classCodeSpinner=[]
        for i in range(0,10):
            self.classCodeSpinner.append(Combobox(self.frame,width=10,state='readonly'))
            self.classCodeSpinner[i].pack()
            self.classCodeSpinner[i]['values']=['']
            self.classCodeSpinner[i].place(x=95,y=22*(i+1))
            self.classCodeSpinner[i].bind('<<ComboboxSelected>>',self.classCodeSelectedHandler)

        #Acilan dersler sutunu
        self.availClassLabel = Label(self.frame,text='Acilan Dersler')
        self.availClassLabel.pack()
        self.availClassLabel.place(x=205,y=3)

        self.availClassSpinner=[]
        for i in range(0,10):
            self.availClassSpinner.append(Combobox(self.frame,width=75,state='readonly'))
            self.availClassSpinner[i].pack()
            self.availClassSpinner[i]['values']=['']
            self.availClassSpinner[i].place(x=205,y=22*(i+1))
            self.availClassSpinner[i].bind('<<ComboboxSelected>>',self.updateSchedule)

        #Haftalik cizelge
        self.weekChart = []
        for i in range(0,14*5):
            self.weekChart.append(Label(self.frame,anchor='center',background='white',width=10))
            self.weekChart[i].pack()
            self.weekChart[i].place(x=(90+85*math.floor(i/14)), y=270+20*(i%14))
        self.chartLabels=[]
        days=['Pazartesi','Sali','Carsamba','Persembe','Cuma']
        for i in range(0,5):
            self.chartLabels.append(Label(self.frame,text=days[i],anchor='center',width=10))
            self.chartLabels[i].pack()
            self.chartLabels[i].place(x=90+i*85, y=250)

        for i in range(0, 14):
            self.chartLabels.append(Label(self.frame,text='{0}:30-{1}:29'.format(8+i,9+i),width=10,anchor='center'))
            self.chartLabels[i+5].pack()
            self.chartLabels[i+5].place(x=5, y=270+20*(i%14))

    def updateDatabase(self,firstBoot=False):
        if firstBoot:
            root = Tk()
            root.withdraw()
            tkinter.messagebox.showinfo('Veritabani guncellemesi','Veritabani simdi guncellenecek. Bu islem yaklasik 1-2 dakika surecektir.')
        else:
            ans=tkinter.messagebox.askquestion('Veritabani guncellemesi','Veritabanini simdi guncellemek istiyor musunuz?. Bu islem yaklasik 1 dakika surecektir.')
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

    def depCodeSelectedHandler(self,event):
        #print('depCodeSelectedHandler')
        depCode = event.widget.get()
        index = int(event.widget.winfo_y()/22 -1)
        if depCode == '':
            self.classCodeSpinner[index]['values'] = ['']
            self.availClassSpinner[index]['values'] = ['']
            self.classCodeSpinner[index].current(0)
            self.availClassSpinner[index].current(0)
            self.updateSchedule(None,index)
            return
        self.db.execute('select distinct Code from classes where Depcode=\'%s\'' % depCode)
        classCodeList = ['']
        for elem in self.db.fetchall():
            classCodeList.append(elem[0])
        self.classCodeSpinner[index]['values'] = classCodeList
        self.classCodeSpinner[index].current(0)
        self.availClassSpinner[index].current(0)
        self.updateSchedule(None,index)

    def classCodeSelectedHandler(self,event):
        #print('classCodeSelectedHandler')
        classCode = event.widget.get()
        index = int(event.widget.winfo_y()/22 -1)
        if classCode == '':
            self.availClassSpinner[index]['values'] = ['']
            self.availClassSpinner[index].current(0)
            self.updateSchedule(None,index)
            return
        self.db.execute('select CRN , Title , Inst  ,Build , Day ,Time  from classes where Code=\'%s\'' % classCode)
        availClassList =['']
        for elem in self.db.fetchall():
            availClassList.append('%s :: %s :: %s :: %s :: %s :: %s' % (elem[0],elem[1],elem[2],elem[4],elem[5],elem[3]))
        self.availClassSpinner[index]['values'] = availClassList
        self.availClassSpinner[index].current(0)
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
                        tkinter.messagebox.showinfo('Hata','Sectiginiz ders baska bir dersinizle cakismaktadir!')
                        return
        for i in range(0,70):
            self.weekChart[i]['background']= 'white'
            self.weekChart[i]['text']=''
            if temp[i] != 0:
                self.weekChart[i]['background']=temp[i]
                self.weekChart[i]['text']= temp2[i]

rand_col = ["#%03x" % random.randint(0, 0xFFF) for x in range(10)]
programci = ITU_Programci()
