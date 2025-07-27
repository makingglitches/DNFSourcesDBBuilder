 insert into installed(
        epoch,
        name,
        version,
        release_ver,
        arch,
        repo
    )
    VALUES
    (
        :epoch, 
        :name,
        :version,
        :release,
        :arch,
        :repo
    )