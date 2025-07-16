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

    maxpieces = math.trunc( maxparamlim / len(collist)) 

    # will error if there is none
    table =  sql[0: sql.index('(')-1].strip().split(' ')[-1]
        
    if maxpieces > tupleLimit:
        maxpieces = tupleLimit

    if len(parameters) > maxpieces:
        raise ValueError("Adjust your logic, for the query provided maximum parameters is exceeded by the list of values supplied")
    elif len(parameters) < maxpieces:
        maxpieces = len(parameters)    
    
    basesql = f"INSERT INTO {table}( {','.join(collist)}) VALUES (\n" 
    basesql = basesql +  ',\t\n'.join( [ valpiece for i in range(0,maxpieces) ]) + "\n);"

    return basesql
                        

if __name__=="__main__":

    sql = "INSERT INTO users (id, name, age) VALUES (?, ?, ?);"

    params = [
                {'id':1, 'name':'john', 'age':85},
                {'id':1, 'name':'moses', 'age':110},
                {'id':1, 'name':'aensley', 'age':80},
                {'id':1, 'name':'allan', 'age':115}                
             ]

    print (getColumnList(sql))

    insql = ""

    # fails
    try:
        insql = genstatement(sql,params,tupleLimit=2)
    except ValueError:
        insql = ""

    # succeeds
    insql = genstatement(sql,params)

    print(insql)



