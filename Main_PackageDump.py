#!/usr/bin/env python3

import sqlite3
import lxml

import fnmatch

import os
import sys

import lxml.etree
import decompression as decomp

import package_sql

NS = {
    'x': 'http://linux.duke.edu/metadata/common',
    'rpm': 'http://linux.duke.edu/metadata/rpm'
}

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

        root = tree.getroot()

        count = int(root.attrib['packages'])
        curr_pkg = 1

        packages = root.findall('x:package',{'x':'http://linux.duke.edu/metadata/common'})
        
        #doesn't make sense.
        #all_packages = []

        repouuid = r['repo_uuid']
        
        for p in packages:

            print(f"Extracting Package {curr_pkg} of {count}", end="\r")
            curr_pkg = curr_pkg + 1

            type_ = p.attrib.get('type')

            name = p.findtext('x:name', namespaces=NS)
            arch = p.findtext('x:arch', namespaces=NS)

            version_tag = p.find('x:version', NS)
            ver_epoch = version_tag.attrib.get('epoch')
            ver_ver = version_tag.attrib.get('ver')
            ver_rel = version_tag.attrib.get('rel')

            checksum_tag = p.find('x:checksum', NS)


            checksum = checksum_tag.text
            checksum_type = checksum_tag.attrib['type']
            checksum_pkgid = checksum_tag.attrib['pkgid']

            summary = p.findtext('x:summary', namespaces=NS)
            description = p.findtext('x:description', namespaces=NS)
            packager = p.findtext('x:packager', namespaces=NS)
            url = p.findtext('x:url', namespaces=NS)

            time_tag = p.find('x:time', NS)
            time_file = time_tag.attrib.get('file')
            time_build = time_tag.attrib.get('build')

            size_tag = p.find('x:size', NS)
            size_pkg = size_tag.attrib.get('package')
            size_inst = size_tag.attrib.get('installed')
            size_arc = size_tag.attrib.get('archive')

            location_tag = p.find('x:location', NS)
            location_href = location_tag.attrib.get('href')

            package_data = {
                'type': type_,                
                'repo_uuid':repouuid,
                'pkgid': checksum,
                'name': name,
                'arch': arch,
                'version': ver_ver,
                'epoch': ver_epoch,
                'release': ver_rel,                                
                'summary': summary,
                'description': description,
                'packager': packager,
                'url': url,
                'time_file': time_file,
                'time_build': time_build,                
                'size_package': size_pkg,
                'size_installed': size_inst,
                'size_archive': size_arc,                
                'location': location_href,                
                'checksum_type':checksum_type,
                'checksum_pkgid':checksum_pkgid,
                'checksum':checksum,
                'license': None,
                'vendor': None,
                'group': None,
                'buildhost': None,
                'sourcerpm': None,
                'header_start': None,
                'header_end':None,
                'requires': [],
                'provides': [],
                'conflicts': [],
                'obsoletes': [],
                'recommends': [],
                'suggests': [],
                'supplements': [],
                'enhances': [],
                'files': []
            }

            format_tag = p.find('x:format', NS)

            if format_tag is not None:

                def extract_entries(tag_name):
                    entries = []
                    tag = format_tag.find(f'rpm:{tag_name}', NS)
                    if tag is not None:
                        for entry in tag.findall('rpm:entry', NS):
                            
                            item = dict(entry.attrib)
                            
                            for oldname in package_sql.ENTRY_FIELDS:
                                newname = package_sql.ENTRY_FIELDS[oldname]

                                if oldname == newname:
                                    if oldname not in item:
                                        item[oldname] = None
                                else:
                                    item[newname] = None if not oldname in item else item.pop(oldname)
                            
                            entries.append(item)

                    return entries

                package_data.update({
                    'license': format_tag.findtext('rpm:license', namespaces=NS),
                    'vendor': format_tag.findtext('rpm:vendor', namespaces=NS),
                    'group': format_tag.findtext('rpm:group', namespaces=NS),
                    'buildhost': format_tag.findtext('rpm:buildhost', namespaces=NS),
                    'sourcerpm': format_tag.findtext('rpm:sourcerpm', namespaces=NS),
                    'header_start': None,
                    'header_end':None,
                    'requires': extract_entries('requires'),
                    'provides': extract_entries('provides'),
                    'conflicts': extract_entries('conflicts'),
                    'obsoletes': extract_entries('obsoletes'),
                    'recommends': extract_entries('recommends'),
                    'suggests': extract_entries('suggests'),
                    'supplements': extract_entries('supplements'),
                    'enhances': extract_entries('enhances'),
                    'files': [
                        {
                            'name': f.text,
                            'type': f.attrib.get('type')
                        } for f in format_tag.findall('rpm:file', NS)
                    ]
                })

                header_range = format_tag.find('rpm:header-range', NS)

                if header_range is not None:
                    package_data['header_start'] = header_range.attrib.get('start')
                    package_data['header_end'] = header_range.attrib.get('end')

            # this doesn't make sense.
            #all_packages.append(package_data)

            package_sql.InsertPackage(conn,package_data)

            for tag in package_sql.RELATION_TAGS:
                for item in package_data[tag]:
                    package_sql.InsertGeneric(conn, tag, repouuid, checksum, item)

        os.remove(decomtemp)
        print()
            
    conn.commit()
    conn.close()
 
    print()
    print("Created Package Database Successfully.")

if __name__ == '__main__':
    main()
