#!/usr/bin/python3
from tkinter import *
import tkinter.messagebox
import sqlite3
import time
from ITUSIS_Parser import ITUSIS_Parser

class ITU_Programci():
    def __init__(self):
        self.conn=sqlite3.connect('classdb.sqlite')
        self.db=self.conn.cursor()
        self.dbUpdateInProgress=False
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
        self.frame = Frame(self.root)
        self.frame.master.title('ITU Programci')
        self.frame.master.geometry('600x400')
        self.frame.pack()

    def initWidgets(self):
        self.deneme = Spinbox(self.root)
        i=0
        for code in self.db.execute('select distinct Depcode from classes'):
            print(code)
        #self.deneme['values'] = self.db.fetchall()
        self.deneme.pack()


    def updateDatabase(self):
        tkinter.commondialog.showinfo('Database guncellemesi','Guncelleme baslamistir. Guncelleme bitince bilgilendirileceksiniz')
        time.sleep(1)
        self.dbUpdateInProgress=True
        self.db.close()
        updater = ITUSIS_Parser()
        updater.getClasses()
        self.conn=sqlite3.connect('classdb.sqlite')
        self.db=self.conn.cursor()
        self.dbUpdateInProgress=False
        tkinter.messagebox.showinfo('Database guncellemesi','Guncelleme bitmistir.')


programci = ITU_Programci()
