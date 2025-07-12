-- repo definition

CREATE TABLE repo (repo_name TEXT, repo_uuid TEXT, primaryxmlfilename TEXT, PRIMARY KEY (repo_name, repo_uuid));


-- packages definition

CREATE TABLE packages (type TEXT, repo_name TEXT, repo_uuid TEXT, pkgid TEXT, name TEXT, arch TEXT, version TEXT, "release" TEXT, epoch TEXT, summary TEXT, description TEXT, packager TEXT, url TEXT, time_file TEXT, time_build TEXT, size_package INTEGER, size_installed INTEGER, size_archive INTEGER, location TEXT, license TEXT, vendor TEXT, "group" TEXT, buildhost TEXT, header_start INTEGER, header_end INTEGER, checksum_type TEXT, checksum_pkgid TEXT, checksum TEXT, PRIMARY KEY (repo_name, repo_uuid, pkgid), FOREIGN KEY (repo_name, repo_uuid) REFERENCES Repo (repo_name, repo_uuid));


-- provides definition

CREATE TABLE provides (
    pkgid     TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid
    )
    REFERENCES packages (pkgid) 
);


-- recommends definition

CREATE TABLE recommends (
    pkgid     TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid
    )
    REFERENCES packages (pkgid) 
);


-- requires definition

CREATE TABLE requires (pkgid TEXT, name TEXT, version TEXT, "release" TEXT, epoch INTEGER, flags TEXT, FOREIGN KEY (pkgid) REFERENCES packages (pkgid));


-- suggests definition

CREATE TABLE suggests (
    pkgid     TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid
    )
    REFERENCES packages (pkgid) 
);


-- conflicts definition

CREATE TABLE conflicts (
    pkgid     TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid
    )
    REFERENCES packages (pkgid) 
);


-- obsoletes definition

CREATE TABLE obsoletes (
    pkgid     TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid
    )
    REFERENCES packages (pkgid) 
);