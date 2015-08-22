#!/usr/bin/python
from ITUSIS_Parser import ITUSIS_Parser
import time
start_time = time.time()
parser = ITUSIS_Parser()
parser.getClasses()
print("--- %s seconds ---" % (time.time() - start_time))
