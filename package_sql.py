import sqlite3
import bulkchunk
import os

import datetime


CURRENT_BATCH_MAX = 10000

def ReadAll(path:str)->str:
    f = open(path, 'r')
    s  = f.read()
    f.close()
    return s


RELATION_TAGS = [
    'requires', 'provides', 'conflicts', 'obsoletes',
    'recommends', 'suggests', 'supplements', 'enhances'
]

ENTRY_FIELDS = {    
    'pkgid':'pkgid', 
    'name':'name', 
    'ver':'version',
    'rel':'release_ver',
    'epoch':'epoch',
    'flags':'flags'
}


create_structure_sql = ReadAll('sql/create_db_structure.sql')
generics_insert = ReadAll('sql/generics_package_insert.sql')
generics_select = ReadAll('sql/generics_package_select.sql')
repo_insert = ReadAll('sql/repo_insert.sql')
package_insert = ReadAll('sql/packages_insert.sql')
installed_insert = ReadAll('sql/installed_insert.sql')

GenericSqlStatements = {}

for tag in RELATION_TAGS:
    GenericSqlStatements[tag] = {}
    GenericSqlStatements[tag]['insert'] = generics_insert.replace('{generic}',tag)
    GenericSqlStatements[tag]['select'] = generics_select.replace('{generic}',tag)


def CreateStructure(wcon:sqlite3.Connection):
    wcon.executescript(create_structure_sql)
    wcon.commit()


def InsertGeneric(wconn:sqlite3.Connection, tag:str, batch:list[dict], useChunk=True):
    
    if len(batch) == 0:
        return (0,0,0)
    
    sql = GenericSqlStatements[tag]['insert']

    rows = len(batch)

    st = datetime.datetime.now(datetime.timezone.utc)

    if useChunk:
        bulkchunk.processBatchInsert(wconn,sql,batch,None,False)
    else:
        bulkchunk.useExecuteManyInsert(wconn,sql,batch,None,False)

    en = datetime.datetime.now(datetime.timezone.utc)
    tim = (en-st).microseconds / 10**6
    rps = rows / tim

    return (rows,tim, rps )
    

def SelectGeneric(rconn:sqlite3.Connection, tag:str, parameters:dict)->list[dict]:
    sql = GenericSqlStatements[tag]['select']
    return rconn.execute(sql,parameters).fetchall()

def InsertRepo(wconn:sqlite3.Connection, parameters:dict):
    wconn.execute(repo_insert,parameters)

def InsertPackage(wcon:sqlite3.Connection, batch:list[dict], useChunk=True):

    rows = len(batch)

    if rows ==0:
        return (0,0,0)

    st = datetime.datetime.now(datetime.timezone.utc)

    if useChunk:
        bulkchunk.processBatchInsert(wcon,package_insert,batch,None, False)
    else:
        bulkchunk.useExecuteManyInsert(wcon,package_insert,batch,None, False)

    en = datetime.datetime.now(datetime.timezone.utc)
    tim = (en-st).microseconds / 10**6
    rps = rows / tim 

    return (rows,tim, rps )

def InsertInstalled(wcon:sqlite3.Connection, batch:list[dict], useChunk=True):

    translate = {
        'release_ver': 'release'
    }

    rows = len(batch)

    st = datetime.datetime.now(datetime.timezone.utc)


    if useChunk:
        bulkchunk.processBatchInsert(wcon,installed_insert, batch,translate,False)
    else:
        bulkchunk.useExecuteManyInsert(wcon,installed_insert, batch,translate,False)

    en = datetime.datetime.now(datetime.timezone.utc)
    tim = (en-st).microseconds/ 10**6
    rps = rows/tim

    return (rows,tim, rps )

def RecreateDB(filepath:str)->sqlite3.Connection:

    if os.path.exists(filepath):
        os.remove(filepath)
    
    conn:sqlite3.Connection = sqlite3.connect(filepath)

    CreateStructure(conn)

    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA temp_store = MEMORY")

    return conn
