import sqlite3

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
    'rel':'release',
    'epoch':'epoch',
    'flags':'flags'
}


create_structure_sql = ReadAll('sql/create_db_structure.sql')
generics_insert = ReadAll('sql/generics_package_insert.sql')
generics_select = ReadAll('sql/generics_package_select.sql')
repo_insert = ReadAll('sql/repo_insert.sql')
package_insert = ReadAll('sql/packages_insert.sql')

GenericSqlStatements = {}

for tag in RELATION_TAGS:
    GenericSqlStatements[tag] = {}
    GenericSqlStatements[tag]['insert'] = generics_insert.replace('{generic}',tag)
    GenericSqlStatements[tag]['select'] = generics_select.replace('{generic}',tag)


def CreateStructure(wcon:sqlite3.Connection):
    wcon.executescript(create_structure_sql)
    wcon.commit()


def InsertGeneric(wconn:sqlite3.Connection, tag:str, repo_uuid:str, pkgid:str,  entry:dict):
    
    parameters = {}

    parameters.update(entry)
    parameters['pkgid'] = pkgid
    parameters['repo_uuid'] = repo_uuid

    for field in ENTRY_FIELDS:
        parameters[field] = None

    sql = GenericSqlStatements[tag]['insert']
    wconn.execute(sql,parameters)

def SelectGeneric(rconn:sqlite3.Connection, tag:str, parameters:dict)->list[dict]:
    sql = GenericSqlStatements[tag]['select']
    return rconn.execute(sql,parameters).fetchall()

def InsertRepo(wconn:sqlite3.Connection, parameters:dict):
    wconn.execute(repo_insert,parameters)

def InsertPackage(wcon:sqlite3.Connection, paramaters:dict):
    wcon.execute(package_insert, paramaters)


