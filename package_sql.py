import sqlite3
import bulkchunk

CURRENT_BATCH_MAX = 1000

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


def InsertGeneric(wconn:sqlite3.Connection, tag:str, batch:list[dict]):
    sql = GenericSqlStatements[tag]['insert']
    bulkchunk.processBatchInsert(wconn,sql,batch)
    

def SelectGeneric(rconn:sqlite3.Connection, tag:str, parameters:dict)->list[dict]:
    sql = GenericSqlStatements[tag]['select']
    return rconn.execute(sql,parameters).fetchall()

def InsertRepo(wconn:sqlite3.Connection, parameters:dict):
    wconn.execute(repo_insert,parameters)

def InsertPackage(wcon:sqlite3.Connection, batch:list[dict]):
    bulkchunk.processBatchInsert(wcon,package_insert,batch)

def InsertInstalled(wcon:sqlite3.Connection, batch:list[dict]):
    bulkchunk.processBatchInsert(wcon,installed_insert, batch)

