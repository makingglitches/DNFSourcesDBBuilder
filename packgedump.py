#!/usr/bin/env python3

import sqlite3
import xml.etree.ElementTree as ET


import os
import sys

import fnmatch
import decompression as decomp




NS = {
    'common': 'http://linux.duke.edu/metadata/common',
    'rpm': 'http://linux.duke.edu/metadata/rpm'
}

RELATION_TAGS = [
    'requires', 'provides', 'conflicts', 'obsoletes',
    'recommends', 'suggests', 'supplements', 'enhances'
]

def open_xml(file_path):
    """Decompress and parse XML, returning the ElementTree."""
    decompressed = decompress_to_temp(file_path)
    try:
        tree = ET.parse(decompressed)
    finally:
        # Only remove temp files we created, not original files or unzck outputs
        if decompressed != file_path and not decompressed.endswith('.xml'):
            try:
                os.unlink(decompressed)
            except Exception:
                pass
    return tree

def create_schema(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            pkgid TEXT PRIMARY KEY,
            name TEXT,
            arch TEXT,
            version TEXT,
            release TEXT,
            epoch TEXT,
            summary TEXT,
            description TEXT
        )
    ''')
    for tag in RELATION_TAGS:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS :tag (
                pkgid TEXT,
                name TEXT,
                pre BOOLEAN,
                flags TEXT,
                FOREIGN KEY(pkgid) REFERENCES packages(pkgid)
            )
        ''')

def insert_relation(cursor, pkgid, tag, entry):
    name = entry.attrib.get('name')
    pre = entry.attrib.get('pre') == '1'
    flags = entry.attrib.get('flags')
    cursor.execute(f'''
        INSERT INTO {tag} (pkgid, name, pre, flags)
        VALUES (?, ?, ?, ?)
    ''', (pkgid, name, pre, flags))

def insert_package(cursor, pkg_elem):
    #TODO: MANUALLY INSPECT THE NAMESPACE, XMLTREE EXPANDS TO 
    #'{http://linux.duke.edu/metadata/common}name'  LIKE A DUMBASS.
    pkgid = pkg_elem.findtext('checksum')
    name = pkg_elem.findtext('name')
    arch = pkg_elem.findtext('arch')
    summary = pkg_elem.findtext('summary')
    description = pkg_elem.findtext('description')

    version_elem = pkg_elem.find('version')
    epoch = version_elem.attrib.get('epoch', '0') if version_elem is not None else '0'
    ver = version_elem.attrib.get('ver') if version_elem is not None else None
    rel = version_elem.attrib.get('rel') if version_elem is not None else None

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO packages (pkgid, name, arch, version, release, epoch, summary, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (pkgid, name, arch, ver, rel, epoch, summary, description))
    except sqlite3.IntegrityError:
        pass

    for tag in RELATION_TAGS:
        rel_root = pkg_elem.find(f'rpm:{tag}', NS)
        if rel_root is not None:
            for entry in rel_root.findall('rpm:entry', NS):
                insert_relation(cursor, pkgid, tag, entry)

def process_file(db_cursor, file_path):
    print(f"Parsing: {file_path}")
    try:
        tree = open_xml(file_path)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return 0

        
    root = tree.getroot()
    count = 0

    total = root.attrib['packages']

    for pkg in root.findall('{http://linux.duke.edu/metadata/common}package'):
        insert_package(db_cursor, pkg)
        count += 1
    return count

def main():
    base_path = "/var/cache/libdnf5"
    if not os.path.exists(base_path):
        print(f"Path {base_path} does not exist.")
        sys.exit(1)

    db_file = "repo_metadata_full.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    create_schema(cur)

    total = 0
    for rootdir, _, files in os.walk(base_path):
        for filename in files:
            if fnmatch.fnmatch(filename, '*primary.xml*'):
                fullpath = os.path.join(rootdir, filename)
                count = process_file(cur, fullpath)
                total += count
                conn.commit()

    conn.close()
    print(f"[✓] Created SQLite database '{db_file}' with {total} packages.")

if __name__ == '__main__':
    main()
