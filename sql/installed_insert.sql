 insert into installed(
        epoch,
        name,
        version,
        release,
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