CREATE TABLE IF NOT EXISTS :tag (
                pkgid TEXT,
                name TEXT,
                pre BOOLEAN,
                flags TEXT,
                FOREIGN KEY(pkgid) REFERENCES packages(pkgid)
            )