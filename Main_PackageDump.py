#!/usr/bin/env python3


import PackageDataClass as pdat
import parseprimaryxml as pxml

import sqlite3
from lxml import etree



import fnmatch

import os
import sys

import decompression as decomp
import datetime

import getinstalled

import package_sql

NS = {
    'x': 'http://linux.duke.edu/metadata/common',
    'rpm': 'http://linux.duke.edu/metadata/rpm'
}

common_ns = "{http://linux.duke.edu/metadata/common}"
rpm_ns = "{http://linux.duke.edu/metadata/rpm}"


def RepoDirParts(repo_path:str):

    fullname =os.path.basename(repo_path)
    uuid = fullname[-16:]
    name = fullname.replace('-'+uuid,'')
    sourcerepo = name.endswith('-source')
    name = name.replace('-source','')
    primaryxml = None

    # KLWY75JQ
    for dirpath, dirs, files in os.walk(os.path.join( repo_path,'repodata')):
        
        dirs.clear()

        for f in files:
            if fnmatch.fnmatch(f,'*primary.xml*'):
                primaryxml = os.path.join(dirpath,f)
                break
        

    return { 
              'repo_name':name,
              'repo_full_name':fullname,
              'repo_uuid':uuid,                 
              'path':repo_path,               
              'is_source_repo':sourcerepo,
              'primaryxmlfilename':primaryxml
        }


def InsertPackageBatch(conn:sqlite3.Connection, pkg_batch:list[pdat.PackageData]):
    
    # insert all the main package records retrieved thus far
    track = {
                'packageinserts': package_sql.InsertPackage(conn,pkg_batch,False), 
                'tagtrack':[],
                'commit_time':0                
            }

    # insert all the prepared tag information (requires, provides, conflicts,etc)
    for pkg in pkg_batch:   
        for tag in package_sql.RELATION_TAGS:
            #print(f"Processing tag: {tag}")
            gen = getattr(pkg,tag)

            tracktag =  package_sql.InsertGeneric(conn,tag,gen,False)

            track['tagtrack'].append(tracktag)

    st = datetime.datetime.utcnow()

    #conn.commit()

    track['commit_time'] = (datetime.datetime.utcnow() - st).microseconds/10**6
            
    return track


