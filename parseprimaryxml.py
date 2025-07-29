import decompression as decomp
from lxml import etree
import PackageDataClass as pdat
import package_sql

common_ns = "{http://linux.duke.edu/metadata/common}"
rpm_ns = "{http://linux.duke.edu/metadata/rpm}"

def tagname(ns,name):
    return f"{ns}{name}"

def extract_entries(tag:etree.Element, pkgid:str, repo_uuid:str):
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




def ParsePackage(pkg:etree.Element,repouuid:str)->pdat.PackageData | None:    

    if pkg.tag == tagname(common_ns,"package"):    
        currRec = pdat.PackageData()
        currRec.type = pkg.attrib.get('type')
        currRec.repo_uuid = repouuid

        # goes through all the attribute fields of the package.                    
        for misc in pkg.iterchildren():
            # go through all the compound and more complicated structures
            # first and leave the generic ones that can simply be 
            # retrieved and assigned for last in each structures case.
            # version defines atributes
            if misc.tag == tagname(common_ns,"version"):
                    currRec.version = misc.attrib.get('ver')
                    currRec.release_ver = misc.attrib.get('rel')
                    currRec.epoch = misc.attrib.get('epoch')
            # go through format tag again
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
        return currRec
    else:
        return None                  
                                                    