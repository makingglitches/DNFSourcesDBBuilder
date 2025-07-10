CREATE TABLE packages (
    repo           TEXT,
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
    PRIMARY KEY (
        repo,
        pkgid
    )
);