def main():

    print ('Building repo database from dnf cache...')

    # check path exists
    # libdnf5 was updated 
    base_path = "/var/cache/libdnf5"

    if not os.path.exists(base_path):
        print(f"Path {base_path} does not exist.")
        sys.exit(1)

    # TODO: update this later, presently recreates database every time.
    # TODO: previously gauged recreaion was better. but perhaps not.
    db_file = "repo_metadata_full.db"

    conn = package_sql.RecreateDB(db_file)

    track = []
    repos = []
    total = 0

    print ('populating repos table...\n ')
    for rootdir, dirs, files in os.walk(base_path):
        for d in dirs:

            # explained as resulting from a repo being added via commandline
            # and temporary.
            if d.startswith('@commandline'):
                continue
            
            fullpath = os.path.join(rootdir,d)
            repos.append(RepoDirParts(fullpath)) 

        dirs.clear()       

    for r in repos:
        print(f'Adding repo: {r['repo_full_name']}')
        package_sql.InsertRepo(conn,r)

    print ('Scanning repos... \n')

    etime = 0
    ecount = 0

    for r in repos:
        
        print(f"Repo: {r['repo_full_name']}...")
    
        decomtemp = decomp.decompress_to_temp(r['primaryxmlfilename'])

        #st = datetime.datetime.now(datetime.timezone.utc)

        #tree:etree.ElementTree = lxml.etree.parse(decomtemp)
        #root:etree.Element = tree.getroot()

        #etime += (datetime.datetime.now(datetime.timezone.utc) - st).microseconds/10**6
        
        count = 0 #int(root.attrib['packages']) # get in start event.

        #ecount += count

        curr_pkg = 1
        repouuid = r['repo_uuid']        
        pkgbatch = []
        
        metadataname = pxml.tagname(pxml.common_ns,'metadata')
        packagename  = pxml.tagname(pxml.common_ns, 'package')

        
        encycle:datetime.datetime = None
        stcycle:datetime.datetime = datetime.datetime.utcnow()
        
        # open only to get first tag. iterparse doesn't always provide an underlying stream close method
        # would make sense has been done, but nope. this is the 'right' way to do it
        with open(decomtemp, 'rb') as f:

            context:etree.iterparse = etree.iterparse(f, events=('start',))            
            for event, elem in context:                        
                if event == 'start' and elem.tag == metadataname:
                    count = int(elem.attrib['packages'])
                    ecount += count
                    encycle = datetime.datetime.utcnow()     
                    etime += (encycle - stcycle).microseconds / 10**6
                    break

        #reopen to emit only start tag events.
        with open(decomtemp, 'rb') as f:
            context = etree.iterparse(decomtemp, events=('end',))

            stcycle:datetime.datetime = datetime.datetime.utcnow()
        
            for event, elem in context:               

                encycle = datetime.datetime.utcnow()     
                etime += (encycle - stcycle).microseconds / 10**6

                st = datetime.datetime.utcnow()
                p = pxml.ParsePackage(elem,repouuid)
                etime += (datetime.datetime.utcnow()-st).microseconds/10**6

                if not p is None: 
                    print(f"Extracting Package {curr_pkg} of {count}", end="\r")
                    curr_pkg = curr_pkg + 1

                    pkgbatch.append(p)

                    if len (pkgbatch) == package_sql.CURRENT_BATCH_MAX:                
                        track.append( InsertPackageBatch(conn,pkgbatch))                    
                        pkgbatch = []

                    elem.clear()

            stcycle = datetime.datetime.utcnow()                 
                                
        if len(pkgbatch) > 0:
            # insert the remaining information
            track.append(  InsertPackageBatch(conn,pkgbatch))

        os.remove(decomtemp)
        print()

        # **********begin refactor to see effects on speed and ********
        # and ram footprint.

        # st = datetime.datetime.now(datetime.timezone.utc)

        # tree:etree.ElementTree = lxml.etree.parse(decomtemp)
        # root:etree.Element = tree.getroot()

        # etime += (datetime.datetime.now(datetime.timezone.utc) - st).microseconds/10**6
        
        # count = int(root.attrib['packages'])

        # ecount += count

        # curr_pkg = 1
        # repouuid = r['repo_uuid']        
        # pkgbatch = []

        # # parse, and store packages
        # for pkg in root.iterchildren():

                
        #     st = datetime.datetime.utcnow()

        #     p = pxml.ParsePackage(pkg,repouuid)

        #     etime += (datetime.datetime.utcnow()-st).microseconds/10**6

        #     if not p is None: 
        #         print(f"Extracting Package {curr_pkg} of {count}", end="\r")
        #         curr_pkg = curr_pkg + 1

        #         pkgbatch.append(p)

        #         if len (pkgbatch) == package_sql.CURRENT_BATCH_MAX:                
        #             track.append( InsertPackageBatch(conn,pkgbatch))                    
        #             pkgbatch = []

        # if len(pkgbatch) > 0:
        #     # insert the remaining information
        #     track.append(  InsertPackageBatch(conn,pkgbatch))

        # os.remove(decomtemp)
        # print()

    #************************ End Refactor here *******************

    print ("Retrieving installed packages...") 
    ipackages = getinstalled.getInstalledPackagesJson()   

    count = 0

    print ('Storeing installed packages.')
    package_sql.InsertInstalled(conn,ipackages)        

    print()

    pcount = 0
    ptime = 0

    gencount = 0 
    gentime = 0

    for t in track:
        pkgins = t['packageinserts']

        pcount += pkgins[0]
        ptime += pkgins[1]

        gens = t['tagtrack']

        for g in gens:
            gencount += g[0]
            gentime += g[1]

    print()
    print(f"Performance:\n\tPkg Inserted: {pcount}\n\tInsert Time: {ptime}\n\t" +\
          f"PPS: {pcount/ptime}\n\t"+\
          f"Generic Inserted: {gencount}\n\t"+\
          f"Insert Time: {gentime}\n\t"+\
          f"PPS: {gencount/gentime}\n")
    
    epps = ecount/etime

    print(f"\tXML Parse Time: {etime}\n\tXML Records: {ecount}\n\tXML PPS:{epps}\n")
          
    conn.commit()
    conn.close()
 
    print()
    print("Created Package Database Successfully.")

if __name__ == '__main__':
    main()
