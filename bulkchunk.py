import sqlite3
import re
import math
import PackageDataClass

# good for the specific usecase
# further refinement is in a heavily modified script sqlcolmap in the gis notes application


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
        



def genstatement(sql:str, tupleLimit=200)->list[str]:

    # its going to be expected that the parameters dictionary
    # contains keys that match the column list of the sql
    collist = getColumnList(sql)

    # single instance of unnamed parameters (?,..,?)
    valpiece = "("+ ','.join( ['?' for i in range(0,len(collist))]) +')'

    maxpieces = maxitemsforstmt(collist) 

    # will error if there is none
    table =  sql[0: sql.index('(')].strip().split(' ')[-1]
        
    if maxpieces > tupleLimit:
        maxpieces = tupleLimit
    elif maxpieces  < tupleLimit:
        raise "your batch size is too large."
  
    basesql = f"INSERT INTO {table}( {','.join(collist)}) VALUES \n" 
    basesql = basesql +  ',\t\n'.join( [ valpiece for i in range(0,maxpieces) ]) + "\n;"

    return basesql

def flattenbatch(collist:list[str], batch:list[object], translate:dict={})->list:

    resbatch = []

    for i in range(0,len(collist)):
        c = collist[i]

        if c in translate:
            collist[i] = translate[c]

    for i in batch:
        item = []

        for c in collist: 
            att = None

            if type(i)  == dict:
                att = i[c]
            else:
                att = getattr(i,c)  

            item.append(att)

        resbatch.extend(item)

    return resbatch

def maxitemsforstmt(collist:list[str])->int:
    return math.trunc(maxparamlim / len(collist))


def useExecuteManyInsert(conn:sqlite3.Connection, 
                         sql:str, 
                         parameters:list[dict], 
                         translate:list[dict] = [],
                         toCommit:bool = True):

    if translate is None:
        translate = []

    if len(parameters) == 0:
        return

    if not conn.in_transaction and toCommit:
        conn.execute('BEGIN')

    noprepare:bool = type(parameters[0]) in (dict,tuple,iter)

    # there was a whole argument and changing backend code regarding this bs
    # trying to force me to write more than one version :p
    # so I created a third with an optional choice between methods of insert
    # and enable tracking how well it works.

    if noprepare:
        for p in parameters:
            
            # just add the damn thingin, sqlite will pick it up.
            for t in translate:
                p[translate[t]] = p[t]
 
        c = conn.executemany(sql,parameters)
    else:
        # assume class instance
        c =  conn.executemany(sql,[ vars(p) for p in parameters])

    if toCommit:
        conn.commit()




# keep this as is for mysql
def processBatchInsert(conn:sqlite3.Connection, 
                       sql:str, 
                       parameters:list[dict], 
                       translate:list[dict] = [],
                       toCommit=True):

    if translate is None:
        translate = []
        
    if toCommit and not conn.in_transaction:
        conn.execute('BEGIN')

    count = 0
    total = len(parameters)
    
    collist = getColumnList(sql)

    # absolute maximum number of records to process in one batch
    maxlimit = maxitemsforstmt(collist)
    
    # # adjust to make sure of no failure.
    # maxlimit = maxlimit if absmax > maxlimit else absmax
    
    while len(parameters) > maxlimit:

        # pull out expected bathsize
        batch,parameters = (parameters[0:maxlimit], parameters[maxlimit:])        

        count  = count + len(batch)

        # generate the multi-insert sql statement
        stmt = genstatement(sql,maxlimit)
        # generate a flat parameter list in the correct order
        batch = flattenbatch(collist,batch,translate)
        
        conn.execute(stmt,batch) 
       
    if len(parameters) > 0:

        #stmt = genstatement(sql, maxlimit)

        stmt = genstatement(sql,len(parameters))
        # for other sql instances this would work.
        batch = flattenbatch(collist, parameters)

        conn.execute(stmt, batch)

    if toCommit:
        conn.commit()

    return total

    #print()

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
        insql = genstatement(sql,tupleLimit=2)
    except ValueError:
        insql = ""

    # succeeds
    insql = genstatement(sql,len(params))

    print(insql)



