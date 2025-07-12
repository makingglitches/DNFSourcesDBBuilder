import sqlite3

testsql = "INSERT INTO :tag (pkgid, name, pre, flags) \
        VALUES (:pkgid, :name, :pre, :flags)"

con = sqlite3.connect("repo_metadata_full.db")

con.execute(testsql, {'tag':'provides', 'pkgid':'1221121', 'pre':True, 'flags':'12212'})

con.commit()

con.close()