try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser

class ITU_HTMLParser(HTMLParser):
    ITU_HTMLParser_DEPCODEMODE = 0
    ITU_HTMLParser_CLASSMODE = 1
    def __init__(self,parsermode):
        self.mode = parsermode
        self.foundClassTable=False
        self.parsedData=[]
        self.classInfo=[]
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if self.mode == self.ITU_HTMLParser_DEPCODEMODE:
            if(tag == 'option'):
                for attr in attrs:
                    if attr[0] == 'value':
                        if attr[1] != '':
                            self.parsedData.append(attr[1])
        elif self.mode == self.ITU_HTMLParser_CLASSMODE:
            if tag == 'table' and attrs != [] and attrs[0][0] == 'class' and attrs[0][1] == 'dersprg':
                if not self.foundClassTable:
                    self.foundClassTable = True
            elif self.foundClassTable and tag == 'tr':
                self.classInfo = []

    def handle_data(self,data):
        if self.foundClassTable:
            forbiddenChars = "/\\?%*:;|\"\'<>."
            for char in forbiddenChars:
                data=data.replace(char,'')
            self.classInfo.append(data)

    def handle_endtag(self,tag):
        if self.foundClassTable and tag =='tr':
            self.parsedData.append(self.classInfo)
        if self.foundClassTable and tag == 'table':
            self.foundClassTable = False

class ITUSIS_Parser:
    import requests

    def __init__(self):
        import sqlite3
        self.db=sqlite3.connect("classdb.sqlite")
        self.cur=self.db.cursor()
        try:
            self.cur.execute('''CREATE TABLE classes
             (CRN TEXT, Code TEXT, Title TEXT, Inst TEXT ,Build TEXT, ClassTime TEXT, Restr TEXT )''')
        except:
            print("Database already exists")

    def getDepartmentCodes(self):
        html = ITUSIS_Parser.requests.get('http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php').text.encode("utf-8")
        parser = ITU_HTMLParser(ITU_HTMLParser.ITU_HTMLParser_DEPCODEMODE)
        parser.feed(html)
        return parser.parsedData

    def getClasses(self):
        for dep in self.getDepartmentCodes():
            html = ITUSIS_Parser.requests.get('http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php?fb='+dep).text.encode("utf-8")
            parser = ITU_HTMLParser(ITU_HTMLParser.ITU_HTMLParser_CLASSMODE)
            parser.feed(html)
            for i in range(0,2):
                parser.parsedData.pop(0)
            self.addToDatabase(parser.parsedData)
        self.db.close()


    def addToDatabase(self,data):
        for classEntry in data:
            print(classEntry)
            self.cur.execute("INSERT INTO classes VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}')".format(classEntry[0],classEntry[1],
            classEntry[2],classEntry[3],classEntry[4],classEntry[6],classEntry[11]))

        self.db.commit()
