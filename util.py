import urllib
from sqlalchemy import create_engine

import pandas as pd

import time
import sys


def get_sql (query):
	params = urllib.parse.quote("DRIVER={ODBC Driver 17 For SQL Server};SERVER=DESKTOP-DPKTO85\SQLEXPRESS;DATABASE=tzhang;TRUSTED_CONNECTION=yes;UseFMTOnly=yes;ColumnEncryption=Enabled")
	ENGINE = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params, fast_executemany=True)
	i_data = pd.read_sql(query,con = ENGINE)
	return i_data


def yz_print(current_index, index_length):
    
    # Variable setup
    	
    barLength = 30 # Modify this to change the length of the progress bar
    status = ""
    progress = current_index / index_length

    if isinstance(progress, int):  #current_index?
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    elif progress >= 1:
        progress = 1
        status = "Done...\r\n"
    else:
        status = 'Working...'
        
    block = int(round(barLength*progress))
    text = "\rProgress: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), round(progress*100,2), status)
    sys.stdout.write(text)
    sys.stdout.flush()

