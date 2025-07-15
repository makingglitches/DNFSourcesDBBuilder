-- repo definition

CREATE TABLE repo (
    repo_full_name     TEXT,  -- full name including source
    repo_name          TEXT,  -- general name for sorting or grouping
    repo_uuid          TEXT,  -- uuid generated from url... possibly my addition
    primaryxmlfilename TEXT,
    path               TEXT,
    is_source_repo     INTEGER DEFAULT (0),
    PRIMARY KEY (
        repo_uuid
    )
);


-- packages definition

CREATE TABLE packages (
    type           TEXT,
    repo_uuid      TEXT    REFERENCES repo (repo_uuid),
    pkgid          TEXT,
    name           TEXT,
    arch           TEXT,
    version        TEXT,
    [release]      TEXT,
    epoch          TEXT,
    summary        TEXT,
    description    TEXT,
    packager       TEXT,
    url            TEXT,
    time_file      TEXT,
    time_build     TEXT,
    size_package   INTEGER,
    size_installed INTEGER,
    size_archive   INTEGER,
    location       TEXT,
    license        TEXT,
    vendor         TEXT,
    [group]        TEXT,
    buildhost      TEXT,
    header_start   INTEGER,
    header_end     INTEGER,
    checksum_type  TEXT,
    checksum_pkgid TEXT,
    checksum       TEXT,
    PRIMARY KEY (
        repo_uuid, pkgid
    )
);

-- provides definition

CREATE TABLE provides (
     pkgid     TEXT,
    repo_uuid TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid,
        repo_uuid
    )
    REFERENCES packages (pkgid,
    repo_uuid) 
);

-- recommends definition

CREATE TABLE recommends (
       pkgid     TEXT,
    repo_uuid TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid,
        repo_uuid
    )
    REFERENCES packages (pkgid,
    repo_uuid) 
);

-- requires definition

CREATE TABLE requires(
    pkgid     TEXT,
    repo_uuid TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid,
        repo_uuid
    )
    REFERENCES packages (pkgid,
    repo_uuid) 
);

-- suggests definition

CREATE TABLE suggests (
    pkgid     TEXT,
    repo_uuid TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid,
        repo_uuid
    )
    REFERENCES packages (pkgid,
    repo_uuid) 
);


-- conflicts definition

CREATE TABLE conflicts (
    pkgid     TEXT,
    repo_uuid TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid,
        repo_uuid
    )
    REFERENCES packages (pkgid,
    repo_uuid) 
);


-- obsoletes definition

CREATE TABLE obsoletes (
    pkgid     TEXT,
    repo_uuid TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid,
        repo_uuid
    )
    REFERENCES packages (pkgid,
    repo_uuid) 
);

-- supplements

CREATE TABLE supplements (
    pkgid     TEXT,
    repo_uuid TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid,
        repo_uuid
    )
    REFERENCES packages (pkgid,
    repo_uuid) 
);

-- enhances

CREATE TABLE enhances (
    pkgid     TEXT,
    repo_uuid TEXT,
    name      TEXT,
    version   TEXT,
    [release] TEXT,
    epoch     INTEGER,
    flags     TEXT,
    FOREIGN KEY (
        pkgid,
        repo_uuid
    )
    REFERENCES packages (pkgid,
    repo_uuid) 
);
