import getinstalled
import package_sql
import sqlite3
import os

conn = package_sql.RecreateDB('test.sqlite')

print('Retrieving Installed Packages...')
installed = getinstalled.getInstalledPackagesJson()

print('Batch Inserting Installed Package Data.')
package_sql.InsertInstalled(conn,installed)
