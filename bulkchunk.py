import sqlite3
import re
import math

# sql internal limit
maxparamlim = 999


def getColumnList(sql:str)->list[str] | None:
    
    match = re.search(r"INSERT\s+INTO\s+\S+\s*\(([^)]+)\)", sql, re.IGNORECASE)

    if match:
        columns = match.group(1).strip()
        column_list = [col.strip().replace('[','').replace(']','') for col in columns.split(',')]
        return column_list
    else:
        return None
        



def genstatement(sql:str, parameters:list[dict], tupleLimit=200)->list[str]:

    # its going to be expected that the parameters dictionary
    # contains keys that match the column list of the sql
    collist = getColumnList(sql)

    # single instance of unnamed parameters (?,..,?)
    valpiece = "("+ ','.join( ['?' for i in range(0,len(collist))]) +')'

    maxpieces = math.trunc( maxparamlim / collist) 

    # will error if there is none
    table =  sql[0: sql.index('(')-1].strip().split(' ')[-1]
        
    if maxpieces > tupleLimit:
        maxpieces = tupleLimit
    
    basesql = f"INSERT INTO {table}( {','.join(collist)}) VALUES ( "



if __name__=="__main__":

    sql = "INSERT INTO users (id, name, age) VALUES (?, ?, ?);"

    print (getColumnList(sql))