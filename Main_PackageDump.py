#!/usr/bin/env python3

import PackageDataClass as pdat

import sqlite3
import lxml

import fnmatch

import os
import sys

import lxml.etree
import decompression as decomp

import getinstalled

import package_sql

NS = {
    'x': 'http://linux.duke.edu/metadata/common',
    'rpm': 'http://linux.duke.edu/metadata/rpm'
}

common_ns = "{http://linux.duke.edu/metadata/common}"
rpm_ns = "{http://linux.duke.edu/metadata/rpm}"

def tagname(ns,name):
    return f"{ns}{name}"

#TODO: UPDATE THIS FOR NEW LOGIC
# see #149
def extract_entries(tag:lxml.etree.Element, pkgid:str, repo_uuid:str):
    entries = []
        
    for entry in tag.iterchildren():
            
            if entry.tag == tagname(rpm_ns,'entry'):            
                item = dict(entry.attrib)
            
                # translate names from xml to table fields
                for oldname in package_sql.ENTRY_FIELDS:
                    newname = package_sql.ENTRY_FIELDS[oldname]

                    if oldname == newname:
                        if oldname not in item:
                            item[oldname] = None
                    else:
                        item[newname] = None if not oldname in item else item.pop(oldname)

                # add primary key reference
                item['pkgid'] = pkgid
                item['repo_uuid'] = repo_uuid 

                entries.append(item)
    return entries

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

    if os.path.exists(db_file):
        os.remove(db_file)


    conn = sqlite3.connect(db_file)    
    package_sql.CreateStructure(conn)

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

    for r in repos:
        
        print(f"Repo: {r['repo_full_name']}...")

        decomtemp = decomp.decompress_to_temp(r['primaryxmlfilename'])

        tree:lxml.etree.ElementTree = lxml.etree.parse(decomtemp)

        root:lxml.etree.Element = tree.getroot()
        

        count = int(root.attrib['packages'])

        # for item in root.iterchildren():
        #     if item.
            
        curr_pkg = 1

        repouuid = r['repo_uuid']

        
        #packages = root.findall('x:package',{'x':'http://linux.duke.edu/metadata/common'})
        #doesn't make sense.
        #all_packages = []    
        
        pkgbatch = []

        for pkg in root.iterchildren():
            if pkg.tag == tagname(common_ns,"package"):    

                print(f"Extracting Package {curr_pkg} of {count}", end="\r")
                curr_pkg = curr_pkg + 1

                currRec = pdat.PackageData()
                currRec.type = pkg.attrib.get('type')
                
                
                
                for misc in pkg.iterchildren():
    
                    if misc.tag == tagname(common_ns,"version"):
                         currRec.version = misc.attrib.get('ver')
                         currRec.release_ver = misc.attrib.get('rel')
                         currRec.epoch = misc.attrib.get('epoch')
                    elif misc.tag == tagname(common_ns,"format"):
                        for field in misc.iterchildren():      

                            #TODO: HANDLE FILES TYPE AS WELL, DOESN'T SEEM TO BE USED MUCH
                            if field.tag == tagname(rpm_ns, 'header-range'):
                                currRec.header_start = field.attrib['start']
                                currRec.header_end = field.attrib['end']
                                continue
                            else:

                                foundtag = False

                                # this is for tags requires, provides, etc.
                                for s  in package_sql.RELATION_TAGS:
                                    if  not foundtag and tagname(rpm_ns, s) == field.tag:
                                        tname = field.tag.replace(rpm_ns,'')
                                        entries = extract_entries(field,currRec.checksum, repouuid)                                                                    
                                        setattr(currRec, tname, entries)                                        
                                        foundtag = True
                                
                                if not foundtag:
                                    # rpm fields
                                    # license, vendor, app_group, builhost, sourcerpm
                                    tname = field.tag.replace(rpm_ns,'')
                                    setattr(currRec,tname, field.text)
                                    #currRec[tname] = field.text                                    

                    elif misc.tag == tagname(common_ns,"checksum"):                                                
                        currRec.checksum= misc.text
                        currRec.checksum_type = misc.attrib['type']
                        currRec.checksum_pkgid =  misc.attrib['pkgid']
                    elif misc.tag == tagname(common_ns,"time"):                        
                        currRec.time_file= misc.attrib.get('file')
                        currRec.time_build = misc.attrib.get('build')
                    elif misc.tag == tagname(common_ns,"size"):                        
                        currRec.size_package= misc.attrib.get('package')
                        currRec.size_installed= misc.attrib.get('installed')
                        currRec.size_archive= misc.attrib.get('archive')
                    elif misc.tag == tagname(common_ns,"location"):
                        currRec.location= misc.attrib.get('href')
                    else:
                        # common field names
                        # name, arch, summary,description, packager, url
                        tname = misc.tag.replace(common_ns,'')       
                        setattr(currRec,tname, misc.text)     
                        #currRec[tname] = misc.text
                                                        
                pkgbatch.append(currRec)

                if len (pkgbatch) == package_sql.CURRENT_BATCH_MAX:
                    package_sql.InsertPackage(conn,pkgbatch)

                    for pkg in pkgbatch:
                        for tag in package_sql.RELATION_TAGS:
                            #print(f"Processing tag: {tag}")
                            gen = getattr(pkg,tag)
                            package_sql.InsertGeneric(conn,tag,gen)

                    pkgbatch = []

        if len(pkgbatch) > 0:
            package_sql.InsertPackage(conn,pkgbatch)

            for pkg in pkgbatch:
                for tag in package_sql.RELATION_TAGS:
                    #print(f"Processing tag: {tag}")
                    gen = getattr(pkg,tag)
                    package_sql.InsertGeneric(conn,tag,gen)

        os.remove(decomtemp)
        print()

    print ("Retrieving installed packages...") 
    ipackages = getinstalled.getInstalledPackagesJson()   

    count = 0

    print ('Storeing installed packages.')
    package_sql.InsertInstalled(conn,ipackages)        

    print()

    conn.commit()
    conn.close()

 
    print()
    print("Created Package Database Successfully.")

if __name__ == '__main__':
    main()
